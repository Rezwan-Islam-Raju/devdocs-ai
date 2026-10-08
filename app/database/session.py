from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings




Base = declarative_base()

engine = create_async_engine(settings.DATABASE_URL,echo=True)

AsyncSessionLocal = async_sessionmaker(
   bind= engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=True
)



async def get_db():
    async with AsyncSessionLocal() as db:
        yield db











