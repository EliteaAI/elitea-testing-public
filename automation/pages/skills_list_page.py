"""Skills List Page - Dashboard view for browsing skills.

Handles: /skills/all
- Skills list display
- Navigate to create skill
"""

import re
import time
import logging
from playwright.sync_api import Page

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
        cards = self.page.get_by_test_id("entity-card-name").all()
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
        cards = self.page.get_by_test_id("entity-card-name").all()
        return [(c.text_content() or "").strip() for c in cards]

    def get_card_tags(self, skill_name: str) -> list[str]:
        """Return the tag chip texts currently rendered on a specific skill's card.

        LOCATOR: tag text (``CardTagSectionItem`` in ``EliteaUI/src/
        components/CardTagSectionItem.jsx``, rendered via
        ``CardTagSection.jsx``) has no ``data-testid`` — confirmed live via
        DOM inspection that it renders as a ``Typography variant="bodySmall"``
        (MUI class ``MuiTypography-bodySmall``), which is not shared with any
        other element inside the card (mirrors the existing
        ``.MuiChip-label`` pattern already used in
        :meth:`SkillFormPage.get_tags`). Scoped to the specific card via the
        nearest ``MuiCard-root`` ancestor of that card's ``entity-card-name``
        element, so two cards can't cross-contaminate each other's tags.

        Args:
            skill_name: The skill's exact name shown on its card
                (case-insensitive substring match, consistent with
                :meth:`skill_exists_in_list`).

        Returns:
            List of tag text strings currently rendered on that card, in
            display order. Empty list if the card isn't found.
        """
        card_name = self.page.get_by_test_id("entity-card-name").filter(
            has_text=re.compile(re.escape(skill_name), re.IGNORECASE)
        ).first
        if card_name.count() == 0:
            return []
        card = card_name.locator(
            "xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), "
            "' MuiCard-root ')]"
        ).first
        tag_labels = card.locator(".MuiTypography-bodySmall")
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
    # Tag filtering
    # ------------------------------------------------------------------

    @action("Filter skills by tag")
    def filter_by_tag(self, tag_name: str, timeout: int = 10000):
        """Click a tag chip in the page-header "Tags" filter panel.

        LOCATOR: the Tags-panel chip (``StyledChip`` in
        ``EliteaUI/src/components/Categories.jsx``) has no ``data-testid`` —
        located by accessible role/name (confirmed live in the ELITEA-1740
        AFS exploration); tag names are unique per project, so this is
        unambiguous without extra scoping.

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
            self.page.get_by_role("button", name=tag_name, exact=True).click()
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
        ``Categories.jsx``) has no ``data-testid`` — it is only rendered
        while a tag filter is active, so it's unambiguous in context.

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
            self.page.get_by_role("button", name="Clear all").click()
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
