"""Add two variables and verify they persist after reload (ELITEA-1883).

Types Instructions containing two `{{variable}}` references into a dedicated
agent, enters a value for each variable, saves, and verifies after a
full-navigation reload that both variables and their values persist exactly
as saved. Sibling of ``test_agent_remove_variable.py`` (ELITEA-1884) — "add +
persist values" instead of "remove + persist absence".

Test-data strategy (per AFS): mirrors the ELITEA-1884/1888 pattern — this
test creates a **dedicated, uniquely-named agent** for each run via
``AgentAPI.create_agent_full()`` with an ``llm_settings`` payload that avoids
the shared ``agent_id`` fixture, which is currently broken
(EliteaAI/elitea-testing-public#563: ``AgentAPI.create_agent()`` hardcodes an
invalid ``temperature`` + ``reasoning_effort`` combo, unrelated to the
already-fixed #524). Setting ``reasoning_effort: "none"`` and omitting
``temperature`` entirely avoids the bad combination. The agent is deleted at
teardown via ``delete_agent_via_menu()``.

Spec: test-specs/agents/l3_add-two-variables-and-verify-they-persist-after-reload_ELITEA-1883.md
"""

import uuid

import pytest
import allure
from playwright.sync_api import Page, Response

from config import settings
from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
SAVE_RESPONSE_TIMEOUT = 15000

