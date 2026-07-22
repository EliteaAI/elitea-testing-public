"""Remove a variable and verify removal persists (ELITEA-1884).

Types Instructions containing two `{{variable}}` references into a dedicated
agent, saves, removes one reference, verifies its Variables row disappears
immediately client-side (before any save), saves again, and verifies after a
full-navigation reload that the removed variable stays gone while the other
variable persists.

Test-data strategy (per AFS — see below): mirrors the ELITEA-1888 pattern —
this test creates a **dedicated, uniquely-named agent** for each run via
`AgentAPI.create_agent_full()` with an `llm_settings` payload that avoids the
open, unrelated EliteaAI/elitea-testing-public#524 defect (`temperature` +
a non-`'none'` `reasoning_effort` 400 on the project's reasoning-capable
default model) by setting `reasoning_effort: "none"` and omitting
`temperature` entirely. The agent is deleted at teardown via
`delete_agent_via_menu()` — this test does not depend on the shared `Test
Agent` (id 3) fixture, per the AFS's explicit instruction not to reuse it.

Spec: test-specs/agents/l3_remove-variable-verify-removal-persists_ELITEA-1884.md
"""

import uuid

import pytest
import allure
from playwright.sync_api import Page, Response

from config import settings
from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
SAVE_RESPONSE_TIMEOUT = 15000


def _is_save_response(response: Response) -> bool:
    """Check if response is an agent save PUT request."""
    return (
        "application/prompt_lib" in response.url
        and response.request.method == "PUT"
    )


