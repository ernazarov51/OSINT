import asyncio
import importlib
import inspect
import pkgutil

import httpx
import holehe.modules as hm

def _load_all_functions():
    funcs = []
    for _, cat, ispkg in pkgutil.iter_modules(hm.__path__):
        if not ispkg:
            continue
        cat_mod = importlib.import_module(f"holehe.modules.{cat}")
        for _, site, _ in pkgutil.iter_modules(cat_mod.__path__):
            site_mod = importlib.import_module(f"holehe.modules.{cat}.{site}")
            for name, obj in inspect.getmembers(site_mod, inspect.iscoroutinefunction):
                if name == site:
                    funcs.append((cat, name, obj))
                    break
    return funcs

ALL_FUNCS = _load_all_functions()

async def holehe_check(email: str) -> dict:
    out: list[dict] = []
    client = httpx.AsyncClient(timeout=15)

    tasks = [func(email, client, out) for _, _, func in ALL_FUNCS]
    await asyncio.gather(*tasks, return_exceptions=True)

    try:
        await client.aclose()
    except Exception:
        pass

    found = []
    not_found = []
    rate_limited = []

    for item in out:
        if item.get("rateLimit"):
            rate_limited.append(item["name"])
        elif item.get("exists"):
            entry = {
                "site": item["name"],
                "domain": item.get("domain"),
            }
            if item.get("emailrecovery"):
                entry["email_recovery"] = item["emailrecovery"]
            if item.get("phoneNumber"):
                entry["phone"] = item["phoneNumber"]
            if item.get("others"):
                entry["extra"] = item["others"]
            found.append(entry)
        else:
            not_found.append(item["name"])

    return {
        "email": email,
        "total_checked": len(out),
        "total_found": len(found),
        "total_rate_limited": len(rate_limited),
        "found_on": found,
        "rate_limited": rate_limited,
    }
