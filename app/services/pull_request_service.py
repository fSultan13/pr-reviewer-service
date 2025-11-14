from app.models import PullRequest
from app.repositories import PullRequestRepository
from app.schemas import (
    PullRequestCreatePayload,
    PullRequestFull,
    PullRequestMergePayload,
    PullRequestReassignPayload,
    TeamBulkDeactivatePayload,
    TeamBulkDeactivateResult,
)


class PullRequestService:
    def __init__(self, repo: PullRequestRepository) -> None:
        self._repo = repo

    @staticmethod
    def _map_pr_model(pr: PullRequest) -> PullRequestFull:
        return PullRequestFull(
            pull_request_id=pr.id,
            pull_request_name=pr.title,
            author_id=pr.author_id,
            status=pr.status,
            assigned_reviewers=[r.reviewer_id for r in pr.reviewers],
            mergedAt=pr.merged_at,
        )

    async def create_pull_request(
        self,
        payload: PullRequestCreatePayload,
    ) -> PullRequestFull:
        pr = await self._repo.create_pull_request(
            pr_id=payload.pull_request_id,
            title=payload.pull_request_name,
            author_id=payload.author_id,
        )
        return self._map_pr_model(pr)

    async def merge_pull_request(
        self,
        payload: PullRequestMergePayload,
    ) -> PullRequestFull:
        pr = await self._repo.merge_pull_request(payload.pull_request_id)
        return self._map_pr_model(pr)

    async def reassign_reviewer(
        self,
        payload: PullRequestReassignPayload,
    ) -> tuple[PullRequestFull, str]:
        pr, replaced_by = await self._repo.reassign_reviewer(
            payload.pull_request_id,
            payload.old_user_id,
        )
        return self._map_pr_model(pr), replaced_by

    async def bulk_deactivate_team_users_and_reassign(
        self,
        payload: TeamBulkDeactivatePayload,
    ) -> TeamBulkDeactivateResult:
        deactivated, reassigned, affected_prs = (
            await self._repo.bulk_deactivate_team_users_and_reassign(
                team_name=payload.team_name,
                user_ids=payload.user_ids,
            )
        )
        return TeamBulkDeactivateResult(
            team_name=payload.team_name,
            deactivated_users=deactivated,
            reassigned_reviewers=reassigned,
            affected_pull_requests=affected_prs,
        )
