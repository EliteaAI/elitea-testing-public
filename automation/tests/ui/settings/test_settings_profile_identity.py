"""UI test -- the Settings Profile card shows the logged-in user's avatar,
display name and email.

Read-only: nothing is created, modified or deleted, and nothing is clicked
beyond the navigation (the field values carry a copy-to-clipboard handler, and
the Log out button below them is destructive -- see `SettingsProfilePage`).

Test case: ELITEA-2373
AFS: test-specs/settings-user-profile/l3_settings_profile_avatar_name_email_ELITEA-2373.md

Case-text drift -- this test asserts the LIVE contract
--------------------------------------------------------
1. The case says "Navigate to Personalization" and read the profile area at the
   top of that page. `/settings/personalization` renders the app's global "Page
   not found" view; the avatar / name / email live on Settings -> Profile
   (`/settings/profile`).
2. The case says "the avatar **image** is shown (not a broken image icon)".
   `UserAvatar` renders an `<img>` only when the account has an avatar URL;
   otherwise it renders MUI's initials fallback. The shared test user has no
   avatar URL, so the live render is initials -- asserting `img[src]`
   unconditionally would assert the stale case text and go red on a correct
   product.

Per the reverse-masking guard this spec asserts the live contract: an avatar is
rendered and is non-empty *in whichever branch the account state produces*, and
the branch is read from the DOM (the `-image` testid's count) rather than
hardcoded -- so the day the account gains an avatar URL, the image branch is
asserted instead, with no edit here. The empty-avatar case (what `UserAvatar`
renders when the name is falsy) is the real failure mode both branches guard.
Clarification: EliteaAI/elitea-testing-public#1960.

Grounding the assertions
------------------------
The email has an oracle external to the UI -- `settings.test_user_email`, from
`.env.test`, the account the dev token authenticates as. The display name has
none (no `TEST_USER_NAME` key exists), so it is grounded by internal
consistency instead: the name is rendered twice (under the avatar and as
`Full name:`), and the avatar's initials are derived from it by the product's
own `getInitials`. All three must agree, which catches either render drifting.

No substitutions: every asserted value is produced by the running app. The one
`evaluate` call reads the browser-computed `naturalWidth` of an image the
product itself requested -- a read, not an injection (see
`SettingsProfilePage.avatar_image_is_loaded`).

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p3: low priority (per AFS metadata: l3 -- case priority `medium`)
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

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000


class TestSettingsProfileIdentity:
    """ELITEA-2373 -- Profile shows the correct avatar, display name and email."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2373_profile-section-shows-correct-user-avatar-display-name-and-email.md",
        "onetest-ai Test Case link",
    )
    def test_settings_profile_avatar_name_email(self, page):
        """Reaching Settings -> Profile through the drawer renders an avatar that
        is non-empty in whichever branch the account state produces, a display
        name that agrees with both the `Full name:` field and the avatar's
        initials, and an email equal to the logged-in account's address. No
        console errors are logged."""
        profile = SettingsProfilePage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 - Navigate to Settings -> Profile via the sidebar and the drawer"):
            profile.open_from_sidebar()
            expect(page).to_have_url(f"{settings.app_base_url}{SETTINGS_PROFILE_PATH}")
            expect(profile.profile_page).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            # Pins that the navigation actually landed, so the reads below
            # cannot come from a stale page.
            expect(profile.nav_item("profile")).to_have_attribute("data-active", "true")

        with allure.step("Step 3 - Verify the display name is rendered and internally consistent"):
            # Read before step 2 because the avatar's initials are derived from
            # this value by the product's own `getInitials`.
            expect(profile.profile_display_name).to_be_visible()
            display_name = (profile.profile_display_name.inner_text() or "").strip()
            assert display_name, "The Profile display name is empty"

            expect(profile.profile_fullname_value).to_be_visible()
            expect(profile.profile_fullname_value).to_have_text(display_name)

        with allure.step("Step 2 - Verify an avatar is rendered and is not empty or broken"):
            expect(profile.profile_avatar).to_be_visible()

            if profile.has_avatar_image():
                # Image branch: the account has an avatar URL. A broken image
                # renders with naturalWidth == 0 -- exactly the "broken image
                # icon" the case names.
                expect(profile.profile_avatar_image).to_be_visible()
                assert profile.avatar_image_is_loaded(), (
                    "The avatar <img> did not decode (naturalWidth == 0) -- a broken image"
                )
            else:
                # Initials branch (the live branch for the shared test user):
                # the avatar must still be non-empty, and its initials must be
                # the ones the product derives from the display name.
                initials = profile.avatar_initials()
                assert initials, (
                    "The avatar rendered neither an image nor initials -- an empty avatar "
                    "is what `UserAvatar` produces when the user's name is falsy"
                )
                assert initials == profile.expected_initials(display_name), (
                    f"Avatar initials {initials!r} do not match the display name "
                    f"{display_name!r} (expected {profile.expected_initials(display_name)!r})"
                )

        with allure.step("Step 4 - Verify the email matches the logged-in user's address"):
            assert settings.test_user_email, (
                "TEST_USER_EMAIL is not configured in .env.test -- this assertion has no oracle"
            )
            expect(profile.profile_email_value).to_be_visible()
            expect(profile.profile_email_value).to_have_text(settings.test_user_email)

        with allure.step("Step 5 - Verify no console errors were logged"):
            # No filter on purpose: `/settings/profile` is clean (the #1771
            # `disableUnderline` warning fires on `/settings/memory` and
            # `/settings/ai-personality`, not here). A filter would be masking.
            assert not console_errors, f"unexpected console errors: {console_errors}"
