from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.deps import PullRequestServiceDep
from app.core.exceptions import (
    AlreadyExistsError,
    NoReplacementCandidateError,
    NotFoundError,
    PullRequestMergedError,
    ReviewerNotAssignedError,
)
from app.schemas import (
    PullRequestCreatePayload,
    PullRequestMergePayload,
    PullRequestReassignPayload,
    PullRequestReassignResponse,
    PullRequestResponse,
    TeamBulkDeactivatePayload,
    TeamBulkDeactivateResult,
)

router = APIRouter(tags=["PullRequests"])


@router.post(
    "/pullRequest/create",
    status_code=status.HTTP_201_CREATED,
    response_model=PullRequestResponse,
)
async def create_pull_request(
    payload: PullRequestCreatePayload,
    service: PullRequestServiceDep,
):
    try:
        pr = await service.create_pull_request(payload)
    except AlreadyExistsError:
        # 409 PR_EXISTS
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "PR_EXISTS",
                    "message": "PR id already exists",
                }
            },
        )
    except NotFoundError:
        # 404 Автор/команда не найдены
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "AUTHOR_OR_TEAM_NOT_FOUND",
                    "message": "author or team not found",
                }
            },
        )

    return {"pr": pr}


@router.post(
    "/pullRequest/merge",
    response_model=PullRequestResponse,
)
async def merge_pull_request(
    payload: PullRequestMergePayload,
    service: PullRequestServiceDep,
):
    try:
        pr = await service.merge_pull_request(payload)
    except NotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "PR_NOT_FOUND",
                    "message": "pull request not found",
                }
            },
        )

    return {"pr": pr}


@router.post(
    "/pullRequest/reassign",
    response_model=PullRequestReassignResponse,
)
async def reassign_reviewer(
    payload: PullRequestReassignPayload,
    service: PullRequestServiceDep,
):
    try:
        pr, replaced_by = await service.reassign_reviewer(payload)
    except NotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "pull request or user not found",
                }
            },
        )
    except PullRequestMergedError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "PR_MERGED",
                    "message": "cannot reassign on merged PR",
                }
            },
        )
    except ReviewerNotAssignedError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "NOT_ASSIGNED",
                    "message": "reviewer is not assigned to this PR",
                }
            },
        )
    except NoReplacementCandidateError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "NO_CANDIDATE",
                    "message": "no active replacement candidate in team",
                }
            },
        )

    return {"pr": pr, "replaced_by": replaced_by}


@router.post(
    "/team/deactivateUsers",
    response_model=TeamBulkDeactivateResult,
)
async def bulk_deactivate_team_users(
    payload: TeamBulkDeactivatePayload,
    service: PullRequestServiceDep,
):
    try:
        result = await service.bulk_deactivate_team_users_and_reassign(payload)
    except NotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "TEAM_OR_USERS_NOT_FOUND",
                    "message": "team or users not found",
                }
            },
        )

    return result
