from pydantic import BaseModel

from app.schemas.pull_request_shema import PRReviewStat, PullRequestShort


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


class UserReviewStat(BaseModel):
    user_id: str
    reviews_assigned: int


class ReviewStats(BaseModel):
    by_user: list[UserReviewStat]
    by_pull_request: list[PRReviewStat]
