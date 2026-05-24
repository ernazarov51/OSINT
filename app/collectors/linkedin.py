import re
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

async def collect_linkedin(username: str) -> dict:
    url = f"https://www.linkedin.com/in/{username}/"
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(url)

            if r.status_code == 404:
                return {"source": "linkedin", "found": False}

            if r.status_code in (999, 429):
                return {"source": "linkedin", "found": False, "error": "LinkedIn bot-himoyasi (qo'lda tekshiring)"}

            if r.status_code != 200:
                return {"source": "linkedin", "found": False, "error": f"HTTP {r.status_code}"}

            text = r.text

            if "profile-not-found" in text or "Page not found" in text:
                return {"source": "linkedin", "found": False}

            title_m = re.search(r'<title>([^<]+)</title>', text)
            og_name = re.search(r'og:title[^>]+content="([^"]+)"', text)
            og_desc = re.search(r'og:description[^>]+content="([^"]+)"', text)
            og_img  = re.search(r'og:image[^>]+content="([^"]+)"', text)

            name = (og_name.group(1) if og_name else None) or (title_m.group(1) if title_m else None)

            if not name or "LinkedIn" == name.strip():
                return {
                    "source": "linkedin",
                    "found": True,
                    "url": url,
                    "confidence": "low",
                    "note": "Sahifa mavjud, lekin login talab qilinadi — brauzerda qo'lda tekshiring",
                }

            return {
                "source": "linkedin",
                "found": True,
                "url": url,
                "name": name,
                "bio": og_desc.group(1) if og_desc else None,
                "avatar": og_img.group(1) if og_img else None,
            }
    except Exception as e:
        return {"source": "linkedin", "found": False, "error": str(e)}
