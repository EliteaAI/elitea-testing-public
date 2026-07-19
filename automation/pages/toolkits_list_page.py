"""Toolkits List Page - Dashboard view for browsing toolkits.

Handles: /toolkits/all
- Toolkit list/dashboard display (shared Card.jsx ``entity-card`` testids)
- Search toolkits by name (shared ``SearchBar.jsx`` component)
- Navigate to the "+ Toolkit" creation wizard

Mirrors ``AgentsListPage``/``McpListPage``'s shape — same shared
``agent-search-input``/``entity-card``/``sidebar-create-button`` testids
(``SearchBar.jsx``/``Card.jsx`` are shared components reused across every
card-rendered list page in this app; see ``McpListPage`` for the identical
precedent). Added for ELITEA-1868 — ``automation/pages/`` previously had
zero coverage of the Toolkits list page (AFS § Overlap check).

Search mirrors ``McpListPage.search()``/``CredentialsListPage.search()`` —
same shared ``SearchBar.jsx`` component, explicit-activation (Enter/send
icon, NOT live-filter-as-you-type). Confirmed live for the Toolkits list
specifically (ELITEA-1868 implementer Phase 2 exploration): the
``entity-card`` count stayed unchanged immediately after typing alone and
only dropped to 0 once Enter was pressed.
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.toolkits_list")


class ToolkitsListPage(BasePage):
    """Page object for the Toolkits list/dashboard page.

    URL: /toolkits/all
    """

    # ------------------------------------------------------------------
    # Locators
    # ------------------------------------------------------------------

    sidebar_create_button = LocatorDescriptor(
        testid="sidebar-create-button",
        description="'+ Toolkit' create button in the sidebar (generic, shared across list pages)",
    )

    # Shared SearchBar.jsx component testid (also used by Agents/MCP/
    # Credentials/Skills list pages) — default testId prop value, confirmed
    # live this IS what the Toolkits list renders (no override at the
    # Toolkits call site).
    search_input = LocatorDescriptor(
        testid="agent-search-input",
        description="Toolkits search box (shared SearchBar.jsx component, default testId)",
    )

    # Shared Card.jsx component testid (also used by Agents/MCP/Pipelines/
    # Credentials list pages) — collection locator, one per visible card.
    entity_card = LocatorDescriptor(
        testid="entity-card",
        description="Toolkit card outer container (card view) — collection locator",
    )

    # Shared EmptyStatePage.jsx component testid (also used by MCP/
    # Applications/Skills/Pipelines list pages) — confirmed live this
    # renders for the Toolkits list's zero-match search state too.
    empty_state_title = LocatorDescriptor(
        testid="empty-state-title",
        description="Zero-results/zero-toolkits empty-state title ('No toolkits yet')",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to toolkits list")
    def navigate(self):
        """Navigate to the Toolkits dashboard and wait until ready."""
        super().navigate("/toolkits/all")
        self.wait_for_page_load()
        logger.info("Navigated to toolkits dashboard and page loaded")

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the toolkits dashboard to load.

        Waits on :attr:`sidebar_create_button` — the one element guaranteed
        present regardless of whether the project currently has any
        toolkits (unlike :attr:`entity_card`, which is absent on a
        zero-toolkit/zero-match project and would never reach "visible").
        """
        self.wait_for_network(timeout=timeout)
        self.sidebar_create_button.wait_for(state="visible", timeout=timeout)
        logger.info("Toolkits dashboard loaded")

    @action("Click '+ Toolkit' to open the creation wizard")
    def click_create_toolkit(self, timeout: int = 15000) -> None:
        """Click the sidebar '+ Toolkit' button and wait for the wizard's URL.

        Args:
            timeout: Maximum wait time in milliseconds for the URL to
                reflect the creation wizard.
        """
        self.sidebar_create_button.click()
        self.page.wait_for_url("**/toolkits/create*", timeout=timeout)
        logger.info("Clicked '+ Toolkit' — now at %s", self.page.url)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    @action("Search toolkits by name")
    def search(self, term: str) -> None:
        """Type *term* into the search box and press Enter (explicit-activation
        control — same ``SearchBar.jsx`` mechanics as
        ``McpListPage.search()``/``CredentialsListPage.search()``: typing
        alone does NOT filter, only Enter/the send icon dispatches it).

        Args:
            term: Search text.
        """
        self.search_input.click()
        self.search_input.press_sequentially(term, delay=20)
        self.search_input.press("Enter")
        self.wait_for_network()
        self.page.wait_for_timeout(1000)  # MUI/React filter re-render settle
        logger.info("Searched toolkits for %r", term)

    # ------------------------------------------------------------------
    # Card list
    # ------------------------------------------------------------------

    def count_visible_cards(self, timeout: int = 5000) -> int:
        """Return the number of toolkit cards currently visible (0 if none).

        Args:
            timeout: Maximum wait time in milliseconds for the first card
                to appear before concluding there are none.
        """
        try:
            self.entity_card.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return 0
        return self.entity_card.count()
