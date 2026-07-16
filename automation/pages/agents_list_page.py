"""Agents List Page - Dashboard view for browsing and searching agents.

Handles: /agents/all
- Agent list/dashboard display
- Search and filter agents
- Navigate to create agent
- Select agent from list
- Import an Agent from an exported ``.agent.md`` file
"""

import re
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

    # Fixed (ELITEA-1870): the previous testid ("create-agent-button") does
    # not exist in the live DOM (confirmed via a full
    # `[data-testid]` inventory on /agents/all — 0 matches); the real,
    # confirmed-live testid on the sidebar create-agent control is
    # "sidebar-create-button". The old `fallback` (a `get_by_label("Create
    # Agent")` role lookup) also doesn't match live and is dropped per the
    # testid-only locator policy (`.claude/rules/page-objects.md` — no
    # fallback param). This is a page-object housekeeping fix; the button's
    # click-to-navigate behavior itself was already correct.
    create_agent_button = LocatorDescriptor(
        testid="sidebar-create-button",
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

    # -- Import (ELITEA-1795, testid-only rework — EliteaUI draft PR #552) --
    import_button = LocatorDescriptor(
        testid="agents-import-button",
        description="Import agent button in the Agents list page toolbar"
    )

    import_preview_dialog = LocatorDescriptor(
        testid="agent-import-preview-dialog",
        description="'Import parameters' preview dialog"
    )

    import_preview_name = LocatorDescriptor(
        testid="agent-import-preview-name",
        description="Import preview — the Main entity (Agent) name"
    )

    import_preview_skill_name = LocatorDescriptor(
        testid="agent-import-preview-skill-name",
        description="Import preview — the embedded Skill's name (shared "
                     "testid across every Skill card in the preview)"
    )

    import_preview_card_toggle = LocatorDescriptor(
        testid="agent-import-preview-card-toggle",
        description="'Show details' toggle, shared by every entity-preview "
                     "card (Main entity + each Skill). Rendered ONLY while "
                     "collapsed (removed from the DOM once expanded) so a "
                     "'click until none remain' loop naturally converges"
    )

    import_preview_skill_instructions = LocatorDescriptor(
        testid="agent-import-preview-skill-instructions",
        description="Import preview — the embedded Skill's instructions "
                     "text (visible only once its card is expanded)"
    )

    import_confirm_button = LocatorDescriptor(
        testid="agent-import-confirm-button",
        description="'Import parameters' dialog's scoped Import (confirm) button"
    )

    import_complete_dialog = LocatorDescriptor(
        testid="agent-import-complete-dialog",
        description="'Import Complete' success dialog"
    )

    import_complete_agents_list = LocatorDescriptor(
        testid="agent-import-complete-list-agents",
        description="'Import Complete' dialog — imported Agents name list"
    )

    import_complete_skills_list = LocatorDescriptor(
        testid="agent-import-complete-list-skills",
        description="'Import Complete' dialog — imported Skills name list"
    )

    import_complete_got_it_button = LocatorDescriptor(
        testid="agent-import-complete-got-it-button",
        description="'Import Complete' dialog's 'Got it' confirm/navigate button"
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
        super().navigate("/agents/all")
        self.wait_for_page_load()
        logger.info("Navigated to agents dashboard and page loaded")

    @action("Navigate to create agent")
    def navigate_to_create(self):
        """Navigate to the create agent page and wait until ready.

        Automatically waits for the form to load. For explicit waiting,
        use AgentFormPage.wait_for_form_load().
        """
        super().navigate("/agents/create?viewMode=owner")
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

    # Fixed (ELITEA-1869): the previous locator —
    # ``'[class*="CardContent"] >> text, [class*="cardContent"] >> text'`` —
    # combined a CSS selector list with a chained Playwright text engine in a
    # single selector string; Playwright parses the whole string as one
    # locator chain, so the comma is consumed inside the chain instead of
    # acting as a top-level OR. The result matched 0 elements (verified via
    # a standalone Playwright script against the live dashboard — 6 real
    # cards present, 0 matched), so this method always returned ``[]``,
    # silently. No existing test exercised this method before ELITEA-1869
    # (confirmed via repo-wide grep), so this is a straight fix, not a
    # shared-caller change. Now resolved via the shared ``entity-card-name``
    # Card.jsx testid (also used by Credentials/Mcp/Skills/Pipelines list
    # pages — see ``CredentialsListPage.entity_card_name`` for the identical
    # collection-locator pattern), a proper class-level ``LocatorDescriptor``
    # per the testid-only policy (`.claude/rules/page-objects.md`), instead
    # of a raw locator string built/used inside the method body.
    entity_card_name = LocatorDescriptor(
        testid="entity-card-name",
        description="Agent card name (title) — collection locator, one per visible card",
    )

    def get_agent_card_names(self, timeout: int = 5000) -> list[str]:
        """Return names of all agent cards visible on the dashboard.

        Returns:
            List of agent name strings.
        """
        self.wait_for_network(timeout=timeout)
        cards = self.entity_card_name

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

    # ------------------------------------------------------------------
    # Import (ELITEA-1795)
    # ------------------------------------------------------------------

    @action("Import agent from file")
    def import_agent(self, file_path: str, timeout: int = 10000):
        """Import an Agent from an exported ``.agent.md`` file.

        Clicks the page-toolbar Import button (``agents-import-button``
        data-testid — added via ``add-data-testid`` in the ELITEA-1795
        testid-only rework, threading an optional ``testId`` prop through
        the shared ``ToolbarImportButton``; see EliteaUI draft PR #552).
        Clicking it opens a native OS file chooser directly (no
        intermediate menu).

        Handles the file chooser and waits for the "Import parameters"
        preview dialog (``agent-import-preview-dialog``) to render. Does
        NOT click the dialog's own Import (confirm) button — call
        :meth:`confirm_agent_import` separately once the preview has been
        verified.

        Args:
            file_path: Absolute path to the exported ``.agent.md`` file.
            timeout: Maximum wait time in milliseconds for the dialog.
        """
        logger.info("Importing agent from file: %s", file_path)
        with self.page.expect_file_chooser() as fc_info:
            self.import_button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)

        self.import_preview_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Import parameters dialog visible")

    @action("Expand import preview details")
    def expand_import_preview_details(self, timeout: int = 10000):
        """Expand every "Show details" toggle in the Import parameters dialog.

        Unlike the Skill import dialog (a single entity preview), the
        Agent import dialog renders two collapsed preview sections —
        "Main entity" (the Agent) and "Skills" (each embedded Skill) —
        each behind its own "Show details" toggle
        (``IWModalEntityCardWrapper``, ``defaultExpanded=false``). Clicks
        all of them so Description/Instructions preview text is actually
        rendered (non-zero height) before assertions read it.

        Every toggle carries the SAME ``agent-import-preview-card-toggle``
        data-testid, but only while its own card is collapsed — the JSX
        omits the attribute once expanded (``IWModalEntityCardWrapper``'s
        own ``isExpanded`` state). So the locator is re-queried and its
        first match clicked repeatedly until none remain — a fixed-count
        loop indexed by ``nth()`` would go out of bounds after the first
        click shrinks the live match set.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        toggles = self.import_preview_card_toggle
        expanded_count = 0
        while toggles.count() > 0:
            toggles.first.click()
            expanded_count += 1
            self.page.wait_for_timeout(200)
        if expanded_count:
            # Grid-template-rows CSS transition (0.4s) — wait for the
            # Skill instructions preview to actually be visible rather
            # than a fixed sleep.
            self.import_preview_skill_instructions.first.wait_for(
                state="visible", timeout=timeout,
            )
        logger.info(
            "Expanded %d 'Show details' toggle(s) in import dialog", expanded_count,
        )

    @action("Confirm agent import in dialog")
    def confirm_agent_import(self, timeout: int = 15000):
        """Click the "Import parameters" dialog's scoped Import (confirm) button.

        Resolved via the ``agent-import-confirm-button`` data-testid —
        distinct from the page-toolbar Import button's own
        ``agents-import-button`` testid, so no dialog-scoping is needed
        (previously both shared the accessible name "Import"). Confirming
        transitions to the "Import Complete" success dialog (handled by
        :meth:`confirm_import_complete`), not directly to the new Agent's
        detail page.

        Args:
            timeout: Maximum wait time in milliseconds for the success dialog.
        """
        logger.info("Confirming agent import")
        self.import_confirm_button.click()
        self.import_complete_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Import Complete dialog visible")

    @action("Confirm import complete")
    def confirm_import_complete(self, timeout: int = 15000) -> int:
        """Click "Got it" on the "Import Complete" success dialog.

        Auto-navigates to the newly imported Agent's detail page. Parses
        and returns the new Agent's numeric ID from the resulting URL.

        Args:
            timeout: Maximum wait time in milliseconds for the navigation.

        Returns:
            The imported Agent's numeric ID.
        """
        self.import_complete_got_it_button.click()
        self.page.wait_for_url(re.compile(r".*/agents/all/\d+"), timeout=timeout)
        self.wait_for_network(timeout=5000)

        match = re.search(r"/agents/all/(\d+)", self.page.url)
        if not match:
            raise ValueError(
                f"Could not parse imported Agent ID from URL: {self.page.url}"
            )
        agent_id = int(match.group(1))
        logger.info("Import complete — navigated to agent id=%d", agent_id)
        return agent_id
