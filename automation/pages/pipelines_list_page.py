"""Pipelines list page object for Elitea pipeline dashboard.

Handles pipeline dashboard operations: search, view switching, navigation.

URL: /pipelines/all
"""

import logging
import re

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.pipelines_list")


class PipelinesListPage(BasePage):
    """Pipeline dashboard page (/pipelines/all).

    Handles:
    - Pipeline search
    - View switching (table/card)
    - Dashboard navigation
    - Pipeline existence checks

    URL: /pipelines/all
    """

    # LocatorDescriptors - testid + fallback pattern
    search_input = LocatorDescriptor(
        testid="pipeline-search-input",
        fallback=lambda page: page.locator('input[placeholder="Let\'s find something amazing!"]'),
        description="Pipeline search input field on dashboard"
    )

    page_header = LocatorDescriptor(
        testid="pipelines-page-header",
        fallback=lambda page: page.locator('text="Pipelines"').first,
        description="Pipelines page header text"
    )

    table_view_button = LocatorDescriptor(
        testid="pipeline-table-view",
        fallback=lambda page: page.locator('[aria-label="Table view"] button'),
        description="Switch to table view button"
    )

    card_view_button = LocatorDescriptor(
        testid="pipeline-card-view",
        fallback=lambda page: page.locator('[aria-label="Card list view"] button'),
        description="Switch to card view button"
    )

    # Shared SearchBar.jsx component testid (also used by MCP/Credentials/
    # Skills/Toolkits list pages) — same generic testid, ELITEA-2023 AFS
    # Concrete Handles.
    search_clear_button = LocatorDescriptor(
        testid="search-clear-button",
        description="Search clear (X) icon — shared SearchBar, generic testid",
    )

    # Shared Card.jsx component testid (also used by Agents/Credentials/Mcp/
    # Skills list pages — see AgentsListPage.entity_card_name for the
    # identical collection-locator pattern) — collection locator, one per
    # visible pipeline card.
    entity_card_name = LocatorDescriptor(
        testid="entity-card-name",
        description="Pipeline card name (title) — collection locator, one per visible card",
    )

    # Shared CreateEntityButton.jsx testid (also used by Agents/Toolkits/
    # Credentials/Chat list pages — see ToolkitsListPage.sidebar_create_button
    # for the identical pattern). Confirmed live (ELITEA-2020 implementer
    # Phase 2 exploration): while on the Pipelines dashboard, this control's
    # label resolves to "Pipeline" (CreateEntityButton.jsx's currentLabel via
    # RouteToLabelMap) and clicking it navigates directly to
    # /pipelines/create?viewMode=owner (no dropdown — isSimpleCreateRoute).
    sidebar_create_button = LocatorDescriptor(
        testid="sidebar-create-button",
        description="'+ Pipeline' create button in the sidebar (generic, shared across list pages)",
    )

    # -- Import (ELITEA-2012) -- ``ToolbarImportButton.jsx`` threaded with
    # ``testId="pipelines-import-button"`` at the Pipelines call site
    # (EliteaAI/EliteaUI@257cd359 on automation/testids) — the ONE new
    # testid this case's AFS calls for. Everything downstream of the click
    # reuses the SAME shared ``ImportWizardModal``/``IWModal*`` testids
    # Agent import already wires (AgentsListPage.import_* fields) — Agent/
    # Skill/Pipeline import all route through one component tree, zero
    # additional testid work needed (AFS Concrete Handles / Automation Hints).
    import_button = LocatorDescriptor(
        testid="pipelines-import-button",
        description="Import pipeline button in the Pipelines list page toolbar",
    )

    import_preview_dialog = LocatorDescriptor(
        testid="agent-import-preview-dialog",
        description="'Import parameters' preview dialog (shared Agent/Skill/Pipeline component)",
    )

    import_preview_name = LocatorDescriptor(
        testid="agent-import-preview-name",
        description="Import preview — the Main entity (Pipeline) name",
    )

    import_confirm_button = LocatorDescriptor(
        testid="agent-import-confirm-button",
        description="'Import parameters' dialog's scoped Import (confirm) button",
    )

    import_complete_dialog = LocatorDescriptor(
        testid="agent-import-complete-dialog",
        description="'Import Complete' success dialog",
    )

    import_complete_pipelines_list = LocatorDescriptor(
        testid="agent-import-complete-list-pipelines",
        description="'Import Complete' dialog — imported Pipelines name list",
    )

    import_complete_got_it_button = LocatorDescriptor(
        testid="agent-import-complete-got-it-button",
        description="'Import Complete' dialog's 'Got it' confirm/navigate button",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self):
        """Navigate to the pipelines dashboard and wait for load."""
        super().navigate("/pipelines/all")
        self.wait_for_page_load()
        logger.info("Navigated to pipelines dashboard")

    def navigate_to_create(self):
        """Navigate to the create pipeline page."""
        super().navigate("/pipelines/create?viewMode=owner")
        logger.info("Navigated to create pipeline page")

    def click_create_pipeline(self, timeout: int = 15000) -> None:
        """Click the sidebar '+' control and wait for the create form's URL.

        Mirrors ``ToolkitsListPage.click_create_toolkit()`` — same shared
        ``sidebar-create-button`` testid (ELITEA-2020 case Step 2: "Click the
        '+' button next to 'Pipeline' label in the sidebar header area").

        Args:
            timeout: Maximum wait time in milliseconds for the URL to
                reflect the create form.
        """
        self.sidebar_create_button.click()
        self.page.wait_for_url("**/pipelines/create*", timeout=timeout)
        logger.info("Clicked sidebar '+ Pipeline' — now at %s", self.page.url)

    # ------------------------------------------------------------------
    # Wait methods
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the pipelines dashboard to fully load.

        Waits for header and network to settle.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.page_header.wait_for(state="visible", timeout=timeout)
        self.wait_for_network(timeout=10000)
        logger.info("Pipelines dashboard loaded")

    def wait_for_search_results(self, timeout: int = 5000):
        """Wait for search results to update after typing query.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.wait_for_network(timeout=timeout)
        self.page.wait_for_timeout(500)  # Search debounce

    def wait_for_view_switch(self):
        """Wait for view switch animation to complete."""
        self.page.wait_for_timeout(500)  # MUI view transition

    # ------------------------------------------------------------------
    # Dashboard actions
    # ------------------------------------------------------------------

    def pipeline_exists_in_list(self, name: str, timeout: int = 5000) -> bool:
        """Check whether a pipeline with *name* is visible on the dashboard.

        Args:
            name: Pipeline name (or prefix) to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if pipeline is visible, False otherwise.
        """
        try:
            self.page.locator(f'text="{name}"').first.wait_for(
                state="visible", timeout=timeout,
            )
            return True
        except Exception:
            return False

    def get_card_names(self, timeout: int = 5000) -> list[str]:
        """Return the exact name text of every currently visible pipeline card.

        Reads each card's own ``text_content()`` off the ``entity-card-name``
        testid rather than matching a raw ``text="..."`` selector (as
        :meth:`pipeline_exists_in_list` does) — needed because an active
        search highlights the matched substring by splitting the name across
        nested ``<span>`` fragments (shared ``Card.jsx``/highlight component);
        confirmed live (ELITEA-2023 implementer Phase 2) that Playwright's
        exact ``text="..."`` locator engine does NOT match the parent
        element's concatenated text in that split-node case, even though
        ``element.textContent`` is correct — a Playwright quirk, not a DOM
        issue. Use this (with an ``in``/``==`` check) instead of
        :meth:`pipeline_exists_in_list` when the grid may be in a filtered
        (highlighted) state.

        Args:
            timeout: How long to wait for at least one card to render before
                concluding the grid is empty.

        Returns:
            List of card name strings (empty list if no cards are visible).
        """
        try:
            self.entity_card_name.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return []
        return [self.entity_card_name.nth(i).text_content() or "" for i in range(self.entity_card_name.count())]

    def search(self, query: str):
        """Type *query* into the search box and press Enter (explicit-activation
        control — typing alone does NOT filter the dashboard grid, per live
        source read of shared ``SearchBar.jsx``: ``onChange`` only updates
        local input state and opens the suggestions popover, the actual
        filter dispatch (``onSearch()`` -> redux ``setQuery``) fires only from
        ``onKeyDown === 'Enter'`` or the send-icon click. Mirrors
        ``McpListPage.search()`` / ``CredentialsListPage.search()`` — same
        shared component (ELITEA-2023 AFS § Extension target).

        Filtering here is client-side against an already-fetched pipeline
        list (no new XHR observed firing on Enter — ELITEA-2023 AFS §
        Network Behavior), so this waits for network-idle plus a short
        settle instead of a response predicate.

        Args:
            query: Text to search for.
        """
        logger.info("Searching pipelines for: %s", query)
        self.search_input.click()
        self.search_input.press_sequentially(query, delay=20)
        self.search_input.press("Enter")
        self.wait_for_network()
        self.page.wait_for_timeout(1000)  # MUI/React filter re-render settle

    def search_and_wait_for_results(self, query: str, timeout: int = 5000):
        """Type a search query and wait for results to update.

        Encapsulates search + debounce wait.

        Args:
            query: Text to search for.
            timeout: Maximum wait for results.
        """
        self.search(query)

    def clear_search(self):
        """Click the search box's Clear (X) icon and wait for the list to settle."""
        self.search_clear_button.click()
        self.wait_for_network()
        self.page.wait_for_timeout(1000)  # MUI/React filter re-render settle

    # ------------------------------------------------------------------
    # View switching
    # ------------------------------------------------------------------

    def switch_to_table_view(self):
        """Switch dashboard to table view and wait for transition."""
        logger.info("Switching to table view")
        self.table_view_button.click(force=True)  # MUI overlay may intercept
        self.wait_for_view_switch()

    def switch_to_card_view(self):
        """Switch dashboard to card view and wait for transition."""
        logger.info("Switching to card view")
        self.card_view_button.click(force=True)  # MUI overlay may intercept
        self.wait_for_view_switch()

    def is_table_view_active(self) -> bool:
        """Check if table view is currently active.

        MUI ToggleButton sets aria-pressed="true" when active.

        Returns:
            True if table view is active, False otherwise.
        """
        try:
            pressed = self.table_view_button.get_attribute("aria-pressed")
            return pressed == "true"
        except Exception:
            classes = self.table_view_button.get_attribute("class") or ""
            return "selected" in classes.lower() or "active" in classes.lower()

    def is_card_view_active(self) -> bool:
        """Check if card view is currently active.

        MUI ToggleButton sets aria-pressed="true" when active.

        Returns:
            True if card view is active, False otherwise.
        """
        try:
            pressed = self.card_view_button.get_attribute("aria-pressed")
            return pressed == "true"
        except Exception:
            classes = self.card_view_button.get_attribute("class") or ""
            return "selected" in classes.lower() or "active" in classes.lower()

    # ------------------------------------------------------------------
    # Import (ELITEA-2012)
    # ------------------------------------------------------------------

    def import_pipeline(self, file_path: str, timeout: int = 10000):
        """Import a Pipeline from an exported ``.pipeline.md`` file.

        Clicks the page-toolbar Import button (``pipelines-import-button``
        data-testid — added via ``add-data-testid``, threading
        ``ToolbarImportButton``'s existing ``testId`` prop, same mechanism
        Agents already uses for ``agents-import-button``). Clicking it opens
        a native OS file chooser directly (no intermediate menu) — mirrors
        ``AgentsListPage.import_agent()``.

        Handles the file chooser and waits for the "Import parameters"
        preview dialog (``agent-import-preview-dialog`` — shared Agent/
        Skill/Pipeline component) to render. Does NOT click the dialog's own
        Import (confirm) button — call :meth:`confirm_pipeline_import`
        separately once the preview has been verified.

        Args:
            file_path: Absolute path to the exported ``.pipeline.md`` file.
            timeout: Maximum wait time in milliseconds for the dialog.
        """
        logger.info("Importing pipeline from file: %s", file_path)
        with self.page.expect_file_chooser() as fc_info:
            self.import_button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)

        self.import_preview_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Import parameters dialog visible")

    def confirm_pipeline_import(self, timeout: int = 15000):
        """Click the "Import parameters" dialog's scoped Import (confirm) button.

        Resolved via the ``agent-import-confirm-button`` data-testid —
        distinct from the page-toolbar Import button's own
        ``pipelines-import-button`` testid, so no dialog-scoping is needed.
        Confirming transitions to the "Import Complete" success dialog
        (handled by :meth:`confirm_import_complete`), not directly to the
        new Pipeline's detail page.

        Args:
            timeout: Maximum wait time in milliseconds for the success dialog.
        """
        logger.info("Confirming pipeline import")
        self.import_confirm_button.click()
        self.import_complete_dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Import Complete dialog visible")

    def confirm_import_complete(self, timeout: int = 15000) -> int:
        """Click "Got it" on the "Import Complete" success dialog.

        Auto-navigates to the newly imported Pipeline's detail page. Parses
        and returns the new Pipeline's numeric ID from the resulting URL.

        Args:
            timeout: Maximum wait time in milliseconds for the navigation.

        Returns:
            The imported Pipeline's numeric ID.
        """
        self.import_complete_got_it_button.click()
        self.page.wait_for_url(re.compile(r".*/pipelines/all/\d+"), timeout=timeout)
        self.wait_for_network(timeout=5000)

        match = re.search(r"/pipelines/all/(\d+)", self.page.url)
        if not match:
            raise ValueError(
                f"Could not parse imported Pipeline ID from URL: {self.page.url}"
            )
        pipeline_id = int(match.group(1))
        logger.info("Import complete — navigated to pipeline id=%d", pipeline_id)
        return pipeline_id
