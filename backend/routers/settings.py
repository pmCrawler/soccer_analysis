"""User settings endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..db import queries
from ..schemas.jobs import UserSettingsOut, UserSettingsUpdate

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=UserSettingsOut)
async def get_settings(db: AsyncSession = Depends(get_db)):
    return await queries.get_settings(db)


@router.put("/settings", response_model=UserSettingsOut)
async def update_settings(body: UserSettingsUpdate, db: AsyncSession = Depends(get_db)):
    return await queries.update_settings(db, **body.model_dump(exclude_none=True))
