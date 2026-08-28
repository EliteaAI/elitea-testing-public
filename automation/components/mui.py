"""Reusable MUI component helpers for Elitea UI tests.

Provides thin wrappers around common Material-UI patterns so that
test code and page objects don't repeat the same locator logic.

Usage::

    from components.mui import Dialog, Popper

    dialog = Dialog.wait_for(page)
    Dialog.click_button(dialog, "Confirm")

    popper = Popper.wait_for(page)
    Popper.search_and_select(popper, page, "My Toolkit")
"""

import logging
from playwright.sync_api import Locator, Page

logger = logging.getLogger("elitea.components.mui")


class Dialog:
    """Helpers for MUI ``[role="dialog"]`` components.

    Covers confirmation dialogs, type-to-confirm dialogs, and
    modal dialogs used throughout the Elitea UI.
    """

    @staticmethod
    def wait_for(page: Page, timeout: int = 5000) -> Locator:
        """Wait for a dialog to become visible and return its locator.

        Args:
            page: Playwright Page instance.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator pointing to the first visible dialog.
        """
        dialog = page.locator('[role="dialog"]')
        dialog.first.wait_for(state="visible", timeout=timeout)
        return dialog.first

    @staticmethod
    def wait_for_visible(page: Page, timeout: int = 5000) -> Locator:
        """Wait for a dialog to become visible, ignoring any ``role="dialog"``
        elements that are kept mounted-but-hidden in the DOM.

        Additive sibling to :meth:`wait_for` — ``wait_for`` itself is NOT
        modified: it has other merged callers relying on its plain
        ``.first`` behavior unchanged (mui-patterns shared-caller rule).

        Some MUI ``Dialog`` consumers set ``keepMounted`` (e.g.
        ``McpAuthModal.jsx``, used by the MCP-card "Log in" flow), so an
        unrelated, permanently-hidden dialog can sort before the dialog
        actually being opened in DOM/portal order. Plain ``.first`` then
        polls the wrong (hidden) element and times out even though a
        different dialog is visible. Scoping to Playwright's ``:visible``
        pseudo-class selects only the dialog that is actually shown.
        Confirmed live for `AgentDetailPage.remove_mcp()` (ELITEA-1950):
        an unauthenticated MCP card's `McpAuthModal` stayed mounted+hidden
        and broke the plain `Dialog.wait_for()` call the "Remove MCP?"
        confirmation dialog needs.

        Args:
            page: Playwright Page instance.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator pointing to the first currently-visible dialog.
        """
        dialog = page.locator('[role="dialog"]:visible')
        dialog.first.wait_for(state="visible", timeout=timeout)
        return dialog.first

    @staticmethod
    def click_button(dialog: Locator, text: str):
        """Click a button inside a dialog by its text content.

        Supports finding buttons with multiple possible labels by
        passing a comma-separated CSS selector, e.g.
        ``Dialog.click_button(dialog, "Confirm")`` or use
        :meth:`click_first_button` for multiple candidates.

        Args:
            dialog: Locator of the dialog element.
            text: Button text to find (exact :has-text match).
        """
        dialog.locator(f'button:has-text("{text}")').click()

    @staticmethod
    def click_first_button(dialog: Locator, *texts: str):
        """Click the first matching button from a list of candidates.

        Useful when different dialog variants use different button
        labels (e.g. "Confirm" vs "Delete" vs "Remove").

        Args:
            dialog: Locator of the dialog element.
            texts: One or more button text candidates.
        """
        selector = ", ".join(f'button:has-text("{t}")' for t in texts)
        dialog.locator(selector).first.click()

    @staticmethod
    def wait_for_hidden(page: Page, timeout: int = 5000):
        """Wait for all dialogs to be hidden.

        Args:
            page: Playwright Page instance.
            timeout: Maximum wait time in milliseconds.
        """
        page.locator('[role="dialog"]').first.wait_for(
            state="hidden", timeout=timeout,
        )

    @staticmethod
    def get_title(dialog: Locator) -> str:
        """Extract the dialog title text.

        Tries multiple selectors:
        1. MUI ``#alert-dialog-title`` element
        2. Heading element inside dialog (h1-h6)
        3. First text node in dialog header

        Args:
            dialog: Locator of the dialog element.

        Returns:
            Title text, or empty string if not found.
        """
        # Try #alert-dialog-title first (older MUI pattern)
        title = dialog.locator("#alert-dialog-title")
        if title.count() > 0:
            return title.text_content().strip()

        # Try heading element (newer pattern: heading contains title + close button)
        heading = dialog.locator("h1, h2, h3, h4, h5, h6").first
        if heading.count() > 0:
            # Get first child text (skip close button)
            first_child = heading.locator("> *").first
            if first_child.count() > 0:
                return first_child.text_content().strip()
            return heading.text_content().strip()

        return ""

    @staticmethod
    def has_button(dialog: Locator, text: str) -> bool:
        """Check if a button with the given text exists in the dialog.

        Args:
            dialog: Locator of the dialog element.
            text: Button text to find (exact :has-text match).

        Returns:
            True if button is visible, False otherwise.
        """
        return dialog.locator(f'button:has-text("{text}")').is_visible()

    @staticmethod
    def type_to_confirm(dialog: Locator, confirmation_text: str):
        """Type text into a dialog's confirmation input.

        Used for type-to-confirm dialogs (e.g. "Delete agent" requires
        typing the agent name). Prefers the ``delete-confirm-name-input``
        testid (present on ``DeleteEntityModal``'s TextField) and falls
        back to a bare ``input`` locator for any dialog that doesn't carry
        that testid yet.

        Args:
            dialog: Locator of the dialog element.
            confirmation_text: Text to type into the input.
        """
        testid_wrapper = dialog.get_by_test_id("delete-confirm-name-input")
        if testid_wrapper.count() > 0:
            confirm_input = testid_wrapper.locator("input")
        else:
            confirm_input = dialog.locator("input")
        confirm_input.click()
        confirm_input.type(confirmation_text)


