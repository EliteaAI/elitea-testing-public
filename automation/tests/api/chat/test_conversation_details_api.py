"""API smoke tests for GET /api/v2/elitea_core/conversation/<mode>/<project_id>/<id>.

Validates the fast-path serialization introduced in elitea_core#221 (issue #5786):
the endpoint now returns a bare Flask Response with a pydantic model_dump_json()
string instead of going through flask_restful's re-serialization.

Connected: https://github.com/EliteaAI/elitea_issues/issues/5786

Markers:
    api: API-only (no browser required)
    smoke: fast critical-path checks (TC-1, TC-2)
    p0: critical priority (TC-1, TC-2)
    p1: high priority (TC-3, TC-4)
    chat: chat domain

Usage::

    cd automation
    pytest tests/api/chat/test_conversation_details_api.py -v
"""

import json
import logging

import allure
import pytest

from api import ConversationAPI

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.api, pytest.mark.chat]

_NONEXISTENT_CONV_ID = 999_999_999


@pytest.mark.p0
@pytest.mark.smoke
class TestConversationDetailsHappyPath:
    """TC-1: Response is valid JSON with correct structure."""

    @allure.issue(
        "https://github.com/EliteaAI/elitea_issues/issues/5786",
        "elitea_issues #5786 — fast-path serialization",
    )
    def test_get_conversation_returns_valid_json(self, conversation_api: ConversationAPI):
        """GET /conversation returns 200 with a well-formed JSON object."""
        conv_id = None
        try:
            with allure.step("Step 1 — Create a conversation via API"):
                conv = conversation_api.create_conversation("at_5786_smoke_valid_json")
                conv_id = conv["id"]
                logger.info("Created conversation id=%s", conv_id)

            with allure.step("Step 2 — Fetch conversation details"):
                data = conversation_api.get_conversation(conv_id)

            with allure.step("Step 3 — Verify response is a dict with required fields"):
                assert isinstance(data, dict), (
                    f"Expected dict from GET /conversation, got {type(data).__name__}"
                )
                assert data.get("id") == conv_id, (
                    f"Expected id={conv_id}, got {data.get('id')}"
                )
                assert "name" in data, "Response missing 'name' field"
                assert "participants" in data, "Response missing 'participants' field (should be present by default)"
                assert "message_groups" in data, "Response missing 'message_groups' field (should be present by default)"
                assert "created_at" in data, "Response missing 'created_at' field"
                assert isinstance(data["id"], int), (
                    f"'id' should be int, got {type(data['id']).__name__}"
                )
        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for conv %s: %s", conv_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/elitea_issues/issues/5786",
        "elitea_issues #5786 — fast-path serialization",
    )
    def test_get_conversation_content_type_is_json(self, conversation_api: ConversationAPI):
        """GET /conversation returns Content-Type: application/json and parseable body."""
        conv_id = None
        try:
            with allure.step("Step 1 — Create a conversation via API"):
                conv = conversation_api.create_conversation("at_5786_smoke_content_type")
                conv_id = conv["id"]

            with allure.step("Step 2 — Fetch raw response (not pre-parsed)"):
                resp = conversation_api.get_conversation_raw(conv_id)

            with allure.step("Step 3 — Verify status code is 200"):
                assert resp.status_code == 200, (
                    f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
                )

            with allure.step("Step 4 — Verify Content-Type header contains application/json"):
                content_type = resp.headers.get("Content-Type", "")
                assert "application/json" in content_type, (
                    f"Expected 'application/json' in Content-Type, got: {content_type!r}"
                )

            with allure.step("Step 5 — Verify body is parseable JSON"):
                try:
                    parsed = json.loads(resp.text)
                except json.JSONDecodeError as exc:
                    pytest.fail(f"Response body is not valid JSON: {exc}\nBody: {resp.text[:500]}")

                assert isinstance(parsed, dict), (
                    f"Expected JSON object (dict), got {type(parsed).__name__}"
                )
        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for conv %s: %s", conv_id, exc)


@pytest.mark.p1
class TestConversationDetailsFields:
    """TC-3: Default field inclusion — participants and message_groups present."""

    @allure.issue(
        "https://github.com/EliteaAI/elitea_issues/issues/5786",
        "elitea_issues #5786 — fast-path serialization",
    )
    def test_participants_included_by_default(self, conversation_api: ConversationAPI):
        """GET /conversation includes 'participants' list by default.

        The PR moved include_participants handling from dict.pop() on the legacy
        path to pydantic exclude= on the fast path.  If the field name or mapping
        changed, participants would vanish silently.
        """
        conv_id = None
        try:
            with allure.step("Step 1 — Create a conversation"):
                conv = conversation_api.create_conversation("at_5786_participants")
                conv_id = conv["id"]

            with allure.step("Step 2 — Fetch conversation details"):
                data = conversation_api.get_conversation(conv_id)

            with allure.step("Step 3 — Verify 'participants' is a list"):
                assert "participants" in data, (
                    "'participants' key missing — field exclusion may have broken default include"
                )
                assert isinstance(data["participants"], list), (
                    f"'participants' should be a list, got {type(data['participants']).__name__}"
                )
        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for conv %s: %s", conv_id, exc)


@pytest.mark.p1
class TestConversationDetailsErrorPath:
    """TC-4: Non-existent conversation returns 400 (error path unchanged)."""

    @allure.issue(
        "https://github.com/EliteaAI/elitea_issues/issues/5786",
        "elitea_issues #5786 — fast-path serialization",
    )
    def test_nonexistent_conversation_returns_400(self, conversation_api: ConversationAPI):
        """GET /conversation with unknown ID returns 400.

        The error branch ('if not result: return {error}, 400') sits immediately
        before the new response_class() return in conversation.py.  Confirms
        the error path was not accidentally affected by the surrounding change.
        """
        with allure.step("Step 1 — GET conversation with a non-existent ID"):
            resp = conversation_api.get_conversation_raw(_NONEXISTENT_CONV_ID)

        with allure.step("Step 2 — Verify status code is 400"):
            assert resp.status_code == 400, (
                f"Expected 400 for non-existent conversation, got {resp.status_code}"
            )

        with allure.step("Step 3 — Verify error body is JSON with 'error' key"):
            try:
                body = resp.json()
            except json.JSONDecodeError:
                pytest.fail(f"400 response body is not JSON: {resp.text[:300]}")
            assert "error" in body, (
                f"Expected 'error' key in 400 response, got keys: {list(body.keys())}"
            )
