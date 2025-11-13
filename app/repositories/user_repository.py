from typing import Type

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import PRReviewer, PullRequest, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def set_is_active(self, user_id: str, is_active: bool) -> Type[User]:
        user = await self._session.get(User, user_id)
        if user is None:
            raise NotFoundError()

        user.is_active = is_active

        await self._session.commit()
        await self._session.refresh(user)

        return user

    async def get_user_review_pull_requests(self, user_id: str) -> list[PullRequest]:
        user = await self._session.get(User, user_id)
        if user is None:
            raise NotFoundError()

        stmt = (
            select(PullRequest)
            .join(PRReviewer, PRReviewer.pr_id == PullRequest.id)
            .where(PRReviewer.reviewer_id == user_id)
        )

        result = await self._session.scalars(stmt)
        return list(result)

    async def get_review_stats_by_user(self) -> list[tuple[str, int]]:
        stmt = select(
            PRReviewer.reviewer_id,
            func.count(PRReviewer.pr_id),
        ).group_by(PRReviewer.reviewer_id)

        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_review_stats_by_pr(
        self,
    ) -> list[tuple[str, int]]:  # TODO: Перенести в репозиторий пр
        stmt = select(
            PRReviewer.pr_id,
            func.count(PRReviewer.reviewer_id),
        ).group_by(PRReviewer.pr_id)

        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]
