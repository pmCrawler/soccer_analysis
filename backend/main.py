"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()  # no-op in containers where env vars are already injected

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.session import engine
from .db.models import Base
from .routers import jobs, teams, settings as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="SoccerCV API", version="0.1.0", lifespan=lifespan)

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
