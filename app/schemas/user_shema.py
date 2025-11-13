from pydantic import BaseModel

from app.schemas.pr_shema import PullRequestShort


class UserFull(BaseModel):
    user_id: str
    username: str
    team_name: str | None
    is_active: bool


class UserGen(BaseModel):
    user: UserFull


class SetIsActiveRequest(BaseModel):
    user_id: str
    is_active: bool


class UserReviewPRs(BaseModel):
    user_id: str
    pull_requests: list[PullRequestShort]