BASE_INSTRUCTIONS = "This is a test agent for UI testing."
INSTRUCTIONS_WITH_VARIABLES = (
    "This is a test agent for UI testing. Focus on {{department}} using a {{tone}} tone."
)
INSTRUCTIONS_AFTER_REMOVAL = (
    "This is a test agent for UI testing. Focus on using a {{tone}} tone."
)
REMOVED_VARIABLE = "department"
PERSISTED_VARIABLE = "tone"


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open #524 defect (`temperature` is not
    allowed together with a `reasoning_effort` other than 'none' on the
    project's reasoning-capable default model). This does not "fix" #524 —
    it simply avoids the known-bad combination in this test's own fixture
    payload; #524 remains open and unrelated to this test's assertions.

    Base instructions carry zero ``{{name}}`` references so the Variables
    section starts entirely absent from the DOM (AFS Step 1).
    """
    return {
        "name": name,
        "description": "Auto-created for ELITEA-1884 remove-variable test",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": BASE_INSTRUCTIONS,
                "variables": [],
                "tools": [],
                "llm_settings": {
                    "max_tokens": -1,
                    "reasoning_effort": "none",
                    "model_name": settings.default_model_name,
                    "model_project_id": settings.default_model_project_id,
                },
                "conversation_starters": [],
                "agent_type": "openai",
                "welcome_message": "",
                "meta": {"step_limit": 25},
            }
        ],
    }


class TestAgentRemoveVariable:
    """Remove a variable and verify removal persists (ELITEA-1884, p3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1884_remove-a-variable-and-verify-removal-persists.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    @pytest.mark.regression
    def test_remove_variable_and_verify_removal_persists(self, page, agent_api):
        """Removing a {{variable}} reference from Instructions removes its
        Variables row immediately (client-side, before Save), and the
        removal persists after Save + a full-navigation reload, while other
        variables remain intact."""
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1884-rv-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = AgentDetailPage(page)
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        try:
            with allure.step("Step 1 — Navigate to agent detail page; no Variables section yet"):
                detail_page.navigate(agent_id)
                assert detail_page.get_instructions() == BASE_INSTRUCTIONS, (
                    "Instructions field should show the agent's current (variable-free) text"
                )
                assert not detail_page.is_variables_section_visible(timeout=2000), (
                    "Variables section should be entirely absent from the DOM when "
                    "Instructions has zero {{name}} references"
                )

            with allure.step(
                "Step 2 — Type instructions containing two {{variable}} references"
            ):
                detail_page.instructions_input.click()
                detail_page.instructions_input.press("ControlOrMeta+a")
                detail_page.instructions_input.press_sequentially(
                    INSTRUCTIONS_WITH_VARIABLES, delay=30
                )
                assert detail_page.get_instructions() == INSTRUCTIONS_WITH_VARIABLES, (
                    "Instructions field should reflect the typed text with both variables"
                )
                assert detail_page.is_variables_section_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Variables section should appear once Instructions has {{name}} references"
                )
                assert detail_page.is_variable_row_visible(REMOVED_VARIABLE), (
                    f"'{REMOVED_VARIABLE}' row should be visible"
                )
                assert detail_page.is_variable_row_visible(PERSISTED_VARIABLE), (
                    f"'{PERSISTED_VARIABLE}' row should be visible"
                )
                assert detail_page.get_variable_row_names() == [
                    REMOVED_VARIABLE, PERSISTED_VARIABLE,
                ], (
                    "Variable rows should render in first-appearance order in the "
                    "Instructions text"
                )

            with allure.step("Step 3 — Click Save (plain Save, base version)"):
                assert detail_page.is_save_enabled(), (
                    "Save should be enabled once the form is dirty"
                )
                with page.expect_response(_is_save_response, timeout=SAVE_RESPONSE_TIMEOUT) as resp_info:
                    detail_page.click_save(timeout=UI_ELEMENT_TIMEOUT)
                save_response = resp_info.value
                assert save_response.status == 201, (
                    f"PUT application/prompt_lib/... should return 201, got {save_response.status}"
                )
                assert not console_errors, (
                    "Expected no console errors after the seed Save, got: "
                    f"{[m.text for m in console_errors]}"
                )

            with allure.step(
                "Step 4 — Remove the {{department}} token; verify its row disappears "
                "immediately, client-side, before any Save"
            ):
                detail_page.instructions_input.click()
                detail_page.instructions_input.press("ControlOrMeta+a")
                detail_page.instructions_input.press_sequentially(
                    INSTRUCTIONS_AFTER_REMOVAL, delay=30
                )
                assert detail_page.get_instructions() == INSTRUCTIONS_AFTER_REMOVAL, (
                    "Instructions field should reflect the text with {{department}} removed"
                )
                detail_page.wait_for_variable_row_hidden(
                    REMOVED_VARIABLE, timeout=UI_ELEMENT_TIMEOUT
                )
                assert not detail_page.is_variable_row_visible(REMOVED_VARIABLE, timeout=1000), (
                    f"'{REMOVED_VARIABLE}' row should be gone immediately after the text "
                    "edit, before any Save"
                )
                assert detail_page.is_variable_row_visible(PERSISTED_VARIABLE, timeout=1000), (
                    f"'{PERSISTED_VARIABLE}' row should remain untouched"
                )

            with allure.step("Step 5 — Click Save again"):
                assert detail_page.is_save_enabled(), (
                    "Save should be enabled again after the removal edit"
                )
                with page.expect_response(_is_save_response, timeout=SAVE_RESPONSE_TIMEOUT) as resp_info:
                    detail_page.click_save(timeout=UI_ELEMENT_TIMEOUT)
                save_response = resp_info.value
                assert save_response.status == 201, (
                    f"PUT application/prompt_lib/... should return 201 on removal save, got {save_response.status}"
                )
                assert not console_errors, (
                    "Expected no console errors after the removal Save, got: "
                    f"{[m.text for m in console_errors]}"
                )

            with allure.step(
                "Step 6 — Reload the page (full navigation); removed variable is gone, "
                "remaining variable persists"
            ):
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert detail_page.get_instructions() == INSTRUCTIONS_AFTER_REMOVAL, (
                    "Instructions field should show the post-removal text after reload"
                )
                assert detail_page.is_variables_section_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Variables section should still be visible (tone remains) after reload"
                )
                assert not detail_page.is_variable_row_visible(REMOVED_VARIABLE, timeout=2000), (
                    f"'{REMOVED_VARIABLE}' row should remain absent after reload"
                )
                assert detail_page.is_variable_row_visible(
                    PERSISTED_VARIABLE, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"'{PERSISTED_VARIABLE}' row should still be present after reload"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    if "/agents/all/" in detail_page.page.url:
                        detail_page.delete_agent_via_menu(timeout=NAVIGATION_TIMEOUT)
                    else:
                        agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
