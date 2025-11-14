from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.models.pull_requests import PRStatus
from app.schemas import (
    PullRequestCreatePayload,
    PullRequestFull,
    PullRequestMergePayload,
    PullRequestReassignPayload,
)
from app.services import PullRequestService


class DummyReviewer:
    def __init__(self, reviewer_id: str):
        self.reviewer_id = reviewer_id


class DummyPullRequest:
    def __init__(
        self,
        id: str,
        title: str,
        author_id: str,
        status: PRStatus,
        reviewers: list[DummyReviewer] | None = None,
        merged_at: datetime | None = None,
    ):
        self.id = id
        self.title = title
        self.author_id = author_id
        self.status = status
        self.reviewers = reviewers or []
        self.merged_at = merged_at


@pytest.fixture
def repo_mock_pull_request() -> AsyncMock:
    return AsyncMock()


def test_map_pr_model():
    reviewers = [DummyReviewer("u2"), DummyReviewer("u3")]
    merged_at = datetime(2025, 1, 1, 12, 0, 0)

    pr = DummyPullRequest(
        id="pr-1001",
        title="Add search",
        author_id="u1",
        status=PRStatus.OPEN,
        reviewers=reviewers,
        merged_at=merged_at,
    )

    result = PullRequestService._map_pr_model(pr)

    assert isinstance(result, PullRequestFull)
    assert result.pull_request_id == "pr-1001"
    assert result.pull_request_name == "Add search"
    assert result.author_id == "u1"
    assert result.status == PRStatus.OPEN
    assert result.assigned_reviewers == ["u2", "u3"]
    assert result.mergedAt == merged_at


@pytest.mark.asyncio
async def test_create_pull_request_uses_repo_and_maps_result(
    repo_mock_pull_request: AsyncMock,
):
    service = PullRequestService(repo_mock_pull_request)

    payload = PullRequestCreatePayload(
        pull_request_id="pr-1001",
        pull_request_name="Add search",
        author_id="u1",
    )

    pr_model = DummyPullRequest(
        id="pr-1001",
        title="Add search",
        author_id="u1",
        status=PRStatus.OPEN,
        reviewers=[DummyReviewer("u2"), DummyReviewer("u3")],
    )

    repo_mock_pull_request.create_pull_request.return_value = pr_model

    result = await service.create_pull_request(payload)

    repo_mock_pull_request.create_pull_request.assert_awaited_once_with(
        pr_id="pr-1001",
        title="Add search",
        author_id="u1",
    )

    assert isinstance(result, PullRequestFull)
    assert result.pull_request_id == "pr-1001"
    assert result.pull_request_name == "Add search"
    assert result.author_id == "u1"
    assert result.status == PRStatus.OPEN
    assert result.assigned_reviewers == ["u2", "u3"]


@pytest.mark.asyncio
async def test_merge_pull_request_uses_repo_and_maps_result(
    repo_mock_pull_request: AsyncMock,
):
    service = PullRequestService(repo_mock_pull_request)

    payload = PullRequestMergePayload(pull_request_id="pr-1001")

    merged_at = datetime(2025, 1, 1, 12, 0, 0)

    pr_model = DummyPullRequest(
        id="pr-1001",
        title="Add search",
        author_id="u1",
        status=PRStatus.MERGED,
        reviewers=[DummyReviewer("u2")],
        merged_at=merged_at,
    )

    repo_mock_pull_request.merge_pull_request.return_value = pr_model

    result = await service.merge_pull_request(payload)

    repo_mock_pull_request.merge_pull_request.assert_awaited_once_with("pr-1001")

    assert isinstance(result, PullRequestFull)
    assert result.pull_request_id == "pr-1001"
    assert result.status == PRStatus.MERGED
    assert result.assigned_reviewers == ["u2"]
    assert result.mergedAt == merged_at


@pytest.mark.asyncio
async def test_reassign_reviewer_uses_repo_and_maps_result(
    repo_mock_pull_request: AsyncMock,
):
    service = PullRequestService(repo_mock_pull_request)

    payload = PullRequestReassignPayload(
        pull_request_id="pr-1001",
        old_user_id="u2",
    )

    pr_model = DummyPullRequest(
        id="pr-1001",
        title="Add search",
        author_id="u1",
        status=PRStatus.OPEN,
        reviewers=[DummyReviewer("u3")],
    )

    repo_mock_pull_request.reassign_reviewer.return_value = (pr_model, "u3")

    result_pr, replaced_by = await service.reassign_reviewer(payload)

    repo_mock_pull_request.reassign_reviewer.assert_awaited_once_with(
        "pr-1001",
        "u2",
    )

    assert isinstance(result_pr, PullRequestFull)
    assert result_pr.pull_request_id == "pr-1001"
    assert result_pr.assigned_reviewers == ["u3"]
    assert replaced_by == "u3"
