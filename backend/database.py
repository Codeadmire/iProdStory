"""
Database engine, session factory and base class.
Supports PostgreSQL (production) and SQLite (fallback dev only).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings

# PostgreSQL needs pool_pre_ping to handle connection drops gracefully.
# SQLite needs check_same_thread=False for dev use.
_connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
