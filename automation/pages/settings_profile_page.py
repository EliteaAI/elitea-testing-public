"""Settings -> Profile page object (the PERSONAL area of Settings).

URL: ``/settings/profile``.

Covers the surface ELITEA-2252 needs: the Settings drawer (shared chrome of
every ``/settings/*`` route) plus the Profile content pane, whose last control
is the **Log out** button.

Where the Log out control actually lives (case-text drift, clarification
EliteaAI/elitea-testing-public#1772): the TMS case describes Log out as "the
last item in the PERSONAL section of the Settings sidebar". The drawer renders
only ``SETTINGS_TABS_CONFIG`` entries and has no Log out node at all -- its
PERSONAL section ends at Notifications. The Log out control is the last control
of the Profile *page* (``Profile.jsx``), and Profile is the first PERSONAL
drawer item. This page object therefore exposes both halves: the button on the
page, and a handle for asserting its **absence** from the drawer.

Locator provenance (all added for this case,
EliteaAI/EliteaUI@e1e031a1 + EliteaAI/EliteaUI@67194ed1, on
``automation/testids``; not yet on ``main``):
``settings-drawer``, ``settings-drawer-menu``, ``settings-nav-item-{tabId}``
(+ ``data-active``) -- ``src/[fsd]/features/settings/ui/settings-drawer/SettingsDrawer.jsx``;
``settings-content`` -- ``src/[fsd]/pages/settings/index.jsx``;
``settings-profile-page``, ``settings-profile-logout-button``,
``settings-profile-logout-icon`` -- ``src/[fsd]/features/settings/ui/profile/Profile.jsx``.

Drawer fields are declared here rather than cross-imported from another page
object, matching the convention the existing settings/analytics/admin page
objects already follow (see ``SettingsProjectGeneralPage`` module docstring).

.. warning::
   **Never click** :attr:`SettingsProfilePage.logout_button` from a spec that
   is not itself about logging out. ``Profile.jsx``'s ``onLogout`` sets
   ``window.location.href`` to ``<origin>/forward-auth/logout``, which leaves
   the browser context outside the SPA -- a teardown hazard for anything that
   runs after it in the same context.
"""

import logging
import re

from playwright.sync_api import Locator, Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.settings_profile")

#: Settings entry point -- ``SettingsButton.jsx`` hardcodes this default tab.
SETTINGS_ENTRY_PATH = "/settings/project-general"

SETTINGS_PROFILE_PATH = "/settings/profile"

APP_ROOT_PATH = "/"


