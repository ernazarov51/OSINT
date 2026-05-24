import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import SearchHistory, User
from ..auth import require_user

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/")
async def get_history(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    search_type: str | None = Query(default=None),
):
    q = select(SearchHistory).where(SearchHistory.user_id == user.id)
    if search_type:
        q = q.where(SearchHistory.search_type == search_type)
    q = q.order_by(SearchHistory.searched_at.desc()).limit(limit).offset(offset)

    result = await db.execute(q)
    items = result.scalars().all()

    total_q = select(func.count()).select_from(SearchHistory).where(SearchHistory.user_id == user.id)
    if search_type:
        total_q = total_q.where(SearchHistory.search_type == search_type)
    total = (await db.execute(total_q)).scalar_one()

    return {
        "total": total,
        "items": [
            {
                "id": item.id,
                "search_type": item.search_type,
                "query": item.query,
                "result": json.loads(item.result),
                "searched_at": item.searched_at.isoformat(),
            }
            for item in items
        ],
    }

@router.delete("/{item_id}")
async def delete_history_item(
    item_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SearchHistory).where(
            SearchHistory.id == item_id,
            SearchHistory.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Topilmadi")
    await db.delete(item)
    await db.commit()
    return {"deleted": True}
