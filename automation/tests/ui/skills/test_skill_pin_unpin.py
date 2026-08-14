"""Test for Skill — Pin/Unpin.

Verifies that a skill can be pinned to the top of the Skills list via the
detail page's three-dot menu ("Pin to top"), that the list view reflects the
pinned state (position + list-row icon), and that unpinning via the same
menu reverts both the menu label and the list position.

Test case: ELITEA-2435
AFS: test-specs/skills/l3_skill-pin-unpin-flow_ELITEA-2435.md
"""

import logging
import time

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage
from pages.skills_list_page import SkillsListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]


class TestSkillPinUnpin:
    """ELITEA-2435 — Skill detail-page pin/unpin round trip."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2435_skill-pin-unpin-flow.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_skill_pin_moves_to_top_and_unpin_reverts(self, page, skill_api):
        """Pinning a skill (via the detail-page menu) moves it to the top of
        the list; unpinning (same menu) reverts it."""
        ts = int(time.time())
        skill_a_name = f"autotest-pin-skill-a-{ts}"[:32]
        skill_b_name = f"autotest-pin-skill-b-{ts + 5}"[:32]
        skill_a_id = None
        skill_b_id = None

        try:
            with allure.step("Setup — Create Skill A and Skill B via API"):
                skill_a = skill_api.create_skill(
                    name=skill_a_name,
                    description="Autotest skill A for ELITEA-2435 pin/unpin flow.",
                    instructions="You are a test skill used for pin/unpin automation. Reply 'ok'.",
                )
                skill_a_id = skill_a["id"]

                # Skill B is created second so it sorts above A under the
                # list's default created_at-desc order — this is what gives
                # Steps 1/9/15 a real "position" to move to/from (AFS Test
                # Data — a single skill wouldn't force a position CHANGE if
                # it happened to already be topmost).
                skill_b = skill_api.create_skill(
                    name=skill_b_name,
                    description="Autotest skill B for ELITEA-2435 pin/unpin flow.",
                    instructions="You are a test skill used for pin/unpin automation. Reply 'ok'.",
                )
                skill_b_id = skill_b["id"]

                assert skill_a_id, "Expected a numeric id for Skill A"
                assert skill_b_id, "Expected a numeric id for Skill B"
                logger.info(
                    "Created skills — A id=%s name=%s, B id=%s name=%s",
                    skill_a_id, skill_a_name, skill_b_id, skill_b_name,
                )

            with allure.step("Step 1 — Navigate to the Skills list and capture the baseline order"):
                list_page = SkillsListPage(page)
                list_page.navigate()

                console_messages = []
                page.on(
                    "console",
                    lambda msg: console_messages.append(msg) if msg.type in ("error", "warning") else None,
                )

                baseline_order = list_page.get_visible_skill_names()
                index_a = baseline_order.index(skill_a_name)
                index_b = baseline_order.index(skill_b_name)
                assert index_b < index_a, (
                    f"Expected Skill B above Skill A before pinning, got order: {baseline_order}"
                )
                assert list_page.get_pin_toggle_label(skill_a_id) == "Pin to top", (
                    "Skill A's list-row pin button should read 'Pin to top' before pinning"
                )

            with allure.step("Step 2 — Open Skill A's detail page"):
                list_page.click_skill_card(skill_a_name)
                detail_page = SkillDetailPage(page)
                detail_page.wait_for_page_load()

            with allure.step("Step 3 — Open the overflow (three-dot) menu"):
                detail_page.open_actions_menu()

            with allure.step("Step 4 — Verify the menu shows 'Pin to top'"):
                assert detail_page.get_pin_toggle_menu_label() == "Pin to top", (
                    "Pin-toggle menu item should read 'Pin to top' before pinning"
                )

            with allure.step("Step 5 — Click 'Pin to top'"):
                response = detail_page.click_pin_toggle_menu_item()
                assert response.status == 201, (
                    f"Expected 201 Created from the pin request, got {response.status}"
                )

            with allure.step("Step 6 — Re-open the overflow menu"):
                detail_page.open_actions_menu()

            with allure.step("Step 7 — Verify the menu now shows 'Unpin from top'"):
                assert detail_page.get_pin_toggle_menu_label() == "Unpin from top", (
                    "Pin-toggle menu item should flip to 'Unpin from top' after pinning"
                )

            with allure.step("Step 8 — Navigate back to the Skills list"):
                list_page.navigate()

            with allure.step(
                "Step 9 — Verify the pinned Skill moved to the top and its list-row icon flipped"
            ):
                pinned_order = list_page.get_visible_skill_names()
                index_a = pinned_order.index(skill_a_name)
                index_b = pinned_order.index(skill_b_name)
                assert index_a < index_b, (
                    f"Expected Skill A above Skill B after pinning, got order: {pinned_order}"
                )
                assert list_page.get_pin_toggle_label(skill_a_id) == "Unpin from top", (
                    "Skill A's list-row pin button should flip to 'Unpin from top' after pinning"
                )

            with allure.step("Step 10 — Re-open the same Skill"):
                list_page.click_skill_card(skill_a_name)
                detail_page.wait_for_page_load()

            with allure.step("Step 11 — Open the overflow menu and click 'Unpin'"):
                detail_page.open_actions_menu()
                response = detail_page.click_pin_toggle_menu_item()
                assert response.status == 204, (
                    f"Expected 204 No Content from the unpin request, got {response.status}"
                )

            with allure.step("Step 12 — Re-open the overflow menu"):
                detail_page.open_actions_menu()

            with allure.step("Step 13 — Verify the menu now shows 'Pin to top' again"):
                assert detail_page.get_pin_toggle_menu_label() == "Pin to top", (
                    "Pin-toggle menu item should flip back to 'Pin to top' immediately after "
                    "unpinning, before navigating away"
                )

            with allure.step("Step 14 — Navigate back to the Skills list"):
                list_page.navigate()

            with allure.step("Step 15 — Verify the Skill is no longer marked as pinned"):
                reverted_order = list_page.get_visible_skill_names()
                index_a = reverted_order.index(skill_a_name)
                index_b = reverted_order.index(skill_b_name)
                assert index_b < index_a, (
                    f"Expected Skill B above Skill A again after unpinning, got order: {reverted_order}"
                )
                assert list_page.get_pin_toggle_label(skill_a_id) == "Pin to top", (
                    "Skill A's list-row pin button should read 'Pin to top' again after unpinning"
                )

            with allure.step("Side-channel check — no console errors/warnings across the full flow"):
                assert not console_messages, (
                    f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
                )

        finally:
            with allure.step("Cleanup — delete both skills created for this test"):
                if skill_a_id is not None:
                    skill_api.delete_skill(skill_a_id)
                    logger.info("Deleted skill id=%s", skill_a_id)
                if skill_b_id is not None:
                    skill_api.delete_skill(skill_b_id)
                    logger.info("Deleted skill id=%s", skill_b_id)
