import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyExistsError,
    NoReplacementCandidateError,
    NotFoundError,
    PullRequestMergedError,
    ReviewerNotAssignedError,
)
from app.models import PRReviewer, PullRequest, Team, User
from app.models.pull_requests import PRStatus
from app.repositories import PullRequestRepository


@pytest.fixture
def pr_repo(session: AsyncSession) -> PullRequestRepository:
    return PullRequestRepository(session)


@pytest.mark.asyncio
async def test_create_pull_request_raises_if_author_not_found(
    pr_repo: PullRequestRepository,
):
    with pytest.raises(NotFoundError):
        await pr_repo.create_pull_request(
            pr_id="pr-1",
            title="My PR",
            author_id="unknown-author",
        )


@pytest.mark.asyncio
async def test_create_pull_request_raises_if_pr_already_exists(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team-1")
    author = User(
        id="author-1",
        username="author",
        is_active=True,
        team_name="team-1",
    )
    pr_existing = PullRequest(
        id="pr-1",
        title="Existing PR",
        author_id="author-1",
    )

    session.add_all([team, author, pr_existing])
    await session.commit()

    with pytest.raises(AlreadyExistsError):
        await pr_repo.create_pull_request(
            pr_id="pr-1",
            title="New title",
            author_id="author-1",
        )


@pytest.mark.asyncio
async def test_create_pull_request_assigns_up_to_two_active_reviewers(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team-alpha")
    author = User(
        id="u1",
        username="author",
        is_active=True,
        team_name="team-alpha",
    )
    reviewer_1 = User(
        id="u2",
        username="rev1",
        is_active=True,
        team_name="team-alpha",
    )
    reviewer_2 = User(
        id="u3",
        username="rev2",
        is_active=True,
        team_name="team-alpha",
    )
    inactive_same_team = User(
        id="u4",
        username="inactive",
        is_active=False,
        team_name="team-alpha",
    )
    other_team = Team(name="team-beta")
    other_team_user = User(
        id="u5",
        username="other-team",
        is_active=True,
        team_name="team-beta",
    )

    session.add_all(
        [
            team,
            other_team,
            author,
            reviewer_1,
            reviewer_2,
            inactive_same_team,
            other_team_user,
        ]
    )
    await session.commit()

    pr = await pr_repo.create_pull_request(
        pr_id="pr-1",
        title="Title",
        author_id="u1",
    )

    assert isinstance(pr, PullRequest)
    assert pr.id == "pr-1"
    assert pr.author_id == "u1"

    reviewer_ids = {r.reviewer_id for r in pr.reviewers}
    assert len(reviewer_ids) == 2
    assert reviewer_ids == {"u2", "u3"}


@pytest.mark.asyncio
async def test_create_pull_request_with_no_candidates_assigns_no_reviewers(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team-alone")
    author = User(
        id="author-1",
        username="author",
        is_active=True,
        team_name="team-alone",
    )
    session.add_all([team, author])
    await session.commit()

    pr = await pr_repo.create_pull_request(
        pr_id="pr-1",
        title="Title",
        author_id="author-1",
    )

    assert isinstance(pr, PullRequest)
    assert pr.id == "pr-1"
    assert len(pr.reviewers) == 0


@pytest.mark.asyncio
async def test_create_pull_request_with_single_candidate_assigns_one(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team-single")
    author = User(
        id="author-1",
        username="author",
        is_active=True,
        team_name="team-single",
    )
    single_reviewer = User(
        id="rev-1",
        username="rev",
        is_active=True,
        team_name="team-single",
    )
    session.add_all([team, author, single_reviewer])
    await session.commit()

    pr = await pr_repo.create_pull_request(
        pr_id="pr-1",
        title="Title",
        author_id="author-1",
    )

    reviewer_ids = [r.reviewer_id for r in pr.reviewers]
    assert len(reviewer_ids) == 1
    assert reviewer_ids[0] == "rev-1"


@pytest.mark.asyncio
async def test_merge_pull_request_raises_if_not_found(
    pr_repo: PullRequestRepository,
):
    with pytest.raises(NotFoundError):
        await pr_repo.merge_pull_request("non-existent-pr")


@pytest.mark.asyncio
async def test_merge_pull_request_is_idempotent_and_keeps_reviewers(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team-merge")
    author = User(
        id="author-1",
        username="author",
        is_active=True,
        team_name="team-merge",
    )
    reviewer_1 = User(
        id="rev-1",
        username="rev1",
        is_active=True,
        team_name="team-merge",
    )
    reviewer_2 = User(
        id="rev-2",
        username="rev2",
        is_active=True,
        team_name="team-merge",
    )
    pr = PullRequest(
        id="pr-merge",
        title="Merge me",
        author_id="author-1",
        status=PRStatus.OPEN,
    )
    pr_rev_1 = PRReviewer(pr_id="pr-merge", reviewer_id="rev-1")
    pr_rev_2 = PRReviewer(pr_id="pr-merge", reviewer_id="rev-2")

    session.add_all([team, author, reviewer_1, reviewer_2, pr, pr_rev_1, pr_rev_2])
    await session.commit()

    pr1 = await pr_repo.merge_pull_request("pr-merge")
    assert pr1.status == PRStatus.MERGED
    assert pr1.merged_at is not None
    reviewer_ids_before = {r.reviewer_id for r in pr1.reviewers}
    merged_at_first = pr1.merged_at

    pr2 = await pr_repo.merge_pull_request("pr-merge")
    assert pr2.status == PRStatus.MERGED
    assert pr2.merged_at == merged_at_first
    reviewer_ids_after = {r.reviewer_id for r in pr2.reviewers}
    assert reviewer_ids_after == reviewer_ids_before


@pytest.mark.asyncio
async def test_reassign_reviewer_success(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team-reassign")
    author = User(
        id="author-1",
        username="author",
        is_active=True,
        team_name="team-reassign",
    )
    old_reviewer = User(
        id="rev-old",
        username="old",
        is_active=True,
        team_name="team-reassign",
    )
    other_reviewer = User(
        id="rev-other",
        username="other",
        is_active=True,
        team_name="team-reassign",
    )
    # Новый кандидат
    new_candidate = User(
        id="rev-new",
        username="new",
        is_active=True,
        team_name="team-reassign",
    )
    session.add_all([team, author, old_reviewer, other_reviewer, new_candidate])

    pr = PullRequest(
        id="pr-1",
        title="Reassign me",
        author_id="author-1",
        status=PRStatus.OPEN,
    )
    pr_rev_old = PRReviewer(pr_id="pr-1", reviewer_id="rev-old")
    pr_rev_other = PRReviewer(pr_id="pr-1", reviewer_id="rev-other")

    session.add_all([pr, pr_rev_old, pr_rev_other])
    await session.commit()

    pr_after, new_reviewer_id = await pr_repo.reassign_reviewer(
        pr_id="pr-1",
        old_reviewer_id="rev-old",
    )

    reviewer_ids = {r.reviewer_id for r in pr_after.reviewers}
    assert "rev-old" not in reviewer_ids
    assert "rev-other" in reviewer_ids
    assert new_reviewer_id in reviewer_ids
    assert new_reviewer_id == "rev-new"


@pytest.mark.asyncio
async def test_reassign_reviewer_raises_if_pr_not_found(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    user = User(
        id="rev-1",
        username="rev",
        is_active=True,
        team_name="team",
    )
    team = Team(name="team")
    session.add_all([team, user])
    await session.commit()

    with pytest.raises(NotFoundError):
        await pr_repo.reassign_reviewer(pr_id="unknown-pr", old_reviewer_id="rev-1")


@pytest.mark.asyncio
async def test_reassign_reviewer_raises_if_old_reviewer_not_found(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team")
    author = User(
        id="author-1",
        username="author",
        is_active=True,
        team_name="team",
    )
    pr = PullRequest(
        id="pr-1",
        title="Title",
        author_id="author-1",
        status=PRStatus.OPEN,
    )

    session.add_all([team, author, pr])
    await session.commit()

    with pytest.raises(NotFoundError):
        await pr_repo.reassign_reviewer(pr_id="pr-1", old_reviewer_id="no-such-user")


@pytest.mark.asyncio
async def test_reassign_reviewer_raises_if_pr_merged(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team")
    author = User(
        id="author-1",
        username="author",
        is_active=True,
        team_name="team",
    )
    old_reviewer = User(
        id="rev-old",
        username="old",
        is_active=True,
        team_name="team",
    )
    pr = PullRequest(
        id="pr-1",
        title="Merged PR",
        author_id="author-1",
        status=PRStatus.MERGED,
    )
    pr_rev = PRReviewer(pr_id="pr-1", reviewer_id="rev-old")

    session.add_all([team, author, old_reviewer, pr, pr_rev])
    await session.commit()

    with pytest.raises(PullRequestMergedError):
        await pr_repo.reassign_reviewer(pr_id="pr-1", old_reviewer_id="rev-old")


@pytest.mark.asyncio
async def test_reassign_reviewer_raises_if_reviewer_not_assigned(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team")
    author = User(
        id="author-1",
        username="author",
        is_active=True,
        team_name="team",
    )
    old_reviewer = User(
        id="rev-old",
        username="old",
        is_active=True,
        team_name="team",
    )
    other_reviewer = User(
        id="rev-other",
        username="other",
        is_active=True,
        team_name="team",
    )

    pr = PullRequest(
        id="pr-1",
        title="PR",
        author_id="author-1",
        status=PRStatus.OPEN,
    )
    # Назначен только other_reviewer
    pr_rev = PRReviewer(pr_id="pr-1", reviewer_id="rev-other")

    session.add_all([team, author, old_reviewer, other_reviewer, pr, pr_rev])
    await session.commit()

    with pytest.raises(ReviewerNotAssignedError):
        await pr_repo.reassign_reviewer(pr_id="pr-1", old_reviewer_id="rev-old")


@pytest.mark.asyncio
async def test_reassign_reviewer_raises_if_no_replacement_candidate(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team")
    author = User(
        id="author-1",
        username="author",
        is_active=True,
        team_name="team",
    )
    old_reviewer = User(
        id="rev-old",
        username="old",
        is_active=True,
        team_name="team",
    )
    other_reviewer = User(
        id="rev-other",
        username="other",
        is_active=True,
        team_name="team",
    )
    inactive_user = User(
        id="inactive",
        username="inactive",
        is_active=False,
        team_name="team",
    )

    pr = PullRequest(
        id="pr-1",
        title="PR",
        author_id="author-1",
        status=PRStatus.OPEN,
    )
    pr_rev_old = PRReviewer(pr_id="pr-1", reviewer_id="rev-old")
    pr_rev_other = PRReviewer(pr_id="pr-1", reviewer_id="rev-other")

    session.add_all(
        [
            team,
            author,
            old_reviewer,
            other_reviewer,
            inactive_user,
            pr,
            pr_rev_old,
            pr_rev_other,
        ]
    )
    await session.commit()

    with pytest.raises(NoReplacementCandidateError):
        await pr_repo.reassign_reviewer(pr_id="pr-1", old_reviewer_id="rev-old")


@pytest.mark.asyncio
async def test_get_review_stats_by_pr_returns_counts_grouped_by_pr(
    pr_repo: PullRequestRepository,
    session: AsyncSession,
):
    team = Team(name="team-stats")
    author = User(
        id="author-1",
        username="author",
        is_active=True,
        team_name="team-stats",
    )
    r1 = User(
        id="rev-1",
        username="rev1",
        is_active=True,
        team_name="team-stats",
    )
    r2 = User(
        id="rev-2",
        username="rev2",
        is_active=True,
        team_name="team-stats",
    )
    r3 = User(
        id="rev-3",
        username="rev3",
        is_active=True,
        team_name="team-stats",
    )

    pr1 = PullRequest(id="pr-1", title="PR 1", author_id="author-1")
    pr2 = PullRequest(id="pr-2", title="PR 2", author_id="author-1")
    pr3 = PullRequest(id="pr-3", title="PR 3", author_id="author-1")

    session.add_all([team, author, r1, r2, r3, pr1, pr2, pr3])

    session.add(PRReviewer(pr_id="pr-1", reviewer_id="rev-1"))
    session.add(PRReviewer(pr_id="pr-1", reviewer_id="rev-2"))
    session.add(PRReviewer(pr_id="pr-2", reviewer_id="rev-3"))

    await session.commit()

    stats = await pr_repo.get_review_stats_by_pr()
    stats_dict = {pr_id: count for pr_id, count in stats}

    assert stats_dict["pr-1"] == 2
    assert stats_dict["pr-2"] == 1
    assert "pr-3" not in stats_dict
