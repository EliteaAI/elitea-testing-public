"""Help Center page object.

Displays the resource cards (Documentation, Release Notes, Video Library,
Tutorials, Interactive Tours) and their links, some of which launch guided
Interactive Tours in a new tab.

URL: /help-center
"""

import logging
import re

from playwright.sync_api import Locator, Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.help_center")

NAVIGATION_TIMEOUT = 15_000

#: Matches the Help Center route on every target: ``APP_PREFIX`` is ``""`` on
#: localhost and ``/app`` on deployed envs, so only the trailing path is stable
#: (``routes.js:160`` returns ``''`` as the router base in DEV).
HELP_CENTER_URL_PATTERN = re.compile(r"/help-center$")


class HelpCenterPage(BasePage):
    """Page object for the Help Center page.

    URL: /help-center
    """

    page_header = LocatorDescriptor(
        testid="help-center-page-header",
        description="'Help Center' page title",
    )

    # --- Version info tooltip (ELITEA-2225, ResourceVersionInfo.jsx) ---
    version_label = LocatorDescriptor(
        testid="help-center-version-label",
        description="'Version: X.Y.Z (DD-Mon-YYYY)' label, top-right of the header",
    )
    version_info_icon = LocatorDescriptor(
        testid="help-center-version-info-icon",
        description="'i' info icon that opens the version-details tooltip on hover",
    )
    version_info_tooltip = LocatorDescriptor(
        testid="help-center-version-info-tooltip",
        description="Tooltip content panel listing each component's name/version + the copy button",
    )
    version_info_copy_button = LocatorDescriptor(
        testid="help-center-version-info-copy-button",
        description="Copies the full version info block to the clipboard",
    )

    # --- App-wide toast (Toast.jsx, src/components/Toast.jsx) — shared
    # component, testids pre-exist and need no EliteaUI change (same
    # component already used by AgentDetailPage.toast_alert/toast_message,
    # ChatPage.toast_alert/toast_message, etc. — existing repo precedent of
    # each page object declaring its own field for this shared component). ---
    toast_alert = LocatorDescriptor(
        testid="toast-alert",
        description="App-wide toast Alert root; carries data-severity (info/warning/error/success).",
    )
    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide toast message text body.",
    )

    # --- Intro block + resource-card composition (ELITEA-2219) ---
    # Testids added EliteaAI/EliteaUI@7a92fbc3 on `automation/testids`.
    intro_title = LocatorDescriptor(
        testid="help-center-intro-title",
        description="Centred intro heading below the header — 'Explore Help Center'.",
    )
    intro_description = LocatorDescriptor(
        testid="help-center-intro-description",
        description="Intro sub-line — 'Guides, documentation, and release notes to "
        "support your work.'",
    )

    # Dynamic testid templates, keyed by the card's CATEGORY — the existing
    # `testidCategory` field on every `RESOURCE_CARD_CONFIGS` entry in
    # `ResourcesPage.jsx` (documentation, release-notes, video-library,
    # tutorials, interactive-tours). Class-level per .claude/rules/page-objects.md
    # — an inline get_by_test_id(f"…") is NOT compliant.
    CARD = '[data-testid="help-center-card-{}"]'
    CARD_ICON = '[data-testid="help-center-card-{}-icon"]'
    CARD_TITLE = '[data-testid="help-center-card-{}-title"]'
    CARD_DESCRIPTION = '[data-testid="help-center-card-{}-description"]'

    #: The card-count oracle. NOTE: the bare `help-center-card-` prefix does NOT
    #: yield one element per card — it matches the root PLUS the -icon/-title/
    #: -description sub-elements, i.e. 20 nodes for 5 cards (measured live
    #: 2026-09-30; the AFS's original claim of 5 was wrong and is amended).
    #: Counting the TITLE nodes is the stable 1:1 proxy: `ResourceCard` renders
    #: exactly one title per card by construction, and unlike a root-prefix
    #: `:not()` chain this cannot be perturbed by a future extra testid inside a
    #: card. A dropped card gives 4, a sixth card gives 6; a RENAMED category is
    #: caught separately by the per-category root assertions.
    CARD_TITLE_ANY = '[data-testid^="help-center-card-"][data-testid$="-title"]'

    #: Every resource link on the page, and the links scoped INSIDE one card.
    CARD_LINK_ANY = '[data-testid^="help-center-tour-link-"]'
    CARD_LINKS = '[data-testid="help-center-card-{}"] [data-testid^="help-center-tour-link-"]'

    #: One NAMED link, scoped inside one card — so 'this card shows that link' is
    #: asserted as containment, not as page-wide presence.
    CARD_LINK = '[data-testid="help-center-card-{}"] [data-testid="help-center-tour-link-{}"]'

    # Dynamic testid template — the resource link slug is the kebab-case of
    # the backend-configured link title (no stable id field exists on the
    # link data). Naming: help-center-tour-link-{slug}.
    TOUR_LINK = '[data-testid="help-center-tour-link-{}"]'

    def navigate(self) -> None:
        """Navigate to the Help Center page and wait for it to load."""
        super().navigate("/help-center")
        self.page_header.wait_for(state="visible", timeout=15000)

    def resource_link(self, slug: str) -> Locator:
        """Return the Locator for a resource card link by its kebab-case slug.

        Args:
            slug: kebab-case slug of the link's title, e.g.
                ``"getting-started"``.

        Returns:
            Locator built from the ``TOUR_LINK`` dynamic-testid template.
        """
        return self.page.locator(self.TOUR_LINK.format(slug))

    # ------------------------------------------------------------------
    # Resource cards (ELITEA-2219)
    # ------------------------------------------------------------------

    def card(self, category: str) -> Locator:
        """Return the root Locator for a resource card by its category.

        Args:
            category: one of ``documentation``, ``release-notes``,
                ``video-library``, ``tutorials``, ``interactive-tours`` — the
                card's own ``testidCategory`` value in ``ResourcesPage.jsx``.
        """
        return self.page.locator(self.CARD.format(category))

    def card_icon(self, category: str) -> Locator:
        """The card's leading icon (an ``<svg>``; SVGR spreads the testid onto it)."""
        return self.page.locator(self.CARD_ICON.format(category))

    def card_title(self, category: str) -> Locator:
        """The card's title node.

        ``to_have_text()`` compares ``textContent``, so the expected value is the
        SOURCE casing ('Documentation'), not the uppercase the user sees — the
        card title carries CSS ``text-transform: uppercase`` from its
        ``variant="subtitle"`` typography (verified live 2026-09-30:
        ``textContent`` 'Documentation' vs ``innerText`` 'DOCUMENTATION'). The
        case text's DOCUMENTATION/RELEASE NOTES spelling is that rendered form.
        """
        return self.page.locator(self.CARD_TITLE.format(category))

    def card_description(self, category: str) -> Locator:
        """The card's subtitle/description node."""
        return self.page.locator(self.CARD_DESCRIPTION.format(category))

    def card_titles(self) -> Locator:
        """All resource-card title nodes — the 'exactly five cards' oracle.

        See :attr:`CARD_TITLE_ANY` for why titles are counted rather than roots.
        """
        return self.page.locator(self.CARD_TITLE_ANY)

    def card_links(self, category: str) -> Locator:
        """The resource links rendered INSIDE one card.

        Scoped to the card root, so 'this card shows its links' is a containment
        relationship rather than a page-wide presence check.
        """
        return self.page.locator(self.CARD_LINKS.format(category))

    def resource_links(self) -> Locator:
        """Every resource link on the page, unscoped."""
        return self.page.locator(self.CARD_LINK_ANY)

    def card_link(self, category: str, slug: str) -> Locator:
        """One named resource link, resolved as a DESCENDANT of its own card.

        Args:
            category: the card's ``testidCategory`` (e.g. ``interactive-tours``).
            slug: kebab-case slug of the link title (e.g.
                ``sidebar-interactive-tour``).
        """
        return self.page.locator(self.CARD_LINK.format(category, slug))

    @action("Wait for the backend-served resource-card links to render")
    def wait_for_resource_links_loaded(self, timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Gate on the product's own 'config resolved' signal before reading links.

        **A card title is NOT a valid gate for link content.** ``ResourceCard``
        renders ``<Skeleton>`` placeholders while ``isConfigLoading``, but the
        title falls back to a HARDCODED default
        (``configValues[config.titleKey] || config.defaultTitle``), so it paints
        immediately — measured live 2026-09-30: at the instant
        ``help-center-card-documentation-title`` became visible there were **16
        skeletons and 0 links** in the DOM. Reading link counts off that state is
        a one-shot zero, which is exactly how this would have flaked.

        The first link becoming visible is the honest signal: links exist only in
        the ``!isConfigLoading && hasLinks`` branch, so their presence IS the
        product saying the ``resources/config`` response landed. Not a sleep.
        """
        self.resource_links().first.wait_for(state="visible", timeout=timeout)

    # ------------------------------------------------------------------
    # Entry paths
    # ------------------------------------------------------------------

    @action("Open the Help Center via the sidebar Help Center control")
    def open_via_sidebar(self, timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Click the sidebar's Help Center ('?') control and wait for the page.

        The sibling of :meth:`navigate` — same destination, but through the
        control a user actually clicks instead of a URL. ``ResourcesButton``
        navigates client-side via react-router (``navigate(RouteDefinitions
        .HelpCenter)``), so there is no document load to wait on: the URL change
        plus the page header are the settle conditions.

        The caller must already be on a page OTHER than ``/help-center`` —
        ``ResourcesButton`` early-returns (``if (isOnResources) return;``) when it
        is already there, making the click a silent no-op.
        """
        self.sidebar_help_center_button.click(timeout=timeout)
        self.page.wait_for_url(HELP_CENTER_URL_PATTERN, timeout=timeout)
        self.page_header.wait_for(state="visible", timeout=timeout)

    @action("Open a resource link in a new tab")
    def open_resource_link_in_new_tab(self, slug: str, timeout: int = 10000) -> Page:
        """Click a resource link (``target="_blank"``) and return the new tab.

        Args:
            slug: kebab-case slug of the link's title, e.g.
                ``"sidebar-interactive-tour"``.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The new ``Page`` object for the opened tab.
        """
        link = self.resource_link(slug)
        link.wait_for(state="visible", timeout=timeout)

        with self.page.context.expect_page() as new_page_info:
            link.click()

        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        logger.info("Opened resource link %r in new tab: %s", slug, new_page.url)
        return new_page

    @action("Open the version info tooltip")
    def open_version_info_tooltip(self, timeout: int = 10000) -> None:
        """Hover the 'i' info icon so the version-details tooltip appears.

        MUI ``Tooltip`` mounts its content into the DOM on hover — the
        ``version_info_tooltip`` locator is not present/visible beforehand.
        """
        self.version_info_icon.hover(timeout=timeout)
        self.version_info_tooltip.wait_for(state="visible", timeout=timeout)

    @action("Copy the version info to the clipboard")
    def copy_version_info(self, timeout: int = 10000) -> str:
        """Click the tooltip's copy button and return the copied clipboard text.

        Clears the clipboard first (real OS clipboard write — permission is
        granted on the browser context, see ``conftest.py``) so waiting for a
        non-empty value afterward is a real condition, not a sleep. Waits for
        the success toast, then polls the clipboard via ``wait_for_function``
        (same pattern as ``test_agent_copy_version_link.py``) rather than a
        direct ``readText()`` call, which can hang on a permission prompt.
        """
        self.page.evaluate("() => navigator.clipboard.writeText('')")
        self.version_info_copy_button.click(timeout=timeout)
        self.toast_message.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_function(
            "async () => { const t = await navigator.clipboard.readText(); return t.length > 0; }",
            timeout=timeout,
        )
        return self.get_clipboard_text()
