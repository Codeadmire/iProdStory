"""
pytest fixtures shared across all test modules.

Uses an in-memory SQLite database so tests run without PostgreSQL.
Celery tasks are run eagerly (synchronously) via CELERY_TASK_ALWAYS_EAGER.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Override settings BEFORE importing app modules ────────────────────────────
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("STORAGE_BACKEND", "local")
os.environ.setdefault("LOCAL_STORAGE_PATH", "/tmp/test_media")
os.environ.setdefault("MEDIA_BASE_URL", "http://localhost:8000/media")

from database import Base, get_db
from main import app

TEST_DB_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Yields a DB session that is rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """TestClient with the test DB injected."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Reusable user factories ───────────────────────────────────────────────────

def register_user(client, email="alice@example.com", password="StrongPass1!",
                  full_name="Alice", workspace_name="Alice Corp"):
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name,
        "workspace_name": workspace_name,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_headers(token: str, workspace_id: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "X-Workspace-Id": workspace_id,
    }
