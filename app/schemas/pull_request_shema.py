from datetime import datetime

from pydantic import BaseModel

from app.models.pull_requests import PRStatus


class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus


class PRReviewStat(BaseModel):
    pull_request_id: str
    reviewers_assigned: int


class PullRequestFull(PullRequestShort):
    assigned_reviewers: list[str]
    mergedAt: datetime | None = None


class PullRequestCreatePayload(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str


class PullRequestMergePayload(BaseModel):
    pull_request_id: str


class PullRequestReassignPayload(BaseModel):
    pull_request_id: str
    old_user_id: str


class PullRequestResponse(BaseModel):
    pr: PullRequestFull


class PullRequestReassignResponse(BaseModel):
    pr: PullRequestFull
    replaced_by: str
