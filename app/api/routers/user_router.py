from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.deps import UserServiceDep
from app.core.exceptions import NotFoundError
from app.schemas import ReviewStats, SetIsActiveRequest, UserGen, UserReviewPRs

router = APIRouter(tags=["Users"])


@router.post(
    "/users/setIsActive",
    status_code=status.HTTP_200_OK,
    response_model=UserGen,
)
async def set_is_active(
    payload: SetIsActiveRequest,
    service: UserServiceDep,
):
    try:
        user = await service.set_is_active(
            user_id=payload.user_id,
            is_active=payload.is_active,
        )
    except NotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "user not found",
                }
            },
        )

    return {"user": user}


@router.get(
    "/users/getReview",
    response_model=UserReviewPRs,
)
async def get_user_review_prs(
    user_id: str,
    service: UserServiceDep,
):
    try:
        return await service.get_review_pull_requests(user_id)
    except NotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "user not found",
                }
            },
        )


@router.get(
    "/stats/review",
    response_model=ReviewStats,
    tags=["Stats"],
)
async def get_review_stats(
    service: UserServiceDep,
):
    return await service.get_review_stats()
