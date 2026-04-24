"""Teams endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..db import queries
from ..schemas.jobs import TeamOut, TeamCreate

router = APIRouter(tags=["teams"])


@router.get("/teams", response_model=list[TeamOut])
async def list_teams(db: AsyncSession = Depends(get_db)):
    return await queries.get_teams(db)


@router.get("/teams/{team_id}", response_model=TeamOut)
async def get_team(team_id: str, db: AsyncSession = Depends(get_db)):
    team = await queries.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("/teams", response_model=TeamOut, status_code=201)
async def create_team(body: TeamCreate, db: AsyncSession = Depends(get_db)):
    return await queries.create_team(db, name=body.name, code=body.code, color=body.color)
