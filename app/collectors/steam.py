import re
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

async def collect_steam(username: str) -> dict:
    url = f"https://steamcommunity.com/id/{username}"
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return {"source": "steam", "found": False, "error": f"HTTP {r.status_code}"}

            text = r.text
            title_m = re.search(r'og:title"\s+content="([^"]+)"', text)
            og_title = title_m.group(1) if title_m else ""

            if "error" in og_title.lower() or "could not be found" in text.lower():
                return {"source": "steam", "found": False}

            return {
                "source": "steam",
                "found": True,
                "url": url,
                "name": og_title.replace("Steam Community :: ", "").strip() or None,
            }
    except Exception as e:
        return {"source": "steam", "found": False, "error": str(e)}
