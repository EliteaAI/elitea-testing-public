"""UI test -- the personality settings are independent of the context-management
toggle (ELITEA-2383).

AFS: test-specs/settings-user-profile/
l2_general-settings-independent-of-context-management_ELITEA-2383.md

MUTATES SHARED ACCOUNT STATE, two structures. This spec flips
`default_context_management.enabled` and changes `personalization.persona`, both
on the shared `${TEST_USER}` record. Both are read before writing and restored
afterwards -- persona first, toggle LAST, so that a failed persona restore can
never leave context management off for every other settings spec.

Case-text drift -- and why the case is still worth automating
--------------------------------------------------------------
The case assumes ONE page carrying both the context-management toggle and the
personality controls, ending with a Save button. Neither holds (case-text
stale, product correct -- clarifications on
EliteaAI/elitea-testing-public#1960, siblings #1238/#1244):

* the toggle is on Settings -> Memory (`CONTEXT MANAGEMENT`); the Default
  persona select and User instructions textarea are on Settings -> AI
  Personality (`PERSONA MANAGEMENT`);
* there is no Save button anywhere in this settings family -- every page
  autosaves, so the autosave `PUT -> 200` is the live equivalent of case step 5,
  and the absence of a Save control is asserted directly.

The risk the case points at SURVIVES the relocation and is more interesting
than the case knew: one `PUT /api/v2/social/author/` carries **both**
structures, so a personality write that clobbered the context-management state
(or the reverse) would be a real regression no other spec in this suite would
catch. That invariant is asserted in both directions.

No substitutions: the toggle is flipped through the UI exactly as the case
says, save outcomes are read from real `PUT` responses, and independence is
verified by re-reading the OTHER page after each write.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p2: medium-high priority (per AFS metadata: l2 -- case priority `high`)
    - regression
"""

import logging

import allure
import pytest
from config import settings
from pages.settings_personalization_page import (
    AI_PERSONALITY_PATH,
    MEMORY_PATH,
    SettingsPersonalizationPage,
)
from pages.user_profile_settings_page import UserProfileSettingsPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors
from utils.personalization_autosave import (
    AUTOSAVE_TIMEOUT,
    best_effort,
    is_author_autosave,
    restore_persona,
    unexpected_console_errors,
)

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.settings,
    pytest.mark.p2,
    pytest.mark.regression,
]

UI_ELEMENT_TIMEOUT = 10_000

#: The persona the case selects at step 4.
TARGET_PERSONA_VALUE = "quirky"
TARGET_PERSONA_LABEL = "Quirky"

#: Used only when the account already sits on the case's target -- the change
#: has to be a real change for the save assertion to mean anything.
ALTERNATIVE_PERSONA_VALUE = "nerdy"
ALTERNATIVE_PERSONA_LABEL = "Nerdy"


def _set_context_management(page, profile: UserProfileSettingsPage, enabled: bool) -> None:
    """Flip the CONTEXT MANAGEMENT toggle, asserting its own autosave PUT.

    `UserProfileSettingsPage.enable/disable_context_management()` wait on
    `networkidle`, which never settles on this app (the persistent Socket.IO
    polling transport, #1847), so the click is driven here and the write is
    asserted instead of merely awaited. No-op when the toggle already holds the
    wanted state -- `useFormikAutoSaveOnBlur` legitimately fires no request when
    Formik is not dirty, so asserting a PUT there would be a false red.
    """
    if profile.is_context_management_enabled() == enabled:
        return
    with page.expect_response(is_author_autosave, timeout=AUTOSAVE_TIMEOUT) as put_info:
        profile.context_management_toggle.click()
    assert put_info.value.status == 200, (
        f"Turning context management {'ON' if enabled else 'OFF'} should autosave via "
        f"PUT -> 200, got {put_info.value.status}"
    )
    assert profile.is_context_management_enabled() is enabled, (
        f"The context management toggle should read {'ON' if enabled else 'OFF'} after the click"
    )


