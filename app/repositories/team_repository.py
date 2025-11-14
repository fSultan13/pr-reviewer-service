from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.models import Team, User
from app.schemas import TeamWithMembers


class TeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_team_with_members(self, team_in: TeamWithMembers) -> Team:
        existing_team = await self._session.get(Team, team_in.team_name)
        if existing_team is not None:
            raise AlreadyExistsError()

        team = Team(name=team_in.team_name)
        self._session.add(team)

        for member_in in team_in.members:
            user = await self._session.get(User, member_in.user_id)

            if user is None:
                user = User(
                    id=member_in.user_id,
                    username=member_in.username,
                    is_active=member_in.is_active,
                    team_name=team_in.team_name,
                )
                self._session.add(user)
            else:
                user.username = member_in.username
                user.is_active = member_in.is_active
                user.team_name = team_in.team_name

        await self._session.commit()

        return team

    async def get_team_with_members(self, team_name: str) -> Team:
        stmt = (
            select(Team).where(Team.name == team_name).options(selectinload(Team.users))
        )
        team = await self._session.scalar(stmt)
        if team is None:
            raise NotFoundError()
        return team
