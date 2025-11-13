from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories import TeamRepository
from app.services import TeamService

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


def get_team_repository(session: DatabaseDep) -> TeamRepository:
    return TeamRepository(session)


TeamRepositoryDep = Annotated[TeamRepository, Depends(get_team_repository)]


def get_team_service(repo: TeamRepositoryDep) -> TeamService:
    return TeamService(repo)


TeamServiceDep = Annotated[TeamService, Depends(get_team_service)]
