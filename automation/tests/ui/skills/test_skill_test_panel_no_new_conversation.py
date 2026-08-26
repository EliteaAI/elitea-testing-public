"""Test — SkillTestPanel does not create a new Chat conversation.

Verifies that running a test prompt through a Skill's SkillTestPanel does
NOT create a new Chat conversation. Three independent checks: (a) zero
network requests fired against any `elitea_core/conversations*` endpoint
during the test-panel run, (b) the Chat sidebar's
`chat-conversation-item-*` DOM count is unchanged, (c)
`ConversationAPI.list_conversations()`'s `total` and conversation id set
are unchanged.

Test case: ELITEA-2441
AFS: test-specs/skills/l3_test-panel-does-not-create-new-chat-conversation_ELITEA-2441.md
"""

import logging
import time

import allure
import pytest
from pages.chat_page import ChatPage
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p3, pytest.mark.regression, pytest.mark.new_verified]

FORM_SAVE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000

CONVERSATIONS_ENDPOINT_MARKER = "elitea_core/conversations"


class TestSkillTestPanelNoNewConversation:
    """ELITEA-2441 — SkillTestPanel does not create a new Chat conversation."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2441_test-panel-does-not-create-a-new-chat-conversation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_test_panel_does_not_create_new_chat_conversation(
        self, page, skill_api, conversation_api
    ):
        """Running a test prompt via the SkillTestPanel must not create a
        new Chat conversation — verified via network capture, Chat sidebar
        DOM count, and the Conversations API ground truth."""
        ts = int(time.time())
        skill_name = f"autotest-2441-{ts}"[:32]
        skill_id = None
        test_message = "Say PONG"

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        conversation_requests = []
        page.on(
            "request",
            lambda req: conversation_requests.append(req.url)
            if CONVERSATIONS_ENDPOINT_MARKER in req.url
            else None,
        )

        try:
            with allure.step(
                "Step 1 — Note the current number of conversations in the Chat section"
            ):
                baseline = conversation_api.list_conversations()
                baseline_total = baseline["total"]
                baseline_ids = {row["id"] for row in baseline["rows"]}
                logger.info(
                    "Baseline conversations — total=%d ids=%s",
                    baseline_total, baseline_ids,
                )

            with allure.step("Step 2 — Open a Skill and run a test via the test panel"):
                list_page = SkillsListPage(page)
                list_page.navigate_to_create()

                form_page = SkillFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=skill_name,
                    instructions="Always reply with the single word: PONG",
                    description="Autotest skill for ELITEA-2441 no-new-conversation flow.",
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = SkillDetailPage(page)
                detail_page.verify_on_detail_page()
                skill_id = detail_page.get_skill_id()
                assert skill_id, "Expected a numeric Skill ID on the detail page"
                logger.info("Created skill id=%s name=%s", skill_id, skill_name)

                initial_count = detail_page.get_test_message_count()
                detail_page.send_test_message(test_message)
                detail_page.wait_for_test_response(
                    initial_count=initial_count,
                    timeout=AI_RESPONSE_TIMEOUT,
                )
                response = detail_page.get_last_test_response()
                assert response, "Expected a non-empty test-panel response"

                assert not conversation_requests, (
                    "Expected zero requests to elitea_core/conversations* during "
                    f"skill creation + test-panel run, got: {conversation_requests}"
                )

            with allure.step("Step 3 — Navigate to Chat"):
                chat_page = ChatPage(page)
                chat_page.navigate_to_chat()
                assert "/chat" in page.url, f"Expected to land on /chat, got: {page.url}"

            with allure.step(
                "Step 4 — Verify no new conversation was created by the Skill test execution"
            ):
                after = conversation_api.list_conversations()
                after_total = after["total"]
                after_ids = {row["id"] for row in after["rows"]}
                assert after_total == baseline_total, (
                    f"Expected conversation total to stay {baseline_total}, got {after_total}"
                )
                assert after_ids == baseline_ids, (
                    f"Expected conversation ids to stay {baseline_ids}, got {after_ids}"
                )

                sidebar_count = chat_page.get_conversation_item_rows().count()
                baseline_sidebar_count = len(baseline_ids)
                assert sidebar_count == baseline_sidebar_count, (
                    f"Expected Chat sidebar conversation-item count to stay "
                    f"{baseline_sidebar_count}, got {sidebar_count}"
                )

            with allure.step(
                "Side-channel check — no console errors across the case's own 4 steps"
            ):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )

        finally:
            with allure.step("Cleanup — delete the skill created for this test"):
                if skill_id is not None:
                    skill_api.delete_skill(int(skill_id))
                    logger.info("Deleted skill id=%s via API", skill_id)