class SettingsProfilePage(BasePage):
    """Settings -> Profile page plus the shared Settings drawer."""

    settings_drawer = LocatorDescriptor(
        testid="settings-drawer",
        description="Settings left drawer root (header + PROJECT/PERSONAL menu)",
    )

    settings_drawer_menu = LocatorDescriptor(
        testid="settings-drawer-menu",
        description="Scrollable menu container inside the Settings drawer -- "
        "the element that carries `overflow: auto`, and therefore the one "
        "whose scroll geometry answers 'does the drawer need scrolling?'",
    )

    settings_content = LocatorDescriptor(
        testid="settings-content",
        description="Settings content pane (`<Box component=\"main\">` hosting "
        "the routed settings page). A bare `main` selector matches TWO elements "
        "on a settings route -- the app shell's and this one -- so the testid "
        "is required, not a convenience.",
    )

    profile_page = LocatorDescriptor(
        testid="settings-profile-page",
        description="Profile page root inside the settings content pane",
    )

    logout_button = LocatorDescriptor(
        testid="settings-profile-logout-button",
        description="'Log out' button -- the last control of the Profile card. "
        "DO NOT CLICK from a spec that is not about logging out (see module "
        "docstring).",
    )

    profile_avatar = LocatorDescriptor(
        testid="settings-profile-avatar",
        description="Avatar element of the Profile card. `UserAvatar` applies the "
        "caller-supplied `testId` in BOTH of its branches -- the `<img>` avatar and "
        "the MUI initials fallback -- so this handle resolves whatever the account "
        "state is.",
    )

    profile_avatar_image = LocatorDescriptor(
        testid="settings-profile-avatar-image",
        description="The `<img>` inside the avatar, present ONLY when the account "
        "has an avatar URL. `UserAvatar` derives this testid from its `testId` prop "
        "via MUI's `imgProps` slot, so its count is the branch discriminator: 1 = a "
        "real image avatar, 0 = the initials fallback.",
    )

    profile_display_name = LocatorDescriptor(
        testid="settings-profile-display-name",
        description="Display name rendered next to the avatar. The same name is "
        "ALSO rendered as the `Full name:` field value, so a text-based locator "
        "would match both -- the testid is required, not a convenience.",
    )

    profile_fullname_value = LocatorDescriptor(
        testid="settings-profile-fullname-value",
        description="Value of the `Full name:` field. Named at the Profile call "
        "site through `FieldWithCopy`'s caller-supplied `testId` prop (the "
        "component is reused by AI Providers, so it hardcodes no feature-scoped "
        "testid). DO NOT CLICK -- the value carries a copy handler + toast.",
    )

    profile_email_value = LocatorDescriptor(
        testid="settings-profile-email-value",
        description="Value of the `Email:` field, named the same way as "
        "`profile_fullname_value`. DO NOT CLICK -- copy handler + toast.",
    )

    logout_button_icon = LocatorDescriptor(
        testid="settings-profile-logout-icon",
        description="Inline SVG rendered by `LogoutIcon` in the button's MUI "
        "`startIcon` slot. svgr (vite-plugin-svgr) spreads props onto the "
        "generated `<svg>` root, so the call site names it directly -- no "
        "wrapper node was added.",
    )

    # Dynamic testid -- one per `SETTINGS_TABS_CONFIG` tab. Declared at class
    # level per `.agents/testing.md` § Locator policy (inline
    # `get_by_test_id(f"...")` is not the compliant shape).
    SETTINGS_NAV_ITEM = '[data-testid="settings-nav-item-{}"]'

    #: Accessible text of a log-out control, as rendered by the live product
    #: ("Log out", with the space). Tolerant of casing/spacing so the absence
    #: assertion below cannot be defeated by a cosmetic relabel.
    LOGOUT_LABEL_PATTERN = re.compile(r"^\s*log\s*out\s*$", re.IGNORECASE)

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def open_from_sidebar(self, timeout: int = 30000) -> None:
        """Reach Settings -> Profile the way a user does.

        App root -> sidebar 'Settings' -> the drawer's 'Profile' item. Going
        through the drawer is deliberate: it is what makes "Profile is an item
        of the PERSONAL section" an observed fact rather than an assumption.
        """
        self.navigate(APP_ROOT_PATH)
        self.sidebar_settings_button.click()
        self.settings_drawer.wait_for(state="visible", timeout=timeout)
        self.nav_item("profile").click()
        self.profile_page.wait_for(state="visible", timeout=timeout)
        logger.info("Opened Settings -> Profile via the sidebar")

    # ------------------------------------------------------------------
    # Drawer
    # ------------------------------------------------------------------

    def nav_item(self, tab_id: str) -> Locator:
        """Drawer nav item for *tab_id* (e.g. ``profile``, ``notifications``).

        Selection state is on the element's ``data-active`` attribute, never in
        the testid value (`.agents/testing.md` § Locator policy, PR #581).
        """
        return self.page.locator(self.SETTINGS_NAV_ITEM.format(tab_id))

    def drawer_logout_controls(self) -> Locator:
        """Handle for asserting that **no** 'Log out' control exists in the drawer.

        Scoped raw handle, sanctioned exception (`.agents/testing.md`
        § Locator policy, #579 discipline): an absence assertion cannot be
        keyed on a testid for a thing that does not exist, so a text-scoped
        child handle is the only shape available. The discipline is honoured --
        the parent is the real app testid ``settings-drawer`` and the raw
        handle is chained off it, never free-floating at page level. Do not
        extend this shape to any handle that COULD carry a testid.

        Returns a locator that is expected to have count 0; if the UI team ever
        moves Log out into the drawer, this goes red and clarification #1772
        gets revisited instead of the drift silently reversing.
        """
        return self.settings_drawer.get_by_text(self.LOGOUT_LABEL_PATTERN)

    # ------------------------------------------------------------------
    # Layout measurement
    # ------------------------------------------------------------------

    @staticmethod
    def is_scrollable(container: Locator) -> bool:
        """Whether *container* has overflowing content the user must scroll to.

        Read-only measurement, NOT a substitution (`.agents/testing.md`
        § Fidelity policy): ``scrollHeight``/``clientHeight`` are computed by
        the browser's layout engine from the product's own DOM. Nothing is
        injected, forced, or fabricated -- this reads a value the system
        produced, exactly like reading rendered text. Playwright exposes no
        native accessor for scroll geometry, so ``evaluate`` is the only route.
        """
        return bool(container.evaluate("el => el.scrollHeight > el.clientHeight"))
    # ------------------------------------------------------------------
    # Profile identity
    # ------------------------------------------------------------------

    def open_profile_tab(self, timeout: int = 30000) -> None:
        """Open Settings -> Profile from a settings route that is already open."""
        self.nav_item("profile").click()
        self.profile_page.wait_for(state="visible", timeout=timeout)
        logger.info("Opened Settings -> Profile via the drawer")

    def has_avatar_image(self) -> bool:
        """Whether the avatar rendered its `<img>` branch rather than initials.

        Read of the live DOM, not an assumption about the account: the shared
        test user has no avatar URL today, but that can change without the
        product being wrong (see the ELITEA-2373 spec docstring).
        """
        return self.profile_avatar_image.count() > 0

    def avatar_image_is_loaded(self) -> bool:
        """Whether the avatar `<img>` actually decoded (not a broken-image icon).

        Read-only measurement, NOT a substitution (`.agents/testing.md`
        § Fidelity policy): `naturalWidth` is computed by the browser from the
        image the product itself requested. Playwright exposes no native
        accessor for it, so `evaluate` is the only route -- the same rationale
        as :meth:`is_scrollable`.
        """
        return bool(self.profile_avatar_image.evaluate("img => img.naturalWidth > 0"))

    def avatar_initials(self) -> str:
        """Text rendered by the avatar's initials fallback."""
        return (self.profile_avatar.inner_text() or "").strip()

    @staticmethod
    def expected_initials(name: str) -> str:
        """Initials the product derives from *name* (`getInitials`, `common/utils.jsx`).

        First character of the first word + first character of the last word,
        upper-cased; a single-word name yields one character.
        """
        parts = name.split(" ")
        first = parts[0]
        last = parts[-1] if len(parts) > 1 else ""
        return f"{first[:1]}{last[:1]}".upper()
