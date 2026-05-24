import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from .collectors import ALL_COLLECTORS
from .lookup import lookup_ip, lookup_phone, lookup_image, holehe_check
from .lookup.email_lookup import lookup_email
from .db import get_db, init_db
from .models import SearchHistory, User
from .auth import get_current_user
from .routers.auth_router import router as auth_router
from .routers.history_router import router as history_router
from .routers.profile_router import router as profile_router
from .routers.ai_router import router as ai_router

STATIC_DIR = Path(__file__).parent.parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="OSINT MVP", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(profile_router)
app.include_router(ai_router)

async def _save(db: AsyncSession, user: User, search_type: str, query: str, result: dict):
    record = SearchHistory(
        user_id=user.id,
        search_type=search_type,
        query=query,
        result=json.dumps(result, ensure_ascii=False),
    )
    db.add(record)
    await db.commit()

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))

@app.get("/search")
async def search(
    username: str = Query(..., min_length=1, max_length=50),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    username = username.strip()
    raw = await asyncio.gather(
        *[c(username) for c in ALL_COLLECTORS],
        return_exceptions=True,
    )
    results = [
        r if not isinstance(r, Exception) else {"found": False, "error": str(r)}
        for r in raw
    ]
    response = {
        "username": username,
        "total_checked": len(results),
        "total_found": sum(1 for r in results if r.get("found")),
        "results": sorted(results, key=lambda x: (not x.get("found"), x.get("source", ""))),
    }
    if current_user:
        await _save(db, current_user, "username", username, response)
    return response

@app.get("/ip")
async def ip_lookup(
    address: str = Query(..., min_length=4),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    address = address.strip()
    result = await lookup_ip(address)
    if current_user:
        await _save(db, current_user, "ip", address, result)
    return result

@app.get("/phone")
async def phone_lookup(
    number: str = Query(..., min_length=4),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    number = number.strip()
    result = await lookup_phone(number)
    if current_user:
        await _save(db, current_user, "phone", number, result)
    return result

@app.get("/image")
async def image_lookup(
    url: str = Query(..., min_length=5),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    url = url.strip()
    result = await lookup_image(url)
    if current_user:
        await _save(db, current_user, "image", url, result)
    return result

@app.get("/holehe")
async def holehe_lookup(
    email: str = Query(..., min_length=5),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    email = email.strip()
    result = await holehe_check(email)
    if current_user:
        await _save(db, current_user, "holehe", email, result)
    return result

@app.get("/email")
async def email_lookup(
    address: str = Query(..., min_length=5),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    address = address.strip()
    result = await lookup_email(address)
    if current_user:
        await _save(db, current_user, "email", address, result)
    return result
