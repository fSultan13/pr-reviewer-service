# ruff: noqa: F821

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Team(Base):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(primary_key=True)

    users: Mapped[list["User"]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )
