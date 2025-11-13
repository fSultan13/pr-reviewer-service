from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories import TeamRepository, UserRepository
from app.services import TeamService, UserService

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


# ===================== TEAM =====================


def get_team_repository(session: DatabaseDep) -> TeamRepository:
    return TeamRepository(session)


TeamRepositoryDep = Annotated[TeamRepository, Depends(get_team_repository)]


def get_team_service(repo: TeamRepositoryDep) -> TeamService:
    return TeamService(repo)


TeamServiceDep = Annotated[TeamService, Depends(get_team_service)]


# ===================== USER =====================


def get_user_repository(session: DatabaseDep) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_service(repo: UserRepositoryDep) -> UserService:
    return UserService(repo)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
