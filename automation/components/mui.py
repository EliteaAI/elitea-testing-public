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

        Looks for the MUI ``#alert-dialog-title`` element.

        Args:
            dialog: Locator of the dialog element.

        Returns:
            Title text, or empty string if not found.
        """
        title = dialog.locator("#alert-dialog-title")
        if title.count() > 0:
            return title.text_content().strip()
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
        typing the agent name).

        Args:
            dialog: Locator of the dialog element.
            confirmation_text: Text to type into the input.
        """
        confirm_input = dialog.locator("input")
        confirm_input.click()
        confirm_input.type(confirmation_text)


class Popper:
    """Helpers for MUI Popper dropdowns with search + menuitem selection.

    Used by agent toolkit search, chat participant add, and
    tool selection dropdowns.
    """

    @staticmethod
    def wait_for(page: Page, timeout: int = 10000) -> Locator:
        """Wait for a MUI Popper to become visible.

        Args:
            page: Playwright Page instance.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator pointing to the first visible popper.
        """
        popper = page.locator(".MuiPopper-root")
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
