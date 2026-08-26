"""Settings drawer page object -- the shared PROJECT/PERSONAL navigation chrome
of every ``/settings/*`` route.

URL family: ``/settings/{tab_id}`` (bare ``/settings`` redirects to
``project-general``, the hardcoded default -- ``SettingsButton.jsx`` navigates
to ``project-general`` unconditionally, it never remembers the last-viewed
tab; see ``test-specs/settings-navigation/_surface.md`` § Default-tab-restore
mechanism).

Covers the surface ELITEA-2242 / ELITEA-2243 / ELITEA-2244 share: the drawer
itself (group headers, nav items, selection state) and the shared content
pane. Declared here rather than cross-imported from
:class:`pages.settings_project_general_page.SettingsProjectGeneralPage` or a
sibling profile page object, matching the convention those page objects'
module docstrings already describe (drawer fields declared locally per
surface).

Locator provenance (`test-specs/settings-navigation/_surface.md` § Testids,
verified `git fetch origin` 2026-08-26):
``settings-drawer``, ``settings-drawer-menu``, ``settings-nav-item-{tabId}``
(+ ``data-active``), ``settings-content`` -- all pre-existing on
``automation/testids`` (``EliteaAI/EliteaUI@e1e031a1``, not yet on ``main``).
``settings-section-header-{project|personal}`` -- added by this implementation
(``EliteaAI/EliteaUI@529e2e4d``) for the group-header assertions in
ELITEA-2242 step 2; no testid existed on the plain ``<Box component="span">``
group-header nodes before this case.
"""

import logging
import re

from playwright.sync_api import Locator, Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.settings_drawer")

#: Settings entry point -- ``SettingsButton.jsx`` hardcodes this default tab
#: regardless of which sub-tab was last viewed.
SETTINGS_ENTRY_PATH = "/settings/project-general"

#: App root -- the `page` fixture starts on a blank page, so every entry via
#: the sidebar button needs somewhere to click FROM.
APP_ROOT_PATH = "/"


