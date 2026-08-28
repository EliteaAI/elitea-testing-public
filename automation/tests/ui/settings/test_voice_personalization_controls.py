"""UI test -- the VOICE PERSONALIZATION controls are interactive: the Voice
dropdown opens and changes selection, both sliders carry their documented range
and land exactly on a dragged value, and 'Preview Voice' is clickable.

Test case: ELITEA-2385
AFS: test-specs/settings-user-profile/
l3_voice-personalization-controls-interactive_ELITEA-2385.md

Read-only with respect to the account: this section's state lives in
`localStorage` (`elitea_voice_config`), not on the `${TEST_USER}` record, and a
pytest browser context is fresh per run -- so nothing is seeded, nothing is
restored, and no other spec reads what this one writes.

Case-text drift -- this test asserts the LIVE contract
--------------------------------------------------------
Both rows are case-text stale / product correct (reverse-masking guard), filed
as clarification EliteaAI/elitea-testing-public#1967, not as defects:

* "Navigate to Personalization -> VOICE PERSONALIZATION" -- there is no
  `/settings/personalization` route (it renders the app's global "Page not
  found"). The section lives on `/settings/preferences`.
* step 7's "range Mute to 100%" -- the volume slider's marks are `0% / 50% /
  100%`; the word "Mute" appears nowhere on the control
  (`VOICE_VOLUME_MARKS` in `voice.constants.js`). This test asserts `0%`.

Sanctioned RED -- defect #1965
------------------------------
On a fresh browser profile the Voice dropdown renders BLANK: the effect that
should default the selection to `alloy` bails on
`config?.voiceId !== undefined` while `useVoiceConfig`'s `DEFAULT_CONFIG.voiceId`
is `null`. Case step 2 says the dropdown "shows a selected option", which is the
correct expectation -- so it is asserted as such, softly, with the defect
linked. This spec is therefore expected to fail on exactly one soft assertion
until #1965 ships (`.agents/testing.md` § Merge gate, sanctioned-RED).

Defect #1966 (arrow keys accumulate floating-point error on both sliders) is NOT
asserted here: the case's interaction is a DRAG, the drag path is clean, and
pinning a keyboard artifact the case never exercises would add a second
permanent red for behaviour outside the case.

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

#: Voice picked by case step 4. Any option other than the current one works; the
#: list is backend-supplied (model TTS), so the spec asserts this row exists
#: rather than asserting the whole list.
TARGET_VOICE_VALUE = "nova"
TARGET_VOICE_LABEL = "Nova"

#: Case step 6 -- Speed slider range is 0.5..2.0, so 1.5x sits at 2/3 of the track.
#: The DOM strings are asserted verbatim (`max` renders as "2", not "2.0").
SPEED_MIN, SPEED_MAX, SPEED_TARGET = 0.5, 2.0, 1.5
SPEED_FRACTION = (SPEED_TARGET - SPEED_MIN) / (SPEED_MAX - SPEED_MIN)
SPEED_MIN_ATTR, SPEED_MAX_ATTR, SPEED_STEP_ATTR = "0.5", "2", "0.1"

#: Case step 8 -- Volume slider range is 0..1, so 50% sits at half the track.
VOLUME_TARGET = 0.5
VOLUME_FRACTION = 0.5

SPEED_MARK_LABELS = ["0.5x", "1x", "1.5x", "2x"]
VOLUME_MARK_LABELS = ["0%", "50%", "100%"]


class TestVoicePersonalizationControls:
    """ELITEA-2385 -- the Voice Personalization controls respond to the user."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/user-profile/ELITEA-2385_voice-personalization-voice-dropdown-speed-and-volume-slider.md",
        "onetest-ai Test Case link",
    )
    def test_voice_personalization_controls_are_interactive(self, page):
        """The Voice select opens and adopts a newly picked voice, the Speed and
        Volume sliders expose their documented ranges and land exactly on the
        value they are dragged to, and 'Preview Voice' is clickable -- with no
        console errors on the route."""
        personalization = SettingsPersonalizationPage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 - Open Settings -> Preferences and find VOICE PERSONALIZATION"):
            personalization.open_settings_tab("preferences")
            expect(page).to_have_url(f"{settings.app_base_url}{PREFERENCES_PATH}")
            expect(personalization.nav_item("preferences")).to_have_attribute("data-active", "true")
            expect(personalization.voice_personalization_section).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            # `BasicAccordion` defaults to expanded; a collapsed accordion keeps
            # its children MOUNTED (visibility: hidden), so a bare presence check
            # below would pass on a collapsed section.
            expect(personalization.voice_personalization_header).to_have_attribute(
                "aria-expanded", "true"
            )

        with allure.step("Step 2 - The Voice dropdown is present and shows a selected option"):
            expect(personalization.voice_select_combobox).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            # Known defect: #1965 -- on a fresh profile the select renders blank
            # because the `alloy` default effect is dead. The case's expectation
            # ("shows a selected option") is the CORRECT one and is asserted as
            # such; soft, so the rest of the case still runs. Do not weaken it.
            expect.soft(personalization.voice_select_combobox).not_to_have_text("")

        with allure.step("Step 3 - Clicking the Voice dropdown shows the list of voices"):
            personalization.open_voice_options(TARGET_VOICE_VALUE, timeout=UI_ELEMENT_TIMEOUT)
            # No exact count: the options are backend-supplied TTS voices, not a
            # front-end constant, so an exact number is a false red waiting to
            # happen. `>= 1` plus the named row is what the case asserts.
            assert personalization.select_options().count() >= 1, (
                "Opening the Voice dropdown should render at least one option row"
            )
            expect(personalization.select_option(TARGET_VOICE_VALUE)).to_be_visible()

        with allure.step(f"Step 4 - Select a different voice ({TARGET_VOICE_LABEL})"):
            # The list is already open from step 3 -- clicking the combobox again
            # would close it rather than select.
            personalization.choose_open_option(TARGET_VOICE_VALUE, timeout=UI_ELEMENT_TIMEOUT)
            expect(personalization.voice_select_combobox).to_have_text(TARGET_VOICE_LABEL)
            expect(personalization.select_option(TARGET_VOICE_VALUE)).not_to_be_visible()

        with allure.step("Step 5 - The Speed slider is present with range 0.5x to 2x"):
            expect(personalization.voice_speed_slider_input).to_have_attribute("min", SPEED_MIN_ATTR)
            expect(personalization.voice_speed_slider_input).to_have_attribute("max", SPEED_MAX_ATTR)
            expect(personalization.voice_speed_slider_input).to_have_attribute("step", SPEED_STEP_ATTR)
            for label in SPEED_MARK_LABELS:
                expect(personalization.voice_speed_slider).to_contain_text(label)

        with allure.step(f"Step 6 - Drag the Speed slider to {SPEED_TARGET}x"):
            personalization.drag_slider_to(
                personalization.voice_speed_slider,
                personalization.voice_speed_slider_thumb,
                SPEED_FRACTION,
            )
            expect(personalization.voice_speed_slider_input).to_have_value(str(SPEED_TARGET))
            # `input.value` is DOM-normalised ("1.5000000000000004" reads back as
            # "1.5"), so only `aria-valuenow` can catch the drag path regressing
            # into the keyboard path's arithmetic (defect #1966).
            expect(personalization.voice_speed_slider_input).to_have_attribute(
                "aria-valuenow", str(SPEED_TARGET)
            )

        with allure.step("Step 7 - The Volume slider is present with range 0% to 100%"):
            expect(personalization.voice_volume_slider_input).to_have_attribute("min", "0")
            expect(personalization.voice_volume_slider_input).to_have_attribute("max", "1")
            expect(personalization.voice_volume_slider_input).to_have_attribute("step", "0.05")
            for label in VOLUME_MARK_LABELS:
                # "Mute" is case-text drift -- the marks are 0% / 50% / 100%.
                expect(personalization.voice_volume_slider).to_contain_text(label)

        with allure.step("Step 8 - Drag the Volume slider to 50%"):
            personalization.drag_slider_to(
                personalization.voice_volume_slider,
                personalization.voice_volume_slider_thumb,
                VOLUME_FRACTION,
            )
            expect(personalization.voice_volume_slider_input).to_have_value(str(VOLUME_TARGET))
            expect(personalization.voice_volume_slider_input).to_have_attribute(
                "aria-valuenow", str(VOLUME_TARGET)
            )

        with allure.step("Step 9 - 'Preview Voice' is clickable"):
            # Deliberately NOT clicked: `speak()` opens a socket TTS stream (or
            # drives speechSynthesis), is audible and slow, and unmounts the
            # button while playing. "Clickable" is fully established by
            # visible + enabled.
            expect(personalization.voice_preview_button).to_be_visible()
            expect(personalization.voice_preview_button).to_be_enabled()

        with allure.step("Step 10 - No console errors were logged"):
            # `/settings/preferences` logs none (verified live). The known #1771
            # `disableUnderline` warning belongs to /settings/memory and
            # /settings/ai-personality -- filtering it HERE would be masking.
            assert not console_errors, f"unexpected console errors: {console_errors}"
