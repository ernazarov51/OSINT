import asyncio
from ddgs import DDGS

DORK_PATTERNS = [
    '"{username}"',
    '"{username}" site:t.me',
    '"{username}" site:olx.uz OR site:olx.kz OR site:avito.ru',
    '"{username}" forum OR muhokama OR elonlar OR объявления',
]


def _ddg_search(query: str, max_results: int = 5) -> list[dict]:
    try:
        results = DDGS().text(query, max_results=max_results)
        return [
            {
                "title":   r.get("title", ""),
                "url":     r.get("href", ""),
                "snippet": r.get("body", ""),
                "query":   query,
            }
            for r in (results or [])
            if r.get("href")
        ]
    except Exception:
        return []


async def collect_web_footprint(username: str) -> dict:
    loop = asyncio.get_event_loop()

    tasks = [
        loop.run_in_executor(None, _ddg_search, pattern.format(username=username), 5)
        for pattern in DORK_PATTERNS
    ]
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    seen_urls: set[str] = set()
    all_hits: list[dict] = []

    for result in results_nested:
        if isinstance(result, Exception):
            continue
        for hit in result:
            url = hit.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_hits.append(hit)

    return {
        "source": "web_footprint",
        "found": bool(all_hits),
        "total": len(all_hits),
        "hits": all_hits,
    }
