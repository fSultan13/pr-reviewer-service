from fastapi import APIRouter, HTTPException, status

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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "PR_EXISTS",
                    "message": "PR id already exists",
                }
            },
        )
    except NotFoundError:
        # 404 Автор/команда не найдены
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "pull request or user not found",
                }
            },
        )
    except PullRequestMergedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "PR_MERGED",
                    "message": "cannot reassign on merged PR",
                }
            },
        )
    except ReviewerNotAssignedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "NOT_ASSIGNED",
                    "message": "reviewer is not assigned to this PR",
                }
            },
        )
    except NoReplacementCandidateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "NO_CANDIDATE",
                    "message": "no active replacement candidate in team",
                }
            },
        )

    return {"pr": pr, "replaced_by": replaced_by}
