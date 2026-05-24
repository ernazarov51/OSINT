import re
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

async def collect_pinterest(username: str) -> dict:
    url = f"https://www.pinterest.com/{username}/"
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code == 404:
                return {"source": "pinterest", "found": False}
            if r.status_code != 200:
                return {"source": "pinterest", "found": False, "error": f"HTTP {r.status_code}"}

            text = r.text
            title_m = re.search(r'og:title[^>]+content="([^"]+)"', text)
            og_title = title_m.group(1) if title_m else ""

            if username.lower() not in og_title.lower():
                return {"source": "pinterest", "found": False}

            return {
                "source": "pinterest",
                "found": True,
                "url": url,
                "name": og_title.split("(")[0].strip() or None,
            }
    except Exception as e:
        return {"source": "pinterest", "found": False, "error": str(e)}
