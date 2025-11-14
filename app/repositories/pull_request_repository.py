import random

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    AlreadyExistsError,
    NoReplacementCandidateError,
    NotFoundError,
    PullRequestMergedError,
    ReviewerNotAssignedError,
)
from app.models import PRReviewer, PullRequest, User
from app.models.pull_requests import PRStatus


class PullRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_pull_request(
        self,
        pr_id: str,
        title: str,
        author_id: str,
    ) -> PullRequest:
        """
        Создать PR и автоматически назначить до двух активных ревьюеров
        из команды автора, исключая самого автора.
        """
        # 409: PR уже существует
        existing_pr = await self._session.get(PullRequest, pr_id)
        if existing_pr is not None:
            raise AlreadyExistsError()

        # 404: автор (и, по сути, его команда) не найден
        author = await self._session.get(User, author_id)
        if author is None:
            raise NotFoundError()

        pr = PullRequest(id=pr_id, title=title, author_id=author_id)
        self._session.add(pr)

        # Находим всех активных кандидатов из команды автора, кроме самого автора
        candidate_ids: list[str] = []
        if author.team_name is not None:
            stmt = select(User.id).where(
                User.team_name == author.team_name,
                User.is_active.is_(True),
                User.id != author_id,
            )
            result = await self._session.scalars(stmt)
            candidate_ids = list(result)

        selected_ids = random.sample(candidate_ids, k=min(2, len(candidate_ids)))

        for reviewer_id in selected_ids:
            self._session.add(
                PRReviewer(
                    pr_id=pr.id,
                    reviewer_id=reviewer_id,
                )
            )

        await self._session.commit()

        return await self._get_pr_with_reviewers(pr.id)

    async def merge_pull_request(self, pr_id: str) -> PullRequest:
        """
        Идемпотентно помечает PR как MERGED.
        Повторный вызов возвращает актуальное состояние.
        """
        pr = await self._session.get(PullRequest, pr_id)
        if pr is None:
            raise NotFoundError()

        if pr.status != PRStatus.MERGED:
            pr.status = PRStatus.MERGED
            pr.merged_at = func.now()
            await self._session.commit()

        return await self._get_pr_with_reviewers(pr_id)

    async def reassign_reviewer(
        self,
        pr_id: str,
        old_reviewer_id: str,
    ) -> tuple[PullRequest, str]:
        # 404: PR не найден
        pr = await self._session.get(PullRequest, pr_id)
        if pr is None:
            raise NotFoundError()

        # 404: пользователь не найден
        old_reviewer = await self._session.get(User, old_reviewer_id)
        if old_reviewer is None:
            raise NotFoundError()

        # 409: нельзя менять после MERGED
        if pr.status == PRStatus.MERGED:
            raise PullRequestMergedError()

        # Проверяем, что пользователь действительно назначен ревьювером этого PR
        stmt_assignment = select(PRReviewer).where(
            PRReviewer.pr_id == pr_id,
            PRReviewer.reviewer_id == old_reviewer_id,
        )

        # 409: NOT_ASSIGNED
        assignment = await self._session.scalar(stmt_assignment)
        if assignment is None:
            raise ReviewerNotAssignedError()

        # Собираем id других ревьюверов, чтобы не назначить дубль
        stmt_other = select(PRReviewer.reviewer_id).where(
            PRReviewer.pr_id == pr_id,
            PRReviewer.reviewer_id != old_reviewer_id,
        )
        other_reviewer_ids = set(await self._session.scalars(stmt_other))

        # Кандидаты: активные пользователи из команды old_reviewer
        candidate_ids: list[str] = []
        if old_reviewer.team_name is not None:
            stmt_candidates = select(User.id).where(
                User.team_name == old_reviewer.team_name,
                User.is_active.is_(True),
            )
            result = await self._session.scalars(stmt_candidates)
            all_team_ids = list(result)

            candidate_ids = [
                uid
                for uid in all_team_ids
                if uid != old_reviewer_id  # не сам заменяемый
                and uid != pr.author_id  # не автор PR
                and uid not in other_reviewer_ids  # не уже назначенный ревьювер
            ]

        # 409: NO_CANDIDATE
        if not candidate_ids:
            raise NoReplacementCandidateError()

        new_reviewer_id = random.choice(candidate_ids)

        assignment.reviewer_id = new_reviewer_id

        await self._session.commit()

        pr_with_reviewers = await self._get_pr_with_reviewers(pr_id)
        return pr_with_reviewers, new_reviewer_id

    async def get_review_stats_by_pr(
        self,
    ) -> list[tuple[str, int]]:
        stmt = select(
            PRReviewer.pr_id,
            func.count(PRReviewer.reviewer_id),
        ).group_by(PRReviewer.pr_id)

        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def _get_pr_with_reviewers(self, pr_id: str) -> PullRequest:
        """
        Вспомогательный метод: получить PR с загруженными ревьюверами.
        Используется для формирования ответа после операций.
        """
        stmt = (
            select(PullRequest)
            .where(PullRequest.id == pr_id)
            .options(selectinload(PullRequest.reviewers))
        )
        pr = await self._session.scalar(stmt)
        if pr is None:
            raise NotFoundError()
        return pr
