import sys
import asyncio


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())




from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db

from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.users.users_router import router as users_router
from app.api.v1.documents.documents_router import router as documents_router
from app.api.v1.ai.ai_chat_router import router as ai_chat_router
from app.api.v1.workspaces.workspace_router import router as workspace_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

frontend_dir = Path(__file__).resolve().parent / "frontend"
app.mount(
    "/static",
    StaticFiles(directory=frontend_dir),
    name="static",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
)

app.include_router(users_router)
app.include_router(workspace_router)
app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])

app.include_router(ai_chat_router)

@app.get("/", include_in_schema=False)
async def frontend():
    return FileResponse(frontend_dir / "index.html")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": f"{settings.APP_NAME} API is running"
    }


@app.get("/health/db")
async def database_health_check(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("SELECT 1;"))
    value = result.scalar()
    return {
        "status": "ok",
        "data": value
    }

