"""Agent page object for Elitea agent management.

This is a facade/wrapper that provides a unified interface for agent operations
by delegating to specialized component pages:
- AgentsListPage: Dashboard, search, and agent selection
- AgentFormPage: Create and edit agent forms
- AgentDetailPage: Agent detail view, toolkits, and embedded chat

For most use cases, import this unified AgentPage class:
    from pages.agent_page import AgentPage

For advanced use cases requiring direct access to specific components:
    from pages.agents_list_page import AgentsListPage
    from pages.agent_form_page import AgentFormPage
    from pages.agent_detail_page import AgentDetailPage
"""

import logging
from playwright.sync_api import Page

from .agents_list_page import AgentsListPage
from .agent_form_page import AgentFormPage
from .agent_detail_page import AgentDetailPage


logger = logging.getLogger("elitea.pages.agent")


class AgentPage:
    """Unified facade for agent management operations.

    This facade delegates to specialized component pages (AgentsListPage,
    AgentFormPage, AgentDetailPage) to provide a unified interface for
    agent-related UI operations.

    IMPORTANT: This is a FACADE ONLY - it delegates method calls but does
    NOT expose locators. For direct access to form fields or other locators,
    import and use the specialized pages directly:
        - AgentsListPage: Dashboard, search, navigation
        - AgentFormPage: Create/edit forms
        - AgentDetailPage: Detail view, toolkits, embedded chat

    Example:
        # For dashboard operations
        from pages.agents_list_page import AgentsListPage
        list_page = AgentsListPage(page)
        list_page.search_input.fill("query")

        # For form operations
        from pages.agent_detail_page import AgentDetailPage
        detail_page = AgentDetailPage(page)
        detail_page.name_input.click()
    """

    def __init__(self, page: Page):
        """Initialize all page objects.

        Args:
            page: Playwright Page instance.
        """
        self.page = page
        self._list_page = AgentsListPage(page)
        self._form_page = AgentFormPage(page)
        self._detail_page = AgentDetailPage(page)

    # ------------------------------------------------------------------
    # Navigation (delegates to appropriate page)
    # ------------------------------------------------------------------

    def navigate_to_agents(self):
        """Navigate to the agents dashboard."""
        return self._list_page.navigate()

    def navigate_to_create_agent(self):
        """Navigate to the create agent page."""
        return self._list_page.navigate_to_create()

    def navigate_to_agent(self, agent_id: int):
        """Navigate to a specific agent's detail page."""
        return self._detail_page.navigate(agent_id)

    # ------------------------------------------------------------------
    # Dashboard actions (delegates to AgentsListPage)
    # ------------------------------------------------------------------

    def wait_for_agents_list(self, timeout: int = 15000):
        """Wait for the agents dashboard to load."""
        return self._list_page.wait_for_page_load(timeout=timeout)

    def click_create_agent(self, timeout: int = 10000):
        """Click the Create Agent button in the sidebar."""
        return self._list_page.click_create_agent(timeout=timeout)

    def get_agent_card_names(self, timeout: int = 5000) -> list[str]:
        """Return names of all agent cards visible on the dashboard."""
        return self._list_page.get_agent_card_names(timeout=timeout)

    def agent_exists_in_list(self, name: str, timeout: int = 5000) -> bool:
        """Check whether an agent with name is visible on the dashboard."""
        return self._list_page.agent_exists_in_list(name, timeout=timeout)

    def select_agent_from_list(self, name: str, timeout: int = 5000):
        """Click an agent card on the dashboard by name."""
        return self._list_page.select_agent(name, timeout=timeout)

    def search_agents(self, query: str, timeout: int = 5000):
        """Type a search query into the agents search box."""
        return self._list_page.search(query, timeout=timeout)

    def clear_search(self):
        """Clear the agents search box."""
        return self._list_page.clear_search()

    # ------------------------------------------------------------------
    # Create / Edit form (delegates to AgentFormPage)
    # ------------------------------------------------------------------

    def wait_for_agent_form(self, timeout: int = 15000):
        """Wait for the agent create/edit form to load."""
        return self._form_page.wait_for_form_load(timeout=timeout)

    def fill_agent_form(
        self,
        name: str,
        description: str,
        instructions: str = "",
        welcome_message: str = "",
    ):
        """Fill in the agent create/edit form."""
        return self._form_page.fill_form(
            name=name,
            description=description,
            instructions=instructions,
            welcome_message=welcome_message,
        )

    def get_agent_name(self) -> str:
        """Read the current value of the Name field."""
        return self._form_page.get_name()

    def get_name(self) -> str:
        """Alias for get_agent_name() - read the current value of the Name field."""
        return self._form_page.get_name()

    def get_agent_description(self) -> str:
        """Read the current value of the Description field."""
        return self._form_page.get_description()

    def get_description(self) -> str:
        """Alias for get_agent_description() - read the current value of the Description field."""
        return self._form_page.get_description()

    def get_agent_instructions(self) -> str:
        """Read the current value of the Instructions field."""
        return self._form_page.get_instructions()

    def get_instructions(self) -> str:
        """Alias for get_agent_instructions() - read the current value of the Instructions field."""
        return self._form_page.get_instructions()

    def click_save(self, timeout: int = 10000):
        """Click the Save button and wait for network."""
        return self._form_page.click_save(timeout=timeout)

    def is_save_enabled(self) -> bool:
        """Check if the Save button is enabled."""
        return self._form_page.is_save_enabled()

    def save_and_wait(self, timeout: int = 15000):
        """Click Save and wait for the save to complete."""
        return self._form_page.save_and_wait(timeout=timeout)

    # ------------------------------------------------------------------
    # Agent detail page (delegates to AgentDetailPage)
    # ------------------------------------------------------------------

    def wait_for_agent_detail(self, timeout: int = 15000):
        """Wait for the agent detail/edit page to fully load."""
        return self._detail_page.wait_for_page_load(timeout=timeout)

    def get_agent_id_from_info(self) -> str:
        """Read the Agent ID from the Information section."""
        return self._detail_page.get_agent_id()

    def get_version_id_from_info(self) -> str:
        """Read the Version ID from the Information section."""
        return self._detail_page.get_version_id()

    # ------------------------------------------------------------------
    # Toolkits (delegates to AgentDetailPage)
    # ------------------------------------------------------------------

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool switch is checked."""
        return self._detail_page.is_tool_enabled(tool_name)

    def toggle_tool(self, tool_name: str):
        """Toggle a tool switch by clicking its label area."""
        return self._detail_page.toggle_tool(tool_name)

    def add_toolkit(self, toolkit_name: str, timeout: int = 10000):
        """Add an external toolkit to the agent."""
        return self._detail_page.add_toolkit(toolkit_name, timeout=timeout)

    def is_toolkit_attached(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check whether a toolkit is attached to the agent."""
        return self._detail_page.is_toolkit_attached(toolkit_name, timeout=timeout)

    def remove_toolkit(self, toolkit_name: str, timeout: int = 10000):
        """Remove a toolkit from the agent configuration."""
        return self._detail_page.remove_toolkit(toolkit_name, timeout=timeout)

    # ------------------------------------------------------------------
    # Embedded chat (delegates to AgentDetailPage)
    # ------------------------------------------------------------------

    def send_message_in_embedded_chat(self, message: str, timeout: int = 10000):
        """Type and send a message in the embedded chat panel."""
        return self._detail_page.send_chat_message(message, timeout=timeout)

    def wait_for_embedded_chat_response(
        self,
        initial_count: int = 0,
        stable_duration_ms: int = 3000,
        timeout: int = 60000,
    ):
        """Wait for the AI response in the embedded chat to stabilize."""
        return self._detail_page.wait_for_chat_response(
            initial_count=initial_count,
            stable_duration_ms=stable_duration_ms,
            timeout=timeout,
        )

    def get_embedded_chat_message_count(self) -> int:
        """Return the number of messages currently in the embedded chat."""
        return self._detail_page._embedded_chat_messages().count()

    def get_embedded_chat_last_message(self) -> str:
        """Return the text content of the last AI message in embedded chat."""
        return self._detail_page.get_last_chat_message()

    # ------------------------------------------------------------------
    # Three-dot menu actions (delegates to AgentDetailPage)
    # ------------------------------------------------------------------

    def open_actions_menu(self):
        """Open the three-dot actions menu on the agent detail page."""
        return self._detail_page.open_actions_menu()

    def delete_agent_via_menu(self, timeout: int = 10000):
        """Delete the current agent via the three-dot menu."""
        return self._detail_page.delete_agent_via_menu(timeout=timeout)

    def click_back_button(self, timeout: int = 5000):
        """Click the back arrow button on the agent detail page."""
        return self._detail_page.click_back_button(timeout=timeout)
