from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from typing import AsyncGenerator

settings = get_settings()

try:
# Create async engine
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=True,  # Set to False in production
        future=True
    )
    print("Connected to the database successfully!")
except Exception as e:
    print(f"Error: {e}")

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise