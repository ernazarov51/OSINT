import httpx

HEADERS = {"User-Agent": "OSINT-MVP/1.0"}

async def collect_hackernews(username: str) -> dict:
    url = f"https://hacker-news.firebaseio.com/v0/user/{username}.json"
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return {"source": "hackernews", "found": False, "error": f"HTTP {r.status_code}"}
            data = r.json()
            if data is None:
                return {"source": "hackernews", "found": False}
            return {
                "source": "hackernews",
                "found": True,
                "url": f"https://news.ycombinator.com/user?id={username}",
                "karma": data.get("karma"),
                "about": data.get("about"),
                "created_at": str(data.get("created")),
            }
    except Exception as e:
        return {"source": "hackernews", "found": False, "error": str(e)}
