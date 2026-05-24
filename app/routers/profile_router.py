import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..collectors import ALL_COLLECTORS
from ..collectors.web_footprint import collect_web_footprint
from ..lookup.holehe_check import holehe_check
from ..lookup.email_lookup import lookup_email
from ..db import get_db
from ..models import SearchHistory, User
from ..auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


def _extract_pivots(collector_results: list[dict]) -> dict:
    emails: list[str]    = []
    phones: list[str]    = []
    locations: list[str] = []
    names: list[str]     = []
    urls: list[str]      = []

    seen_emails    = set()
    seen_phones    = set()
    seen_locations = set()
    seen_names     = set()

    for r in collector_results:
        if not r.get("found"):
            continue

        email = r.get("email")
        if email and email not in seen_emails:
            seen_emails.add(email)
            emails.append(email)

        phone = r.get("phone")
        if phone and phone not in seen_phones:
            seen_phones.add(phone)
            phones.append(phone)

        for loc_key in ("location", "country", "city", "region"):
            loc = r.get(loc_key)
            if loc and loc not in seen_locations:
                seen_locations.add(loc)
                locations.append(loc)
                break

        for name_key in ("name", "full_name", "display_name"):
            name = r.get(name_key)
            if name and name not in seen_names:
                seen_names.add(name)
                names.append(name)
                break

        url = r.get("url")
        if url:
            urls.append(url)

    return {
        "emails": emails,
        "phones": phones,
        "locations": locations,
        "names": names,
        "urls": urls,
    }


@router.get("")
async def build_profile(
    username: str = Query(..., min_length=1, max_length=50),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    username = username.strip()

    collector_tasks = [c(username) for c in ALL_COLLECTORS] + [collect_web_footprint(username)]
    raw = await asyncio.gather(*collector_tasks, return_exceptions=True)

    collector_results = [
        r if not isinstance(r, Exception) else {"found": False, "error": str(r)}
        for r in raw
    ]

    pivots = _extract_pivots(collector_results)

    email_details: list[dict] = []
    holehe_results: list[dict] = []

    if pivots["emails"]:
        email_tasks   = [lookup_email(em) for em in pivots["emails"]]
        holehe_tasks  = [holehe_check(em) for em in pivots["emails"]]
        email_raw, holehe_raw = await asyncio.gather(
            asyncio.gather(*email_tasks,  return_exceptions=True),
            asyncio.gather(*holehe_tasks, return_exceptions=True),
        )
        for r in email_raw:
            if not isinstance(r, Exception):
                email_details.append(r)
        for r in holehe_raw:
            if not isinstance(r, Exception):
                holehe_results.append(r)

    social_found = [r for r in collector_results if r.get("found") and r.get("source") != "web_footprint"]
    web_result   = next((r for r in collector_results if r.get("source") == "web_footprint"), {})

    profile = {
        "username": username,
        "summary": {
            "social_found": len(social_found),
            "social_checked": len(ALL_COLLECTORS),
            "web_mentions": web_result.get("total", 0),
            "emails_found": len(pivots["emails"]),
            "names": pivots["names"],
            "locations": pivots["locations"],
        },
        "pivots": pivots,
        "social": sorted(collector_results, key=lambda x: (not x.get("found"), x.get("source", ""))),
        "web_footprint": web_result.get("hits", []),
        "email_details": email_details,
        "holehe": holehe_results,
    }

    if current_user:
        record = SearchHistory(
            user_id=current_user.id,
            search_type="profile",
            query=username,
            result=json.dumps(profile, ensure_ascii=False),
        )
        db.add(record)
        await db.commit()

    return profile
