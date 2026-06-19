"""API Health Check Tests for Elitea Platform.

Verifies that the Elitea API is reachable and responds correctly.
These tests use the shared ``api`` fixture (APIClient) from conftest.

Markers:
    - smoke: quick sanity checks
    - api: API-only (no browser required)

Usage::

    cd automation
    pytest test_api_health.py -v
"""

import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.api]


class TestAPIHealth:
    """Basic health and connectivity checks for the Elitea API."""

    def test_api_root_reachable(self, api):
        """Verify the API base URL is reachable (any 2xx/3xx/401 is fine)."""
        resp = api.get("/")
        # A working server should not return 5xx
        assert resp.status_code < 500, (
            f"API returned server error {resp.status_code}: {resp.text[:200]}"
        )

    def test_api_returns_json(self, api):
        """Verify the API responds with JSON content type."""
        resp = api.get("/")
        content_type = resp.headers.get("content-type", "")
        # Most API endpoints return JSON; a redirect (3xx) may not
        if resp.status_code == 200:
            assert "json" in content_type or "text" in content_type, (
                f"Expected JSON-like content-type, got: {content_type}"
            )


class TestAuthenticatedAPI:
    """Tests that require a valid ELITEA_API_TOKEN.

    Skipped automatically when the token is not configured.
    """

    @pytest.fixture(autouse=True)
    def _require_token(self, api):
        """Skip the entire class if no API token is set."""
        if not api.api_token:
            pytest.skip("ELITEA_API_TOKEN not configured in .env.test")

    def test_list_agents(self, api):
        """Verify we can list agents for the configured project."""
        params = {
            "agents_type": "classic",
            "sort_by": "created_at",
            "sort_order": "desc",
            "query": "",
            "limit": 50,
            "offset": 0,
        }
        resp = api.get(f"/elitea_core/applications/prompt_lib/{api.project_id}", params=params)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert isinstance(data, (list, dict)), "Expected list or dict response"
