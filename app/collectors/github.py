import asyncio
import httpx

HEADERS = {"User-Agent": "OSINT-MVP/1.0"}


async def collect_github(username: str) -> dict:
    url = f"https://api.github.com/users/{username}"
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
            user_resp, repos_resp = await asyncio.gather(
                client.get(url),
                client.get(f"https://api.github.com/users/{username}/repos",
                           params={"per_page": 100, "sort": "updated"}),
            )

            if user_resp.status_code == 404:
                return {"source": "github", "found": False}
            if user_resp.status_code != 200:
                return {"source": "github", "found": False,
                        "error": f"HTTP {user_resp.status_code}"}

            data = user_resp.json()

            repos = []
            if repos_resp.status_code == 200:
                for r in repos_resp.json():
                    if r.get("fork"):
                        continue  # skip forks, show only own repos
                    repos.append({
                        "name":        r.get("name"),
                        "description": r.get("description") or "",
                        "url":         r.get("html_url"),
                        "language":    r.get("language"),
                        "stars":       r.get("stargazers_count", 0),
                        "forks":       r.get("forks_count", 0),
                        "topics":      r.get("topics", []),
                        "updated_at":  (r.get("updated_at") or "")[:10],
                    })
                # Sort by stars desc
                repos.sort(key=lambda x: x["stars"], reverse=True)

            return {
                "source":       "github",
                "found":        True,
                "url":          data.get("html_url"),
                "name":         data.get("name"),
                "bio":          data.get("bio"),
                "followers":    data.get("followers"),
                "following":    data.get("following"),
                "public_repos": data.get("public_repos"),
                "avatar":       data.get("avatar_url"),
                "created_at":   (data.get("created_at") or "")[:10],
                "email":        data.get("email"),
                "location":     data.get("location"),
                "blog":         data.get("blog"),
                "company":      data.get("company"),
                "twitter_username": data.get("twitter_username"),
                "repos":        repos,
            }
    except Exception as exc:
        return {"source": "github", "found": False, "error": str(exc)}
