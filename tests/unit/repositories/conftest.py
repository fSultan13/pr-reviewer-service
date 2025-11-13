import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.db import Base
from app.repositories import TeamRepository, UserRepository

TEST_DATABASE_URL = settings.get_async_database_test_uri


@pytest_asyncio.fixture
async def engine():
    """
    Отдельный AsyncEngine на каждый тест.
    На нём же мы чистим схему (drop_all/create_all).
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)

    async with engine.begin() as conn:
        # на всякий случай полностью пересоздаём схему
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncSession:
    """
    AsyncSession для теста.
    Никаких DELETE FROM вручную — схему уже почистили выше.
    """
    async_session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with async_session_maker() as session:
        yield session
        # откатываем всё незакоммиченное (на всякий случай)
        await session.rollback()


@pytest.fixture
def team_repo(session: AsyncSession) -> TeamRepository:
    return TeamRepository(session)


@pytest.fixture
def user_repo(session: AsyncSession) -> UserRepository:
    return UserRepository(session)
