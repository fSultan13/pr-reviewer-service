from unittest.mock import AsyncMock

import pytest

from app.schemas import TeamMember, TeamWithMembers
from app.services import TeamService


class DummyUser:
    def __init__(self, id: str, username: str, is_active: bool = True) -> None:
        self.id = id
        self.username = username
        self.is_active = is_active


class DummyTeam:
    def __init__(self, name: str, users: list[DummyUser]) -> None:
        self.name = name
        self.users = users


@pytest.fixture
def repo_mock() -> AsyncMock:
    repo = AsyncMock()
    return repo


def test_map_team_model_with_members():
    team = DummyTeam(
        name="backend",
        users=[
            DummyUser(id="u1", username="Alice", is_active=True),
            DummyUser(id="u2", username="Bob", is_active=False),
        ],
    )

    result = TeamService._map_team_model(team)

    assert isinstance(result, TeamWithMembers)
    assert result.team_name == "backend"
    assert len(result.members) == 2

    m1, m2 = result.members
    assert isinstance(m1, TeamMember)
    assert m1.user_id == "u1"
    assert m1.username == "Alice"
    assert m1.is_active is True

    assert m2.user_id == "u2"
    assert m2.username == "Bob"
    assert m2.is_active is False


def test_map_team_model_without_members():
    team = DummyTeam(name="empty-team", users=[])

    result = TeamService._map_team_model(team)

    assert result.team_name == "empty-team"
    assert result.members == []


@pytest.mark.asyncio
async def test_create_team_with_members_uses_repo_and_maps_result(repo_mock: AsyncMock):
    service = TeamService(repo_mock)

    input_schema = TeamWithMembers(
        team_name="backend",
        members=[
            TeamMember(user_id="u1", username="Alice", is_active=True),
            TeamMember(user_id="u2", username="Bob", is_active=True),
        ],
    )

    team_model = DummyTeam(
        name="backend",
        users=[
            DummyUser(id="u1", username="Alice", is_active=True),
            DummyUser(id="u2", username="Bob", is_active=True),
        ],
    )

    repo_mock.get_team_with_members.return_value = team_model
    repo_mock.create_team_with_members.return_value = team_model

    result = await service.create_team_with_members(input_schema)

    repo_mock.create_team_with_members.assert_awaited_once_with(input_schema)

    assert isinstance(result, TeamWithMembers)
    assert result.team_name == "backend"
    assert len(result.members) == 2
    assert result.members[0].user_id == "u1"
    assert result.members[1].user_id == "u2"


@pytest.mark.asyncio
async def test_get_team_with_members_uses_repo_and_maps_result(repo_mock: AsyncMock):
    service = TeamService(repo_mock)
    team_name = "backend"

    team_model = DummyTeam(
        name=team_name,
        users=[DummyUser(id="u1", username="Alice", is_active=True)],
    )

    repo_mock.get_team_with_members.return_value = team_model

    result = await service.get_team_with_members(team_name)

    repo_mock.get_team_with_members.assert_awaited_once_with(team_name)

    assert isinstance(result, TeamWithMembers)
    assert result.team_name == team_name
    assert len(result.members) == 1
    assert result.members[0].user_id == "u1"
    assert result.members[0].username == "Alice"
    assert result.members[0].is_active is True
