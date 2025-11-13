# ruff: noqa: F821

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PRReviewer(Base):
    __tablename__ = "pr_reviewers"

    __table_args__ = (UniqueConstraint("pr_id", "reviewer_id", name="uq_pr_reviewer"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    pr_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    pr: Mapped["PullRequest"] = relationship(back_populates="reviewers")
    reviewer: Mapped["User"] = relationship(back_populates="reviewing_prs")