INSTRUCTIONS_WITH_VARIABLES = "{{MY_VAR}} and {{API_URL}}"
MY_VAR_VALUE = "hello_world"
API_URL_VALUE = "https://example.com"
# Live DOM/server order is alphabetical by variable name, NOT first-appearance
# order in the Instructions text (MY_VAR appears first in the text, but
# API_URL renders first) — confirmed live in the ELITEA-1883 AFS, correcting
# a coincidental claim in the ELITEA-1884 AFS.
EXPECTED_ROW_ORDER = ["API_URL", "MY_VAR"]


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the ``agent_id`` fixture's known-bad payload
    (issue #563) — this does not "fix" #563, it simply avoids the known-bad
    combination in this test's own fixture payload.

    Instructions start as an empty string (zero ``{{name}}`` references), so
    the Variables section starts entirely absent from the DOM (AFS Step 1).
    """
    return {
        "name": name,
        "description": "Auto-created for ELITEA-1883 add-variables test",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": "",
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


def _is_save_response(response: Response) -> bool:
    """Match the agent Save PUT: `.../application/prompt_lib/{project}/{id}`."""
    return (
        "application/prompt_lib" in response.url
        and response.request.method == "PUT"
    )


class TestAgentAddVariablesPersistAfterReload:
    """Add two variables and verify they persist after reload (ELITEA-1883, p3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1883_add-two-variables-and-verify-they-persist-after-reload.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    @pytest.mark.regression
    def test_add_two_variables_and_verify_they_persist_after_reload(self, page: Page, agent_api):
        """Adding two {{variable}} references to Instructions, entering their
        values, and saving persists both name+value pairs after a
        full-navigation reload — asserted via both the DOM and the Save PUT
        response body."""
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1883-av-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = AgentDetailPage(page)
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        try:
            with allure.step(
                "Step 1 — Navigate to agent detail page; Instructions empty, "
                "no Variables section yet"
            ):
                detail_page.navigate(agent_id)
                assert detail_page.get_instructions() == "", (
                    "Instructions field should be empty on a freshly-created "
                    "agent with no seed instructions"
                )
                assert not detail_page.is_variables_section_visible(timeout=2000), (
                    "Variables section should be entirely absent from the DOM "
                    "when Instructions has zero {{name}} references"
                )

            with allure.step(
                "Step 2 — Type Instructions containing two {{variable}} references"
            ):
                detail_page.instructions_input.click()
                detail_page.instructions_input.press("ControlOrMeta+a")
                detail_page.instructions_input.press_sequentially(
                    INSTRUCTIONS_WITH_VARIABLES, delay=30
                )
                assert detail_page.get_instructions() == INSTRUCTIONS_WITH_VARIABLES, (
                    "Instructions field should reflect the typed text with "
                    "both variables"
                )

            with allure.step(
                "Step 3 — Verify the Variables section appears automatically, "
                "with a row for each of MY_VAR and API_URL"
            ):
                assert detail_page.is_variables_section_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Variables section should appear once Instructions has "
                    "{{name}} references"
                )
                assert detail_page.is_variable_row_visible("MY_VAR"), (
                    "'MY_VAR' row should be visible"
                )
                assert detail_page.is_variable_row_visible("API_URL"), (
                    "'API_URL' row should be visible"
                )
                # Rows render alphabetically by name, not first-appearance
                # order in the Instructions text (MY_VAR appears first in the
                # text, but API_URL renders first) — see EXPECTED_ROW_ORDER.
                assert detail_page.get_variable_row_names() == EXPECTED_ROW_ORDER, (
                    "Variable rows should render alphabetically by name "
                    f"({EXPECTED_ROW_ORDER}), not first-appearance-in-text order"
                )

            with allure.step("Step 4 — Enter a value for MY_VAR"):
                detail_page.fill_variable_value("MY_VAR", MY_VAR_VALUE)
                assert detail_page.get_variable_value("MY_VAR") == MY_VAR_VALUE, (
                    "'MY_VAR' input should show the typed value immediately"
                )

            with allure.step("Step 5 — Enter a value for API_URL"):
                detail_page.fill_variable_value("API_URL", API_URL_VALUE)
                assert detail_page.get_variable_value("API_URL") == API_URL_VALUE, (
                    "'API_URL' input should show the typed value immediately"
                )

            with allure.step("Step 6 — Click Save (plain Save, base version)"):
                assert detail_page.is_save_enabled(), (
                    "Save should be enabled once the form is dirty"
                )
                with page.expect_response(
                    _is_save_response, timeout=SAVE_RESPONSE_TIMEOUT
                ) as response_info:
                    detail_page.click_save(timeout=UI_ELEMENT_TIMEOUT)
                save_response = response_info.value
                assert save_response.status == 201, (
                    "PUT application/prompt_lib/... should return 201 on Save, "
                    f"got {save_response.status}"
                )
                saved_variables = {
                    v["name"]: v["value"]
                    for v in save_response.json()["version_details"]["variables"]
                }
                assert saved_variables == {"MY_VAR": MY_VAR_VALUE, "API_URL": API_URL_VALUE}, (
                    "Save response body's version_details.variables should "
                    f"contain both variables with their values, got: {saved_variables!r}"
                )
                assert not console_errors, (
                    "Expected no console errors after Save, got: "
                    f"{[m.text for m in console_errors]}"
                )

            with allure.step("Step 7 — Reload the page (full navigation)"):
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert not console_errors, (
                    "Expected no console errors after reload, got: "
                    f"{[m.text for m in console_errors]}"
                )

            with allure.step(
                "Step 8 — Verify both MY_VAR and API_URL appear in the "
                "Variables section with their correct values after reload"
            ):
                assert detail_page.get_instructions() == INSTRUCTIONS_WITH_VARIABLES, (
                    "Instructions field should show the saved text after reload"
                )
                assert detail_page.is_variable_row_visible(
                    "MY_VAR", timeout=UI_ELEMENT_TIMEOUT
                ), "'MY_VAR' row should still be present after reload"
                assert detail_page.is_variable_row_visible(
                    "API_URL", timeout=UI_ELEMENT_TIMEOUT
                ), "'API_URL' row should still be present after reload"
                assert detail_page.get_variable_value("MY_VAR") == MY_VAR_VALUE, (
                    "'MY_VAR' value should persist exactly as saved after reload"
                )
                assert detail_page.get_variable_value("API_URL") == API_URL_VALUE, (
                    "'API_URL' value should persist exactly as saved after reload"
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
