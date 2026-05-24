import asyncio
import hashlib
import re

import dns.resolver
import httpx

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com", "throwaway.email",
    "yopmail.com", "sharklasers.com", "grr.la", "10minutemail.com",
    "trashmail.com", "dispostable.com", "maildrop.cc",
}

CATCHALL_PROVIDERS = {
    "gmail.com", "googlemail.com",
    "yahoo.com", "yahoo.co.uk", "yahoo.fr",
    "outlook.com", "hotmail.com", "live.com", "msn.com",
    "icloud.com", "me.com", "mac.com",
    "protonmail.com", "pm.me",
    "mail.ru", "yandex.ru", "yandex.com",
}

def _mx_records(domain: str) -> list[str]:
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return sorted(str(r.exchange).rstrip(".") for r in answers)
    except Exception:
        return []

async def _smtp_verify(email: str, mx_host: str) -> dict:
    """
    SMTP RCPT TO orqali email mavjudligini tekshiradi.
    Returns: {result, code, note}
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(mx_host, 25),
            timeout=8,
        )

        async def recv_line():
            return (await asyncio.wait_for(reader.readline(), timeout=6)).decode(errors="ignore")

        async def recv_full():
            lines = []
            while True:
                line = await recv_line()
                lines.append(line)
                if len(line) < 4 or line[3] != "-":
                    break
            return "".join(lines)

        await recv_full()

        writer.write(b"EHLO osint-check.local\r\n")
        await writer.drain()
        await recv_full()

        writer.write(b"MAIL FROM: <check@osint-check.local>\r\n")
        await writer.drain()
        mail_resp = await recv_line()

        writer.write(f"RCPT TO: <{email}>\r\n".encode())
        await writer.drain()
        rcpt_resp = await recv_line()

        try:
            writer.write(b"QUIT\r\n")
            await writer.drain()
        except Exception:
            pass
        writer.close()

        code = int(rcpt_resp[:3]) if rcpt_resp[:3].isdigit() else 0

        if code == 250 or code == 251:
            return {"result": "possible", "code": code,
                    "note": "Server qabul qildi"}
        elif code in (550, 551, 553, 554):
            return {"result": "rejected", "code": code,
                    "note": f"Server rad etdi ({code}) — lekin bu spam-himoya ham bo'lishi mumkin"}
        elif code in (450, 451, 452):
            return {"result": "unknown", "code": code,
                    "note": f"Vaqtinchalik rad ({code}) — keyinroq urinib ko'ring"}
        else:
            return {"result": "unknown", "code": code,
                    "note": f"Noaniq javob: {rcpt_resp.strip()}"}

    except asyncio.TimeoutError:
        return {"result": "unknown", "note": "Server javob bermadi (timeout)"}
    except ConnectionRefusedError:
        return {"result": "unknown", "note": "Port 25 yopiq yoki bloklanagan"}
    except Exception as e:
        return {"result": "unknown", "note": str(e)}

async def _check_gravatar(email: str) -> dict:
    h = hashlib.md5(email.lower().strip().encode()).hexdigest()
    url = f"https://www.gravatar.com/avatar/{h}?d=404"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url)
            if r.status_code == 200:
                return {"has_gravatar": True,
                        "gravatar_url": f"https://www.gravatar.com/avatar/{h}?s=200"}
    except Exception:
        pass
    return {"has_gravatar": False}

async def _check_emailrep(email: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=6, headers={"User-Agent": "OSINT-MVP/1.0"}) as client:
            r = await client.get(f"https://emailrep.io/{email}")
            if r.status_code == 200:
                d = r.json()
                det = d.get("details", {})
                return {
                    "reputation": d.get("reputation"),
                    "is_suspicious": d.get("suspicious"),
                    "is_disposable": det.get("disposable"),
                    "is_free_provider": det.get("free_provider"),
                    "profiles": det.get("profiles", []),
                    "first_seen": det.get("first_seen"),
                    "last_seen": det.get("last_seen"),
                }
    except Exception:
        pass
    return {}

async def lookup_email(address: str) -> dict:
    address = address.strip().lower()

    if not EMAIL_RE.match(address):
        return {"found": False, "error": "Noto'g'ri email format"}

    domain = address.split("@")[1]

    mx = await asyncio.get_event_loop().run_in_executor(None, _mx_records, domain)
    gravatar, emailrep = await asyncio.gather(
        _check_gravatar(address),
        _check_emailrep(address),
    )

    result = {
        "email": address,
        "domain": domain,
        "domain_has_mx": bool(mx),
        "mx_records": mx,
        "is_disposable_domain": domain in DISPOSABLE_DOMAINS,
    }
    result.update(gravatar)
    result.update(emailrep)

    if not mx:
        result["smtp"] = {"result": "unknown", "note": "MX yozuvi yo'q — domen pochta qabul qilmaydi"}
    elif domain in CATCHALL_PROVIDERS:
        result["smtp"] = {
            "result": "unverifiable",
            "note": f"{domain} barcha manzillarni qabul qiladi — SMTP orqali tekshirib bo'lmaydi",
        }
    else:
        result["smtp"] = await _smtp_verify(address, mx[0])

    smtp_res = result["smtp"].get("result")
    has_gravatar = result.get("has_gravatar", False)
    has_profiles = bool(result.get("profiles")) or bool(result.get("first_seen"))
    has_evidence = has_gravatar or has_profiles

    if not mx:
        result["found"] = False
        result["existence"] = "mavjud emas (domen pochta qabul qilmaydi)"
    elif has_evidence:
        result["found"] = True
        evidence = []
        if has_gravatar:   evidence.append("Gravatar")
        if has_profiles:   evidence.append("profillar/bazalar")
        result["existence"] = f"mavjud — dalil: {', '.join(evidence)}"
    elif smtp_res == "possible":
        result["found"] = True
        result["existence"] = "ehtimol mavjud (SMTP 250)"
    elif smtp_res == "rejected":
        result["found"] = None
        result["existence"] = "noaniq (SMTP rad etdi, lekin bu spam-himoya bo'lishi mumkin)"
    elif smtp_res == "unverifiable":
        result["found"] = None
        result["existence"] = "tekshirib bo'lmadi (yirik provayder catch-all ishlatadi)"
    else:
        result["found"] = None
        result["existence"] = "noaniq (server javob bermadi)"

    return result
