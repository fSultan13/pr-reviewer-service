# ruff: noqa: F821

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )

    team: Mapped["Team"] = relationship(back_populates="users")

    authored_prs: Mapped[list["PullRequest"]] = relationship(
        back_populates="author", foreign_keys="PullRequest.author_id"
    )

    reviewing_prs: Mapped[list["PRReviewer"]] = relationship(
        back_populates="reviewer", cascade="all, delete-orphan"
    )
