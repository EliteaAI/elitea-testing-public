"""Agent "Save As Version" preserves all attached Skills (ELITEA-1889).

Creates a Skill and an Agent via the live UI create flows, attaches the
Skill to the Agent, then uses "Save As Version" to create a new named
version ("v1") and verifies the attached Skill is still listed under the
new version — both in the UI (skill card + counter) and at the API layer
(a fresh `GET .../application_skills/prompt_lib/{project_id}/{new_version_id}`
response), so the assertion isn't resting on a possibly-stale client-side
render carried over from the prior version's state.

This is a **resume** of a case previously blocked by
EliteaAI/elitea-testing-public#524 (Agent creation 400 on default LLM
settings via the plain `/agents/create` UI form). That defect is confirmed
fixed on the DEV backend as of this AFS pass — the plain UI create flow is
used here deliberately (mirroring `test_skill_agent_version_selector.py`,
ELITEA-1789) specifically because it exercises the previously-blocking
path end-to-end, rather than routing around it via
`AgentAPI.create_agent_full()`.

Known, separate, still-open issue (NOT exercised by this test): the
API-level `AgentAPI.create_agent()` helper (`automation/api/client.py:366`,
used by the shared `agent_id` pytest fixture) hard-codes
`temperature: 0.6, reasoning_effort: "medium"` and still 400s against the
project's reasoning-capable default model. This test avoids that helper
entirely by creating its Agent via the UI form (as ELITEA-1789 does), so it
is unaffected by that still-open sub-issue.

Spec: test-specs/agents/lcritical_agent-save-as-version-preserves-skills_ELITEA-1889.md
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

pytestmark = [pytest.mark.ui, pytest.mark.agents]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.agents")

SKILL_NAME = "elitea-1889-versioned-skill"
SKILL_INSTRUCTIONS = (
    "You are a test skill created for ELITEA-1889 save-as-version "
    "preservation verification. Respond with VERSIONED."
)
AGENT_NAME = "elitea-1889-versioning-agent"
VERSION_NAME = "v1"


def _create_skill(page, name: str, instructions: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Mirrors the create flow already proven in
    `test_skill_agent_version_selector.py` (ELITEA-1789): fill the form
    (name / description / CodeMirror instructions), save, and confirm on
    the detail page.
    """
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(
        name=name,
        instructions=instructions,
        description=f"ELITEA-1889 automation skill — {name}",
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


class TestAgentSaveAsVersionPreservesSkills:
    """Agent "Save As Version" preserves all attached Skills (ELITEA-1889, l1/p0)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1889_agent-save-as-version-preserves-skills.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/524",
        "Verifies fix: plain UI Agent create form (default LLM settings) no "
        "longer 400s",
    )
    @pytest.mark.p0
    @pytest.mark.regression
    def test_agent_save_as_version_preserves_skills(self, page, agent_api, skill_api):
        """Create a Skill + Agent (both via UI), attach the Skill, Save As
        Version, and verify the Skill is still attached under the new
        version — confirmed both via the UI and a fresh API response."""
        skill_id = None
        agent_id = None
        detail_page = None

        try:
            with allure.step("Step 1 — Create a Skill with a saved base version"):
                skill_id = _create_skill(page, SKILL_NAME, SKILL_INSTRUCTIONS)

            with allure.step(
                "Step 2 — Create an Agent via the plain UI create form "
                "(default LLM settings, no fields touched beyond Name/"
                "Description) — verifies EliteaAI/elitea-testing-public#524 "
                "is fixed: Save must succeed with a 201, not 400"
            ):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME,
                    description="ELITEA-1889 automation agent — save-as-version preserves skills",
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling Name + Description "
                    "with default LLM settings left untouched"
                )

                with page.expect_response(
                    lambda r: (
                        "/elitea_core/applications/prompt_lib/" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=FORM_SAVE_TIMEOUT,
                ) as create_response_info:
                    form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                assert create_response_info.value.status == 201, (
                    "Agent create POST should return 201 with default LLM "
                    f"settings (regression check for #524), got: "
                    f"{create_response_info.value.status}"
                )

                detail_page = AgentDetailPage(page)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                detail_page.verify_on_detail_page()
                agent_id = int(detail_page.get_agent_id())
                base_version_id = detail_page.get_version_id()
                logger.info("Created agent %r with id=%d", AGENT_NAME, agent_id)

            with allure.step("Step 3 — Attach the Skill to the Agent"):
                detail_page.ensure_skills_section_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert "0/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 0 skills attached before attaching"
                )

                detail_page.attach_skill(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching"
                )
                assert detail_page.is_skill_attached(SKILL_NAME), (
                    f"Skill card for '{SKILL_NAME}' should render after attaching"
                )
                assert detail_page.get_skill_version_text(
                    SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT
                ) == "base", (
                    "Attached skill card should show version 'base' before "
                    "Save As Version"
                )

            with allure.step(
                'Step 4 — Click "Save As Version", enter "v1", and confirm — '
                "the dialog's Save stays disabled until the Name field is "
                "non-empty"
            ):
                detail_page.open_save_as_version_dialog(timeout=UI_ELEMENT_TIMEOUT)
                assert not detail_page.create_version_save_button.is_enabled(), (
                    "Dialog Save button should be disabled while Name is empty"
                )

                with page.expect_response(
                    lambda r: (
                        "/elitea_core/application_skills/prompt_lib/" in r.url
                        and r.request.method == "GET"
                    ),
                    timeout=NAVIGATION_TIMEOUT,
                ) as skills_response_info:
                    detail_page.confirm_new_version(VERSION_NAME, timeout=NAVIGATION_TIMEOUT)

                assert detail_page.get_version_selector_value() == VERSION_NAME, (
                    f"VERSION selector should show {VERSION_NAME!r} after Save As Version"
                )
                new_version_id = detail_page.get_version_id()
                assert new_version_id != base_version_id, (
                    "Version ID should change after creating a new named version"
                )
                assert f"/{new_version_id}" in skills_response_info.value.url, (
                    "The application_skills GET captured around the version "
                    "confirm should be scoped to the NEW version id, not the "
                    f"base one — got: {skills_response_info.value.url!r}"
                )

            with allure.step(
                'Step 5 — Verify the Skill is still listed in the SKILLS '
                'section of the new version "v1" — confirmed both via a '
                "fresh application_skills API response and the rendered UI"
            ):
                skills_json = skills_response_info.value.json()
                skills_entries = skills_json.get("skills") or []
                assert len(skills_entries) == 1, (
                    "Expected exactly one attached Skill in the new version's "
                    f"application_skills response, got: {skills_entries!r}"
                )
                skill_entry = skills_entries[0]
                assert skill_entry.get("name") == SKILL_NAME, (
                    "application_skills response entry name should match the "
                    f"attached Skill's name, got: {skill_entry.get('name')!r}"
                )
                assert skill_entry.get("skill_id") == skill_id, (
                    "application_skills response entry skill_id should match "
                    f"the attached Skill's id, got: {skill_entry.get('skill_id')!r}"
                )

                counter_text = detail_page.wait_for_skills_counter(
                    "1/", timeout=UI_ELEMENT_TIMEOUT,
                )
                assert counter_text.startswith("1/"), (
                    "Skills counter should still show 1 skill attached under "
                    f"the new version, got: {counter_text!r}"
                )
                assert detail_page.is_skill_attached(SKILL_NAME), (
                    f"Skill card for '{SKILL_NAME}' should still render under "
                    "the new version 'v1'"
                )
                assert detail_page.get_skill_version_text(
                    SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT
                ) == "base", (
                    "Attached skill's own version reference should still read "
                    "'base' — the Skill entity itself is unversioned by this "
                    "action, only the Agent gained a new version"
                )

        finally:
            # Cleanup per AFS: delete agent first (teardown hygiene, removes
            # base + v1 in one action), then the skill, tolerating individual
            # failures (mirrors ELITEA-1789's cleanup pattern).
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
