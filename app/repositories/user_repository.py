from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import PRReviewer, PullRequest, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def set_is_active(self, user_id: str, is_active: bool) -> User:

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
