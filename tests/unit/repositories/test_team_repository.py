import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.db import Base
from app.core.exceptions import TeamAlreadyExistsError, TeamNotFoundError
from app.models import Team, User
from app.repositories import TeamRepository
from app.schemas import TeamMember, TeamWithMembers

# ---------- БАЗОВЫЕ FIXTURE’Ы ДЛЯ БД ----------

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
def repo(session: AsyncSession) -> TeamRepository:
    return TeamRepository(session)


@pytest.mark.asyncio
async def test_create_team_with_members_creates_team_and_users(
    repo: TeamRepository, session: AsyncSession
):
    team_in = TeamWithMembers(
        team_name="team-alpha",
        members=[
            TeamMember(user_id="1", username="alice", is_active=True),
            TeamMember(user_id="2", username="bob", is_active=False),
        ],
    )

    team = await repo.create_team_with_members(team_in)

    assert isinstance(team, Team)
    assert team.name == "team-alpha"

    db_team = await session.get(Team, "team-alpha")
    assert db_team is not None
    assert db_team.name == "team-alpha"

    result = await session.execute(select(User).order_by(User.id))
    users = result.scalars().all()

    assert len(users) == 2
    assert {u.username for u in users} == {"alice", "bob"}
    assert {u.id for u in users} == {"1", "2"}
    assert all(u.team_name == "team-alpha" for u in users)


@pytest.mark.asyncio
async def test_create_team_with_members_raises_if_team_already_exists(
    repo: TeamRepository, session: AsyncSession
):
    existing_team = Team(name="existing-team")
    session.add(existing_team)
    await session.commit()

    team_in = TeamWithMembers(
        team_name="existing-team",
        members=[],
    )

    with pytest.raises(TeamAlreadyExistsError):
        await repo.create_team_with_members(team_in)


@pytest.mark.asyncio
async def test_create_team_with_members_updates_existing_users(
    repo: TeamRepository, session: AsyncSession
):
    existing_team = Team(name="old-team")
    session.add(existing_team)
    await session.commit()

    existing_user = User(
        id="1",
        username="old-name",
        is_active=False,
        team_name="old-team",
    )
    session.add(existing_user)
    await session.commit()

    team_in = TeamWithMembers(
        team_name="new-team",
        members=[
            TeamMember(user_id="1", username="new-name", is_active=True),
        ],
    )

    await repo.create_team_with_members(team_in)

    user_from_db = await session.get(User, "1")
    assert user_from_db is not None
    assert user_from_db.username == "new-name"
    assert user_from_db.is_active is True
    assert user_from_db.team_name == "new-team"

    team_from_db = await session.get(Team, "new-team")
    assert team_from_db is not None


@pytest.mark.asyncio
async def test_get_team_with_members_returns_team_and_users(
    repo: TeamRepository, session: AsyncSession
):
    team_in = TeamWithMembers(
        team_name="team-with-members",
        members=[
            TeamMember(user_id="1", username="alice", is_active=True),
            TeamMember(user_id="2", username="bob", is_active=False),
        ],
    )
    await repo.create_team_with_members(team_in)

    team = await repo.get_team_with_members("team-with-members")

    assert isinstance(team, Team)
    assert team.name == "team-with-members"

    assert hasattr(team, "users")
    assert len(team.users) == 2
    usernames = {u.username for u in team.users}
    assert usernames == {"alice", "bob"}


@pytest.mark.asyncio
async def test_get_team_with_members_raises_if_not_found(repo: TeamRepository):
    with pytest.raises(TeamNotFoundError):
        await repo.get_team_with_members("non-existing-team")
