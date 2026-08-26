"""UI test -- the Log out control of the PERSONAL area of Settings is present,
labelled, iconed and reachable without scrolling or expanding.

Read-only verification against the logged-in user's own identity
(`.agents/testing.md` § Test data strategy). Nothing is created, modified or
deleted, and -- deliberately -- nothing is clicked after the navigation: see
"Why this test never clicks Log out" below.

Test case: ELITEA-2252
AFS: test-specs/settings-user-profile/l2_settings_profile_logout_button_visible_ELITEA-2252.md

Case-text drift -- this test asserts the LIVE contract
--------------------------------------------------------
The TMS case says Log out is "the last item in the PERSONAL section of the
Settings sidebar". The live product does not render it there and never did on
`automation/testids`: `SettingsDrawer.jsx` renders only `SETTINGS_TABS_CONFIG`
entries, and the drawer's PERSONAL section ends at Notifications. The Log out
control lives in the *content pane* of Settings -> Profile, as the last control
of the Profile card (`Profile.jsx`). Profile IS the first PERSONAL item, so the
case's intent -- "log out is reachable in the PERSONAL area of Settings,
visible without scrolling or expanding" -- is satisfiable; only its stated
location is wrong.

Per the reverse-masking guard, this spec asserts the live contract and does NOT
assert the stale case text. The clarification is already tracked as
EliteaAI/elitea-testing-public#1772 (row 4, "There is no Log out item anywhere
in the Settings drawer"); this case's occurrence was commented there rather
than filed again. Step 2 also asserts the *absence* half, so the drift is a
test-enforced invariant rather than a comment: if the UI team ever moves Log
out into the drawer, this spec goes red and the case text gets revisited.

Why this test never clicks Log out
----------------------------------
`Profile.jsx`'s `onLogout` sets `window.location.href` to
`<origin>/forward-auth/logout`, taking the browser out of the SPA and leaving
the context on the app's "Page not found" view -- a teardown hazard for
whatever runs next in the same context. The click is ELITEA-2253's subject, and
that case is `blocked` (its observable cannot be produced on localhost). This
spec is presence-only by design, which is exactly what the case asks for.

No substitutions: every asserted value is produced by the running app. The one
`evaluate` call reads browser-computed scroll geometry (`scrollHeight` /
`clientHeight`) off the product's own DOM -- a read, not an injection; see
`SettingsProfilePage.is_scrollable`.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p2: medium priority (per AFS metadata: l2 -- case priority `medium`)
    - regression
"""

import logging

import allure
import pytest
from config import settings
from pages.settings_profile_page import SETTINGS_PROFILE_PATH, SettingsProfilePage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

#: The live label, with the space. `UserButton.jsx` (dead code) uses "Logout"
#: without one -- pinning the live string keeps a future copy-paste from
#: silently changing the user-facing label.
LOGOUT_LABEL = "Log out"

#: Live last item of the drawer's PERSONAL section (`SETTINGS_TABS_CONFIG`).
LAST_PERSONAL_TAB_ID = "notifications"


class TestSettingsProfileLogoutButtonVisible:
    """ELITEA-2252 -- Log out is visible in the PERSONAL area of Settings."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2252_settings-profile-logout-button-visible.md",
        "onetest-ai Test Case link",
    )
    def test_settings_profile_logout_button_visible(self, page):
        """Reaching Settings -> Profile through the sidebar and the drawer's
        PERSONAL section renders a Log out button that is labelled `Log out`,
        enabled, carries its log-out icon, and sits inside the viewport with
        neither the drawer menu nor the content pane needing to scroll -- while
        the drawer itself contains no Log out control at all (the #1772 drift,
        asserted as an invariant). No console errors are logged."""
        profile = SettingsProfilePage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 - Navigate to Settings -> Profile via the sidebar and the drawer"):
            profile.open_from_sidebar()
            expect(page).to_have_url(f"{settings.app_base_url}{SETTINGS_PROFILE_PATH}")
            expect(profile.profile_page).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 2 - Verify the drawer's PERSONAL section: Profile is the active item, "
            "Notifications is its last item, and NO Log out control exists in the drawer"
        ):
            profile_nav_item = profile.nav_item("profile")
            expect(profile_nav_item).to_be_visible()
            # Selection state lives on `data-active`, never in the testid value
            # -- so this also proves the assertions below are being made on the
            # Profile page reached THROUGH the drawer.
            expect(profile_nav_item).to_have_attribute("data-active", "true")
            expect(profile.nav_item(LAST_PERSONAL_TAB_ID)).to_be_visible()

            # The drift assertion (see module docstring / clarification #1772).
            expect(profile.drawer_logout_controls()).to_have_count(0)

            assert not profile.is_scrollable(profile.settings_drawer_menu), (
                "The Settings drawer menu is scrollable -- the PERSONAL section is no "
                "longer reachable without additional scrolling (case step 5)"
            )

        with allure.step("Step 3 - Verify the Log out button is present, labelled and enabled"):
            expect(profile.logout_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(profile.logout_button).to_have_text(LOGOUT_LABEL)
            expect(profile.logout_button).to_be_enabled()

        with allure.step("Step 4 - Verify it carries a recognizable log-out icon"):
            # Presence + visibility of the icon element only. Asserting the SVG
            # path data or the asset filename would pin implementation, not
            # behaviour.
            expect(profile.logout_button_icon).to_have_count(1)
            expect(profile.logout_button_icon).to_be_visible()

        with allure.step(
            "Step 5 - Verify it is visible without any additional scrolling or expanding"
        ):
            # No interaction has happened since the navigation in step 1 -- no
            # scroll, no accordion, no expand -- so an in-viewport button here
            # IS "visible without additional scrolling or expanding".
            expect(profile.logout_button).to_be_in_viewport()
            assert not profile.is_scrollable(profile.settings_content), (
                "The Settings content pane is scrollable -- the Log out button is no "
                "longer reachable without additional scrolling (case step 5)"
            )

        with allure.step("Step 6 - Verify no unexpected console errors were logged"):
            # No filter is applied on purpose: this path visits neither AI
            # Personality (#1771) nor Secrets (#1203), and both loads observed
            # live were clean. A filter here would be masking, not noise
            # handling (`.agents/testing.md` § Known issues).
            assert not console_errors, f"unexpected console errors: {console_errors}"
