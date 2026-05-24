import re
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# Generic Telegram logo — means no real profile photo
_GENERIC_PHOTO = "telegram.org/img/t_logo"

# Real CDN domains for profile photos
_CDN_DOMAINS = ("cdn1.telesco.pe", "cdn2.telesco.pe", "cdn3.telesco.pe",
                "cdn4.telesco.pe", "cdn5.telesco.pe", "telegram-cdn.org")


def _meta(text: str, prop: str) -> str | None:
    m = re.search(rf'<meta\s+property="{re.escape(prop)}"\s+content="([^"]*)"', text)
    if not m:
        m = re.search(rf'<meta\s+content="([^"]*)"\s+property="{re.escape(prop)}"', text)
    return m.group(1).strip() if m else None


async def collect_telegram(username: str) -> dict:
    url = f"https://t.me/{username}"
    try:
        async with httpx.AsyncClient(timeout=12, headers=HEADERS,
                                     follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return {"source": "telegram", "found": False,
                        "error": f"HTTP {r.status_code}"}

            text = r.text
            og_title = _meta(text, "og:title") or ""
            og_image = _meta(text, "og:image") or ""
            og_desc  = _meta(text, "og:description") or ""

            # Non-existent user: title is "Telegram: Contact @username"
            if (og_title.startswith("Telegram:") or
                    not og_title or
                    "tgme_page_title" not in text):
                return {"source": "telegram", "found": False}

            # Determine account type
            account_type = "user"
            if re.search(r'tgme_icon_channel|"channel"', text):
                account_type = "channel"
            elif re.search(r'tgme_icon_group|"group"', text):
                account_type = "group"
            elif re.search(r'tgme_icon_bot|"bot"', text):
                account_type = "bot"

            # Subscribers/members count
            subscribers = None
            m = re.search(r'class="tgme_page_extra">([^<]+)<', text)
            if m:
                subscribers = m.group(1).strip()

            # Profile photo — only if it's a real CDN image, not the generic logo
            avatar = None
            photo_public = False
            if og_image and not _GENERIC_PHOTO in og_image:
                if any(cdn in og_image for cdn in _CDN_DOMAINS):
                    avatar = og_image
                    photo_public = True

            result: dict = {
                "source":       "telegram",
                "found":        True,
                "url":          url,
                "name":         og_title,
                "bio":          og_desc or None,
                "account_type": account_type,
                "subscribers":  subscribers,
                "photo_public": photo_public,
            }
            if avatar:
                result["avatar"] = avatar

            return result

    except Exception as exc:
        return {"source": "telegram", "found": False, "error": str(exc)}
