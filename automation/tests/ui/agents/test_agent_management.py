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

import pytest
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


class TestCreateAgent:
    """Create Agent (P0): create via UI, verify in list and via API."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0145_agent-creation-ui-and-api.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_create_agent_via_ui(self, page, agent_api):
        """Create an agent through the UI form and verify it appears in the list.

        Steps:
        1. Navigate to create agent page
        2. Fill in name + description + instructions
        3. Click Save
        4. Verify user lands on the agent detail page
        5. Navigate back to agents list
        6. Verify agent appears in the list
        """
        agent_name = "autotest_create_ui"
        agent_desc = "Created by UI automation test"
        agent_instr = "You are a test assistant created by automation."
        created_agent_id = None  # Initialize for cleanup

        # Step 1: Navigate to create page
        list_page = AgentsListPage(page)
        list_page.navigate_to_create()

        # Step 2: Fill and submit form
        form_page = AgentFormPage(page)
        form_page.wait_for_form_load()
        form_page.fill_form(
            name=agent_name,
            description=agent_desc,
            instructions=agent_instr,
        )

        # Step 3: Verify Save is enabled and click it
        form_page.wait_for_form_validation()
        assert form_page.is_save_enabled(), "Save button should be enabled after filling required fields"
        form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

        # Step 4: Verify user lands on the agent detail page
        detail_page = AgentDetailPage(page)
        detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
        detail_page.verify_on_detail_page()

        try:
            # Capture agent ID immediately so cleanup is guaranteed even if
            # later assertions fail.
            agent_id_str = detail_page.get_agent_id()
            try:
                created_agent_id = int(agent_id_str)
            except (ValueError, TypeError) as e:
                pytest.fail(f"Failed to parse agent ID '{agent_id_str}': {e}")

            # Verify we're on the correct agent's page
            displayed_name = detail_page.name_input.input_value()
            assert displayed_name == agent_name, f"Expected agent name '{agent_name}', got '{displayed_name}'"

            # Step 5: Navigate back to agents list
            list_page.navigate()

            # Step 6: Verify agent appears in the list
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
        """Create an agent via API fixture and verify it shows in the UI list.

        The ``agent_id`` fixture creates the agent; this test navigates to
        the agents dashboard and checks for its presence.
        """
        agent = agent_api.get_agent(agent_id)
        agent_name = agent.get("name", "")

        list_page = AgentsListPage(page)
        list_page.navigate()

        assert list_page.agent_exists_in_list(agent_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"Agent '{agent_name}' should appear in the agents list"
        )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0136_agent-creation-field-validation.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0145_agent-creation-ui-and-api.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_create_agent_required_fields_validation(self, page):
        """Save button should be disabled when required fields are empty."""
        list_page = AgentsListPage(page)
        list_page.navigate_to_create()

        form_page = AgentFormPage(page)
        form_page.wait_for_form_load()

        # With empty fields, Save should be disabled
        assert not form_page.is_save_enabled(), "Save should be disabled with empty required fields"

        # Fill only name — still missing description
        form_page.fill_form(name="autotest_partial", description="")
        form_page.wait_for_form_validation()
        assert not form_page.is_save_enabled(), "Save should be disabled without description"

        # Fill both required fields — Save must now be enabled
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
        agent = agent_api.get_agent(agent_id)

        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        assert detail_page.name_input.input_value() == agent.get("name", ""), "Name should match"
        assert detail_page.description_input.input_value() == agent.get("description", ""), "Description should match"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0141_agent-detail-page-configuration-and-tabs.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_agent_instructions_field(self, page, agent_id):
        """Instructions field should be visible and editable."""
        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        assert detail_page.instructions_input.is_visible(), "Instructions field should be visible"

        # The fixture sets instructions to "You are a test agent."
        value = detail_page.instructions_input.input_value()
        assert "test agent" in value.lower(), (
            f"Instructions should contain 'test agent', got: {value}"
        )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0141_agent-detail-page-configuration-and-tabs.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_agent_information_section(self, page, agent_id):
        """Information section should display Agent ID and Version ID."""
        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        agent_id_text = detail_page.get_agent_id()
        version_id_text = detail_page.get_version_id()

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
        """Toolkits section should be visible with tool switches.

        Note: get_available_tools() already verifies visibility internally by
        checking each tool switch is visible before adding to the list. This test
        verifies the toolkits section loaded with at least one tool available.
        """
        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        # Get all available tools dynamically (robust to UI changes)
        # Note: get_available_tools() automatically scrolls to toolkits section
        # and only returns tools that are actually visible on the page
        available_tools = detail_page.get_available_tools()

        # Should have at least one internal tool
        assert len(available_tools) > 0, (
            "Should have at least one internal tool available in toolkits section"
        )

        # Log what tools were found for debugging
        print(f"Available tools: {[t.value for t in available_tools]}")

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0141_agent-detail-page-configuration-and-tabs.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_internal_tools_enum_usage(self, page, agent_id):
        """Verify internal tools can be toggled using the enum-based API.

        Note: This is a smoke test for the toggle_tool() API accepting enum values.
        Full state verification (checking if checkbox actually changed) is not
        performed due to MUI DOM complexity making is_tool_enabled() unreliable.
        See test_internal_tools_enable_disable (skipped) for details.

        This test verifies:
        - toggle_tool() accepts InternalTool enum values
        - Method completes without errors
        - Can be called multiple times without breaking
        """
        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        # Get all available tools (automatically scrolls to toolkits section)
        available_tools = detail_page.get_available_tools()
        assert len(available_tools) > 0, "Should have at least one internal tool available"

        test_tool = available_tools[0]
        print(f"Testing toggle API with tool: {test_tool.value}")

        # Toggle tool (will raise exception if method fails).
        # Note: MUI toggle switches do not reliably update the form's dirty
        # state, so is_save_enabled() is not asserted here. The test verifies
        # that toggle_tool() accepts InternalTool enum values without throwing.
        try:
            detail_page.toggle_tool(test_tool)
            detail_page.wait_for_network(timeout=2000)

            # Toggle back — verifies the method can be called multiple times
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
        """Agents dashboard loads with functional header and search.

        Verifies:
        - Dashboard navigates successfully
        - Header is visible
        - Search input is visible and editable (not just rendered)
        - Search input accepts text input (functional check)
        """
        list_page = AgentsListPage(page)
        list_page.navigate()

        # Header "Agents" should be visible
        list_page.verify_dashboard_header_visible()

        # Search input should be present and functional
        assert list_page.search_input.is_visible(), "Search input should be visible"
        assert list_page.search_input.is_editable(), (
            "Search input should be editable (not just visible)"
        )

        # Verify search is functional by typing and clearing via page object method
        # This tests that the input accepts text (React onChange fires)
        list_page.verify_search_functional()

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0140_agent-dashboard-and-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_agent_search(self, page, agent_id, agent_api):
        """Search for an agent by name on the dashboard."""
        agent = agent_api.get_agent(agent_id)
        agent_name = agent.get("name", "")

        list_page = AgentsListPage(page)
        list_page.navigate()

        # Search for the agent (includes debounce wait)
        list_page.search_and_wait_for_results(agent_name)

        assert list_page.agent_exists_in_list(agent_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"Agent '{agent_name}' should appear in search results"
        )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0140_agent-dashboard-and-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_agent_search_no_results(self, page):
        """Searching for a non-existent agent should show no results."""
        list_page = AgentsListPage(page)
        list_page.navigate()

        list_page.search_and_wait_for_results("zzzz_nonexistent_agent_12345")

        assert not list_page.agent_exists_in_list(
            "zzzz_nonexistent_agent_12345", timeout=3000
        ), "Non-existent agent should not appear in results"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0140_agent-dashboard-and-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_view_toggle_table_and_card(self, page):
        """Dashboard should support switching between table and card views.

        Verifies:
        - View toggle buttons are visible
        - Clicking table view activates table view
        - Clicking card view activates card view
        - Dashboard header remains visible after view changes
        """
        list_page = AgentsListPage(page)
        list_page.navigate()

        # View toggle buttons should be visible
        assert list_page.table_view_button.is_visible(), "Table view button should exist"
        assert list_page.card_view_button.is_visible(), "Card view button should exist"

        # Switch to table view and verify
        list_page.switch_to_table_view()
        assert list_page.is_table_view_active(), (
            "Table view should be active after clicking table view button"
        )

        # Switch back to card view and verify
        list_page.switch_to_card_view()
        assert list_page.is_card_view_active(), (
            "Card view should be active after clicking card view button"
        )

        # Dashboard header should still be visible after view changes
        list_page.verify_dashboard_header_visible()


class TestAgentActions:
    """Agent Actions (P1): edit agent, delete agent, verify cleanup."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0144_agent-edit-and-delete.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0138_agent-edit-operations-name-and-description.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_edit_agent_name(self, page, agent_id):
        """Edit an agent's name and verify the change persists."""
        new_name = "autotest_renamed_agent"

        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        # Update name (handles React onChange trigger and validation wait)
        detail_page.update_name(new_name)

        # Save should be enabled
        assert detail_page.is_save_enabled(), "Save should be enabled after name change"
        detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        # Reload and verify
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

        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        # Update description (handles React onChange trigger and validation wait)
        detail_page.update_description(new_desc)

        assert detail_page.is_save_enabled(), "Save should be enabled after description change"
        detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        # Reload and verify (consistent with test_edit_agent_name)
        detail_page.reload_and_wait()
        assert detail_page.description_input.input_value() == new_desc, (
            f"Agent description should be '{new_desc}' after save"
        )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0144_agent-edit-and-delete.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_delete_agent_via_api(self, page, agent_api):
        """Create an agent, delete via API, and verify it's gone from the UI."""
        agent = agent_api.create_agent(
            name="autotest_delete_api",
            description="Will be deleted",
        )
        aid = agent["id"]
        agent_name = "autotest_delete_api"

        try:
            list_page = AgentsListPage(page)
            list_page.navigate()

            # Verify it appears
            assert list_page.agent_exists_in_list(agent_name, timeout=UI_ELEMENT_TIMEOUT)

            # Delete via API
            agent_api.delete_agent(aid)
            aid = None  # Mark as deleted so finally block skips

            # Reload and verify gone
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
        agent = agent_api.create_agent(
            name="autotest_delete_ui",
            description="Will be deleted via UI",
        )
        aid = agent["id"]

        try:
            detail_page = AgentDetailPage(page)
            detail_page.navigate(aid)

            # delete_agent_via_menu includes navigation wait internally
            detail_page.delete_agent_via_menu(timeout=NAVIGATION_TIMEOUT)
            aid = None  # Mark as deleted so finally block skips

            # Navigate to agents list and verify absence
            list_page = AgentsListPage(page)
            list_page.navigate()  # Includes built-in waits for page load
            assert not list_page.agent_exists_in_list("autotest_delete_ui", timeout=3000), (
                "Agent should not appear in list after UI deletion"
            )
        finally:
            if aid is not None:
                try:
                    agent_api.delete_agent(aid)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {aid}: {cleanup_exc}")
