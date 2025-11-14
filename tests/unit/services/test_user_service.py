from unittest.mock import AsyncMock

import pytest

from app.models.pull_requests import PRStatus
from app.schemas import PullRequestShort, UserFull, UserReviewPRs
from app.services import UserService


class DummyUser:
    def __init__(self, id: str, username: str, team_name: str | None, is_active: bool):
        self.id = id
        self.username = username
        self.team_name = team_name
        self.is_active = is_active


class DummyPullRequest:
    def __init__(self, id: str, title: str, author_id: str, status: PRStatus):
        self.id = id
        self.title = title
        self.author_id = author_id
        self.status = status


@pytest.fixture
def repo_mock_user() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repo_mock_pull_request() -> AsyncMock:
    return AsyncMock()


def test_map_user_model():
    user = DummyUser(id="u1", username="Alice", team_name="backend", is_active=True)

    result = UserService._map_user_model(user)

    assert isinstance(result, UserFull)
    assert result.user_id == "u1"
    assert result.username == "Alice"
    assert result.team_name == "backend"
    assert result.is_active is True


def test_map_user_model_without_team():
    user = DummyUser(id="u2", username="Bob", team_name=None, is_active=False)

    result = UserService._map_user_model(user)

    assert result.user_id == "u2"
    assert result.username == "Bob"
    assert result.team_name is None
    assert result.is_active is False


def test_map_pr_model():
    pr = DummyPullRequest(
        id="pr-1001",
        title="Add search",
        author_id="u1",
        status=PRStatus.OPEN,
    )

    result = UserService._map_pr_model(pr)

    assert isinstance(result, PullRequestShort)
    assert result.pull_request_id == "pr-1001"
    assert result.pull_request_name == "Add search"
    assert result.author_id == "u1"
    assert result.status == PRStatus.OPEN


@pytest.mark.asyncio
async def test_set_is_active_uses_repo_and_maps_result(
    repo_mock_user: AsyncMock, repo_mock_pull_request: AsyncMock
):
    service = UserService(repo_mock_user, repo_mock_pull_request)

    user_model = DummyUser(
        id="u1",
        username="Alice",
        team_name="backend",
        is_active=False,
    )

    repo_mock_user.set_is_active.return_value = user_model

    result = await service.set_is_active(user_id="u1", is_active=False)

    repo_mock_user.set_is_active.assert_awaited_once_with("u1", False)

    assert isinstance(result, UserFull)
    assert result.user_id == "u1"
    assert result.username == "Alice"
    assert result.team_name == "backend"
    assert result.is_active is False


@pytest.mark.asyncio
async def test_get_review_pull_requests_uses_repo_and_maps_result(
    repo_mock_user: AsyncMock, repo_mock_pull_request: AsyncMock
):
    service = UserService(repo_mock_user, repo_mock_pull_request)

    pr1 = DummyPullRequest(
        id="pr-1001",
        title="Add search",
        author_id="u1",
        status=PRStatus.OPEN,
    )
    pr2 = DummyPullRequest(
        id="pr-1002",
        title="Fix bug",
        author_id="u3",
        status=PRStatus.MERGED,
    )

    repo_mock_user.get_user_review_pull_requests.return_value = [pr1, pr2]

    result = await service.get_review_pull_requests(user_id="u2")

    repo_mock_user.get_user_review_pull_requests.assert_awaited_once_with("u2")

    assert isinstance(result, UserReviewPRs)
    assert result.user_id == "u2"
    assert len(result.pull_requests) == 2

    r1, r2 = result.pull_requests
    assert isinstance(r1, PullRequestShort)
    assert r1.pull_request_id == "pr-1001"
    assert r1.pull_request_name == "Add search"
    assert r1.author_id == "u1"
    assert r1.status == PRStatus.OPEN

    assert r2.pull_request_id == "pr-1002"
    assert r2.pull_request_name == "Fix bug"
    assert r2.author_id == "u3"
    assert r2.status == PRStatus.MERGED


@pytest.mark.asyncio
async def test_get_review_pull_requests_empty_list(
    repo_mock_user: AsyncMock, repo_mock_pull_request: AsyncMock
):
    service = UserService(repo_mock_user, repo_mock_pull_request)

    repo_mock_user.get_user_review_pull_requests.return_value = []

    result = await service.get_review_pull_requests(user_id="u2")

    repo_mock_user.get_user_review_pull_requests.assert_awaited_once_with("u2")
    assert isinstance(result, UserReviewPRs)
    assert result.user_id == "u2"
    assert result.pull_requests == []
