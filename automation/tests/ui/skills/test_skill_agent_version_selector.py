"""Attach a Skill to an Agent and verify the version selector (ELITEA-1789).

Verifies the functional flow of attaching a skill to an agent: the attached
skill card shows a version selector (`.version-text` + chevron), the default
version (`base`) is pre-selected, the selector opens a real "Versions" menu
when clicked via a correctly-scoped locator, and attachment + version
selection persist across a full page reload (attach is auto-saved via API,
so there is no explicit agent-level Save to click).

Known defect (non-blocking, isolated) — SPLIT in the ELITEA-1789 testid-only
rework: the version-selector trigger's testid gap is now closed
(`skill-version-selector-trigger-{skill_id}` / `skill-version-selector-menu-{skill_id}`
/ `skill-version-option-{version_name}`, added via `add-data-testid`, EliteaUI
draft PR #545) — but the trigger still carries no ARIA role, no accessible
name, and `tabIndex=-1`, so it remains not keyboard-operable. That surviving
a11y half stays open as github.com/EliteaAI/elitea-testing-public/issues/46.
Per the AFS, this case's own pass/fail criteria are hard-asserted (not
`expect.soft()`'d): nothing here is flaky, and the gap is a handle-quality/
accessibility issue, not an intermittent functional failure.
`AgentDetailPage.open_skill_version_selector()` / `get_skill_version_text()`
now use testid-scoped `LocatorDescriptor`/template-constant locators —
replacing this test's PR #47 predecessor's CSS-class (`.version-text`) +
raw-text + xpath-ancestor handles, per `.agents/testing.md` § Locator policy.

Spec: test-specs/skills/l3_attach-skill-to-agent-with-version-selector_ELITEA-1789.md
"""

import logging

import allure
import pytest

from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.skills")

SKILL_NAME = "elitea-1789-versel-skill"
SKILL_INSTRUCTIONS = (
    "You are a test skill created for ELITEA-1789 version selector "
    "verification. Respond with VERSEL."
)
AGENT_NAME = "elitea-1789-versel-agent"


def _create_skill(page, name: str, instructions: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Mirrors the create flow in test_skill_agent_interaction.py: fill the form
    (name / description / CodeMirror instructions), save, and confirm the
    nav-blocker dialog that fires on every save from the create form.
    """
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(
        name=name,
        instructions=instructions,
        description=f"ELITEA-1789 automation skill — {name}",
    )
    form_page.wait_for_form_validation()
    assert form_page.is_save_enabled(), (
        f"Save should be enabled after filling all required fields for skill '{name}'"
    )
    form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

    detail_page = SkillDetailPage(page)
    detail_page.verify_on_detail_page()
    skill_id = int(detail_page.get_skill_id())
    logger.info("Created skill %r with id=%d", name, skill_id)
    return skill_id


class TestAttachSkillToAgentWithVersionSelector:
    """Attach a Skill to an Agent and verify version selector (ELITEA-1789, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1789_attach-skill-to-agent-with-version-selector.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/46",
        "Known defect: version-selector trigger not keyboard-accessible / no testid",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_attach_skill_to_agent_with_version_selector(self, page, agent_api, skill_api):
        """Create a skill + agent, attach the skill, and verify the version
        selector shows the default version, opens a real Versions menu, and
        persists across a full page reload.

        Steps (AFS test-specs/skills/l3_attach-skill-to-agent-with-version-selector_ELITEA-1789.md):
        1. Create a Skill with a saved `base` version.
        2. Create an Agent.
        3. Locate the Skills attachment section (expanded by default).
        4-5. Attach the Skill; verify the counter updates and the card renders.
        6. Verify the attached Skill card shows a version selector, and that
           clicking it (via a correctly-scoped `.version-text` locator, NOT a
           role-based one) opens a real "Versions" menu — hard-asserted
           functional flow per the AFS (known defect #46 is a handle-quality/
           accessibility gap, not a flaky functional failure).
        7. Confirm the default version (`base`) is shown pre-selected, both
           on the card and as the sole entry in the opened Versions menu.
        8. Confirm persistence via a full page reload (no explicit
           agent-level Save is available — attach is auto-saved via API).
        """
        skill_id = None
        agent_id = None

        try:
            with allure.step("Step 1 — Create a Skill with a saved base version"):
                skill_id = _create_skill(page, SKILL_NAME, SKILL_INSTRUCTIONS)

            with allure.step("Step 2 — Create an Agent"):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME,
                    description="ELITEA-1789 automation agent — version selector",
                    instructions="You are a helpful assistant.",
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required agent fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = AgentDetailPage(page)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                detail_page.verify_on_detail_page()
                agent_id = int(detail_page.get_agent_id())
                logger.info("Created agent %r with id=%d", AGENT_NAME, agent_id)

            with allure.step("Step 3 — Skills attachment section is visible"):
                detail_page.ensure_skills_section_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert "0/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 0 skills attached before attaching"
                )

            with allure.step("Step 4-5 — Attach the Skill to the Agent"):
                detail_page.attach_skill(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching"
                )
                assert detail_page.is_skill_attached(SKILL_NAME), (
                    f"Skill card for '{SKILL_NAME}' should render after attaching"
                )

            with allure.step(
                "Step 6 — Version selector is present and functional "
                "(hard-asserted: known defect #46 is a handle-quality/accessibility "
                "gap on the trigger, not a flaky functional failure)"
            ):
                version_text = detail_page.get_skill_version_text(
                    SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )
                assert version_text == "base", (
                    f"Attached skill card should show version 'base', got: {version_text!r}"
                )

                detail_page.open_skill_version_selector(
                    SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )
                assert detail_page.is_versions_menu_open(
                    SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT,
                ), (
                    "Clicking the version selector (testid-scoped trigger) "
                    "should open a real 'Versions' menu"
                )

            with allure.step("Step 7 — Default version (base) is pre-selected"):
                menu_items = detail_page.get_versions_menu_item_names(
                    SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )
                assert menu_items == ["base"], (
                    f"Versions menu should list exactly one entry, 'base' "
                    f"(sole saved version), got: {menu_items!r}"
                )
                detail_page.close_versions_menu()

            with allure.step(
                "Step 8 — Confirm persistence via full page reload "
                "(attach is auto-saved via API; no explicit agent-level Save "
                "action is available once a skill is attached)"
            ):
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                counter_after_reload = detail_page.wait_for_skills_counter(
                    "1/", timeout=UI_ELEMENT_TIMEOUT,
                )
                assert "1/" in counter_after_reload, (
                    "Skills counter should still show 1 skill attached after reload, "
                    f"got: {counter_after_reload!r}"
                )
                assert detail_page.is_skill_attached(SKILL_NAME), (
                    f"Skill card for '{SKILL_NAME}' should still render after reload"
                )
                version_text_after_reload = detail_page.get_skill_version_text(
                    SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )
                assert version_text_after_reload == "base", (
                    "Attached skill's version should still be 'base' after reload, "
                    f"got: {version_text_after_reload!r}"
                )

        finally:
            # Cleanup per AFS: delete agent first (teardown hygiene), then the
            # skill, tolerating individual failures (mirrors ELITEA-1735/1737/
            # 1738/1739's cleanup pattern).
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning("Cleanup: failed to delete agent id=%s: %s", agent_id, exc)
            if skill_id is not None:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%d", skill_id)
                except Exception as exc:
                    logger.warning("Cleanup: failed to delete skill id=%s: %s", skill_id, exc)
