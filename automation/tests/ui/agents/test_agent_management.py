"""UI Tests for Elitea Agent Management.

Tests agent creation, configuration, listing, search, edit, and deletion.

Each test that modifies agents uses the ``agent_id`` fixture so it gets
a fresh, isolated agent that is cleaned up automatically after the test.

Spec: docs/UI_TEST_EPICS.md EPIC 2: Agents
Covers: Dashboard, Create Agent, Agent Configuration, Agent Actions

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - p0: critical priority tests
    - p1: high priority tests

Usage:
    cd automation
    pytest test_agent_management.py -v
    pytest test_agent_management.py -v -m p0
"""

import time
import uuid

import pytest
from config import settings
from pages.agents_list_page import AgentsListPage
from pages.agent_form_page import AgentFormPage
from pages.agent_detail_page import AgentDetailPage
from pages.internal_tools import InternalTool
import allure

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
FORM_SAVE_TIMEOUT = 15000
AI_RESPONSE_TIMEOUT = 30000

# ELITEA-1872 test data
SEED_INSTRUCTIONS = "You are a test agent."
NEW_INSTRUCTIONS = "You are an updated test assistant."


def _wait_for_resolved_save_count(
    page, save_requests: list, expected_count: int, timeout: int = FORM_SAVE_TIMEOUT
) -> None:
    """Poll *save_requests* until at least *expected_count* entries resolve.

    The Save PUT is dispatched after a short client-side debounce, so
    ``wait_for_load_state("networkidle")`` (via ``click_save()``) can resolve
    before the debounced PUT is even issued — confirmed live, same race
    documented in ``test_agent_remove_variable.py`` (ELITEA-1884). Poll the
    captured entries (populated by ``capture_requests_matching``) instead of
    asserting immediately after ``click_save()``.
    """
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        resolved = [r for r in save_requests if r["status"] is not None]
        if len(resolved) >= expected_count:
            return
        page.wait_for_timeout(200)


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open, unrelated
    https://github.com/EliteaAI/elitea-testing-public/issues/524 defect
    (``temperature`` is not allowed together with a ``reasoning_effort``
    other than ``'none'`` on the project's reasoning-capable default model).
    This does not "fix" #524 — it simply avoids the known-bad combination in
    this test's own fixture payload; #524 remains open and unrelated to this
    test's assertions. Same pattern as
    ``tests/ui/agents/test_agent_remove_variable.py`` (ELITEA-1884).
    """
    return {
        "name": name,
        "description": "Auto-created for ELITEA-1872 edit-instructions test",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": SEED_INSTRUCTIONS,
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


def _wait_for_chat_message_count(
    detail_page, min_count: int, timeout: int = UI_ELEMENT_TIMEOUT
) -> int:
    """Poll the embedded chat message count until it exceeds *min_count*.

    The user's own message is appended client-side right after the send
    click, but rendering isn't synchronous with the click event returning —
    asserting ``get_chat_message_count() > min_count`` immediately after
    ``send_chat_message()`` races the render and can observe the pre-send
    count (confirmed live). Poll instead, same bounded-deadline idiom as
    ``_wait_for_resolved_save_count`` above.

    Returns:
        The observed message count once it exceeds *min_count* (or the last
        observed count if the timeout elapses).
    """
    deadline = time.time() + timeout / 1000
    count = detail_page.get_chat_message_count()
    while time.time() < deadline and count <= min_count:
        detail_page.page.wait_for_timeout(200)
        count = detail_page.get_chat_message_count()
    return count


def _build_execution_agent_payload(name: str, description: str, instructions: str) -> dict:
    """Build a create-agent payload for a dedicated, toolkit-free execution-test agent
    that both creates successfully AND can open an embedded-chat conversation.

    Uses ``reasoning_effort: "low"`` (fast, minimal-step reasoning — avoids
    the multi-minute "thinking" latency observed live with ``"medium"``,
    which exceeded this test's 30s ``AI_RESPONSE_TIMEOUT``) and omits both
    ``temperature`` and the model fields (``model_name``/``model_project_id``)
    entirely, letting the backend apply its own valid default model (same as
    the plain UI create-form path, which never sets ``llm_settings`` model
    fields either).

    This combination was reached by live elimination during ELITEA-1897
    implementation (2026-07-16), not copied from the existing
    ``reasoning_effort: "none"`` workaround pattern
    (``_build_dedicated_agent_payload`` above / ELITEA-1884's
    ``test_agent_remove_variable.py``):

    - ``reasoning_effort`` other than ``"none"`` + an explicit ``temperature``
      hits the known, unrelated #524 defect (400 on *creation*).
    - ``reasoning_effort: "none"`` avoids #524's 400 on creation, but — newly
      confirmed live in this pass — breaks the embedded chat entirely: the
      ``POST .../conversations/prompt_lib/{project}`` call needed to open the
      chat panel 500s ("Internal Server Error") whenever the agent's
      ``llm_settings.reasoning_effort`` is ``"none"``, regardless of whether
      model fields are set. Confirmed via live elimination: same payload with
      only ``reasoning_effort`` flipped from ``"none"`` to ``"medium"`` (model
      fields held constant/absent both times) changes the conversation-create
      response from 500 to 201. Filed as a new defect — see
      https://github.com/EliteaAI/elitea-testing-public/issues/560.
    - ``reasoning_effort: "medium"`` avoids both #524 and the "none" conversation-
      creation 500, but drives noticeably slower "thinking" latency on this
      project's default reasoning-capable model — observed live to exceed a
      30s response wait. ``"low"`` (fast, minimal-step reasoning per the UI's
      own ``ReasoningSlider`` tooltip) keeps the same safe combination while
      responding well within timeout.
    - Setting ``settings.default_model_name``/``default_model_project_id``
      (used by the *other* existing "none" fixtures, which never open the
      embedded chat and so never exercise conversation-creation) is also
      stale/invalid for this project (``model_project_id: 0`` resolves to no
      real model) — irrelevant to those fixtures' own assertions, but would
      have compounded confusion here. Omitting the model fields entirely
      (backend default, same as the UI form) sidesteps that gap too.

    Deliberately carries no ``tools``/toolkit attachment — ELITEA-1897's whole
    point is proving a *plain*, toolkit-free instructions field is sufficient
    for chat execution.
    """
    return {
        "name": name,
        "description": description,
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": instructions,
                "variables": [],
                "tools": [],
                "llm_settings": {
                    "max_tokens": -1,
                    "reasoning_effort": "low",
                },
                "conversation_starters": [],
                "agent_type": "openai",
                "welcome_message": "",
                "meta": {"step_limit": 25},
            }
        ],
    }


class TestCreateAgent:
    """Create Agent (P0): create via UI, verify in list and via API."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0145_agent-creation-ui-and-api.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_create_agent_via_ui(self, page, agent_api):
        """Create an agent through the UI form and verify it appears in the list."""
        agent_name = "autotest_create_ui"
        agent_desc = "Created by UI automation test"
        agent_instr = "You are a test assistant created by automation."
        created_agent_id = None

        # ------------------------------------------------------------------
        # Step 1 — Navigate to create agent page
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Navigate to create agent page"):
            list_page = AgentsListPage(page)
            list_page.navigate_to_create()

        # ------------------------------------------------------------------
        # Step 2 — Fill in name + description + instructions
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Fill in name + description + instructions"):
            form_page = AgentFormPage(page)
            form_page.wait_for_form_load()
            form_page.fill_form(
                name=agent_name,
                description=agent_desc,
                instructions=agent_instr,
            )

        # ------------------------------------------------------------------
        # Step 3 — Click Save
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Click Save"):
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), "Save button should be enabled after filling required fields"
            form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 4 — Verify user lands on the agent detail page
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Verify user lands on the agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
            detail_page.verify_on_detail_page()

        try:
            agent_id_str = detail_page.get_agent_id()
            try:
                created_agent_id = int(agent_id_str)
            except (ValueError, TypeError) as e:
                pytest.fail(f"Failed to parse agent ID '{agent_id_str}': {e}")

            displayed_name = detail_page.name_input.input_value()
            assert displayed_name == agent_name, f"Expected agent name '{agent_name}', got '{displayed_name}'"

            # ------------------------------------------------------------------
            # Step 5 — Navigate back to agents list
            # ------------------------------------------------------------------
            with allure.step("Step 5 — Navigate back to agents list"):
                list_page.navigate()

            # ------------------------------------------------------------------
            # Step 6 — Verify agent appears in the list
            # ------------------------------------------------------------------
            with allure.step("Step 6 — Verify agent appears in the list"):
                assert list_page.agent_exists_in_list(agent_name, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent '{agent_name}' should appear in the agents list"
                )
        finally:
            if created_agent_id is not None:
                try:
                    agent_api.delete_agent(created_agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {created_agent_id}: {cleanup_exc}")

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0145_agent-creation-ui-and-api.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_create_agent_via_api_visible_in_ui(self, page, agent_id, agent_api):
        """Create an agent via API fixture and verify it shows in the UI list."""
        with allure.step("Step 1 — Get agent name from API"):
            agent = agent_api.get_agent(agent_id)
            agent_name = agent.get("name", "")

        with allure.step("Step 2 — Navigate to agents list"):
            list_page = AgentsListPage(page)
            list_page.navigate()

        with allure.step("Step 3 — Verify agent appears in list"):
            assert list_page.agent_exists_in_list(agent_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Agent '{agent_name}' should appear in the agents list"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0136_agent-creation-field-validation.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0145_agent-creation-ui-and-api.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_create_agent_required_fields_validation(self, page):
        """Save button should be disabled when required fields are empty."""
        with allure.step("Step 1 — Navigate to create agent page"):
            list_page = AgentsListPage(page)
            list_page.navigate_to_create()
            form_page = AgentFormPage(page)
            form_page.wait_for_form_load()

        with allure.step("Step 2 — Verify Save disabled with empty fields"):
            assert not form_page.is_save_enabled(), "Save should be disabled with empty required fields"

        with allure.step("Step 3 — Fill only name and verify Save still disabled"):
            form_page.fill_form(name="autotest_partial", description="")
            form_page.wait_for_form_validation()
            assert not form_page.is_save_enabled(), "Save should be disabled without description"

        with allure.step("Step 4 — Fill both fields and verify Save enabled"):
            form_page.fill_form(name="autotest_partial", description="Some description")
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), (
                "Save should be enabled when both name and description are filled"
            )


class TestAgentConfiguration:
    """Agent Configuration (P1): system prompt, detail page, form fields."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0141_agent-detail-page-configuration-and-tabs.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_agent_detail_page_loads(self, page, agent_id, agent_api):
        """Navigate to an agent's detail page and verify form fields are populated."""
        with allure.step("Step 1 — Get agent data from API"):
            agent = agent_api.get_agent(agent_id)

        with allure.step("Step 2 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)

        with allure.step("Step 3 — Verify form fields match API data"):
            assert detail_page.name_input.input_value() == agent.get("name", ""), "Name should match"
            assert detail_page.description_input.input_value() == agent.get("description", ""), "Description should match"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0141_agent-detail-page-configuration-and-tabs.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_agent_instructions_field(self, page, agent_id):
        """Instructions field should be visible and editable."""
        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)

        with allure.step("Step 2 — Verify instructions field is visible"):
            assert detail_page.instructions_input.is_visible(), "Instructions field should be visible"

        with allure.step("Step 3 — Verify instructions content"):
            value = detail_page.instructions_input.input_value()
            assert "test agent" in value.lower(), (
                f"Instructions should contain 'test agent', got: {value}"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0141_agent-detail-page-configuration-and-tabs.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_agent_information_section(self, page, agent_id):
        """Information section should display Agent ID and Version ID."""
        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)

        with allure.step("Step 2 — Get Agent ID and Version ID"):
            agent_id_text = detail_page.get_agent_id()
            version_id_text = detail_page.get_version_id()

        with allure.step("Step 3 — Verify Agent ID and Version ID are displayed"):
            assert agent_id_text, "Agent ID should be displayed"
            assert version_id_text, "Version ID should be displayed"
            assert version_id_text.isdigit() or "-" in version_id_text, (
                f"Version ID '{version_id_text}' should be a numeric ID or UUID-like string"
            )
            assert agent_id_text == str(agent_id), (
                f"Displayed Agent ID '{agent_id_text}' should match fixture ID '{agent_id}'"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0141_agent-detail-page-configuration-and-tabs.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @pytest.mark.smoke
    def test_agent_toolkits_section_visible(self, page, agent_id):
        """Toolkits section should be visible with tool switches."""
        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)

        with allure.step("Step 2 — Get available tools"):
            available_tools = detail_page.get_available_tools()

        with allure.step("Step 3 — Verify at least one tool is available"):
            assert len(available_tools) > 0, (
                "Should have at least one internal tool available in toolkits section"
            )
            print(f"Available tools: {[t.value for t in available_tools]}")

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0141_agent-detail-page-configuration-and-tabs.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_internal_tools_enum_usage(self, page, agent_id):
        """Verify internal tools can be toggled using the enum-based API.
    
        Note: This is a smoke test for the toggle_tool() API accepting enum values.
        Full state verification (checking if checkbox actually changed) is not
        performed due to MUI DOM complexity making is_tool_enabled() unreliable.
        See test_internal_tools_enable_disable (skipped) for details.
        """

        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)

        with allure.step("Step 2 — Get available tools"):
            available_tools = detail_page.get_available_tools()
            assert len(available_tools) > 0, "Should have at least one internal tool available"
            test_tool = available_tools[0]
            print(f"Testing toggle API with tool: {test_tool.value}")

        with allure.step("Step 3 — Toggle tool on and off"):
            try:
                detail_page.toggle_tool(test_tool)
                detail_page.wait_for_network(timeout=2000)
                detail_page.toggle_tool(test_tool)
                detail_page.wait_for_network(timeout=2000)
            except Exception as e:
                pytest.fail(
                    f"toggle_tool() failed with enum {test_tool}: {e}. "
                    "Enum-based API should accept InternalTool values."
                )


class TestAgentList:
    """Agent List (P1): list agents, search, view toggles."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0140_agent-dashboard-and-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @pytest.mark.smoke
    def test_agents_dashboard_loads(self, page):
        """Agents dashboard loads with functional header and search."""
        with allure.step("Step 1 — Navigate to agents dashboard"):
            list_page = AgentsListPage(page)
            list_page.navigate()

        with allure.step("Step 2 — Verify dashboard header is visible"):
            list_page.verify_dashboard_header_visible()

        with allure.step("Step 3 — Verify search input is visible and editable"):
            assert list_page.search_input.is_visible(), "Search input should be visible"
            assert list_page.search_input.is_editable(), (
                "Search input should be editable (not just visible)"
            )

        with allure.step("Step 4 — Verify search input is functional"):
            list_page.verify_search_functional()

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0140_agent-dashboard-and-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_agent_search(self, page, agent_id, agent_api):
        """Search for an agent by name on the dashboard."""
        with allure.step("Step 1 — Get agent name from API"):
            agent = agent_api.get_agent(agent_id)
            agent_name = agent.get("name", "")

        with allure.step("Step 2 — Navigate to agents list"):
            list_page = AgentsListPage(page)
            list_page.navigate()

        with allure.step("Step 3 — Search for agent by name"):
            list_page.search_and_wait_for_results(agent_name)

        with allure.step("Step 4 — Verify agent appears in search results"):
            assert list_page.agent_exists_in_list(agent_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Agent '{agent_name}' should appear in search results"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0140_agent-dashboard-and-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_agent_search_no_results(self, page):
        """Searching for a non-existent agent should show no results."""
        with allure.step("Step 1 — Navigate to agents list"):
            list_page = AgentsListPage(page)
            list_page.navigate()

        with allure.step("Step 2 — Search for non-existent agent"):
            list_page.search_and_wait_for_results("zzzz_nonexistent_agent_12345")

        with allure.step("Step 3 — Verify no results found"):
            assert not list_page.agent_exists_in_list(
                "zzzz_nonexistent_agent_12345", timeout=3000
            ), "Non-existent agent should not appear in results"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0140_agent-dashboard-and-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_view_toggle_table_and_card(self, page):
        """Dashboard should support switching between table and card views."""
        with allure.step("Step 1 — Navigate to agents list"):
            list_page = AgentsListPage(page)
            list_page.navigate()

        with allure.step("Step 2 — Verify view toggle buttons are visible"):
            assert list_page.table_view_button.is_visible(), "Table view button should exist"
            assert list_page.card_view_button.is_visible(), "Card view button should exist"

        with allure.step("Step 3 — Switch to table view and verify"):
            list_page.switch_to_table_view()
            assert list_page.is_table_view_active(), (
                "Table view should be active after clicking table view button"
            )

        with allure.step("Step 4 — Switch to card view and verify"):
            list_page.switch_to_card_view()
            assert list_page.is_card_view_active(), (
                "Card view should be active after clicking card view button"
            )

        with allure.step("Step 5 — Verify dashboard header still visible"):
            list_page.verify_dashboard_header_visible()


class TestAgentActions:
    """Agent Actions (P1): edit agent, delete agent, verify cleanup."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0144_agent-edit-and-delete.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0138_agent-edit-operations-name-and-description.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_edit_agent_name(self, page, agent_id):
        """Edit an agent's name and verify the change persists."""
        new_name = "autotest_renamed_agent"

        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)

        with allure.step("Step 2 — Update agent name"):
            detail_page.update_name(new_name)

        with allure.step("Step 3 — Verify Save is enabled and click Save"):
            assert detail_page.is_save_enabled(), "Save should be enabled after name change"
            detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        with allure.step("Step 4 — Reload and verify name persisted"):
            detail_page.reload_and_wait()
            assert detail_page.name_input.input_value() == new_name, (
                f"Agent name should be '{new_name}' after save"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0144_agent-edit-and-delete.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0138_agent-edit-operations-name-and-description.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_edit_agent_description(self, page, agent_id):
        """Edit an agent's description and verify the change persists."""
        new_desc = "Updated description by automation"

        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)

        with allure.step("Step 2 — Update agent description"):
            detail_page.update_description(new_desc)

        with allure.step("Step 3 — Verify Save is enabled and click Save"):
            assert detail_page.is_save_enabled(), "Save should be enabled after description change"
            detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        with allure.step("Step 4 — Reload and verify description persisted"):
            detail_page.reload_and_wait()
            assert detail_page.description_input.input_value() == new_desc, (
                f"Agent description should be '{new_desc}' after save"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1872_edit-agent-instructions-and-verify-persistence.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/538", "Known defect #538")
    @pytest.mark.p1
    @pytest.mark.regression
    def test_edit_agent_instructions(self, page, agent_api):
        """Edit an agent's Instructions field and verify the change persists
        after a full-navigation page reload (ELITEA-1872).

        Uses a dedicated, disposable agent created via
        ``AgentAPI.create_agent_full()`` (not the shared ``agent_id``
        fixture) because the fixture's plain ``create_agent()`` call
        currently 400s against the DEV backend
        (https://github.com/EliteaAI/elitea-testing-public/issues/524) —
        same workaround as ``test_agent_remove_variable.py`` (ELITEA-1884).

        Known defect #538 (isolated, non-blocking): typing into the
        Instructions field triggers a React "Maximum update depth exceeded"
        console warning (confirmed live: fires on the typing step only, not
        on navigate or save; does not block the Save request or persistence).
        The console side-channel check is deferred to the end of the test
        (after the case's own persistence assertions have run and proven the
        feature under test has no defect) so this pre-existing, isolated
        warning doesn't mask the Steps 1-5 verification — same scoping
        precedent as ``test_credential_required_fields_validation.py``.
        """
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1872-instr-{uuid.uuid4().hex[:8]}"[:32]
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = AgentDetailPage(page)
        console_messages = []
        page.on(
            "console",
            lambda msg: console_messages.append(msg)
            if msg.type in ("error", "warning")
            else None,
        )
        save_requests = detail_page.capture_requests_matching(
            "application/prompt_lib", method="PUT"
        )

        try:
            with allure.step("Step 1 — Navigate to agent detail page"):
                detail_page.navigate(agent_id)
                assert detail_page.get_instructions() == SEED_INSTRUCTIONS, (
                    "Instructions field should show the agent's seeded text"
                )
                assert not detail_page.is_save_enabled(), (
                    "Save should start disabled before any edit"
                )

            with allure.step(
                "Step 2 — Clear Instructions field and enter new text "
                "(Known defect #538: typing triggers a React 'Maximum update "
                "depth exceeded' console warning, asserted in the deferred "
                "side-channel check below — does not block this step)"
            ):
                detail_page.update_text_field("instructions", NEW_INSTRUCTIONS)
                assert detail_page.get_instructions() == NEW_INSTRUCTIONS, (
                    "Instructions field should reflect the newly typed text"
                )
                assert detail_page.is_save_enabled(), (
                    "Save should be enabled after the Instructions edit"
                )

            with allure.step("Step 3 — Click Save and wait for network idle"):
                detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)
                _wait_for_resolved_save_count(page, save_requests, expected_count=1)
                save_responses = [r for r in save_requests if r["status"] is not None]
                assert save_responses and save_responses[-1]["status"] == 201, (
                    f"PUT application/prompt_lib/... should return 201, captured: {save_requests!r}"
                )
                assert not detail_page.is_save_enabled(), (
                    "Save should return to disabled after a successful save"
                )

            with allure.step("Step 4 — Reload the page (full navigation)"):
                detail_page.reload_and_wait(timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Step 5 — Verify the Instructions field contains the saved text"
            ):
                assert detail_page.instructions_input.input_value() == NEW_INSTRUCTIONS, (
                    "Instructions field should retain the new value after reload, got: "
                    f"{detail_page.instructions_input.input_value()!r}"
                )

            with allure.step(
                "Side-channel check — no console errors/warnings across the flow "
                "(deferred: Known defect #538 fires during Step 2 typing; checked "
                "last so the persistence proof above runs and passes regardless)"
            ):
                assert not console_messages, (
                    "Unexpected console errors/warnings — see #538 if this is the "
                    "known 'Maximum update depth exceeded' warning from typing into "
                    f"Instructions: {[m.text for m in console_messages]}"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1885_welcome-message-is-shown-as-agent-bubble-before-first-user-message.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_welcome_message_shown_as_agent_bubble_before_first_message(
        self, page, agent_api
    ):
        """Configured welcome message persists and renders as an agent
        bubble in the embedded chat panel before any user message is sent
        (ELITEA-1885).

        Uses a dedicated, disposable agent created via
        ``AgentAPI.create_agent_full()`` (not the shared ``agent_id``
        fixture) — same #524 workaround as ``test_edit_agent_instructions``
        above.

        Asserts the POST-SAVE / POST-RELOAD persisted state as the pass
        criterion, not the live keystroke-preview render: the welcome
        message also renders in the chat panel on every keystroke before
        Save, but that is not itself the case's pass criterion (see AFS
        Metadata note). A full-navigation reload after Save both
        re-verifies persistence and gives a pristine "before any user
        message" state, uncontaminated by Step 2's live-preview render.
        """
        welcome_message = (
            "Welcome! I am your test assistant. How can I help you today?"
        )

        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1885-welcome-{uuid.uuid4().hex[:8]}"[:32]
            agent = agent_api.create_agent_full(
                _build_dedicated_agent_payload(agent_name)
            )
            agent_id = agent["id"]

        detail_page = AgentDetailPage(page)
        console_messages = []
        page.on(
            "console",
            lambda msg: console_messages.append(msg)
            if msg.type in ("error", "warning")
            else None,
        )
        save_requests = detail_page.capture_requests_matching(
            "application/prompt_lib", method="PUT"
        )

        try:
            with allure.step("Step 1 — Navigate to agent detail page"):
                detail_page.navigate(agent_id)
                assert detail_page.get_chat_message_count() == 0, (
                    "Embedded chat panel should be empty before a welcome "
                    "message is set"
                )

            with allure.step("Step 2 — Set the welcome message"):
                detail_page.update_welcome_message(welcome_message)
                assert detail_page.get_welcome_message() == welcome_message, (
                    "Welcome message field should reflect the typed text"
                )

            with allure.step("Step 3 — Click Save and wait for network idle"):
                detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)
                _wait_for_resolved_save_count(page, save_requests, expected_count=1)
                save_responses = [r for r in save_requests if r["status"] is not None]
                assert save_responses and save_responses[-1]["status"] == 201, (
                    "PUT application/prompt_lib/... should return 201, "
                    f"captured: {save_requests!r}"
                )

            with allure.step(
                "Step 4 — Full-navigation reload for a pristine, persisted, "
                "before-any-user-message state"
            ):
                detail_page.reload_and_wait(timeout=NAVIGATION_TIMEOUT)
                detail_page.chat_message_list.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )
                detail_page.chat_message_list.locator(
                    detail_page.CHAT_MESSAGE_ITEM_SELECTOR
                ).first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 5 — Verify exactly one message is present and it is "
                "the welcome message"
            ):
                message_count = detail_page.get_chat_message_count()
                assert message_count == 1, (
                    "Expected exactly 1 message (the welcome message) before "
                    f"any user message, found {message_count}"
                )
                assert detail_page.get_last_chat_response_text() == welcome_message, (
                    "The single chat message's text should equal the saved "
                    f"welcome message, got: {detail_page.get_last_chat_response_text()!r}"
                )

            with allure.step(
                "Step 6 — Verify the welcome message appears as an agent "
                "bubble (not a user bubble)"
            ):
                has_read_out, has_answer_marker, has_delete_button = (
                    detail_page.get_last_chat_message_agent_markers()
                )
                assert has_read_out, (
                    "Welcome message bubble should carry the agent-only "
                    "chat-read-out-button (TTS read-out)"
                )
                assert has_answer_marker, (
                    "Welcome message bubble should carry an agent-answer "
                    "marker (skill-test-last-response or chat-answer-content)"
                )
                assert not has_delete_button, (
                    "Welcome message bubble should NOT carry the "
                    "chat-message-delete-button (user-message-only)"
                )

            with allure.step(
                "Side-channel check — no console errors/warnings across the flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors/warnings: "
                    f"{[m.text for m in console_messages]}"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0144_agent-edit-and-delete.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_delete_agent_via_api(self, page, agent_api):
        """Create an agent, delete via API, and verify it's gone from the UI."""
        with allure.step("Step 1 — Create agent via API"):
            agent = agent_api.create_agent(
                name="autotest_delete_api",
                description="Will be deleted",
            )
            aid = agent["id"]
            agent_name = "autotest_delete_api"

        try:
            with allure.step("Step 2 — Navigate to agents list"):
                list_page = AgentsListPage(page)
                list_page.navigate()

            with allure.step("Step 3 — Verify agent appears in list"):
                assert list_page.agent_exists_in_list(agent_name, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Delete agent via API"):
                agent_api.delete_agent(aid)
                aid = None

            with allure.step("Step 5 — Reload and verify agent is gone"):
                list_page.reload_and_wait()
                assert not list_page.agent_exists_in_list(agent_name, timeout=3000), (
                    f"Agent '{agent_name}' should be gone after API deletion"
                )
        finally:
            if aid is not None:
                try:
                    agent_api.delete_agent(aid)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {aid}: {cleanup_exc}")

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0144_agent-edit-and-delete.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_delete_agent_via_ui_menu(self, page, agent_api):
        """Create an agent, delete via the UI three-dot menu, and verify removal."""
        with allure.step("Step 1 — Create agent via API"):
            agent = agent_api.create_agent(
                name="autotest_delete_ui",
                description="Will be deleted via UI",
            )
            aid = agent["id"]

        try:
            with allure.step("Step 2 — Navigate to agent detail page"):
                detail_page = AgentDetailPage(page)
                detail_page.navigate(aid)

            with allure.step("Step 3 — Delete agent via three-dot menu"):
                detail_page.delete_agent_via_menu(timeout=NAVIGATION_TIMEOUT)
                aid = None

            with allure.step("Step 4 — Navigate to agents list and verify agent is gone"):
                list_page = AgentsListPage(page)
                list_page.navigate()
                assert not list_page.agent_exists_in_list("autotest_delete_ui", timeout=3000), (
                    "Agent should not appear in list after UI deletion"
                )
        finally:
            if aid is not None:
                try:
                    agent_api.delete_agent(aid)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {aid}: {cleanup_exc}")


class TestAgentExecution:
    """Agent execution — instructions field alone does not prevent execution (ELITEA-1897).

    Verifies that an agent created with only Name + Description + Instructions
    (no toolkit attached) executes correctly via the embedded chat: the Save
    button succeeds, the chat accepts a message, the agent responds with the
    expected content, and no persistent spinner/error state is left behind.

    Spec: test-specs/agents/l2_agent-execution-name-description-sufficient_ELITEA-1897.md

    Note: this case's differentiator vs ``TestCreateAgent.test_create_agent_via_ui``
    is chat *execution* (steps 2-4 below), not agent creation mechanics — agent
    creation here goes through ``agent_api.create_agent_full()`` (a dedicated,
    toolkit-free payload, per the AFS's Automation Hints and Cleanup
    recommendation), not the UI create-form, since UI-form creation is already
    covered by ``test_create_agent_via_ui``.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1897_agent-execution-name-description-sufficient.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_agent_executes_with_name_description_instructions_only(self, page, agent_api):
        """A toolkit-free agent (Name+Description+Instructions only) executes
        via the embedded chat and responds without hanging."""
        agent_name = f"autotest_{uuid.uuid4().hex[:8]}_1897"[:32]
        agent_description = (
            "Agent for ELITEA-1897 — name+description+instructions execution check"
        )
        agent_instructions = (
            "You are a plain test assistant with no external tools attached. "
            "Follow the user's literal instructions exactly."
        )
        test_message = "Reply with: CONFIRMED"

        with allure.step(
            "Step 1 — Create agent with Name, Description, Instructions filled"
        ):
            payload = _build_execution_agent_payload(
                agent_name, agent_description, agent_instructions
            )
            agent = agent_api.create_agent_full(payload)
            agent_id = agent["id"]
            assert agent_id, "Agent creation response should include an id"

        detail_page = AgentDetailPage(page)
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        try:
            with allure.step(
                "Step 1 (verify) — Agent created successfully; detail page shows it"
            ):
                detail_page.navigate(agent_id)
                assert detail_page.get_name() == agent_name, (
                    f"Agent detail page should show the created agent's name '{agent_name}'"
                )

            with allure.step(f'Step 2 — Send "{test_message}" in the embedded chat'):
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(test_message)
                after_send_count = _wait_for_chat_message_count(
                    detail_page, initial_count, timeout=UI_ELEMENT_TIMEOUT
                )
                assert after_send_count > initial_count, (
                    "Embedded chat should show the user's message after sending "
                    f"(count stayed at {after_send_count})"
                )

            with allure.step(
                'Step 3 — Verify agent responds with a message containing "CONFIRMED"'
            ):
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT
                )
                response_text = detail_page.get_last_chat_response_text()
                assert response_text, (
                    "Embedded chat should show a non-empty AI response after the wait"
                )
                assert "CONFIRMED" in response_text.upper(), (
                    f"Expected response to contain 'CONFIRMED', got: {response_text!r}"
                )

            with allure.step(
                "Step 4 — Verify no persistent spinner/error state (no hang)"
            ):
                # No dedicated spinner-absence testid exists (AFS Concrete
                # Handles gap) — stand-in per existing wait_for_chat_response
                # convention: response actually arrived, chat input is
                # re-enabled (not stuck), and no console errors were raised.
                assert detail_page.get_chat_message_count() > initial_count, (
                    "Response should have actually arrived (message count increased), "
                    "not left the chat hanging"
                )
                assert detail_page.chat_message_input.is_enabled(), (
                    "Chat input should be re-enabled after the response, not stuck "
                    "disabled/hung"
                )
                assert not console_errors, (
                    "Expected no console errors during agent execution, got: "
                    f"{[m.text for m in console_errors]}"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
