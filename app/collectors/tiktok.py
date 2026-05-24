import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

async def collect_tiktok(username: str) -> dict:
    url = f"https://www.tiktok.com/@{username}"
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code == 404:
                return {"source": "tiktok", "found": False}
            if r.status_code == 200:
                return {
                    "source": "tiktok",
                    "found": True,
                    "url": url,
                    "confidence": "low",
                    "note": "JS-render: brauzerda qo'lda tekshiring",
                }
            return {"source": "tiktok", "found": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "tiktok", "found": False, "error": str(e)}
