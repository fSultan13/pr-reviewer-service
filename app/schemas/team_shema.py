from pydantic import BaseModel


class TeamMember(BaseModel):
    user_id: str
    username: str
    is_active: bool


class TeamWithMembers(BaseModel):
    team_name: str
    members: list[TeamMember]
