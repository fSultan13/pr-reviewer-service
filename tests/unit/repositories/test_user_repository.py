import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import PRReviewer, PullRequest, Team, User
from app.models.pull_requests import PRStatus
from app.repositories import UserRepository


@pytest.mark.asyncio
async def test_set_is_active_updates_user_flag(
    user_repo: UserRepository,
    session: AsyncSession,
):
    team = Team(name="backend")
    session.add(team)
    await session.commit()

    user = User(
        id="u1",
        username="Alice",
        team_name="backend",
        is_active=True,
    )
    session.add(user)
    await session.commit()

    updated_user = await user_repo.set_is_active(user_id="u1", is_active=False)

    assert isinstance(updated_user, User)
    assert updated_user.id == "u1"
    assert updated_user.is_active is False

    user_from_db = await session.get(User, "u1")
    assert user_from_db is not None
    assert user_from_db.is_active is False


@pytest.mark.asyncio
async def test_set_is_active_raises_not_found_for_unknown_user(
    user_repo: UserRepository,
):
    with pytest.raises(NotFoundError):
        await user_repo.set_is_active(user_id="unknown", is_active=True)


@pytest.mark.asyncio
async def test_get_user_review_pull_requests_returns_only_assigned_prs(
    user_repo: UserRepository,
    session: AsyncSession,
):
    team = Team(name="backend")
    session.add(team)
    await session.commit()

    reviewer = User(
        id="u1",
        username="Reviewer",
        is_active=True,
        team_name="backend",
    )
    author = User(
        id="u2",
        username="Author",
        is_active=True,
        team_name="backend",
    )
    session.add_all([reviewer, author])
    await session.commit()

    pr1 = PullRequest(
        id="pr-1",
        author_id="u2",
        title="Add feature 1",
        status=PRStatus("OPEN"),
    )
    pr2 = PullRequest(
        id="pr-2",
        author_id="u2",
        title="Add feature 2",
        status=PRStatus("OPEN"),
    )
    pr_other = PullRequest(
        id="pr-3",
        author_id="u2",
        title="Other PR",
        status=PRStatus("OPEN"),
    )
    session.add_all([pr1, pr2, pr_other])
    await session.commit()

    r1 = PRReviewer(pr_id="pr-1", reviewer_id="u1")
    r2 = PRReviewer(pr_id="pr-2", reviewer_id="u1")
    r_other = PRReviewer(pr_id="pr-3", reviewer_id="u2")
    session.add_all([r1, r2, r_other])
    await session.commit()

    # действие
    prs = await user_repo.get_user_review_pull_requests(user_id="u1")

    # проверка
    assert isinstance(prs, list)
    assert all(isinstance(pr, PullRequest) for pr in prs)

    pr_ids = {pr.id for pr in prs}
    assert pr_ids == {"pr-1", "pr-2"}
    assert "pr-3" not in pr_ids


@pytest.mark.asyncio
async def test_get_user_review_pull_requests_returns_empty_list_when_no_assignments(
    user_repo: UserRepository,
    session: AsyncSession,
):
    team = Team(name="backend")
    session.add(team)
    await session.commit()

    reviewer = User(
        id="u1",
        username="Reviewer",
        is_active=True,
        team_name="backend",
    )
    session.add(reviewer)
    await session.commit()

    prs = await user_repo.get_user_review_pull_requests(user_id="u1")

    assert prs == []


@pytest.mark.asyncio
async def test_get_user_review_pull_requests_raises_not_found_for_unknown_user(
    user_repo: UserRepository,
):
    with pytest.raises(NotFoundError):
        await user_repo.get_user_review_pull_requests(user_id="unknown")
