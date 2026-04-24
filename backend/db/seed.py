"""Seed initial data — run once after alembic upgrade head."""

import asyncio
from .session import AsyncSessionLocal
from .queries import create_team, get_teams, get_settings


SEED_TEAMS = [
    {"name": "FC Northside", "code": "FCN", "color": "#7ab8e0"},
    {"name": "Lakeside Park", "code": "LKP", "color": "#6ee7b7"},
    {"name": "Riverside United", "code": "RVU", "color": "#fbbf24"},
    {"name": "Eastbank FC", "code": "EBK", "color": "#f87171"},
]


async def seed():
    async with AsyncSessionLocal() as db:
        existing = await get_teams(db)
        existing_names = {t.name for t in existing}
        for t in SEED_TEAMS:
            if t["name"] not in existing_names:
                await create_team(db, **t)
                print(f"  + team: {t['name']}")
        # Ensure singleton settings row exists
        await get_settings(db)
        print("  + user_settings singleton")


if __name__ == "__main__":
    asyncio.run(seed())