class TestPersonalityIndependentOfContextManagement:
    """ELITEA-2383 -- personality settings do not depend on context management."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/user-profile/ELITEA-2383_general-settings-personality-and-instructions-are-independen.md",
        "onetest-ai Test Case link",
    )
    def test_personality_settings_independent_of_context_management(self, page):
        """With context management OFF the personality controls stay visible,
        enabled, editable and un-grayed; changing the persona then saves via
        autosave (no Save button exists), and neither write disturbs the other
        structure."""
        profile = UserProfileSettingsPage(page)
        personalization = SettingsPersonalizationPage(page)
        console_errors = collect_console_errors(page)
        original_toggle_enabled = None
        original_persona_label = None

        try:
            with allure.step(
                "Setup - Record the account's current context-management and "
                "persona state (never assume defaults -- both are shared)"
            ):
                profile.navigate_to_profile()
                expect(profile.context_management_section).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                original_toggle_enabled = profile.is_context_management_enabled()

                personalization.go_to_settings_tab("ai-personality")
                personalization.wait_for_persona_select()
                original_persona_label = personalization.get_persona()
                assert original_persona_label, "Could not read the current Default persona"
                logger.info(
                    "Account originals: context_management=%s persona=%r",
                    original_toggle_enabled,
                    original_persona_label,
                )

                if original_persona_label == TARGET_PERSONA_LABEL:
                    target_value, target_label = (
                        ALTERNATIVE_PERSONA_VALUE,
                        ALTERNATIVE_PERSONA_LABEL,
                    )
                else:
                    target_value, target_label = TARGET_PERSONA_VALUE, TARGET_PERSONA_LABEL

            with allure.step("Step 1 - Navigate to the settings area (Settings -> Memory)"):
                personalization.go_to_settings_tab("memory")
                expect(page).to_have_url(f"{settings.app_base_url}{MEMORY_PATH}")
                expect(personalization.nav_item("memory")).to_have_attribute(
                    "data-active", "true"
                )
                expect(personalization.context_management_section).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 2 - Turn OFF the context management toggle"):
                # The case's action has to be a real transition, whatever the
                # last session left behind.
                _set_context_management(page, profile, enabled=True)
                _set_context_management(page, profile, enabled=False)
                # The toggle really took effect: the numeric fields are
                # conditionally UNMOUNTED when it is off -- `to_have_count(0)`,
                # not `not_to_be_visible()` (that is the accordion's separate
                # `visibility: hidden` mechanism).
                expect(profile.max_context_tokens_input).to_have_count(0)

            with allure.step(
                "Step 3 - The personality controls remain editable and are NOT "
                "grayed out (they live on Settings -> AI Personality)"
            ):
                personalization.go_to_settings_tab("ai-personality")
                expect(page).to_have_url(f"{settings.app_base_url}{AI_PERSONALITY_PATH}")
                personalization.wait_for_persona_select()

                expect(personalization.persona_section).to_be_visible()
                expect(personalization.persona_select_combobox).to_be_visible()
                expect(personalization.user_instructions_textarea).to_be_visible()

                expect(personalization.user_instructions_textarea).to_be_editable()
                expect(personalization.persona_select_combobox).not_to_have_attribute(
                    "aria-disabled", "true"
                )
                # "Not grayed out": MUI expresses disabled-ness with a class it
                # adds at render time -- see the page object's #579 declaration.
                expect(personalization.persona_section_disabled_elements()).to_have_count(0)

                # Interactive, not merely present: a control can look enabled
                # and still refuse to open.
                personalization.open_persona_options(timeout=UI_ELEMENT_TIMEOUT)
                expect(personalization.persona_option(TARGET_PERSONA_VALUE)).to_be_visible()
                personalization.close_persona_options(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(f"Step 4 - Change the Default Personality to {target_label}"):
                with page.expect_response(is_author_autosave, timeout=AUTOSAVE_TIMEOUT) as autosave:
                    personalization.select_persona(target_value)
                assert autosave.value.status == 200, (
                    f"Changing the persona with context management OFF should autosave via "
                    f"PUT -> 200, got {autosave.value.status} from {autosave.value.url}"
                )
                expect(personalization.persona_select_combobox).to_have_text(target_label)

            with allure.step(
                "Step 5 - The settings saved without error -- and there is no "
                "Save button to click (the page autosaves)"
            ):
                # "Without error" is already asserted, twice, and NOT here:
                # this surface has no error toast/alert of its own (no such
                # handle exists anywhere in the suite for it), so the two
                # observables it really produces carry the case's step 5 --
                # Step 4's `PUT -> 200` above (the write succeeded) and Step 8's
                # console-error check below (nothing failed client-side).
                # Absence assertions are first-class references (canon #511
                # extension): if a Save button ever appears here, the autosave
                # premise this whole case family rests on has stopped holding.
                expect(personalization.save_buttons()).to_have_count(0)
                expect(personalization.page_save_buttons()).to_have_count(0)

            with allure.step(
                "Step 6 (beyond the case) - The persona write did not disturb "
                "context management: the toggle is still OFF"
            ):
                # One PUT carries BOTH structures, so a serialization bug could
                # clobber the toggle -- nothing else in this suite would catch it.
                personalization.go_to_settings_tab("memory")
                expect(personalization.context_management_section).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert not profile.is_context_management_enabled(), (
                    "Context management must still be OFF after the persona write -- the two "
                    "structures share one PUT and must not clobber each other"
                )
                expect(profile.max_context_tokens_input).to_have_count(0)

            with allure.step(
                "Step 7 (beyond the case) - The inverse direction: turning "
                "context management back ON does not reset the persona"
            ):
                _set_context_management(page, profile, enabled=True)
                personalization.go_to_settings_tab("ai-personality")
                personalization.wait_for_persona_select()
                expect(personalization.persona_select_combobox).to_have_text(target_label)

            with allure.step("Step 8 - No unexpected console errors were logged"):
                # Both routes always log the #1771 `disableUnderline` warning;
                # nothing else is tolerated. Known defect: #1771.
                assert not unexpected_console_errors(console_errors), (
                    f"unexpected console errors: {unexpected_console_errors(console_errors)}"
                )

        except BaseException:
            # The body already failed -- restore best-effort so the REAL failure
            # stays the report. Persona first, toggle last.
            if original_persona_label:
                best_effort(
                    lambda: restore_persona(personalization, original_persona_label),
                    f"restore the original persona ({original_persona_label})",
                )
            if original_toggle_enabled is not None:
                best_effort(
                    lambda: self._restore_toggle(page, profile, original_toggle_enabled),
                    "restore the context management toggle",
                )
            raise
        else:
            if original_persona_label:
                restore_persona(personalization, original_persona_label)
            if original_toggle_enabled is not None:
                self._restore_toggle(page, profile, original_toggle_enabled)

    @staticmethod
    def _restore_toggle(page, profile: UserProfileSettingsPage, enabled: bool) -> None:
        """Put the shared account's context-management toggle back.

        Route-guarded for the same reason the persona restore is: the test can
        fail on `/settings/ai-personality`, where the toggle does not exist at
        all, and reading it there would auto-wait and raise a `TimeoutError`
        that REPLACES the real failure in the report.
        """
        if MEMORY_PATH not in page.url:
            profile.navigate_to_profile()
        expect(profile.context_management_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        _set_context_management(page, profile, enabled=enabled)
