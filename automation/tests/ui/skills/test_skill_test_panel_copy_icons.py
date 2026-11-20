"""Skill test panel — Copy markdown / Copy text icons visible, clickable, toast-confirmed (ELITEA-4757).

Spec: test-specs/skills/l1_skill-test-panel-copy-markdown-and-copy-text-icons-toast_ELITEA-4757.md
"""

import re
import time

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p1, pytest.mark.regression]

T = 15_000
RUN_TIMEOUT = 90_000
TOAST_DISMISS_TIMEOUT = 20_000


@pytest.mark.tms("ELITEA-4757")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/skills/"
    "ELITEA-4757_skill-test-panel-copy-markdown-and-copy-text-actions.md",
    "onetest-ai Test Case link",
)
def test_skill_test_panel_copy_icons_show_tooltip_and_toast(page: Page, skill_api):
    """Both copy icons are visible under the skill response; tooltips and click toasts match."""
    page.set_viewport_size({"width": 1600, "height": 1400})
    detail = SkillDetailPage(page)
    skills = SkillsListPage(page)
    form = SkillFormPage(page)
    skill_id = None
    try:
        with allure.step("Step 1 — Create a skill; its page opens with the Test button visible and enabled"):
            skills.navigate_to_create()
            skills.dismiss_announcement_dialog_if_present()
            form.fill_form(
                name=f"autotest-4757-{int(time.time())}"[:32],
                instructions="reply echo",
                description="Autotest skill for ELITEA-4757.",
            )
            form.save_and_wait_for_navigation()
            detail.verify_on_detail_page()
            skill_id = int(re.search(r"/skills/all/(\d+)", page.url).group(1))
            expect(detail.test_skill_button).to_be_visible(timeout=T)
            expect(detail.test_skill_button).to_be_enabled(timeout=T)

        with allure.step("Step 2 — Click Test; panel with input opens"):
            detail.open_test_skill_panel(timeout=T)
            expect(detail.test_panel).to_be_visible(timeout=T)
            expect(detail.test_panel_input).to_be_visible(timeout=T)

        with allure.step("Step 3 — Send message; the skill response is shown"):
            detail.send_test_message("run")
            detail.wait_for_test_response(initial_count=0, timeout=RUN_TIMEOUT)
            assert detail.get_last_test_response(), "Skill response should be non-empty"

        with allure.step("Step 4 — Copy markdown and Copy text icons are visible and enabled"):
            assert detail.is_last_response_copy_icon_enabled("markdown"), "Copy markdown icon not visible/enabled"
            assert detail.is_last_response_copy_icon_enabled("text"), "Copy text icon not visible/enabled"

        with allure.step("Step 5 — Hover the Copy markdown icon; tooltip 'Copy markdown'"):
            assert detail.hover_last_response_copy_icon("markdown") == "Copy markdown"

        with allure.step("Step 6 — Click Copy markdown; toast 'Markdown copied to clipboard.'"):
            toast = detail.click_last_response_copy_icon("markdown")
            assert toast == "Markdown copied to clipboard.", f"Unexpected toast: {toast!r}"
            expect(detail.toast_message).to_have_count(0, timeout=TOAST_DISMISS_TIMEOUT)

        with allure.step("Step 7 — Hover the Copy text icon; tooltip 'Copy text'"):
            assert detail.hover_last_response_copy_icon("text") == "Copy text"

        with allure.step("Step 8 — Click Copy text; toast 'Text copied to clipboard.'"):
            toast = detail.click_last_response_copy_icon("text")
            assert toast == "Text copied to clipboard.", f"Unexpected toast: {toast!r}"
    finally:
        with allure.step("Cleanup — delete the skill"):
            if skill_id is not None:
                skill_api.delete_skill(skill_id)
