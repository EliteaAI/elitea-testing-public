"""UI test — the Settings drawer's Notifications entry is always visible without scrolling.

Read-only navigation: nothing is created, modified or deleted.

Test case: ELITEA-2260
AFS: test-specs/settings-notifications/l2_sidebar-notifications-entry-visible-without-scrolling_ELITEA-2260.md

"The sidebar" in this case is the **Settings drawer** — the case names its
PERSONAL section explicitly. The drawer is config-driven from
`SETTINGS_TABS_CONFIG` (`src/[fsd]/pages/settings/index.jsx`) and rendered by
`SettingsDrawer.jsx`.

ZERO substitution — no route mock, no injected state, no API seeding. The
geometry assertions are pure READS of what the product rendered (bounding boxes
and the menu's own scroll metrics); nothing is scrolled, forced or written.

Case-text drift — this test asserts the LIVE contract
-----------------------------------------------------
The case's step 4 expects "any unread count badge displayed next to
'Notifications'". Live (verified at 1728x861 and at the headless test viewport
1366x768), the Settings drawer renders **no badge or counter next to any item**:
`SettingsDrawer.jsx` renders `icon + label` only. The product's unread indication
is a **boolean red dot** — not a count — on the app sidebar header's bell
(`sidebar-notifications-bell-icon[data-has-messages]`, `BellIcon`'s extra
`<circle fill="#D71616">`).

This is not a product defect: nothing is broken, the case describes a control
that was never built on this surface, and the real indication exists elsewhere.
Per `.agents/role-overrides.md` § interaction-discovery ladder (step 6, read the
source — decisive) it is a case-text clarification, recorded as another
occurrence on the existing settings-drawer drift card
EliteaAI/elitea-testing-public#1772 rather than filed as a duplicate. Per the
reverse-masking guard (`.agents/testing.md`), this test asserts the live
contract: the drawer entry renders its label only, and the unread indicator is
asserted where the product actually exposes it. The bell's `"true"` state and
its popover behaviour stay ELITEA-2234's scope
(`tests/ui/onboarding/test_sidebar_notification_badge.py`) — this spec only
asserts that the indicator ATTRIBUTE exists, so the two do not duplicate.

Markers:
    - ui: requires browser
    - settings: settings pages tests (matches the sibling drawer specs)
    - p2: priority (AFS metadata l2 — case priority `medium`)
    - regression
"""

import logging

import allure
import pytest
from pages.settings_drawer_page import SettingsDrawerPage
from pages.sidebar_header_page import SidebarHeaderPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

#: A Settings sub-page that is NOT Notifications — so "visible" is not trivially
#: satisfied by the entry being the active tab (the case says "any Settings sub-page").
OTHER_SETTINGS_PATH = "/settings/profile"

NOTIFICATIONS_TAB_ID = "notifications"
PERSONAL_SECTION_ID = "personal"
PROJECT_SECTION_ID = "project"

EXPECTED_NAV_ITEM_TEXT = "Notifications"

#: The drawer's PROJECT tab ids, in `SETTINGS_TABS_CONFIG` order. Membership of the
#: PERSONAL group is asserted as "after every one of these", not by a literal count
#: (Users/Analytics/Usage are project-dependent — see
#: `test-specs/settings-navigation/_surface.md`).
PROJECT_TAB_IDS = {
    "project-general",
    "ai-providers",
    "project-context",
    "secrets",
    "users",
    "analytics",
    "usage",
    "prompts",
    "environment",
}


