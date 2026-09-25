"""
Alembic env.py — wired to our multi-tenant models and DATABASE_URL from config.
Run migrations:
    alembic upgrade head
Generate a new migration:
    alembic revision --autogenerate -m "description"
"""
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Make the backend package importable from this file
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import settings
import models  # noqa: F401 — ensures all models are registered on Base.metadata
from database import Base

alembic_config = context.config

# Point Alembic at our DATABASE_URL (overrides alembic.ini value)
alembic_config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
