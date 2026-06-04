"""
Alembic migration environment — env.py

This file is called by Alembic on every migration command.
It reads the sync DATABASE_URL from our application settings so there is
a single source of truth for the connection string.

We import all models via `app.models` to ensure Alembic autogenerate
can detect table additions, deletions, and column changes automatically.
"""

import sys
from pathlib import Path

# Make the project root importable when running: alembic upgrade head
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base

# Import all models so Alembic autogenerate sees them
import app.models  # noqa: F401

# Alembic Config object (provides access to alembic.ini values)
config = context.config

# Override the SQLAlchemy URL from our settings (sync DSN for psycopg2)
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

# Logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (generate SQL script without a live DB).
    Useful for generating migration scripts to review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,           # detect column type changes
        compare_server_default=True, # detect server_default changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode against a live database connection.
    This is the default path used by `alembic upgrade head`.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No pooling in migration context
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
