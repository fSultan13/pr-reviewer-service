from app.models import PullRequest, User
from app.repositories import UserRepository
from app.schemas import (
    PRReviewStat,
    PullRequestShort,
    ReviewStats,
    UserFull,
    UserReviewPRs,
    UserReviewStat,
)


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    @staticmethod
    def _map_user_model(user: User) -> UserFull:
        return UserFull(
            user_id=user.id,
            username=user.username,
            team_name=user.team_name,
            is_active=user.is_active,
        )

    @staticmethod
    def _map_pr_model(pr: PullRequest) -> PullRequestShort:
        return PullRequestShort(
            pull_request_id=pr.id,
            pull_request_name=pr.title,
            author_id=pr.author_id,
            status=pr.status,
        )

    async def set_is_active(self, user_id: str, is_active: bool) -> UserFull:
        user_model = await self._repo.set_is_active(user_id, is_active)
        return self._map_user_model(user_model)

    async def get_review_pull_requests(self, user_id: str) -> UserReviewPRs:
        prs = await self._repo.get_user_review_pull_requests(user_id)
        return UserReviewPRs(
            user_id=user_id,
            pull_requests=[self._map_pr_model(pr) for pr in prs],
        )

    async def get_review_stats(self) -> ReviewStats:
        """
        Статистика назначений:
        - по пользователям
        - по PR.
        """
        by_user_raw = await self._repo.get_review_stats_by_user()
        by_pr_raw = await self._repo.get_review_stats_by_pr()

        return ReviewStats(
            by_user=[
                UserReviewStat(user_id=user_id, reviews_assigned=count)
                for user_id, count in by_user_raw
            ],
            by_pull_request=[
                PRReviewStat(
                    pull_request_id=pr_id,
                    reviewers_assigned=count,
                )
                for pr_id, count in by_pr_raw
            ],
        )
