"""Remove attached Skill from Agent (ELITEA-1792).

Verifies that a Skill attached to an Agent can be detached via the
attached-skill card's hover-revealed "remove skill" icon button, gated by a
"Remove skill?" confirmation dialog (an additive discovery not mentioned in
the case text — see AFS Metadata). Confirming removes only the targeted
Skill: the other attached Skill remains, the removal persists across a full
page reload (detach auto-saves via API, same as attach), and the removed
Skill continues to exist as a standalone entity (not deleted, only detached).

No product defect found.

Spec: test-specs/skills/l3_remove-attached-skill-from-agent_ELITEA-1792.md
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

SKILL_A_NAME = "elitea-1792-skill-a"
SKILL_A_DESCRIPTION = "Test skill A for ELITEA-1792 remove-attached-skill verification."
SKILL_A_INSTRUCTIONS = (
    "You are Skill A, created for ELITEA-1792 verification. Respond with SKILLA."
)
SKILL_B_NAME = "elitea-1792-skill-b"
SKILL_B_DESCRIPTION = "Test skill B for ELITEA-1792 remove-attached-skill verification."
SKILL_B_INSTRUCTIONS = (
    "You are Skill B, created for ELITEA-1792 verification. Respond with SKILLB."
)
AGENT_NAME = "elitea-1792-remove-skill-agent"


def _create_skill(page, name: str, description: str, instructions: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Mirrors the create flow shared across ELITEA-1735/1737/1738/1739/1789/1790:
    fill the form (name / description / CodeMirror instructions), save, and
    confirm the nav-blocker dialog that fires on every save from the create
    form.
    """
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(name=name, instructions=instructions, description=description)
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


