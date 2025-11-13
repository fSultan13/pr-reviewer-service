from pydantic import BaseModel

from app.models.pull_requests import PRStatus


class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus
