# ruff: noqa: F821

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PRStatus(str, Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id: Mapped[str] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    author_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[PRStatus] = mapped_column(
        SAEnum(PRStatus, name="pr_status_enum"), default=PRStatus.OPEN, nullable=False
    )
    merged_at: Mapped[datetime | None]


    author: Mapped["User"] = relationship(back_populates="authored_prs")
    reviewers: Mapped[list["PRReviewer"]] = relationship(
        back_populates="pr", cascade="all, delete-orphan"
    )
