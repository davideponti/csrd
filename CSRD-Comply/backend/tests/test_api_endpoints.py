"""
CSRD Comply — Step 30: Integration tests for all API endpoints.

Tests:
- Health / Root
- Auth (register, login)
- Companies
- Reports CRUD
- Subscriptions

NOTE: These tests use strict assertions. Every endpoint is expected to
return a specific status code and response shape. Conditional assertions
(if res.status_code == 200) have been removed — tests will fail loudly
if an endpoint is broken.
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthRoot:
    """Health and root endpoints."""

    def test_root(self, client: TestClient):
        res = client.get("/")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["message"] == "CSRD Comply API"
        assert data["version"] == "1.0.0"

    def test_health(self, client: TestClient):
        res = client.get("/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["status"] == "healthy"


class TestAuth:
    """Auth endpoints (register, login)."""

    REGISTER_URL = "/api/v1/auth/register"
    LOGIN_URL = "/api/v1/auth/login"

    def test_register_success(self, client: TestClient):
        res = client.post(self.REGISTER_URL, json={
            "email": "newuser@test.com",
            "password": "TestPass123!",
            "company_name": "New Company Srl",
        })
        assert res.status_code in (200, 201), (
            f"Registration failed: {res.status_code} {res.text}"
        )
        data = res.json()
        assert "access_token" in data, f"Response missing access_token: {data}"

    def test_register_invalid_email(self, client: TestClient):
        res = client.post(self.REGISTER_URL, json={
            "email": "not-an-email",
            "password": "TestPass123!",
            "company_name": "Test",
        })
        assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"

    def test_login_success(self, client: TestClient, auth_header, db):
        # Register a user first
        res = client.post(self.REGISTER_URL, json={
            "email": "login@test.com",
            "password": "TestPass123!",
            "company_name": "Login Test Srl",
        })
        assert res.status_code in (200, 201), (
            f"Registration failed: {res.status_code} {res.text}"
        )

        # Now login
        res2 = client.post(self.LOGIN_URL, json={
            "email": "login@test.com",
            "password": "TestPass123!",
        })
        assert res2.status_code == 200, f"Login failed: {res2.status_code} {res2.text}"
        assert "access_token" in res2.json(), f"Response missing access_token: {res2.json()}"

    def test_login_wrong_password(self, client: TestClient):
        res = client.post(self.LOGIN_URL, json={
            "email": "nobody@test.com",
            "password": "wrongpass",
        })
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


class TestCompanies:
    """Companies endpoints."""

    ME_URL = "/api/v1/companies/me"

    def test_get_me_unauthorized(self, client: TestClient):
        res = client.get(self.ME_URL)
        assert res.status_code in (401, 403), (
            f"Expected 401/403, got {res.status_code}: {res.text}"
        )

    def test_get_me_authorized(self, client: TestClient, auth_header):
        res = client.get(self.ME_URL, headers=auth_header)
        assert res.status_code == 200, (
            f"Expected 200, got {res.status_code}: {res.text}"
        )
        data = res.json()
        assert "company_name" in data, f"Response missing company_name: {data}"

    def test_update_me(self, client: TestClient, auth_header):
        res = client.patch(
            self.ME_URL,
            headers=auth_header,
            json={"company_name": "Updated Name Srl"},
        )
        assert res.status_code == 200, (
            f"Expected 200, got {res.status_code}: {res.text}"
        )
        data = res.json()
        assert data["company_name"] == "Updated Name Srl"


class TestReports:
    """Reports endpoints."""

    BASE_URL = "/api/v1/reports"

    def test_list_reports(self, client: TestClient, auth_header):
        res = client.get(self.BASE_URL, headers=auth_header)
        assert res.status_code == 200, (
            f"Expected 200, got {res.status_code}: {res.text}"
        )
        data = res.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}: {data}"

    def test_create_report(self, client: TestClient, auth_header):
        res = client.post(
            self.BASE_URL,
            headers=auth_header,
            json={"reporting_year": 2026, "title": "Test Report"},
        )
        assert res.status_code in (200, 201), (
            f"Expected 200/201, got {res.status_code}: {res.text}"
        )
        data = res.json()
        assert data["title"] == "Test Report"
        assert data["status"] == "draft"

    def test_create_report_missing_fields(self, client: TestClient, auth_header):
        res = client.post(
            self.BASE_URL,
            headers=auth_header,
            json={},
        )
        assert res.status_code == 422, (
            f"Expected 422, got {res.status_code}: {res.text}"
        )

    def test_get_report(self, client: TestClient, auth_header, sample_report, db):
        res = client.get(
            f"{self.BASE_URL}/{sample_report.id}",
            headers=auth_header,
        )
        assert res.status_code == 200, (
            f"Expected 200, got {res.status_code}: {res.text}"
        )
        data = res.json()
        assert str(data["id"]) == str(sample_report.id)


class TestSubscriptions:
    """Subscriptions endpoints."""

    BASE_URL = "/api/v1/subscriptions"

    def test_list_plans(self, client: TestClient):
        res = client.get(f"{self.BASE_URL}/plans")
        assert res.status_code == 200, (
            f"Expected 200, got {res.status_code}: {res.text}"
        )
        data = res.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) >= 4, f"Expected >=4 plans, got {len(data)}"
        plan_names = [p["name"] for p in data]
        assert "Free" in plan_names
        assert "Pro" in plan_names

    def test_get_plan_detail(self, client: TestClient):
        res = client.get(f"{self.BASE_URL}/plans/pro")
        assert res.status_code == 200, (
            f"Expected 200, got {res.status_code}: {res.text}"
        )
        data = res.json()
        assert data["name"] == "Pro"
        assert data["price_monthly"] == 49

    def test_get_plan_not_found(self, client: TestClient):
        res = client.get(f"{self.BASE_URL}/plans/nonexistent")
        assert res.status_code == 404, (
            f"Expected 404, got {res.status_code}: {res.text}"
        )

    def test_subscribe_unauthenticated(self, client: TestClient):
        res = client.post(
            f"{self.BASE_URL}/subscribe",
            json={"plan_id": "pro", "billing_cycle": "monthly"},
        )
        assert res.status_code in (401, 403), (
            f"Expected 401/403, got {res.status_code}: {res.text}"
        )
