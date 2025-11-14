import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.models import Team, User
from app.repositories import TeamRepository
from app.schemas import TeamMember, TeamWithMembers


@pytest.mark.asyncio
async def test_create_team_with_members_creates_team_and_users(
    team_repo: TeamRepository, session: AsyncSession
):
    team_in = TeamWithMembers(
        team_name="team-alpha",
        members=[
            TeamMember(user_id="1", username="alice", is_active=True),
            TeamMember(user_id="2", username="bob", is_active=False),
        ],
    )

    team = await team_repo.create_team_with_members(team_in)

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
    team_repo: TeamRepository, session: AsyncSession
):
    existing_team = Team(name="existing-team")
    session.add(existing_team)
    await session.commit()

    team_in = TeamWithMembers(
        team_name="existing-team",
        members=[],
    )

    with pytest.raises(AlreadyExistsError):
        await team_repo.create_team_with_members(team_in)


@pytest.mark.asyncio
async def test_create_team_with_members_updates_existing_users(
    team_repo: TeamRepository, session: AsyncSession
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

    await team_repo.create_team_with_members(team_in)

    user_from_db = await session.get(User, "1")
    assert user_from_db is not None
    assert user_from_db.username == "new-name"
    assert user_from_db.is_active is True
    assert user_from_db.team_name == "new-team"

    team_from_db = await session.get(Team, "new-team")
    assert team_from_db is not None


@pytest.mark.asyncio
async def test_get_team_with_members_returns_team_and_users(
    team_repo: TeamRepository, session: AsyncSession
):
    team_in = TeamWithMembers(
        team_name="team-with-members",
        members=[
            TeamMember(user_id="1", username="alice", is_active=True),
            TeamMember(user_id="2", username="bob", is_active=False),
        ],
    )
    await team_repo.create_team_with_members(team_in)

    team = await team_repo.get_team_with_members("team-with-members")

    assert isinstance(team, Team)
    assert team.name == "team-with-members"

    assert hasattr(team, "users")
    assert len(team.users) == 2
    usernames = {u.username for u in team.users}
    assert usernames == {"alice", "bob"}


@pytest.mark.asyncio
async def test_get_team_with_members_raises_if_not_found(team_repo: TeamRepository):
    with pytest.raises(NotFoundError):
        await team_repo.get_team_with_members("non-existing-team")
