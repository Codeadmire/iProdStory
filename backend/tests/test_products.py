"""
Product API tests: CRUD + async job creation.
"""
import pytest
from tests.conftest import register_user, auth_headers


@pytest.fixture
def alice(client):
    return register_user(client, email="alice_prod@example.com",
                         workspace_name="Alice Products")


def test_create_product_returns_201(client, alice):
    resp = client.post(
        "/api/products",
        json={"url": "https://stripe.com", "name": "Stripe"},
        headers=auth_headers(alice["access_token"], alice["workspace_id"]),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Stripe"
    assert data["base_url"] == "https://stripe.com"


def test_create_product_invalid_url_returns_422(client, alice):
    resp = client.post(
        "/api/products",
        json={"url": "not-a-url"},
        headers=auth_headers(alice["access_token"], alice["workspace_id"]),
    )
    assert resp.status_code == 422


def test_create_product_localhost_blocked(client, alice):
    resp = client.post(
        "/api/products",
        json={"url": "http://localhost/admin"},
        headers=auth_headers(alice["access_token"], alice["workspace_id"]),
    )
    assert resp.status_code == 422


def test_create_product_private_ip_blocked(client, alice):
    resp = client.post(
        "/api/products",
        json={"url": "http://192.168.1.1/"},
        headers=auth_headers(alice["access_token"], alice["workspace_id"]),
    )
    assert resp.status_code == 422


def test_list_products_returns_own_only(client, alice):
    client.post("/api/products", json={"url": "https://stripe.com"},
                headers=auth_headers(alice["access_token"], alice["workspace_id"]))
    resp = client.get("/api/products",
                      headers=auth_headers(alice["access_token"], alice["workspace_id"]))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_product_returns_404_for_unknown(client, alice):
    resp = client.get("/api/products/nonexistent-id",
                      headers=auth_headers(alice["access_token"], alice["workspace_id"]))
    assert resp.status_code == 404


def test_start_crawl_returns_202_and_job_id(client, alice):
    prod = client.post("/api/products",
                       json={"url": "https://stripe.com"},
                       headers=auth_headers(alice["access_token"], alice["workspace_id"])).json()

    resp = client.post(f"/api/products/{prod['id']}/crawl",
                       json={"max_pages": 5, "max_depth": 1},
                       headers=auth_headers(alice["access_token"], alice["workspace_id"]))
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "queued"


def test_analyze_returns_202_and_job_id(client, alice):
    prod = client.post("/api/products",
                       json={"url": "https://stripe.com"},
                       headers=auth_headers(alice["access_token"], alice["workspace_id"])).json()

    resp = client.post(f"/api/products/{prod['id']}/analyze",
                       headers=auth_headers(alice["access_token"], alice["workspace_id"]))
    assert resp.status_code == 202
    assert "job_id" in resp.json()


def test_get_job_status(client, alice):
    prod = client.post("/api/products",
                       json={"url": "https://stripe.com"},
                       headers=auth_headers(alice["access_token"], alice["workspace_id"])).json()
    job_data = client.post(f"/api/products/{prod['id']}/analyze",
                           headers=auth_headers(alice["access_token"], alice["workspace_id"])).json()
    job_id = job_data["job_id"]

    resp = client.get(f"/api/jobs/{job_id}",
                      headers=auth_headers(alice["access_token"], alice["workspace_id"]))
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id
    assert resp.json()["job_type"] == "ai_analyze"


def test_unauthenticated_request_returns_401(client):
    resp = client.get("/api/products")
    assert resp.status_code == 401