class Popper:
    """Helpers for MUI Popper dropdowns with search + menuitem selection.

    Used by agent toolkit search, chat participant add, and
    tool selection dropdowns.
    """

    # A MUI ``Tooltip``'s root is ALSO a ``.MuiPopper-root`` (its class list is
    # ``MuiPopper-root MuiTooltip-popper MuiTooltip-popperInteractive``) and it
    # portals to ``<body>``, so a tooltip that is already open when a dropdown
    # opens sorts *ahead* of the dropdown and ``.first`` returns the tooltip.
    # Excluding ``.MuiTooltip-popper`` is what discriminates "the dropdown I
    # just opened" from "some other popper that happens to be mounted".
    DROPDOWN_POPPER_SELECTOR = ".MuiPopper-root:not(.MuiTooltip-popper)"

    @staticmethod
    def wait_for(page: Page, timeout: int = 10000) -> Locator:
        """Wait for a MUI Popper to become visible.

        Args:
            page: Playwright Page instance.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator pointing to the first visible popper.
        """
        popper = page.locator(".MuiPopper-root").first  # Use .first to avoid strict mode violation
        popper.wait_for(state="visible", timeout=timeout)
        return popper

    @staticmethod
    def wait_for_dropdown(page: Page, timeout: int = 10000) -> Locator:
        """Wait for a MUI Popper *dropdown* to become visible, ignoring tooltips.

        Additive sibling to :meth:`wait_for` — ``wait_for`` itself is NOT
        modified: it has 9 merged callers relying on its plain ``.first``
        behavior unchanged (mui-patterns shared-caller rule, same discipline
        as :meth:`Dialog.wait_for_visible`).

        ``wait_for`` resolves ``.MuiPopper-root >> nth=0``, i.e. *the first
        popper in ``<body>`` order* — not "the popper I just opened". A MUI
        ``Tooltip`` is a ``.MuiPopper-root`` too and portals to ``<body>``, so
        a tooltip that mounted first sorts at ``nth=0`` and is returned
        instead of the dropdown. Confirmed live (EliteaAI/elitea-testing-public#1891,
        ELITEA-2037): the pipeline detail page's embedded chat panel wraps its
        model-selector button in ``<Tooltip title="Select LLM Model">``
        (``LLMModelSelector.jsx:174-182``); with that tooltip open when TOOLS
        "+ MCP" is clicked, ``wait_for`` returns the tooltip, whose
        ``is_visible()`` is legitimately ``True`` and which legitimately
        contains zero ``toolkit-search-input`` fields — producing the CI
        signature ``assert 0 > 0 ... selector='.MuiPopper-root >> nth=0'``
        while the dropdown itself is open and correct one node later.

        A ``:visible`` filter does **not** help: it preserves DOM order and the
        tooltip is visible too (measured — 2 visible poppers, tooltip still
        first). ``.last`` is rejected on principle: it only works while the
        dropdown happens to be the newest node, and nothing guarantees that.

        **Declared improvisation** (``.agents/role-overrides.md`` §
        declared-improvisation protocol; canon card
        EliteaAI/elitea-testing-public#1922). ``.MuiPopper-root:not(.MuiTooltip-popper)``
        is a structural, non-testid handle. It is used because the node that
        must be identified is **MUI's own portal root**, emitted by the
        library's ``Popper`` component rather than by app JSX
        (``UnifiedDropdown.jsx:188`` renders ``<Popper …>`` with no root-level
        testid) — the #579 *shape*, declared rather than assumed sanctioned.
        Content-scoping instead (``:has([data-testid="toolkit-search-input"])``)
        was measured equally effective and is mechanically cleaner, but it was
        rejected: the callers' specs *assert* that the popper renders
        ``toolkit-search-input``, so selecting the popper by that testid would
        make those assertions vacuous — a change to *what* is verified, which a
        declaration may never authorise. Giving ``UnifiedDropdown`` a
        caller-supplied ``popperTestId`` prop is the correct long-term fix and
        is tracked in #1922; it cannot be used here because a new testid does
        not reach ``dev.elitea.ai`` until a human promotes it to EliteaUI
        ``main`` *and* it deploys, which would leave this already-promoted test
        red on DEV.

        Args:
            page: Playwright Page instance.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator pointing to the first visible non-tooltip popper.
        """
        popper = page.locator(Popper.DROPDOWN_POPPER_SELECTOR).first
        popper.wait_for(state="visible", timeout=timeout)
        return popper

    @staticmethod
    def search(popper: Locator, query: str, page: Page, settle_ms: int = 1000):
        """Type a search query into the popper's search input.

        Args:
            popper: Locator of the popper element.
            query: Text to type into the search field.
            page: Playwright Page for timeout waits.
            settle_ms: Milliseconds to wait after typing for results.
        """
        search_input = popper.locator('input[placeholder*="Search"]')
        # press_sequentially triggers React onChange per keystroke; fill() bypasses it
        search_input.first.click()
        search_input.first.press_sequentially(query, delay=50)
        page.wait_for_timeout(settle_ms)

    @staticmethod
    def select_menuitem(
        popper: Locator, text: str, page: Page, timeout: int = 10000,
    ):
        """Select a menuitem from the popper by text.

        Args:
            popper: Locator of the popper element.
            text: Text content of the menuitem to select.
            page: Playwright Page for logging.
            timeout: Maximum wait time in milliseconds.
        """
        option = popper.locator(
            f'li[role="menuitem"]:has-text("{text}")'
        ).first
        option.wait_for(state="visible", timeout=timeout)
        logger.info("Selecting menuitem: %s", option.text_content().strip()[:60])
        option.click()

    @staticmethod
    def select_menuitem_by_testid(
        popper: Locator, text: str, page: Page, timeout: int = 10000,
    ):
        """Select a menuitem from the popper by text, scoped to the
        ``toolkit-menu-item`` testid (shared across every ``UnifiedDropdown``
        consumer — toolkits, participants, skills).

        Additive sibling to :meth:`select_menuitem` — added for
        ELITEA-1735's testid-only rework. ``select_menuitem`` itself is NOT
        modified: it has other merged callers (toolkit/participant flows)
        that rely on its raw ``li[role="menuitem"]:has-text(...)`` behavior
        unchanged (`.claude/rules/page-objects.md` § shared-caller files).
        Use this method for any new caller that can rely on the
        ``toolkit-menu-item`` testid being present.

        Args:
            popper: Locator of the popper element.
            text: Text content of the menuitem to select.
            page: Playwright Page for logging.
            timeout: Maximum wait time in milliseconds.
        """
        option = popper.locator('[data-testid="toolkit-menu-item"]').filter(
            has_text=text
        ).first
        option.wait_for(state="visible", timeout=timeout)
        logger.info(
            "Selecting menuitem (by testid): %s",
            option.text_content().strip()[:60],
        )
        option.click()

    @staticmethod
    def search_and_select(
        popper: Locator,
        page: Page,
        query: str,
        *,
        select_text: str | None = None,
        settle_ms: int = 1000,
        timeout: int = 10000,
    ):
        """Search in a popper and select the first matching menuitem.

        Combines :meth:`search` and :meth:`select_menuitem` for the
        common pattern of typing a query then clicking a result.

        Args:
            popper: Locator of the popper element.
            page: Playwright Page instance.
            query: Text to type into the search field.
            select_text: Text to match in the menuitem. Defaults to
                         *query* if not provided.
            settle_ms: Milliseconds to wait after typing.
            timeout: Maximum wait time for the menuitem.
        """
        Popper.search(popper, query, page, settle_ms=settle_ms)
        Popper.select_menuitem(
            popper, select_text or query, page, timeout=timeout,
        )

    @staticmethod
    def find_visible_search_input(page: Page, timeout: int = 10000) -> Locator:
        """Find the first visible search input on the page.

        Useful when the popper is not scoped (e.g. tool selection
        dropdowns where the popper locator isn't readily available).

        Args:
            page: Playwright Page instance.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator for the visible search input.
        """
        search_input = page.locator('input[placeholder*="Search"]')
        for i in range(search_input.count()):
            si = search_input.nth(i)
            if si.is_visible():
                return si
        # Fallback: wait and return first
        search_input.first.wait_for(state="visible", timeout=timeout)
        return search_input.first

    @staticmethod
    def select_menuitem_by_content(
        page: Page, match_fn, timeout: int = 10000,
    ) -> bool:
        """Iterate menuitems/options and click the first one matching a predicate.

        Searches both [role="menuitem"] (MUI Menu) and [role="option"]
        (MUI Select/Autocomplete) to handle different dropdown types.

        Args:
            page: Playwright Page instance.
            match_fn: Callable taking a text string, returning True to select.
            timeout: Maximum wait time (not currently used for polling).

        Returns:
            True if a menuitem/option was selected, False otherwise.
        """
        items = page.locator('[role="menuitem"], [role="option"]')
        for i in range(items.count()):
            item = items.nth(i)
            if item.is_visible() and match_fn(item.text_content() or ""):
                item.click()
                return True
        return False
