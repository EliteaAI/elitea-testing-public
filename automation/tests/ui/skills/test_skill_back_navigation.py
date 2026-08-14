"""UI Test for Skill editor Back-button navigation (ELITEA-2429).

Verifies that clicking the Back button on a Skill editor page returns the
user to the Skills list (/skills/all), rather than redirecting to Chat or
another page.

Spec: test-specs/skills/l2_skill-editor-back-button-returns-to-skills-list_ELITEA-2429.md

Markers:
    - ui: requires browser
    - skills: skill-related tests
    - p2: medium priority (case frontmatter priority is "medium")
"""

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.new]

NAVIGATION_TIMEOUT = 15000


@pytest.mark.p2
@pytest.mark.regression
def test_back_button_from_skill_editor_returns_to_skills_list(page):
    """Back button on the Skill editor page returns to the Skills list
    (/skills/all), not Chat or any other page (ELITEA-2429).

    Reuses an existing skill from the project's Skills list — read-only,
    no test data created or torn down.
    """
    list_page = SkillsListPage(page)
    detail_page = SkillDetailPage(page)

    console_messages = []
    page.on(
        "console",
        lambda msg: console_messages.append(msg) if msg.type == "error" else None,
    )

    with allure.step("Step 1 — Open any Skill for editing"):
        list_page.navigate()
        skills_before = list_page.get_skill_card_names(timeout=NAVIGATION_TIMEOUT)
        assert skills_before, (
            "Precondition: at least one skill must exist in the project's "
            "Skills list for this case to be exercised"
        )

        target_skill_name = skills_before[0]
        list_page.click_skill_card(target_skill_name)
        detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
        assert "/skills/all/" in page.url, (
            f"Expected to land on a skill detail/editor route after selecting "
            f"'{target_skill_name}', got: {page.url}"
        )

    with allure.step("Step 2 — Click the Back button in the Skill editor header"):
        detail_page.click_back_button(timeout=NAVIGATION_TIMEOUT)
        list_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)

    with allure.step(
        "Step 3 — Verify navigation goes to the Skills list page and NOT "
        "to the Chats page"
    ):
        assert "/skills/all" in page.url, (
            f"Back navigation should return to the Skills list route "
            f"(/skills/all), got: {page.url}"
        )
        assert "/chat" not in page.url, (
            f"Back navigation must NOT redirect to the Chats page, got: {page.url}"
        )
        list_page.verify_dashboard_header_visible()

        skills_after = list_page.get_skill_card_names(timeout=NAVIGATION_TIMEOUT)
        assert target_skill_name in skills_after, (
            f"Skills list after Back navigation should still contain the "
            f"skill opened in Step 1 ('{target_skill_name}') — list should "
            f"be freshly re-rendered, not blank or stuck. Visible skills: "
            f"{skills_after}"
        )

    with allure.step(
        "Side-channel check — no console errors across the navigate → "
        "detail → back flow"
    ):
        assert not console_messages, (
            "Unexpected console errors during Back navigation: "
            f"{[m.text for m in console_messages]}"
        )