class SettingsDrawerPage(BasePage):
    """Settings drawer (PROJECT/PERSONAL nav) plus the shared content pane."""

    settings_drawer = LocatorDescriptor(
        testid="settings-drawer",
        description="Settings left drawer root (header + PROJECT/PERSONAL menu)",
    )

    settings_drawer_menu = LocatorDescriptor(
        testid="settings-drawer-menu",
        description="Menu container inside the Settings drawer -- both the "
        "PROJECT and PERSONAL groups render inside it, in DOM order",
    )

    settings_content = LocatorDescriptor(
        testid="settings-content",
        description='Settings content pane (`<Box component="main">` hosting '
        "the routed settings page). A bare `main` selector matches TWO "
        "elements on a settings route -- the app shell's and this one -- so "
        "the testid is required, not a convenience.",
    )

    # Dynamic testid -- one per `SETTINGS_TABS_CONFIG` tab. Declared at class
    # level per `.agents/testing.md` § Locator policy (inline
    # `get_by_test_id(f"...")` is not the compliant shape). Selection state
    # lives on `data-active`, never in the testid value (PR #581).
    SETTINGS_NAV_ITEM = '[data-testid="settings-nav-item-{}"]'

    # Dynamic testid for the drawer's two group headers ("PROJECT"/"PERSONAL"),
    # added for this case -- `EliteaAI/EliteaUI@529e2e4d`. Keyed by the
    # lowercased section id, matching `SettingsDrawer.jsx`'s
    # `` `settings-section-header-${section.section.toLowerCase()}` ``.
    SETTINGS_SECTION_HEADER = '[data-testid="settings-section-header-{}"]'

    # Scoped compound selector -- every rendered nav item, scoped inside the
    # drawer menu's own testid (`settings-drawer-menu`), matched by the
    # `settings-nav-item-` testid prefix. Class-level UPPER_CASE constant per
    # `.claude/rules/page-objects.md` "Scoped selectors" -- used by
    # `nav_item_ids_in_order()` and `last_personal_nav_item()` so the compound
    # selector lives in exactly one place instead of being duplicated inline
    # in each method body.
    SETTINGS_NAV_ITEMS_IN_MENU = '[data-testid="settings-drawer-menu"] [data-testid^="settings-nav-item-"]'

    #: Accessible text of a log-out control, as rendered by the live product
    #: ("Log out", with the space). Tolerant of casing/spacing. Used only for
    #: the drift's absence assertion (see `drawer_logout_controls`).
    LOGOUT_LABEL_PATTERN = re.compile(r"^\s*log\s*out\s*$", re.IGNORECASE)

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def open_via_sidebar(self, timeout: int = 30000) -> None:
        """Navigate to the app root, click sidebar 'Settings', wait for the drawer.

        The sidebar button hardcodes the destination to `project-general`
        (see module docstring) -- this always lands on the default tab,
        regardless of which Settings sub-tab, if any, was last viewed. Starts
        from the app root since the `page` fixture begins on a blank page.
        """
        self.navigate(APP_ROOT_PATH)
        self.sidebar_settings_button.click()
        self.settings_drawer.wait_for(state="visible", timeout=timeout)
        logger.info("Opened Settings via the sidebar button")

    # ------------------------------------------------------------------
    # Drawer -- nav items and group headers
    # ------------------------------------------------------------------

    def nav_item(self, tab_id: str) -> Locator:
        """Drawer nav item for *tab_id* (e.g. ``project-general``, ``tokens``)."""
        return self.page.locator(self.SETTINGS_NAV_ITEM.format(tab_id))

    def section_header(self, section_id: str) -> Locator:
        """Drawer group header for *section_id* (``project`` or ``personal``)."""
        return self.page.locator(self.SETTINGS_SECTION_HEADER.format(section_id))

    def click_nav_item(self, tab_id: str, timeout: int = 15000) -> None:
        """Click the *tab_id* nav item and wait for its selection state.

        Waits on `data-active="true"` -- a real product signal -- rather than
        a fixed timeout (`.agents/testing.md` § no-sleeps rule).
        """
        self.nav_item(tab_id).click()
        self.page.locator(self.SETTINGS_NAV_ITEM.format(tab_id)).wait_for(state="visible", timeout=timeout)
        self.page.wait_for_function(
            """(sel) => {
                const el = document.querySelector(sel);
                return el && el.getAttribute('data-active') === 'true';
            }""",
            arg=self.SETTINGS_NAV_ITEM.format(tab_id),
            timeout=timeout,
        )
        logger.info("Clicked Settings nav item %s", tab_id)

    def drawer_logout_controls(self) -> Locator:
        """Handle for asserting that **no** 'Log out' control exists in the drawer.

        DECLARED IMPROVISATION -- canon gap, escalated to the lead
        (`.agents/role-overrides.md` § Declared-improvisation protocol), NOT
        the #579 exception. #579 sanctions a scoped raw handle only for two
        shapes -- a third-party widget subtree, or a third-party editor
        library's internal render nodes -- neither of which applies here: the
        Settings drawer is first-party EliteaUI JSX we own, so a missing
        testid there is normally "work to do", not a stop+flag case
        (`.agents/testing.md` § Locator policy: "Missing testid on the target?
        That is work to do, not a reason to rung down.").

        The reason that escape hatch doesn't close this gap: the AFS asserts
        ABSENCE of a 'Log out' drawer control that the live product never
        renders at all (case-text drift, clarification #1772,
        `EliteaAI/elitea-testing-public#1772`) -- there is no JSX node to add
        a testid to, so "add the testid" is not an available action for an
        element that does not exist. `.agents/testing.md`'s absence-assertion
        rulings (#511 extension, #277) both presuppose a testid that exists on
        an alternate/untested branch; they don't cover "the branch itself was
        never authored". Canon is silent on this exact case, hence the
        escalation rather than a citation.

        Chosen shape, and why it's the most spirit-compliant option available
        pending the lead's ruling: a text-scoped child handle chained off the
        real app testid parent (`settings_drawer`), never free-floating at
        page level -- this keeps the SAME discipline #579 requires (bounded
        blast radius, parent is a real testid) even though the exception
        itself doesn't formally apply. Do not extend this shape to any handle
        that COULD carry a testid. (Same pattern as
        `pages.settings_profile_page.SettingsProfilePage.drawer_logout_controls`
        on the sibling ELITEA-2252 case -- also flagged there, not yet
        resolved by a canon addition.)
        """
        return self.settings_drawer.get_by_text(self.LOGOUT_LABEL_PATTERN)

    def nav_item_ids_in_order(self) -> list[str]:
        """Tab ids of every rendered nav item, in DOM order.

        The PROJECT group renders before PERSONAL (`SETTINGS_TABS_CONFIG`
        order), so the first N ids are PROJECT and the rest are PERSONAL --
        callers slice by their own known-item-count rather than this method
        guessing the split.
        """
        testids: list[str] = self.page.locator(self.SETTINGS_NAV_ITEMS_IN_MENU).evaluate_all(
            "els => els.map(el => el.getAttribute('data-testid'))"
        )
        prefix = "settings-nav-item-"
        return [t[len(prefix) :] if t.startswith(prefix) else t for t in testids]

    def last_personal_nav_item(self) -> Locator:
        """The literal last `settings-nav-item-*` element rendered in the drawer menu.

        DOM-order assertion, not an assumption -- proves whichever tab is
        actually last (e.g. Notifications), rather than trusting the known
        inventory to stay in that order.
        """
        return self.page.locator(self.SETTINGS_NAV_ITEMS_IN_MENU).last
