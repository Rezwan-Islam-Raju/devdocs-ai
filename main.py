from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db



app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


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