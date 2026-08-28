"""UI test -- the SOUND NOTIFICATIONS controls are interactive: the
'Play sound when tasks complete' toggle turns the section's volume slider and
'Preview Sound' button on and off, the slider carries its documented range and
responds to a drag, and the user's volume survives an OFF/ON cycle.

Test case: ELITEA-2386
AFS: test-specs/settings-user-profile/
l3_sound-notifications-toggle-and-volume-interactive_ELITEA-2386.md

Read-only with respect to the account: this section's state lives in
`localStorage` (`elitea_ui.sound_notifications`), not on the `${TEST_USER}`
record, and a pytest browser context is fresh per run -- so nothing is seeded,
nothing is restored, and no other spec reads what this one writes. The toggle is
still read BEFORE it is written (the context restores whatever it restores), so
the test asserts the ON->OFF->ON transition rather than a hardcoded start state.

Case-text drift -- this test asserts the LIVE contract
--------------------------------------------------------
Both rows are case-text stale / product correct (reverse-masking guard), filed
as clarification EliteaAI/elitea-testing-public#1967, not as defects:

* "Navigate to Personalization -> SOUND NOTIFICATIONS" -- there is no
  `/settings/personalization` route; the section lives on
  `/settings/preferences`.
* step 5's "the Volume slider is disabled or hidden" -- the product UNMOUNTS it.
  `SoundNotificationControls.jsx` guards both the slider and the Preview Sound
  button with `{config.enabled && ...}`, so nothing is ever
  rendered-but-disabled. The case's "or hidden" branch is what happens, and it
  is asserted as `to_have_count(0)` -- never `to_be_disabled()`, which would
  pass vacuously on an element that no longer exists.

Two different hide mechanisms live on this one page and the wrong one is a
silent false pass: a collapsed ACCORDION keeps its children mounted and hides
them with `visibility: hidden` (`not_to_be_visible()`), while this TOGGLE
conditionally unmounts them (`to_have_count(0)`).

No substitutions: every asserted value is produced by the running app.

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
from pages.settings_personalization_page import (
    PREFERENCES_PATH,
    SettingsPersonalizationPage,
)
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

TOGGLE_LABEL_TEXT = "Play sound when tasks complete"
VOLUME_MARK_LABELS = ["0%", "50%", "100%"]

#: Beyond the case (step 8): the drag goes to 0% first and only then to 50%, so
#: the assertion is falsifiable whatever value the slider starts on -- a slider
#: that already sat at 50% would make a single drag-to-50% prove nothing.
DRAG_FRACTIONS_AND_VALUES = [(0.0, "0"), (0.5, "0.5")]


class TestSoundNotificationsControls:
    """ELITEA-2386 -- the Sound Notifications toggle and volume slider respond."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/user-profile/ELITEA-2386_sound-notifications-toggle-and-volume-slider-are-interactive.md",
        "onetest-ai Test Case link",
    )
    def test_sound_notifications_toggle_and_volume_are_interactive(self, page):
        """Turning 'Play sound when tasks complete' off unmounts the volume
        slider and the Preview Sound button; turning it back on restores both
        with the user's volume intact, the slider exposes its documented range
        and lands exactly where it is dragged, and Preview Sound is clickable."""
        personalization = SettingsPersonalizationPage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 - Open Settings -> Preferences and find SOUND NOTIFICATIONS"):
            personalization.open_settings_tab("preferences")
            expect(page).to_have_url(f"{settings.app_base_url}{PREFERENCES_PATH}")
            expect(personalization.nav_item("preferences")).to_have_attribute("data-active", "true")
            expect(personalization.sound_notifications_section).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            # A collapsed accordion keeps its children mounted, so the unmount
            # assertions below would be indistinguishable from a collapse
            # without pinning the section open first.
            expect(personalization.sound_notifications_header).to_have_attribute(
                "aria-expanded", "true"
            )
            expect(personalization.sound_notifications_content).to_be_visible()

            # Read-before-write: the case's steps 4-6 assume the ON state, but
            # the starting state is whatever the browser context restores.
            if not personalization.is_sound_notifications_enabled():
                logger.info("Toggle started OFF - turning it on to reach the case's start state")
                personalization.sound_notifications_toggle.click()
            expect(personalization.sound_notifications_toggle_input).to_be_checked()

        with allure.step(f"Step 2 - The '{TOGGLE_LABEL_TEXT}' toggle is present"):
            expect(personalization.sound_notifications_toggle).to_be_visible()
            expect(personalization.sound_notifications_toggle_input).to_be_enabled()
            expect(personalization.sound_notifications_toggle_input).to_be_checked()
            # The toggle's own label, not the section heading ("Sound Notifications").
            expect(personalization.sound_notifications_content).to_contain_text(TOGGLE_LABEL_TEXT)

        with allure.step("Step 3 - The Volume slider is present with range 0% to 100%"):
            expect(personalization.sound_volume_slider_input).to_have_attribute("min", "0")
            expect(personalization.sound_volume_slider_input).to_have_attribute("max", "1")
            expect(personalization.sound_volume_slider_input).to_have_attribute("step", "0.05")
            for label in VOLUME_MARK_LABELS:
                expect(personalization.sound_volume_slider).to_contain_text(label)

            volume_before_toggle_off = personalization.sound_volume_slider_input.input_value()
            logger.info("Volume before the OFF/ON cycle: %s", volume_before_toggle_off)

        with allure.step(f"Step 4 - Toggle '{TOGGLE_LABEL_TEXT}' OFF"):
            personalization.sound_notifications_toggle.click()
            expect(personalization.sound_notifications_toggle_input).not_to_be_checked()

        with allure.step("Step 5 - The Volume slider is gone (the product unmounts it)"):
            expect(personalization.sound_volume_slider).to_have_count(0)
            # Beyond the case: the SAME `config.enabled &&` guard controls the
            # Preview Sound button. A build that hid the slider but left a live
            # Preview Sound button is a real regression the case's wording misses.
            expect(personalization.sound_preview_button).to_have_count(0)
            # ...and the section itself did NOT collapse - only its conditional
            # children unmounted (the two hide mechanisms look alike on screen).
            expect(personalization.sound_notifications_content).to_be_visible()
            expect(personalization.sound_notifications_content).to_contain_text(TOGGLE_LABEL_TEXT)

        with allure.step("Step 6 - Toggle back ON: the Volume slider is back and usable"):
            personalization.sound_notifications_toggle.click()
            expect(personalization.sound_notifications_toggle_input).to_be_checked()
            expect(personalization.sound_volume_slider).to_have_count(1)
            expect(personalization.sound_volume_slider).to_be_visible()
            expect(personalization.sound_volume_slider_input).to_be_enabled()
            # Beyond the case: an unmount/remount that resets the user's volume
            # is a classic conditional-render bug the case's "re-enabled" wording
            # does not pin.
            expect(personalization.sound_volume_slider_input).to_have_value(
                volume_before_toggle_off
            )

        with allure.step("Step 7 - 'Preview Sound' is clickable"):
            # Deliberately NOT clicked: `playCompletionSound()` plays audio, and
            # "clickable" is fully established by visible + enabled.
            expect(personalization.sound_preview_button).to_be_visible()
            expect(personalization.sound_preview_button).to_be_enabled()

        with allure.step("Step 8 - Beyond the case: the Volume slider really moves"):
            # The case TITLE claims the slider is interactive but no case step
            # ever moves it - presence alone would let a frozen slider pass.
            for fraction, expected_value in DRAG_FRACTIONS_AND_VALUES:
                personalization.drag_slider_to(
                    personalization.sound_volume_slider,
                    personalization.sound_volume_slider_thumb,
                    fraction,
                )
                expect(personalization.sound_volume_slider_input).to_have_value(expected_value)
                # `input.value` is DOM-normalised, so only `aria-valuenow` would
                # expose the drag path regressing into the keyboard path's
                # floating-point arithmetic (defect #1966).
                expect(personalization.sound_volume_slider_input).to_have_attribute(
                    "aria-valuenow", expected_value
                )

        with allure.step("Step 9 - No console errors were logged"):
            # `/settings/preferences` logs none (verified live). The known #1771
            # `disableUnderline` warning belongs to other routes -- filtering it
            # HERE would be masking.
            assert not console_errors, f"unexpected console errors: {console_errors}"
