from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.engine import URL

Base = declarative_base()

db_url = URL.create(
    drivername="postgresql+asyncpg",
    username="postgres.ojmkdcjgvvvsauvyjkxa",
    password="msSPb85iHvLboOM7",
    host="aws-0-ap-southeast-2.pooler.supabase.com",
    port=6543,
    database="postgres",
    query={"prepared_statement_cache_size": "0"}
)

engine = create_async_engine(db_url, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=True
)

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
