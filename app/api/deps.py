from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories import PullRequestRepository, TeamRepository, UserRepository
from app.services import PullRequestService, TeamService, UserService

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


# ===================== TEAM =====================


def get_team_repository(session: DatabaseDep) -> TeamRepository:
    return TeamRepository(session)


TeamRepositoryDep = Annotated[TeamRepository, Depends(get_team_repository)]


def get_team_service(repo: TeamRepositoryDep) -> TeamService:
    return TeamService(repo)


TeamServiceDep = Annotated[TeamService, Depends(get_team_service)]


# ===================== Pull Request =====================


def get_pull_request_repository(session: DatabaseDep) -> PullRequestRepository:
    return PullRequestRepository(session)


PullRequestRepositoryDep = Annotated[
    PullRequestRepository, Depends(get_pull_request_repository)
]


def get_pull_request_service(repo: PullRequestRepositoryDep) -> PullRequestService:
    return PullRequestService(repo)


PullRequestServiceDep = Annotated[PullRequestService, Depends(get_pull_request_service)]


# ===================== USER =====================


def get_user_repository(session: DatabaseDep) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_service(
    repo_user: UserRepositoryDep, repo_pr: PullRequestRepositoryDep
) -> UserService:
    return UserService(repo_user, repo_pr)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
