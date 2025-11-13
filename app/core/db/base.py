import typing as t
import uuid
from datetime import datetime

from sqlalchemy import func, inspect, text
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    __abstract__ = True
    __mapper_args__ = {"eager_defaults": True}

    created_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={getattr(self, 'id', None)}>"

    def as_dict(self, excluded_fields: t.Iterable[str] | None = None) -> dict:
        excluded = set(excluded_fields or [])
        state = inspect(self)
        out = {}
        for attr in state.mapper.column_attrs:
            key = attr.key
            if key in excluded:
                continue
            if key in state.unloaded:
                continue
            val = getattr(self, key, None)
            if isinstance(val, datetime):
                val = val.isoformat()
            out[key] = val
        return out
