from pydantic import BaseModel


class TeamMemberIn(BaseModel):
    user_id: str
    username: str
    is_active: bool


class TeamWithMembers(BaseModel):
    team_name: str
    members: list[TeamMemberIn]
