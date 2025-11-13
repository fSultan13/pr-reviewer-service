from app.models import Team
from app.repositories import TeamRepository
from app.schemas import TeamMember, TeamWithMembers


class TeamService:
    def __init__(self, repo: TeamRepository) -> None:
        self._repo = repo

    @staticmethod
    def _map_team_model(team: Team) -> TeamWithMembers:
        return TeamWithMembers(
            team_name=team.name,
            members=[
                TeamMember(
                    user_id=user.id,
                    username=user.username,
                    is_active=user.is_active,
                )
                for user in team.users
            ],
        )

    async def create_team_with_members(
        self, team_in: TeamWithMembers
    ) -> TeamWithMembers:
        team_model = await self._repo.create_team_with_members(team_in)
        return self._map_team_model(team_model)

    async def get_team_with_members(self, team_name: str) -> TeamWithMembers:
        team_model = await self._repo.get_team_with_members(team_name)
        return self._map_team_model(team_model)
