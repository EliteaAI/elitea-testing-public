"""Help Center page object for the Elitea Help Center surface (/help-center).

First page object for this surface — built as part of the cov60 campaign's
foundation pass (test-specs/help-center/l3_page-loads-via-sidebar-icon_ELITEA-2219.md).
Read-only, project-independent: reached via the sidebar "?" icon, shows five
fixed resource cards (Documentation, Release Notes, Video Library, Tutorials,
Interactive Tours) plus a header title/subtitle/description and a
version-info block.

URL: /help-center
"""

import logging
import re

from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.help_center")

# "Version: X.X.X (DD-Mon-YYYY)" — version/date are release-dependent, so the
# AFS asserts the PATTERN, never the literal string.
VERSION_PATTERN = re.compile(r"^Version: \d+\.\d+\.\d+ \(\d{2}-[A-Za-z]{3}-\d{4}\)$")


class HelpCenterPage(BasePage):
    """Page object for the Elitea Help Center (/help-center).

    Reached from any authenticated page via the sidebar "?" icon (next to
    Support Bot). Read-only surface — no fixtures, no cleanup, safe to run
    in parallel with other tests.

    URL: /help-center
    """

    # ------------------------------------------------------------------
    # Sidebar entry point
    # ------------------------------------------------------------------
    sidebar_help_center_button = LocatorDescriptor(
        testid="sidebar-help-center-button",
        description='Sidebar "?" Help Center icon, next to Support Bot.',
    )

    # ------------------------------------------------------------------
    # Page shell
    # ------------------------------------------------------------------
    resources_page = LocatorDescriptor(
        testid="resources-page",
        description="Help Center page root container.",
    )
    help_center_page_title = LocatorDescriptor(
        testid="help-center-page-title",
        description='Header title — "Help Center".',
    )
    help_center_subtitle = LocatorDescriptor(
        testid="help-center-subtitle",
        description='Intro subtitle — "Explore Help Center".',
    )
    help_center_description = LocatorDescriptor(
        testid="help-center-description",
        description="Intro description paragraph.",
    )
    help_center_version_info = LocatorDescriptor(
        testid="help-center-version-info",
        description='Version label — "Version: X.X.X (DD-Mon-YYYY)".',
    )
    help_center_version_info_icon = LocatorDescriptor(
        testid="help-center-version-info-icon",
        description='"i" info icon next to the version label.',
    )

    # ------------------------------------------------------------------
    # Resource cards — exactly 5 known, fixed cards (not an unbounded
    # runtime list), so each gets its own named field.
    # ------------------------------------------------------------------
    resources_documentation_card = LocatorDescriptor(
        testid="resources-documentation-card", description="Documentation resource card."
    )
    resources_release_notes_card = LocatorDescriptor(
        testid="resources-release-notes-card", description="Release Notes resource card."
    )
    resources_video_library_card = LocatorDescriptor(
        testid="resources-video-library-card", description="Video Library resource card."
    )
    resources_tutorials_card = LocatorDescriptor(
        testid="resources-tutorials-card", description="Tutorials resource card."
    )
    resources_interactive_tours_card = LocatorDescriptor(
        testid="resources-interactive-tours-card", description="Interactive Tours resource card."
    )

    # Generic, scoped-per-card sub-elements — dynamic testid template
    # constants per .agents/testing.md § Locator policy. Format with the
    # owning card's own testid string (never a free-floating page-level
    # handle for these — always scoped to a specific card).
    RESOURCE_CARD_ICON = '[data-testid="{}"] [data-testid="resource-card-icon"]'
    RESOURCE_CARD_TITLE = '[data-testid="{}"] [data-testid="resource-card-title"]'
    RESOURCE_CARD_SUBTITLE = '[data-testid="{}"] [data-testid="resource-card-subtitle"]'
    RESOURCE_CARD_LINK = '[data-testid="{}"] [data-testid="resource-card-link"]'

    CARD_TESTIDS = (
        "resources-documentation-card",
        "resources-release-notes-card",
        "resources-video-library-card",
        "resources-tutorials-card",
        "resources-interactive-tours-card",
    )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    @action("Open Help Center via sidebar icon")
    def open_via_sidebar(self, timeout: int = 15000) -> None:
        """Click the sidebar "?" icon and wait for the Help Center page shell.

        Reachable from any authenticated page — the sidebar icon and the
        page it opens are project-independent (AFS ELITEA-2219 §
        Environment Explored). Confirmed live the URL updates to
        ``/help-center`` before the resources-config fetch resolves, so
        page-shell visibility (not URL alone) is the load-complete signal.
        """
        self.sidebar_help_center_button.click()
        self.resources_page.wait_for(state="visible", timeout=timeout)

    # ------------------------------------------------------------------
    # Card content getters — scoped per card via the templated constants.
    # Playwright's ``text_content()`` re-reads live, so callers waiting on
    # a specific title (e.g. via Playwright's ``expect()``) naturally ride
    # out the MUI Skeleton placeholder shown while
    # ``plugin_config_values/prompt_lib/resources`` is in flight.
    # ------------------------------------------------------------------
    def card_title_locator(self, card_testid: str):
        """Return the title locator scoped to *card_testid*'s card."""
        return self.page.locator(self.RESOURCE_CARD_TITLE.format(card_testid))

    def card_subtitle_locator(self, card_testid: str):
        """Return the subtitle locator scoped to *card_testid*'s card."""
        return self.page.locator(self.RESOURCE_CARD_SUBTITLE.format(card_testid))

    def card_icon_locator(self, card_testid: str):
        """Return the icon locator scoped to *card_testid*'s card."""
        return self.page.locator(self.RESOURCE_CARD_ICON.format(card_testid))

    def card_link_locators(self, card_testid: str):
        """Return the (possibly multi-match) links locator scoped to *card_testid*'s card."""
        return self.page.locator(self.RESOURCE_CARD_LINK.format(card_testid))

    def get_version_info_text(self) -> str:
        """Return the version-info label's text content."""
        return self.help_center_version_info.text_content() or ""
