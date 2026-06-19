"""Agents List Page - Dashboard view for browsing and searching agents.

Handles: /app/agents/all
- Agent list/dashboard display
- Search and filter agents
- Navigate to create agent
- Select agent from list
"""

import logging
from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action


logger = logging.getLogger("elitea.pages.agents_list")


class AgentsListPage(BasePage):
    """Page object for the agents list/dashboard page."""

    # Locators - using annotation-driven descriptors
    search_input = LocatorDescriptor(
        testid="agent-search-input",
        fallback=lambda page: page.locator('input[placeholder="Let\'s find something amazing!"]'),
        description="Search agents input field"
    )

    create_agent_button = LocatorDescriptor(
        testid="create-agent-button",
        fallback=lambda page: page.get_by_label("Create Agent").get_by_role("button"),
        description="Create Agent button in sidebar"
    )

    table_view_button = LocatorDescriptor(
        testid="agent-table-view-button",
        fallback=lambda page: page.locator('[aria-label="Table view"] button'),
        description="Switch to table view"
    )

    card_view_button = LocatorDescriptor(
        testid="agent-card-view-button",
        fallback=lambda page: page.locator('[aria-label="Card list view"] button'),
        description="Switch to card view"
    )

    page_header = LocatorDescriptor(
        testid="agents-page-header",
        fallback=lambda page: page.locator('text="Agents"').first,
        description="Agents page header"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to agents list")
    def navigate(self):
        """Navigate to the agents dashboard and wait until ready.

        Automatically waits for the "Agents" heading to appear and network
        to settle. For explicit waiting (e.g., after reload), use
        wait_for_page_load().
        """
        super().navigate("/app/agents/all")
        self.wait_for_page_load()
        logger.info("Navigated to agents dashboard and page loaded")

    @action("Navigate to create agent")
    def navigate_to_create(self):
        """Navigate to the create agent page and wait until ready.

        Automatically waits for the form to load. For explicit waiting,
        use AgentFormPage.wait_for_form_load().
        """
        super().navigate("/app/agents/create?viewMode=owner")
        self.wait_for_network(timeout=10000)
        logger.info("Navigated to create agent page and page loaded")

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the agents dashboard to load."""
        self.page_header.wait_for(state="visible", timeout=timeout)
        self.wait_for_network(timeout=10000)
        self.dismiss_banner_if_present()
        logger.info("Agents dashboard loaded")

    def verify_dashboard_header_visible(self):
        """Verify the Agents header is visible.

        Uses global timeout (10s) configured in conftest.py.
        """
        self.page_header.wait_for(state="visible")
        logger.info("Verified dashboard header is visible")

    # ------------------------------------------------------------------
    # Agent list operations
    # ------------------------------------------------------------------

    def get_agent_card_names(self, timeout: int = 5000) -> list[str]:
        """Return names of all agent cards visible on the dashboard.

        Returns:
            List of agent name strings.
        """
        self.wait_for_network(timeout=timeout)
        cards = self.page.locator('[class*="CardContent"] >> text, [class*="cardContent"] >> text')

        try:
            cards.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return []

        names = []
        for i in range(cards.count()):
            names.append(cards.nth(i).text_content().strip())
        return names

    def agent_exists_in_list(self, name: str, timeout: int = 5000) -> bool:
        """Check whether an agent with the given name is visible.

        Args:
            name: Agent name (or prefix) to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if agent is visible, False otherwise.
        """
        try:
            self.page.locator(f'text="{name}"').first.wait_for(
                state="visible", timeout=timeout,
            )
            return True
        except Exception:
            return False

    @action("Select agent")
    def select_agent(self, name: str, timeout: int = 5000):
        """Click an agent card on the dashboard by name.

        Args:
            name: The agent name to click.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting agent: %s", name)
        card = self.page.locator(f'text="{name}"').first
        card.wait_for(state="visible", timeout=timeout)
        card.click(force=True)
        self.wait_for_network(timeout=timeout)

    # ------------------------------------------------------------------
    # Search operations
    # ------------------------------------------------------------------

    @action("Search agents")
    def search(self, query: str, timeout: int = 5000):
        """Type a search query into the agents search box.

        Args:
            query: Text to search for.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Searching agents for: %s", query)
        self.search_input.wait_for(state="visible", timeout=timeout)
        self.search_input.fill(query)
        self.wait_for_network(timeout=timeout)

    @action("Search agents and wait")
    def search_and_wait_for_results(self, query: str, timeout: int = 2000):
        """Search and wait for results to appear.

        Handles search debounce automatically.

        Args:
            query: Text to search for
            timeout: Maximum wait time in milliseconds
        """
        self.search(query)
        self.wait_for_network(timeout=1000)
        self.page.wait_for_timeout(1000)  # Search debounce
        logger.info(f"Searched for '{query}' and results ready")

    @action("Clear agent search")
    def clear_search(self):
        """Clear the agents search box."""
        self.search_input.fill("")
        self.wait_for_network(timeout=5000)

    def verify_search_functional(self, query: str = "test", timeout: int = 5000) -> bool:
        """Verify the search input is functional by typing a query then clearing.

        Uses press_sequentially to trigger React onChange. Verifies that
        the typed text actually appears in the input field. Leaves the field
        empty after the call so callers do not need to clean up.

        Args:
            query: Text to type (default "test").
            timeout: Maximum wait for the input to be visible (ms).

        Returns:
            True if the search input accepted the text correctly.

        Raises:
            AssertionError: If the input value doesn't match the typed query.
        """
        self.search_input.wait_for(state="visible", timeout=timeout)
        self.search_input.click(force=True)
        self.search_input.press_sequentially(query, delay=50)

        # Verify the input actually accepted the text
        actual_value = self.search_input.input_value()
        assert actual_value == query, (
            f"Search input should contain '{query}' after typing, got '{actual_value}'"
        )

        self.search_input.clear()
        logger.info("Verified search input is functional")
        return True

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    @action("Click create agent")
    def click_create_agent(self, timeout: int = 10000):
        """Click the Create Agent button in the sidebar."""
        logger.info("Clicking Create Agent button")
        self.create_agent_button.wait_for(state="visible", timeout=timeout)
        self.create_agent_button.click(force=True)
        self.wait_for_network(timeout=timeout)

    # ------------------------------------------------------------------
    # View switching
    # ------------------------------------------------------------------

    @action("Switch to table view")
    def switch_to_table_view(self, wait_for_render: bool = True, timeout: int = 1000):
        """Switch to table view and optionally wait for rendering.

        Args:
            wait_for_render: Wait for view switch animation to complete
            timeout: Maximum wait time in milliseconds
        """
        self.table_view_button.click(force=True)
        if wait_for_render:
            self.page.wait_for_timeout(500)  # View switch animation
        logger.info("Switched to table view")

    @action("Switch to card view")
    def switch_to_card_view(self, wait_for_render: bool = True, timeout: int = 1000):
        """Switch to card view and optionally wait for rendering.

        Args:
            wait_for_render: Wait for view switch animation to complete
            timeout: Maximum wait time in milliseconds
        """
        self.card_view_button.click(force=True)
        if wait_for_render:
            self.page.wait_for_timeout(500)  # View switch animation
        logger.info("Switched to card view")

    def is_table_view_active(self) -> bool:
        """Check if table view is currently active.

        Returns:
            True if table view is active, False if card view is active.
        """
        # MUI ToggleButton sets aria-pressed="true" when active
        try:
            pressed = self.table_view_button.get_attribute("aria-pressed")
            return pressed == "true"
        except Exception:
            # Fallback: check if button has active/selected class
            classes = self.table_view_button.get_attribute("class") or ""
            return "selected" in classes.lower() or "active" in classes.lower()

    def is_card_view_active(self) -> bool:
        """Check if card view is currently active.

        Returns:
            True if card view is active, False if table view is active.
        """
        # MUI ToggleButton sets aria-pressed="true" when active
        try:
            pressed = self.card_view_button.get_attribute("aria-pressed")
            return pressed == "true"
        except Exception:
            # Fallback: check if button has active/selected class
            classes = self.card_view_button.get_attribute("class") or ""
            return "selected" in classes.lower() or "active" in classes.lower()