class TestSettingsDrawerNotificationsEntry:
    """ELITEA-2260 — Notification entry in the Settings drawer is visible without scrolling."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-notifications/ELITEA-2260_notification-entry-in-sidebar-is-always-visible-without-scrolling.md",
        "onetest-ai Test Case link",
    )
    def test_settings_drawer_notifications_entry_visible_without_scrolling(self, page):
        """On a non-Notifications Settings sub-page, the PERSONAL group's Notifications
        entry renders fully inside the drawer menu and the viewport with no scrolling
        required; it carries no unread count (the unread indication lives on the
        sidebar bell)."""
        drawer_page = SettingsDrawerPage(page)
        sidebar = SidebarHeaderPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1-2 — Logged in (auth_state) and navigated to a Settings sub-page "
            f"other than Notifications ({OTHER_SETTINGS_PATH})"
        ):
            drawer_page.navigate(OTHER_SETTINGS_PATH)
            expect(drawer_page.settings_drawer).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(drawer_page.settings_drawer_menu).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert page.title().startswith("Settings: profile"), (
                f"Expected page title to start with 'Settings: profile', got {page.title()!r}"
            )

        with allure.step(
            'Step 3a — "Notifications" is rendered in the drawer and is NOT the active tab'
        ):
            nav_item = drawer_page.nav_item(NOTIFICATIONS_TAB_ID)
            expect(nav_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(nav_item).to_have_text(EXPECTED_NAV_ITEM_TEXT)
            expect(nav_item).to_have_attribute("data-active", "false")

        with allure.step(
            'Step 3b — It belongs to the PERSONAL group: it renders after the PERSONAL '
            "section header and after every PROJECT item"
        ):
            expect(drawer_page.section_header(PROJECT_SECTION_ID)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(drawer_page.section_header(PERSONAL_SECTION_ID)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

            tab_ids = drawer_page.nav_item_ids_in_order()
            assert NOTIFICATIONS_TAB_ID in tab_ids, (
                f"Expected '{NOTIFICATIONS_TAB_ID}' among the drawer's nav items, got {tab_ids}"
            )
            notifications_index = tab_ids.index(NOTIFICATIONS_TAB_ID)
            project_indexes = [i for i, t in enumerate(tab_ids) if t in PROJECT_TAB_IDS]
            assert project_indexes, f"Expected at least one PROJECT nav item, got {tab_ids}"
            assert notifications_index > max(project_indexes), (
                f"Expected Notifications (index {notifications_index}) to render after every "
                f"PROJECT item (last at index {max(project_indexes)}) — i.e. inside the "
                f"PERSONAL group. Order: {tab_ids}"
            )

            personal_header_box = drawer_page.section_header(PERSONAL_SECTION_ID).bounding_box()
            nav_item_box = nav_item.bounding_box()
            assert personal_header_box and nav_item_box, (
                "Expected both the PERSONAL header and the Notifications entry to have a "
                "rendered bounding box"
            )
            assert nav_item_box["y"] > personal_header_box["y"], (
                f"Expected Notifications (y={nav_item_box['y']}) to render below the PERSONAL "
                f"section header (y={personal_header_box['y']})"
            )

        with allure.step("Step 3c — It is fully visible WITHOUT scrolling the drawer"):
            metrics = drawer_page.nav_item_visibility_metrics(NOTIFICATIONS_TAB_ID)
            assert metrics["item_found"], (
                "Expected the Notifications nav item inside the drawer menu container"
            )
            assert metrics["menu_scroll_top"] == 0, (
                f"Expected the drawer menu to be unscrolled, got scrollTop="
                f"{metrics['menu_scroll_top']}"
            )
            assert metrics["menu_scroll_height"] <= metrics["menu_client_height"], (
                f"Expected the drawer menu not to overflow (nothing in it can require "
                f"scrolling), got scrollHeight={metrics['menu_scroll_height']} > "
                f"clientHeight={metrics['menu_client_height']}"
            )
            assert metrics["item_inside_menu"], (
                "Expected the Notifications entry's box to lie entirely inside the drawer "
                "menu's visible box"
            )
            assert metrics["item_inside_viewport"], (
                "Expected the Notifications entry's box to lie entirely inside the viewport"
            )

        with allure.step(
            "Step 4 — Unread indication: the drawer entry carries NO count badge (live "
            "contract, clarification #1772); the product's unread indicator lives on the "
            "sidebar bell"
        ):
            nav_item_text = nav_item.inner_text().strip()
            assert nav_item_text == EXPECTED_NAV_ITEM_TEXT, (
                f"Expected the drawer's Notifications entry to render its label only "
                f"(no unread count appended), got {nav_item_text!r}"
            )

            expect(sidebar.notifications_bell_icon).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            has_messages = sidebar.notifications_bell_icon.get_attribute("data-has-messages")
            assert has_messages in {"true", "false"}, (
                f"Expected the sidebar bell to expose the product's boolean unread indicator "
                f"via data-has-messages ('true'/'false'), got {has_messages!r}. The bell's "
                f"'true' state and popover behaviour are ELITEA-2234's scope."
            )
            logger.info("Sidebar bell data-has-messages=%s", has_messages)

        with allure.step("Step 5 — No unexpected console errors were logged"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
