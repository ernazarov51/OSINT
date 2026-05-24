import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

async def collect_youtube(username: str) -> dict:
    url = f"https://www.youtube.com/@{username}"
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code == 404:
                return {"source": "youtube", "found": False}
            if r.status_code == 200:
                not_found = "404 not found" in r.text.lower() or \
                            "this page isn't available" in r.text.lower()
                if not_found:
                    return {"source": "youtube", "found": False}
                return {
                    "source": "youtube",
                    "found": True,
                    "url": url,
                }
            return {"source": "youtube", "found": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "youtube", "found": False, "error": str(e)}