class TestRemoveAttachedSkillFromAgent:
    """Remove attached Skill from Agent (ELITEA-1792, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1792_remove-attached-skill-from-agent.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_remove_attached_skill_from_agent(self, page, agent_api, skill_api):
        """Create two Skills + an Agent, attach both, remove Skill B via the
        hover-revealed remove control + confirmation dialog, and verify Skill
        A remains attached while Skill B survives standalone.

        Steps (AFS test-specs/skills/l3_remove-attached-skill-from-agent_ELITEA-1792.md):
        1. Create Skill A and Skill B via UI.
        2. Create an Agent.
        3. Attach both Skills to the Agent (precondition for this case).
        4. Locate the hover-revealed "remove skill" control for Skill B.
        5. Click it; confirm the "Remove skill?" dialog; Skill B is removed
           from the UI list while Skill A remains.
        6. Confirm persistence via a full page reload (detach auto-saves via
           API; no explicit agent-level Save is available for this action).
        7. Reopen the Agent (same reload satisfies this — no separate
           close/reopen gesture exists in the live flow); only Skill A is
           attached.
        8. Navigate directly to Skill B's detail page and to the Skills list;
           Skill B still exists standalone (detached, not deleted).
        """
        skill_a_id = None
        skill_b_id = None
        agent_id = None
        console_messages = None  # CapturedConsoleMessages, needs stop() in finally
        detach_requests = None  # CapturedRequests, needs stop() in finally

        try:
            with allure.step("Step 1 — Create Skill A and Skill B via UI"):
                skill_a_id = _create_skill(
                    page, SKILL_A_NAME, SKILL_A_DESCRIPTION, SKILL_A_INSTRUCTIONS,
                )
                skill_b_id = _create_skill(
                    page, SKILL_B_NAME, SKILL_B_DESCRIPTION, SKILL_B_INSTRUCTIONS,
                )
                assert skill_b_id != skill_a_id, (
                    "Skill B should have a distinct ID from Skill A"
                )

            with allure.step("Step 2 — Create an Agent"):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME,
                    description=(
                        "Agent for ELITEA-1792 remove-attached-skill verification."
                    ),
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

            with allure.step(
                "Step 3 — Attach both Skills to the Agent (precondition: "
                "Agent exists with >=2 Skills attached)"
            ):
                # Console-error capture across the remainder of the flow
                # (attach, remove, reload, standalone-navigation).
                console_messages = detail_page.capture_console_errors()
                # Capture skill-detach PATCH requests specifically, so Step 5
                # can assert on real network traffic (200, contrast with
                # attach's 201) rather than only UI state.
                detach_requests = detail_page.capture_requests_matching(
                    "skill/prompt_lib", method="PATCH"
                )

                detail_page.attach_skill(SKILL_A_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching Skill A"
                )
                assert detail_page.is_skill_attached(SKILL_A_NAME), (
                    f"Skill card for '{SKILL_A_NAME}' should render after attaching"
                )

                detail_page.attach_skill(SKILL_B_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "2/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 2 skills attached after attaching Skill B"
                )
                assert detail_page.is_skill_attached(SKILL_B_NAME), (
                    f"Skill card for '{SKILL_B_NAME}' should render after attaching"
                )
                assert detail_page.get_skill_version_text(SKILL_A_NAME) == "base", (
                    "Skill A's card should show 'base' as its version"
                )
                assert detail_page.get_skill_version_text(SKILL_B_NAME) == "base", (
                    "Skill B's card should show 'base' as its version"
                )
                # Only attach traffic (201) should exist so far — no detach
                # PATCH has fired yet.
                assert all(req["status"] == 201 for req in detach_requests), (
                    f"All requests captured before removal should be attach "
                    f"(201) responses, captured: {detach_requests!r}"
                )

            with allure.step(
                "Step 4 — Locate the hover-revealed remove control for Skill B"
            ):
                # is_skill_attached() already proved the card is present;
                # the "remove skill" icon itself is only revealed on hover
                # of that specific card — remove_skill() performs the hover
                # internally, so this step's own assertion is on the
                # pre-hover state via the accessibility tree.
                assert not detail_page.is_remove_skill_button_visible(
                    SKILL_B_NAME, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    "The 'remove skill' button should not be present in the "
                    "accessibility tree before Skill B's card is hovered"
                )

            with allure.step(
                "Step 5 — Click 'remove skill' for Skill B, confirm the "
                "'Remove skill?' dialog; Skill B is removed, Skill A remains"
            ):
                detail_page.remove_skill(SKILL_B_NAME, timeout=UI_ELEMENT_TIMEOUT)

                counter_after_remove = detail_page.get_skills_counter_text()
                assert "1/" in counter_after_remove, (
                    "Skills counter should show 1 skill attached after "
                    f"removing Skill B, got: {counter_after_remove!r}"
                )
                assert not detail_page.is_skill_attached(SKILL_B_NAME), (
                    f"Skill card for '{SKILL_B_NAME}' should no longer render "
                    "after removal"
                )
                assert detail_page.is_skill_attached(SKILL_A_NAME), (
                    f"Skill card for '{SKILL_A_NAME}' should still render — "
                    "removing Skill B must not affect Skill A"
                )
                # Filter by BOTH url and status=200: Skill B's id also
                # appears in its own earlier attach PATCH (status 201), so a
                # url-only filter would over-match — detach is distinguished
                # from attach by response status per the AFS (200 vs 201).
                detach_calls = [
                    req for req in detach_requests
                    if req["url"].endswith(f"/{skill_b_id}") and req["status"] == 200
                ]
                assert len(detach_calls) == 1, (
                    "Exactly one skill-detach (200) PATCH targeting Skill B's "
                    f"id should have fired, captured: {detach_requests!r}"
                )
                assert detach_calls[0]["status"] == 200, (
                    "Skill-detach PATCH for Skill B should return 200 "
                    f"(contrast with attach's 201), got: {detach_calls[0]!r}"
                )
                assert not console_messages, (
                    "Expected no console errors after removing Skill B, got: "
                    f"{[m.text for m in console_messages]}"
                )

            with allure.step(
                "Step 6 — Confirm persistence via a full page reload "
                "(detach auto-saves via API; no explicit agent-level Save "
                "is available for this action)"
            ):
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                counter_after_reload = detail_page.wait_for_skills_counter(
                    "1/", timeout=UI_ELEMENT_TIMEOUT,
                )
                assert "1/" in counter_after_reload, (
                    "Skills counter should still show 1 skill attached after "
                    f"reload, got: {counter_after_reload!r}"
                )
                assert not console_messages, (
                    "Expected no console errors after the full page reload, "
                    f"got: {[m.text for m in console_messages]}"
                )

            with allure.step(
                "Step 7 — Reopen the Agent (same reload as Step 6): only "
                "Skill A is attached; Skill B is no longer listed"
            ):
                assert detail_page.is_skill_attached(SKILL_A_NAME), (
                    f"Skill card for '{SKILL_A_NAME}' should be present "
                    "after reload"
                )
                assert not detail_page.is_skill_attached(SKILL_B_NAME), (
                    f"Skill card for '{SKILL_B_NAME}' should NOT be present "
                    "after reload — removal must have persisted server-side"
                )

            with allure.step(
                "Step 8 — Navigate directly to Skill B's detail page and to "
                "the Skills list; Skill B still exists standalone (detached, "
                "not deleted)"
            ):
                skill_detail_page = SkillDetailPage(page)
                skill_detail_page.navigate(skill_b_id)
                skill_detail_page.verify_on_detail_page()
                assert skill_detail_page.get_name() == SKILL_B_NAME, (
                    f"Skill B's detail page should still show its name "
                    f"'{SKILL_B_NAME}' after being detached from the agent"
                )
                assert skill_detail_page.get_description() == SKILL_B_DESCRIPTION, (
                    "Skill B's description should remain intact after detachment"
                )
                assert skill_detail_page.get_instructions() == SKILL_B_INSTRUCTIONS, (
                    "Skill B's instructions should remain intact after detachment"
                )

                skills_list_page = SkillsListPage(page)
                skills_list_page.navigate()
                assert skills_list_page.skill_exists_in_list(SKILL_B_NAME), (
                    f"Skill B ('{SKILL_B_NAME}') should still appear in the "
                    "project's Skills list after being detached from the agent"
                )

        finally:
            # Stop listeners to prevent resource leaks that cause test hangs.
            if console_messages is not None:
                console_messages.stop()
            if detach_requests is not None:
                detach_requests.stop()

            # Cleanup per AFS: delete the agent first (teardown hygiene —
            # remove the thing with attached-state dependencies first), then
            # both skills, tolerating individual failures (mirrors
            # ELITEA-1735/1737/1738/1739/1789/1790's cleanup pattern).
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete agent id=%s: %s", agent_id, exc
                    )
            for skill_id in (skill_a_id, skill_b_id):
                if skill_id is not None:
                    try:
                        skill_api.delete_skill(skill_id)
                        logger.info("Cleanup: deleted skill id=%d", skill_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup: failed to delete skill id=%s: %s", skill_id, exc
                        )
