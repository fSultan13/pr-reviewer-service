from fastapi import APIRouter, HTTPException, status

from app.api.deps import TeamServiceDep
from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.schemas import TeamWithMembers, TeamWithMembersGen

router = APIRouter(tags=["Teams"])


@router.post(
    "/team/add",
    status_code=status.HTTP_201_CREATED,
    response_model=TeamWithMembersGen,
)
async def add_team(
    payload: TeamWithMembers,
    service: TeamServiceDep,
):
    try:
        team = await service.create_team_with_members(payload)
    except AlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "TEAM_EXISTS",
                    "message": "team_name already exists",
                }
            },
        )

    return {"team": team}


@router.get(
    "/team/get",
    response_model=TeamWithMembers,
)
async def get_team(
    team_name: str,
    service: TeamServiceDep,
):
    try:
        return await service.get_team_with_members(team_name)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TEAM_NOT_FOUND",
                    "message": "team not found",
                }
            },
        )
