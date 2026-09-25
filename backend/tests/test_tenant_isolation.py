"""
Tenant isolation tests — the most critical security tests for a SaaS product.

Verifies that:
  - User A cannot read User B's products
  - User A cannot trigger actions on User B's products
  - User A cannot poll User B's jobs
  - Cross-workspace access returns 403 or 404, never 200

These tests MUST pass before any production deployment.
"""
import pytest
from tests.conftest import register_user, auth_headers


@pytest.fixture
def alice(client):
    return register_user(client, email="alice_iso@example.com",
                         workspace_name="Alice Workspace")


@pytest.fixture
def bob(client):
    return register_user(client, email="bob_iso@example.com",
                         workspace_name="Bob Workspace")


@pytest.fixture
def alice_product(client, alice):
    resp = client.post(
        "/api/products",
        json={"url": "https://stripe.com", "name": "Alice Product"},
        headers=auth_headers(alice["access_token"], alice["workspace_id"]),
    )
    assert resp.status_code == 201
    return resp.json()


# ── Test 1: Bob cannot read Alice's product ───────────────────────────────────

def test_bob_cannot_get_alice_product(client, alice_product, bob):
    resp = client.get(
        f"/api/products/{alice_product['id']}",
        headers=auth_headers(bob["access_token"], bob["workspace_id"]),
    )
    # Must be 404 (product doesn't exist in Bob's workspace) — NOT 200
    assert resp.status_code == 404, (
        f"SECURITY FAILURE: Bob got HTTP {resp.status_code} on Alice's product. "
        f"Response: {resp.text}"
    )


# ── Test 2: Bob cannot list Alice's products in his workspace response ─────────

def test_bobs_product_list_does_not_contain_alices_products(client, alice_product, bob):
    resp = client.get(
        "/api/products",
        headers=auth_headers(bob["access_token"], bob["workspace_id"]),
    )
    assert resp.status_code == 200
    product_ids = [p["id"] for p in resp.json()]
    assert alice_product["id"] not in product_ids, (
        "SECURITY FAILURE: Alice's product appeared in Bob's product list."
    )


# ── Test 3: Bob cannot trigger crawl on Alice's product ───────────────────────

def test_bob_cannot_crawl_alice_product(client, alice_product, bob):
    resp = client.post(
        f"/api/products/{alice_product['id']}/crawl",
        json={"max_pages": 5},
        headers=auth_headers(bob["access_token"], bob["workspace_id"]),
    )
    assert resp.status_code == 404, (
        f"SECURITY FAILURE: Bob could trigger a crawl on Alice's product. "
        f"HTTP {resp.status_code}"
    )


# ── Test 4: Bob cannot trigger AI analysis on Alice's product ──────────────────

def test_bob_cannot_analyze_alice_product(client, alice_product, bob):
    resp = client.post(
        f"/api/products/{alice_product['id']}/analyze",
        headers=auth_headers(bob["access_token"], bob["workspace_id"]),
    )
    assert resp.status_code == 404, (
        f"SECURITY FAILURE: Bob triggered AI analysis on Alice's product. "
        f"HTTP {resp.status_code}"
    )


# ── Test 5: Bob cannot poll Alice's job ───────────────────────────────────────

def test_bob_cannot_poll_alice_job(client, alice_product, alice, bob):
    # Alice creates a job
    job_resp = client.post(
        f"/api/products/{alice_product['id']}/analyze",
        headers=auth_headers(alice["access_token"], alice["workspace_id"]),
    )
    assert job_resp.status_code == 202
    alice_job_id = job_resp.json()["job_id"]

    # Bob tries to poll it with his workspace header
    resp = client.get(
        f"/api/jobs/{alice_job_id}",
        headers=auth_headers(bob["access_token"], bob["workspace_id"]),
    )
    assert resp.status_code == 404, (
        f"SECURITY FAILURE: Bob could poll Alice's job. HTTP {resp.status_code}"
    )


# ── Test 6: Wrong workspace header for valid user ─────────────────────────────

def test_valid_token_wrong_workspace_returns_403(client, alice, bob):
    """Alice's token + Bob's workspace ID must be rejected."""
    resp = client.get(
        "/api/products",
        headers={
            "Authorization": f"Bearer {alice['access_token']}",
            "X-Workspace-Id": bob["workspace_id"],  # Wrong workspace
        },
    )
    assert resp.status_code == 403, (
        f"SECURITY FAILURE: Alice's token accepted for Bob's workspace. "
        f"HTTP {resp.status_code}"
    )


# ── Test 7: Missing workspace header ─────────────────────────────────────────

def test_missing_workspace_header_returns_400(client, alice):
    resp = client.get(
        "/api/products",
        headers={"Authorization": f"Bearer {alice['access_token']}"},
    )
    assert resp.status_code == 400


# ── Test 8: Bob cannot get/update Alice's product page ───────────────────────

def test_bob_cannot_read_alice_product_page(client, alice_product, bob):
    resp = client.get(
        f"/api/products/{alice_product['id']}/product-page",
        headers=auth_headers(bob["access_token"], bob["workspace_id"]),
    )
    assert resp.status_code in (403, 404)


def test_bob_cannot_generate_media_for_alice_product(client, alice_product, bob):
    resp = client.post(
        f"/api/products/{alice_product['id']}/media",
        headers=auth_headers(bob["access_token"], bob["workspace_id"]),
    )
    assert resp.status_code == 404
