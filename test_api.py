"""API tests for the SafeVillage hackathon demo."""

import os
import tempfile
from pathlib import Path

_db_file = Path(tempfile.gettempdir()) / "safevillage-pytest.db"
if _db_file.exists():
    _db_file.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.as_posix()}"
os.environ["SECRET_KEY"] = "test-only-secret-key-with-32-characters"
os.environ["ENVIRONMENT"] = "test"
os.environ["SEED_DEMO_DATA"] = "true"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["AI_API_KEY"] = ""
os.environ["MAPS_API_KEY"] = ""
os.environ["DEBUG"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security.rate_limit import limiter


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_and_me(client: TestClient):
    created = client.post(
        "/api/auth/register",
        json={
            "full_name": "Rina Das",
            "email": "rina@example.com",
            "password": "Village@123",
            "phone": "9876543210",
            "village": "Demo Gram",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["role"] == "citizen"
    assert "hashed_password" not in body
    assert "password" not in body

    duplicate = client.post(
        "/api/auth/register",
        json={"full_name": "Rina Das", "email": "rina@example.com", "password": "Village@123"},
    )
    assert duplicate.status_code == 409

    unauthenticated = client.get("/api/auth/me")
    assert unauthenticated.status_code == 401

    bad_login = client.post("/api/auth/login", json={"email": "rina@example.com", "password": "WrongPass1"})
    assert bad_login.status_code == 401

    login = client.post("/api/auth/login", json={"email": "rina@example.com", "password": "Village@123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/api/auth/me", headers=_auth(token))
    assert me.status_code == 200
    assert me.json()["email"] == "rina@example.com"

    logout = client.post("/api/auth/logout", headers=_auth(token))
    assert logout.status_code == 200
    assert client.get("/api/auth/me", headers=_auth(token)).status_code == 401


def test_complaint_ownership_and_admin_permissions(client: TestClient):
    assert client.post(
        "/api/complaints",
        json={
            "contact_name": "Nobody",
            "contact_phone": "9876543210",
            "category": "road_damage",
            "description": "This should be rejected because nobody is logged in.",
        },
    ).status_code == 401

    owner = client.post(
        "/api/auth/register",
        json={"full_name": "Owner One", "email": "owner@example.com", "password": "Village@123"},
    )
    assert owner.status_code == 201
    owner_token = client.post(
        "/api/auth/login", json={"email": "owner@example.com", "password": "Village@123"}
    ).json()["access_token"]

    created = client.post(
        "/api/complaints",
        headers=_auth(owner_token),
        json={
            "contact_name": "Owner One",
            "contact_phone": "9876543210",
            "category": "road_damage",
            "description": "The sample village road has a deep pothole near the school.",
            "village": "Demo Gram",
        },
    )
    assert created.status_code == 201
    payload = created.json()
    tracking_id = payload["tracking_id"]
    assert tracking_id.startswith("SV-")
    assert "government department" in payload["disclaimer"].lower() or "not been submitted" in payload["message"].lower()
    assert "contact_phone" not in payload

    other = client.post(
        "/api/auth/register",
        json={"full_name": "Other Person", "email": "other@example.com", "password": "Village@123"},
    )
    assert other.status_code == 201
    other_token = client.post(
        "/api/auth/login", json={"email": "other@example.com", "password": "Village@123"}
    ).json()["access_token"]
    assert client.get(f"/api/complaints/{tracking_id}", headers=_auth(other_token)).status_code == 404

    forbidden = client.patch(
        f"/api/complaints/{tracking_id}/status",
        headers=_auth(owner_token),
        json={"status": "resolved", "note": "Citizen cannot do this."},
    )
    assert forbidden.status_code == 403
    assert client.get("/api/admin/dashboard", headers=_auth(owner_token)).status_code == 403
    assert client.get("/api/admin/dashboard").status_code == 401

    admin_login = client.post(
        "/api/auth/login",
        json={"email": "admin@safevillage.demo", "password": "Admin@12345"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    dashboard = client.get("/api/admin/dashboard", headers=_auth(admin_token))
    assert dashboard.status_code == 200
    stats = dashboard.json()
    assert stats["total_citizens"] >= 1
    assert "hashed_password" not in dashboard.text
    assert "access_token" not in dashboard.text

    users = client.get("/api/admin/users", headers=_auth(admin_token))
    assert users.status_code == 200
    assert "hashed_password" not in users.text

    updated = client.patch(
        f"/api/admin/complaints/{tracking_id}",
        headers=_auth(admin_token),
        json={"status": "in_progress", "note": "Demo review only. Not a government action."},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"

    checked = client.get(f"/api/complaints/{tracking_id}", headers=_auth(owner_token))
    assert checked.status_code == 200
    assert checked.json()["status"] == "in_progress"
    assert len(checked.json()["history"]) >= 2


def test_schemes_are_marked_as_demo(client: TestClient):
    listing = client.get("/api/schemes")
    assert listing.status_code == 200
    body = listing.json()
    assert body["schemes"]
    assert all(item["is_demo"] is True for item in body["schemes"])
    assert "official" in body["notice"].lower()
    assert client.get("/api/schemes/categories").status_code == 200
    search = client.get("/api/schemes/search", params={"q": "PMAY"})
    assert search.status_code == 200
    assert any(item["short_name"] == "PMAY" for item in search.json()["schemes"])
    assert search.json()["schemes"][0]["official_url"].startswith("https://")


def test_location_search_validation(client: TestClient):
    short = client.get("/api/locations/search", params={"q": "a"})
    assert short.status_code == 422
    unsafe = client.get("/api/locations/search", params={"q": "<script>"})
    assert unsafe.status_code == 422
    missing = client.get("/api/locations/nearby")
    assert missing.status_code == 422

    found = client.get("/api/locations/search", params={"q": "hospital"})
    assert found.status_code == 200
    body = found.json()
    assert body["maps_configured"] is False
    assert body["results"]
    assert all(item["maps_url"].startswith("https://www.google.com/maps/search/") for item in body["results"])
    assert "maps_api_key" not in found.text
    assert "AIza" not in found.text
    categories = client.get("/api/locations/categories")
    assert categories.status_code == 200
    assert "hospital" in {item["code"] for item in categories.json()["categories"]}


def test_ai_fallback_in_bengali(client: TestClient):
    health = client.get("/api/ai/health")
    assert health.status_code == 200
    assert health.json()["provider_configured"] is False
    assert health.json()["speech_to_text"] == "not_configured"

    languages = client.get("/api/ai/languages")
    assert {item["code"] for item in languages.json()["languages"]} == {"bn", "hi", "en"}

    chat = client.post("/api/ai/chat", json={"message": "সরকারি প্রকল্প সম্পর্কে বলুন", "language": "bn"})
    assert chat.status_code == 200
    body = chat.json()
    assert body["mode"] == "demo_fallback"
    assert body["demo_label"]
    assert "112" in body["disclaimer"] or "সরকারি" in body["disclaimer"] or "government" in body["disclaimer"].lower()
    assert "ডেমো" in body["reply"] or "ডেমো" in body["demo_label"]


def test_emergency_contacts_are_informational(client: TestClient):
    response = client.get("/api/emergency/contacts")
    assert response.status_code == 200
    body = response.json()
    assert body["live_dispatch"] is False
    phones = {item["phone"] for item in body["contacts"]}
    assert "112" in phones
    assert all(item["is_informational"] is True for item in body["contacts"])


def test_hackathon_demonstration_flow(client: TestClient):
    registered = client.post(
        "/api/auth/register",
        json={"full_name": "Demo Flow Citizen", "email": "flow@example.com", "password": "Village@123", "village": "Demo Gram"},
    )
    assert registered.status_code == 201

    login = client.post("/api/auth/login", json={"email": "flow@example.com", "password": "Village@123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    bengali = client.post(
        "/api/ai/chat",
        headers=_auth(token),
        json={"message": "কাছের হাসপাতালের জন্য কী করব?", "language": "bn"},
    )
    assert bengali.status_code == 200
    assert bengali.json()["emergency"] is True
    assert "112" in bengali.json()["reply"]

    nearby = client.get("/api/locations/nearby", params={"category": "hospital", "q": "West Bengal"})
    assert nearby.status_code == 200
    assert nearby.json()["results"]

    schemes = client.get("/api/schemes")
    assert schemes.status_code == 200

    complaint = client.post(
        "/api/complaints",
        headers=_auth(token),
        json={
            "contact_name": "Demo Flow Citizen",
            "contact_phone": "9123456780",
            "category": "sanitation",
            "description": "Sample drain behind the community hall is blocked.",
            "village": "Demo Gram",
        },
    )
    assert complaint.status_code == 201
    tracking_id = complaint.json()["tracking_id"]

    admin_token = client.post(
        "/api/auth/login",
        json={"email": "admin@safevillage.demo", "password": "Admin@12345"},
    ).json()["access_token"]
    review = client.patch(
        f"/api/admin/complaints/{tracking_id}",
        headers=_auth(admin_token),
        json={"status": "under_review", "note": "Seen by the demo administrator."},
    )
    assert review.status_code == 200

    status_check = client.get(f"/api/complaints/{tracking_id}", headers=_auth(token))
    assert status_check.status_code == 200
    assert status_check.json()["status"] == "under_review"
