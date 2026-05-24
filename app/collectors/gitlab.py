import httpx

HEADERS = {"User-Agent": "OSINT-MVP/1.0"}

async def collect_gitlab(username: str) -> dict:
    url = f"https://gitlab.com/api/v4/users?username={username}"
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return {"source": "gitlab", "found": False, "error": f"HTTP {r.status_code}"}
            data = r.json()
            if not data:
                return {"source": "gitlab", "found": False}
            user = data[0]
            return {
                "source": "gitlab",
                "found": True,
                "url": user.get("web_url"),
                "name": user.get("name"),
                "bio": user.get("bio"),
                "avatar": user.get("avatar_url"),
                "created_at": user.get("created_at"),
                "website": user.get("website_url"),
                "location": user.get("location"),
            }
    except Exception as e:
        return {"source": "gitlab", "found": False, "error": str(e)}
