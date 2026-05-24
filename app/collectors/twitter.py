import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

async def collect_twitter(username: str) -> dict:
    url = f"https://x.com/{username}"
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code == 404:
                return {"source": "twitter_x", "found": False}
            if r.status_code == 200:
                return {
                    "source": "twitter_x",
                    "found": True,
                    "url": url,
                    "confidence": "low",
                    "note": "JS-render: brauzerda qo'lda tekshiring",
                }
            return {"source": "twitter_x", "found": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "twitter_x", "found": False, "error": str(e)}
