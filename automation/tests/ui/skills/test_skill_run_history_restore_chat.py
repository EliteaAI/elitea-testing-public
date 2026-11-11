"""Test — Skill Run History page display and Restore chat from history.

Test case: ELITEA-4631
AFS: test-specs/skills/l2_skill-run-history-display-and-restore-chat_ELITEA-4631.md
"""

import logging
import re
import time

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression]

AI_RESPONSE_TIMEOUT = 45_000


class TestSkillRunHistory:
    """ELITEA-4631 — run history table + Restore chat continues the conversation."""

    @pytest.mark.tms("ELITEA-4631")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-4631_skill-run-history-and-restore-chat.md",
        "onetest-ai Test Case link",
    )
    def test_skill_run_history_display_and_restore_chat(self, page, skill_api):
        ts = int(time.time())
        skill_name = f"autotest-4631-{ts}"[:32]
        skill_id = None
        created = skill_api.create_skill(
            name=skill_name,
            description="Autotest skill for ELITEA-4631 run history.",
            instructions="Convert the user text to UPPERCASE and reply with only that.",
        )
        skill_id = created["id"] if isinstance(created, dict) else created
        try:
            detail = SkillDetailPage(page)

            with allure.step("Step 1 — Open the skill and run one prompt in the test panel"):
                detail.navigate(int(skill_id))
                detail.dismiss_platform_release_banner_if_present()
                detail.open_test_skill_panel()
                initial = detail.get_test_message_count()
                detail.send_test_message("hello one")
                detail.wait_for_test_response(initial_count=initial, timeout=AI_RESPONSE_TIMEOUT)
                assert "HELLO ONE" in detail.get_last_test_response().upper()

            with allure.step("Step 2 — Open Run History from the overflow menu"):
                detail.open_run_history()
                assert re.search(rf"/skills/all/{skill_id}/history", page.url), page.url
                assert detail.page_contains_text(skill_name), (
                    "Breadcrumb should show the skill name"
                )

            with allure.step("Step 3 — Verify table columns and a single run row"):
                header = (detail.run_history_header.text_content() or "")
                for col in ("Date", "Version", "Duration"):
                    assert col in header, f"Column {col!r} missing from header {header!r}"
                assert detail.run_history_rows.count() == 1, "Fresh skill must have exactly one run"

            with allure.step("Step 4 — Verify date, version and duration formats"):
                row_text = detail.get_run_history_row_texts()[0]
                assert re.search(r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)", row_text), row_text
                assert "base" in row_text, row_text
                assert re.search(r"\d+(\.\d+)? s", row_text), row_text

            with allure.step("Step 5 — Verify the row is selected and shows the run transcript"):
                detail.wait_for_selected_run_with_messages()
                transcript = " ".join(detail.get_message_texts())
                assert "hello one" in transcript
                assert "HELLO ONE" in transcript

            with allure.step("Step 6 — Open the row menu and verify Restore chat is offered"):
                detail.open_run_row_menu()
                names = detail.get_run_row_menu_item_names()
                assert any("Restore chat" in n for n in names), names

            with allure.step("Step 7 — Click Restore chat and verify prior messages are restored"):
                detail.click_restore_chat()
                detail.open_test_skill_panel()
                detail.wait_for_any_message()
                restored = " ".join(detail.get_message_texts())
                assert "hello one" in restored
                assert "HELLO ONE" in restored
                before = detail.get_test_message_count()
                assert before == 2, f"Expected 2 restored messages, got {before}"

            with allure.step("Step 8 — Send a new message in the restored chat and verify the reply"):
                detail.send_test_message("hello two")
                detail.wait_for_test_response(initial_count=before, timeout=AI_RESPONSE_TIMEOUT)
                assert detail.get_test_message_count() == 4
                assert "HELLO TWO" in detail.get_last_test_response().upper()
                texts = detail.get_message_texts()
                assert "HELLO ONE" in texts[1].upper() and "HELLO TWO" in texts[3].upper()
        finally:
            with allure.step("Cleanup — delete the skill"):
                skill_api.delete_skill(int(skill_id))
