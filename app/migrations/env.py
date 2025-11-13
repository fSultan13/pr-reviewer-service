# ruff: noqa: F403, F401
import os
import re
from logging.config import fileConfig

from alembic import context
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, pool

from app.core.config import settings
from app.core.db import Base
from app.models import *

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
VERSIONS_RE = re.compile(r"^(\d+)_")


def _next_numeric_rev_id() -> str:
    script_dir = ScriptDirectory.from_config(context.config)
    versions_dir = script_dir.versions
    max_num = 0
    if versions_dir and os.path.isdir(versions_dir):
        for fname in os.listdir(versions_dir):
            m = VERSIONS_RE.match(fname)
            if m:
                try:
                    max_num = max(max_num, int(m.group(1)))
                except ValueError:
                    pass
    return f"{max_num + 1:04d}"


def process_revision_directives(context, revision, directives):
    if not directives:
        return
    script = directives[0]

    if isinstance(getattr(script, "down_revision", None), tuple):
        return

    current = getattr(script, "rev_id", None)
    if not (isinstance(current, str) and current.isdigit()):
        script.rev_id = _next_numeric_rev_id()


def run_migrations_offline():
    context.configure(
        url=settings.get_database_uri.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(
        settings.get_database_uri.render_as_string(hide_password=False),
        poolclass=pool.NullPool,
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
