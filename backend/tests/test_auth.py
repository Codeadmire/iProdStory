"""
Auth endpoint tests: register, login, /me, duplicate email.
"""
import pytest
from tests.conftest import register_user, auth_headers


def test_register_creates_user_and_workspace(client):
    data = register_user(client)
    assert "access_token" in data
    assert "workspace_id" in data
    assert data["workspace_id"] != ""


def test_register_duplicate_email_returns_409(client):
    register_user(client, email="dup@example.com")
    resp = client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "password": "password123",
        "full_name": "Dup",
        "workspace_name": "Dup Corp",
    })
    assert resp.status_code == 409


def test_login_returns_token(client):
    register_user(client, email="login@example.com", password="MyPass99!")
    resp = client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "MyPass99!",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_returns_401(client):
    register_user(client, email="wp@example.com", password="correct")
    resp = client.post("/api/auth/login", json={
        "email": "wp@example.com",
        "password": "wrong",
    })
    assert resp.status_code == 401


def test_me_returns_user_info(client):
    data = register_user(client, email="me@example.com")
    resp = client.get("/api/auth/me",
                      headers={"Authorization": f"Bearer {data['access_token']}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_me_without_token_returns_401(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_invalid_token_returns_401(client):
    resp = client.get("/api/auth/me",
                      headers={"Authorization": "Bearer not.a.valid.token"})
    assert resp.status_code == 401
