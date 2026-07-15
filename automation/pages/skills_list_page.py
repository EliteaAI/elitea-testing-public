"""Skills List Page - Dashboard view for browsing skills.

Handles: /skills/all
- Skills list display
- Navigate to create skill
"""

import re
import time
import logging
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from components.mui import Dialog
from utils.actions import action


logger = logging.getLogger("elitea.pages.skills_list")


class SkillsListPage(BasePage):
    """Page object for the skills list/dashboard page.

    URL: /skills/all
    """

    page_header = LocatorDescriptor(
        testid="skills-page-header",
        description="Skills page header"
    )

    import_button = LocatorDescriptor(
        testid="skills-import-button",
        description="Import skill button in the page toolbar"
    )

    import_preview_name = LocatorDescriptor(
        testid="skill-import-preview-name",
        description="Import parameters dialog — previewed skill name"
    )

    import_preview_type_version = LocatorDescriptor(
        testid="skill-import-preview-type-version",
        description="Import parameters dialog — previewed 'Type: ... | Version: ...' label"
    )

    import_preview_description = LocatorDescriptor(
        testid="skill-import-preview-description",
        description="Import parameters dialog — previewed skill description (expanded details)"
    )

    import_preview_instructions = LocatorDescriptor(
        testid="skill-import-preview-instructions",
        description="Import parameters dialog — previewed skill instructions (expanded details)"
    )

    import_success_toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide Toast component's message container"
    )

    search_input = LocatorDescriptor(
        testid="agent-search-input",
        description=(
            "Page-header search input. Shared SearchBar component "
            "(EliteaUI/src/components/SearchBar.jsx, rendered from "
            "RightPanel.jsx) — the testid literally says 'agent' even "
            "though this same instance renders on the Skills page "
            "(ELITEA-1739 AFS Concrete Handles); not a functional defect."
        )
    )

    search_send_button = LocatorDescriptor(
        testid="skills-search-send-button",
        description=(
            "Send-icon button next to the search input (StyledSendIcon, "
            "SearchBar.jsx onClick={onSearch}) — one of the two intended "
            "activation modes that trigger the grid-fetch (the other is "
            "pressing Enter in the input)."
        )
    )

    skill_card_name = LocatorDescriptor(
        testid="entity-card-name",
        description=(
            "Skill card name (title) — shared component testid (Card.jsx, "
            "renders for skills/agents/pipelines alike); collection locator, "
            "one per visible card."
        )
    )

    skill_card = LocatorDescriptor(
        testid="entity-card",
        description=(
            "Skill card outer container (Card.jsx wrapper Box) — scopes "
            "per-card queries (e.g. that card's own tag chips) without an "
            "xpath-ancestor/CSS-class hack. Shared component testid; "
            "collection locator, one per visible card."
        )
    )

    tags_panel_clear_all = LocatorDescriptor(
        testid="tags-panel-clear-all",
        description=(
            "\"Clear all\" button in the page-header Tags filter panel "
            "(Categories.jsx) — only rendered while a tag filter is active."
        )
    )

    # Dynamic (runtime-parameterized) testid template — Tags filter panel's
    # per-tag chip (Categories.jsx StyledChip). See ``filter_by_tag()``.
    TAGS_PANEL_CHIP = '[data-testid="tags-panel-chip-{}"]'

    # Scoped sub-selector — a skill card's own (non-overflow) tag chip.
    # See ``get_card_tags()``.
    CARD_TAG_CHIP = '[data-testid="entity-card-tag-chip"]'

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to skills list")
    def navigate(self):
        """Navigate to the skills dashboard and wait until ready."""
        super().navigate("/skills/all")
        self.wait_for_page_load()
        logger.info("Navigated to skills dashboard and page loaded")

    @action("Navigate to create skill")
    def navigate_to_create(self):
        """Navigate directly to the create skill page.

        Uses direct URL navigation for reliability.
        """
        super().navigate("/skills/create")
        self.wait_for_network(timeout=10000)
        logger.info("Navigated to create skill page")

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the skills list page to fully load.

        Uses a regex with $ anchor to ensure we are on /skills/all and not
        on /skills/all/{id} (the detail page URL).  Glob patterns like
        **/skills/all also match /skills/all/4, so regex is required here.
        """
        self.page.wait_for_url(
            re.compile(r".*/skills/all/?$"),
            timeout=timeout,
        )
        self.wait_for_network(timeout=5000)
        self.dismiss_banner_if_present()
        logger.info("Skills list page loaded")

    # ------------------------------------------------------------------
    # List queries
    # ------------------------------------------------------------------

    def skill_exists_in_list(self, name: str) -> bool:
        """Return True if a skill with the given name is currently visible.

        Point-in-time check — no waiting.  Uses case-insensitive match
        because the UI title-cases skill names.

        Args:
            name: Skill name to look for (case-insensitive substring).

        Returns:
            True if the skill is visible right now, False otherwise.
        """
        cards = self.skill_card_name.all()
        return any(name.lower() in (c.text_content() or "").lower() for c in cards)

    def get_visible_skill_names(self) -> list[str]:
        """Return the names of all skill cards currently visible in the grid.

        Point-in-time check — no waiting. Companion to
        :meth:`skill_exists_in_list`, used when a test needs the exact set
        of visible skills (e.g. tag-filter exclusion checks), not just a
        single name's presence.

        Returns:
            List of card name strings, in display order (as rendered — not
            lower-cased; callers doing case-insensitive comparison should
            lower-case both sides themselves).
        """
        cards = self.skill_card_name.all()
        return [(c.text_content() or "").strip() for c in cards]

    def get_card_tags(self, skill_name: str) -> list[str]:
        """Return the tag chip texts currently rendered on a specific skill's card.

        LOCATOR: each tag chip carries its own ``entity-card-tag-chip``
        testid, set on ``CardTagSectionItem``'s root element
        (``EliteaUI/src/components/CardTagSectionItem.jsx``, rendered via
        ``CardTagSection.jsx``) — distinct from the "+N" overflow badge,
        which now carries ``entity-card-tag-overflow`` instead (a boolean
        ``isOverflow`` prop drives which testid renders; ELITEA-1740
        rework). Scoped to the specific card via the ``entity-card``
        container testid on ``Card.jsx``'s outer wrapper, filtered to the
        card whose ``entity-card-name`` matches ``skill_name`` — so two
        cards can't cross-contaminate each other's tags, and the "+N"
        overflow badge / ``Like.jsx``'s like-count element (previously a
        collision risk under the shared ``.MuiTypography-bodySmall`` CSS
        class) can no longer be picked up by this query.

        Args:
            skill_name: The skill's exact name shown on its card
                (case-insensitive substring match, consistent with
                :meth:`skill_exists_in_list`).

        Returns:
            List of tag text strings currently rendered on that card, in
            display order. Empty list if the card isn't found.
        """
        card_name = self.skill_card_name.filter(
            has_text=re.compile(re.escape(skill_name), re.IGNORECASE)
        ).first
        if card_name.count() == 0:
            return []
        card = self.skill_card.filter(has=card_name).first
        tag_labels = card.locator(self.CARD_TAG_CHIP)
        return [
            (tag_labels.nth(i).text_content() or "").strip()
            for i in range(tag_labels.count())
        ]

    def wait_for_skill_absent(self, name: str, timeout: int = 10000):
        """Wait until a skill is no longer visible in the list.

        Use after deletion — waits for the list to re-fetch and remove the
        skill card.  Succeeds immediately if the skill is already absent.

        Args:
            name: Skill name (case-insensitive).
            timeout: How long to wait in ms.
        """
        deadline = time.time() + timeout / 1000
        while time.time() < deadline:
            if not self.skill_exists_in_list(name):
                return
            self.page.wait_for_timeout(500)
        raise TimeoutError(
            f"Skill '{name}' still visible in list after {timeout}ms"
        )

    # ------------------------------------------------------------------
    # Search (ELITEA-1739)
    # ------------------------------------------------------------------
    #
    # SearchBar.jsx's onChange handler deliberately only updates local
    # component state — it never fetches. The grid-fetching endpoint
    # (GET .../elitea_core/skills/prompt_lib/{project}?...&query=<text>)
    # only re-fires on one of two intended activation events: pressing
    # Enter in the input, or clicking the send-icon button. A fill-and-wait
    # alone does NOT activate the filter — this is confirmed, intended
    # product behavior (see AFS ELITEA-1739), not a workaround for a bug.

    SKILLS_GRID_ENDPOINT = "/elitea_core/skills/prompt_lib/"

    def _wait_for_grid_response(self, timeout: int):
        """Context manager waiting for the grid-fetching GET to resolve."""
        return self.page.expect_response(
            lambda r: self.SKILLS_GRID_ENDPOINT in r.url and r.request.method == "GET",
            timeout=timeout,
        )

    def _settle_after_grid_response(self):
        """Give the grid a moment to re-render after its response resolves.

        Mirrors :meth:`filter_by_tag`'s documented lag: the response
        resolving doesn't guarantee the grid has re-rendered yet (RTK
        Query → Redux store → React re-render is one more tick) — querying
        ``entity-card-name`` immediately after the response can still
        return the pre-filter card set.
        """
        self.wait_for_network(timeout=5000)
        self.page.wait_for_timeout(300)

    def _type_query(self, query: str, timeout: int):
        """Type a query into the search input via real keyboard events.

        ``StyledInputBase`` (MUI ``InputBase``) needs real keyboard events
        to trigger React's ``onChange`` — Playwright's ``.fill()`` sets the
        DOM value directly and React's controlled-input tracking doesn't
        see it as user input (``.claude/rules/mui-patterns.md`` § MUI Form
        Fields), so ``searchString`` component state never updates and the
        subsequent Enter/send-icon activation submits a stale (empty)
        query. ``press_sequentially`` fires the same keydown/input events a
        real user typing would.

        Args:
            query: Text to type.
            timeout: Maximum wait time in milliseconds for the input to be visible.
        """
        self.search_input.wait_for(state="visible", timeout=timeout)
        self.search_input.click(force=True)
        self.search_input.press_sequentially(query, delay=50)

    @action("Search skills (Enter activation)")
    def search(self, query: str, timeout: int = 10000):
        """Type the query and press Enter to activate the grid fetch.

        Args:
            query: Text to search for.
            timeout: Maximum wait time in milliseconds for the grid response.
        """
        logger.info("Searching skills for: %r (Enter activation)", query)
        self._type_query(query, timeout)
        with self._wait_for_grid_response(timeout):
            self.search_input.press("Enter")
        self._settle_after_grid_response()
        logger.info("Search activated via Enter for query: %r", query)

    @action("Search skills (send-icon activation)")
    def search_via_send_button(self, query: str, timeout: int = 10000):
        """Type the query and click the send-icon to activate the grid fetch.

        Alternate activation mode to :meth:`search` — both are intended
        entry points per ``SearchBar.jsx`` (``onKeyDown`` on Enter,
        ``onClick={onSearch}`` on the send-icon).

        Args:
            query: Text to search for.
            timeout: Maximum wait time in milliseconds for the grid response.
        """
        logger.info("Searching skills for: %r (send-icon activation)", query)
        self._type_query(query, timeout)
        with self._wait_for_grid_response(timeout):
            self.search_send_button.click()
        self._settle_after_grid_response()
        logger.info("Search activated via send-icon for query: %r", query)

    @action("Clear skills search")
    def clear_search(self, timeout: int = 10000):
        """Clear the search box, restoring the full grid.

        Bare ``.fill("")`` was unreliable during analyst exploration on
        this input (one attempt left stale characters concatenated with
        new input) — see AFS ELITEA-1739 Concrete Handles. Clears via the
        native ``HTMLInputElement`` value-setter + a bubbling ``input``
        event instead (mirrors a real backspace-to-empty).

        Confirmed live (Phase 2 exploration): this alone re-fetches the
        grid — ``SearchBar.jsx``'s ``onChange`` handler (``handleInputChange``)
        calls ``onClear()`` directly whenever the value becomes empty with
        no active tag filters, which dispatches ``resetQuery()`` and causes
        an immediate re-fetch; no Enter/send-icon press is needed or wanted
        here. (Pressing Enter afterward would instead re-run ``onSearch()``
        with an empty, sub-minimum-length string, surfacing the "at least 3
        letters" toast for no benefit — see :meth:`search_below_min_length`.)

        A re-fetch only happens if the Redux ``query`` state actually
        changes. If the field held leftover text from a query that was
        NEVER actually dispatched (e.g. a sub-minimum-length attempt via
        :meth:`search_below_min_length` — state stayed at its previous
        value the whole time), clearing is a no-op transition and no
        request fires; this is tolerated rather than treated as a failure.

        Args:
            timeout: Maximum wait time in milliseconds for the grid response.
        """
        logger.info("Clearing skills search")
        self.search_input.wait_for(state="visible", timeout=timeout)
        clear_js = (
            "el => {"
            " const setter = Object.getOwnPropertyDescriptor("
            "   window.HTMLInputElement.prototype, 'value').set;"
            " setter.call(el, '');"
            " el.dispatchEvent(new Event('input', { bubbles: true }));"
            "}"
        )
        try:
            with self._wait_for_grid_response(timeout=min(timeout, 3000)):
                self.search_input.evaluate(clear_js)
            self._settle_after_grid_response()
            logger.info("Search cleared and grid re-fetched")
        except PlaywrightTimeoutError:
            logger.info(
                "Search cleared — no grid re-fetch (query state was already "
                "empty, e.g. a prior sub-minimum-length query never activated)"
            )

    @action("Attempt skills search below minimum query length")
    def search_below_min_length(self, query: str, timeout: int = 3000):
        """Type a sub-minimum-length query and press Enter; verify no fetch.

        EliteaUI enforces a client-side minimum search length
        (``MIN_SEARCH_KEYWORD_LENGTH = 3``, ``EliteaUI/src/common/
        constants.js``) inside ``SearchBar.jsx``'s ``onSearch()`` — below
        that length it shows a "must be at least 3 letters" toast instead
        of dispatching a query, for BOTH activation modes (Enter and the
        send-icon share the same ``onSearch`` callback). Confirmed live
        during ELITEA-1739 Phase 2 exploration — a 2-character query
        (e.g. the case's literal "Co") cannot activate the grid filter;
        see AFS Known Defects — Clarification #4 (case-text drift, not a
        product bug).

        Does not raise if the grid unexpectedly DOES fire — it returns
        ``False`` so the caller can assert honestly either way, rather
        than this helper silently swallowing a product regression.

        Args:
            query: A query string shorter than the minimum (e.g. ``"Co"``).
            timeout: Grace window in milliseconds to detect an unexpected fetch.

        Returns:
            True if the grid-fetching endpoint did NOT fire (expected,
            current product behavior); False if it unexpectedly did.
        """
        logger.info("Attempting sub-minimum-length skills search: %r", query)
        self._type_query(query, timeout=10000)
        try:
            with self._wait_for_grid_response(timeout):
                self.search_input.press("Enter")
            logger.warning(
                "Grid unexpectedly re-fetched for sub-minimum-length query %r", query
            )
            return False
        except PlaywrightTimeoutError:
            logger.info(
                "Confirmed: grid did not re-fetch for sub-minimum-length query %r", query
            )
            return True

    # ------------------------------------------------------------------
    # Tag filtering
    # ------------------------------------------------------------------

    @action("Filter skills by tag")
    def filter_by_tag(self, tag_name: str, timeout: int = 10000):
        """Click a tag chip in the page-header "Tags" filter panel.

        LOCATOR: the Tags-panel chip (``StyledChip`` in
        ``EliteaUI/src/components/Categories.jsx``) carries a dynamic
        ``tags-panel-chip-{name}`` testid (ELITEA-1740 rework) via the
        :attr:`TAGS_PANEL_CHIP` template constant.

        Waits for the grid-fetching endpoint
        (``GET .../elitea_core/skills/prompt_lib/{project}?...``) to re-fire
        with the new ``tags=<id>`` query param before returning — the URL
        updates synchronously via React Router, but the grid re-render
        depends on the API round trip.

        Args:
            tag_name: Tag chip text to click (e.g. ``"formatting"``).
            timeout: Maximum wait time in milliseconds for the grid response.
        """
        logger.info("Filtering skills by tag: %r", tag_name)
        with self.page.expect_response(
            lambda r: "/elitea_core/skills/prompt_lib/" in r.url
            and r.request.method == "GET",
            timeout=timeout,
        ):
            self.page.locator(self.TAGS_PANEL_CHIP.format(tag_name)).click()
        # The response resolving doesn't guarantee the grid has re-rendered
        # yet (RTK Query → Redux store → React re-render is one more tick) —
        # confirmed live: querying entity-card-name immediately after the
        # response can still return the pre-filter card set.
        self.wait_for_network(timeout=5000)
        self.page.wait_for_timeout(300)
        logger.info("Tag filter applied: %r — URL: %s", tag_name, self.page.url)

    @action("Clear tag filter")
    def clear_tag_filter(self, timeout: int = 10000):
        """Click "Clear all" in the Tags filter panel to reset the filter.

        LOCATOR: "Clear all" (``Tooltip`` wrapping an ``IconButton`` in
        ``Categories.jsx``) carries a static ``tags-panel-clear-all`` testid
        (ELITEA-1740 rework) — it is only rendered while a tag filter is
        active.

        Waits for the grid-fetching endpoint to re-fire with the ``tags``
        param cleared before returning.

        Args:
            timeout: Maximum wait time in milliseconds for the grid response.
        """
        logger.info("Clearing tag filter")
        with self.page.expect_response(
            lambda r: "/elitea_core/skills/prompt_lib/" in r.url
            and r.request.method == "GET",
            timeout=timeout,
        ):
            self.tags_panel_clear_all.click()
        # See filter_by_tag() docstring — grid re-render lags the response.
        self.wait_for_network(timeout=5000)
        self.page.wait_for_timeout(300)
        logger.info("Tag filter cleared — URL: %s", self.page.url)

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    @action("Import skill from file")
    def import_skill(self, file_path: str, timeout: int = 10000):
        """Import a skill from an exported ``.md`` file.

        Clicks the toolbar Import button, handles the native file chooser,
        and waits for the "Import parameters" dialog to render the parsed
        skill preview.  Does NOT click the dialog's Import (confirm) button
        — call :meth:`confirm_import` separately once the preview has been
        verified.

        Args:
            file_path: Absolute path to the ``.md`` file to upload.
            timeout: Maximum wait time in milliseconds for the dialog.
        """
        logger.info("Importing skill from file: %s", file_path)
        with self.page.expect_file_chooser() as fc_info:
            self.import_button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)

        # Wait for the "Import parameters" dialog to render the parsed preview.
        dialog = Dialog.wait_for(self.page, timeout=timeout)
        dialog.get_by_text("Import parameters").wait_for(state="visible", timeout=timeout)
        logger.info("Import parameters dialog visible")

    @action("Expand import preview details")
    def expand_import_preview_details(self, timeout: int = 10000):
        """Expand the "Show details" section of the Import parameters dialog.

        The dialog's entity card (``IWModalEntityCardWrapper``) renders its
        Description/Instructions preview fields collapsed by default
        (``defaultExpanded=false``) — the container is present in the DOM
        but has zero height until "Show details" is clicked, so preview
        text is not reliably readable before this call.

        Args:
            timeout: Maximum wait time in milliseconds for the button.
        """
        dialog = self.page.get_by_role("dialog")
        show_details_button = dialog.get_by_role("button", name="Show details")
        show_details_button.wait_for(state="visible", timeout=timeout)
        show_details_button.click()
        # Grid-template-rows CSS transition (0.4s) — wait for the
        # Instructions label to actually be visible rather than a fixed sleep.
        dialog.get_by_text("Instructions:").wait_for(state="visible", timeout=timeout)

    @action("Confirm import in dialog")
    def confirm_import(self, timeout: int = 15000):
        """Click the "Import parameters" dialog's Import (confirm) button.

        Scoped to the dialog because the toolbar Import button and the
        dialog's confirm button share the same accessible name ("Import").
        """
        logger.info("Confirming import")
        dialog = self.page.get_by_role("dialog")
        dialog.get_by_role("button", name="Import").click()
        self.page.wait_for_url("**/skills/all/**", timeout=timeout)
        self.wait_for_network(timeout=5000)
        logger.info("Import confirmed — URL: %s", self.page.url)
