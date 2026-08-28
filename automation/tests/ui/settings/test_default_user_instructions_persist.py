"""UI test -- Default User Instructions text survives autosave and a full page
reload (ELITEA-2382).

AFS: test-specs/settings-user-profile/
l3_default-user-instructions-persist-after-reload_ELITEA-2382.md

MUTATES SHARED ACCOUNT STATE. Both `persona` and the per-persona
`personality_instructions` map live on the shared `${TEST_USER}` record and feed
real chat behaviour (they are the very fields ELITEA-2384 observes), so this
spec reads both before writing and restores both afterwards -- strict on the
success path, best-effort on the failure path, route-guarded either way.

Case-text drift -- this spec asserts the LIVE contract
------------------------------------------------------
Both divergences are *case-text stale, product correct*; neither assertion is
weakened toward the stale text (reverse-masking guard), and both are filed as
clarifications on EliteaAI/elitea-testing-public#1960 rather than as defects:

1. "Personalization -> GENERAL section" does not exist. The field is the
   `User instructions` textarea of the `PERSONA MANAGEMENT` accordion on
   Settings -> AI Personality (`/settings/ai-personality`).
2. **The field is not global -- it is stored per persona.**
   `AIPersonalityPersonalization.jsx` writes
   `personality_instructions.<persona>`, renders only the currently selected
   persona's slot, and omits the textarea from the DOM entirely while the
   persona is `None`. The case is silent on this, so the spec PINS the persona
   before typing and reads back under that same persona -- otherwise the
   read-back would be non-deterministic on whatever the previous run left --
   and asserts the per-persona isolation directly.

No substitutions: the text is typed into the real control, saved by the
product's own blur-driven autosave, and re-read after a real page reload, so
the asserted value is the one the server returned.

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
from pages.settings_personalization_page import AI_PERSONALITY_PATH, SettingsPersonalizationPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors
from utils.personalization_autosave import (
    AUTOSAVE_TIMEOUT,
    best_effort,
    is_author_autosave,
    restore_persona,
    restore_user_instructions,
    unexpected_console_errors,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

#: The persona whose instructions slot this spec writes. Any non-`none` persona
#: works; pinning one is what makes the read-back deterministic.
PINNED_PERSONA_VALUE = "nerdy"
PINNED_PERSONA_LABEL = "Nerdy"

#: A second persona, used only by the per-persona-isolation assertion.
OTHER_PERSONA_VALUE = "quirky"
OTHER_PERSONA_LABEL = "Quirky"

#: Verbatim from case step 3.
INSTRUCTIONS_TEXT = "Always respond in a concise manner. Focus on practical solutions."

#: `PERSONA_INSTRUCTIONS_PLACEHOLDERS`, `EliteaUI` `src/common/constants.js`.
#: The placeholder names the persona, so it proves WHICH slot the textarea is
#: showing -- without it the spec could write one slot and read another.
PERSONA_INSTRUCTIONS_PLACEHOLDERS = {
    "nerdy": "No custom instructions for the Nerdy persona yet. Type here to add some.",
    "quirky": "No custom instructions for the Quirky persona yet. Type here to add some.",
}


class TestDefaultUserInstructionsPersist:
    """ELITEA-2382 -- Default User Instructions persist after save and reload."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/user-profile/ELITEA-2382_default-user-instructions-text-persists-after-save-and-reloa.md",
        "onetest-ai Test Case link",
    )
    def test_default_user_instructions_persist_after_reload(self, page):
        """Typing instructions and clicking outside fires an autosave PUT (200);
        after a full page reload the field still shows the entered text, and the
        text lives in the pinned persona's slot only."""
        personalization = SettingsPersonalizationPage(page)
        console_errors = collect_console_errors(page)
        original_persona_label = None
        original_instructions = None

        try:
            with allure.step("Step 1 - Open Settings -> AI Personality"):
                personalization.open_settings_tab("ai-personality")
                expect(page).to_have_url(f"{settings.app_base_url}{AI_PERSONALITY_PATH}")
                expect(personalization.nav_item("ai-personality")).to_have_attribute(
                    "data-active", "true"
                )
                expect(personalization.persona_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # Element wait, never a sleep -- the select renders a beat after
                # the route resolves.
                personalization.wait_for_persona_select()

                original_persona_label = personalization.get_persona()
                assert original_persona_label, "Could not read the current Default persona"
                logger.info("Original persona: %r", original_persona_label)

            with allure.step(
                f"Setup - Pin the persona to {PINNED_PERSONA_LABEL} so the "
                "read-back reads the slot this spec writes"
            ):
                if original_persona_label != PINNED_PERSONA_LABEL:
                    with page.expect_response(
                        is_author_autosave, timeout=AUTOSAVE_TIMEOUT
                    ) as pin:
                        personalization.select_persona(PINNED_PERSONA_VALUE)
                    assert pin.value.status == 200, (
                        f"Pinning the persona to {PINNED_PERSONA_LABEL} should autosave via "
                        f"PUT -> 200, got {pin.value.status}"
                    )
                expect(personalization.persona_select_combobox).to_have_text(PINNED_PERSONA_LABEL)
                expect(personalization.user_instructions_textarea).to_have_attribute(
                    "placeholder", PERSONA_INSTRUCTIONS_PLACEHOLDERS[PINNED_PERSONA_VALUE]
                )
                original_instructions = personalization.get_user_instructions()
                logger.info(
                    "Original %s instructions slot: %r",
                    PINNED_PERSONA_LABEL,
                    original_instructions,
                )

            with allure.step("Step 2 - Click the Default User Instructions textarea"):
                personalization.user_instructions_textarea.click()
                expect(personalization.user_instructions_textarea).to_be_focused()
                # "The field accepts the input" is only meaningful if the field
                # CAN accept it -- a readonly field pre-filled by a previous run
                # would satisfy a value-only assertion.
                expect(personalization.user_instructions_textarea).to_be_editable()

            with allure.step("Step 3 - Enter the instructions text"):
                personalization.fill_user_instructions(INSTRUCTIONS_TEXT)
                expect(personalization.user_instructions_textarea).to_have_value(INSTRUCTIONS_TEXT)

            with allure.step("Step 4 - Click outside to trigger autosave"):
                # Blur genuinely IS the trigger for this control (unlike the
                # persona select): `AIPersonalityFormContent` wraps the form in
                # `useFormikAutoSaveOnBlur`, and `handleInstructionsChange` does
                # not request a save itself. NOT the accordion header as the
                # "outside" target -- clicking that collapses the section.
                with page.expect_response(is_author_autosave, timeout=AUTOSAVE_TIMEOUT) as autosave:
                    personalization.click_neutral_content_area()
                assert autosave.value.status == 200, (
                    f"Blurring the instructions field should autosave via PUT -> 200, got "
                    f"{autosave.value.status} from {autosave.value.url}"
                )

            with allure.step("Step 5 - Reload the page"):
                page.reload()
                personalization.wait_for_persona_select()
                expect(personalization.user_instructions_textarea).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 6 - The field still shows the entered text"):
                # Guard the read: a reload that landed on a different persona
                # would be reading a different storage slot.
                expect(personalization.persona_select_combobox).to_have_text(PINNED_PERSONA_LABEL)
                expect(personalization.user_instructions_textarea).to_have_value(INSTRUCTIONS_TEXT)

            with allure.step(
                "Step 7 (beyond the case) - The text lives in the pinned "
                f"persona's slot only: switching to {OTHER_PERSONA_LABEL} shows "
                "an empty field, switching back restores the text"
            ):
                with page.expect_response(is_author_autosave, timeout=AUTOSAVE_TIMEOUT) as other:
                    personalization.select_persona(OTHER_PERSONA_VALUE)
                assert other.value.status == 200, (
                    f"Switching to {OTHER_PERSONA_LABEL} should autosave via PUT -> 200, got "
                    f"{other.value.status}"
                )
                expect(personalization.user_instructions_textarea).to_have_value("")
                expect(personalization.user_instructions_textarea).to_have_attribute(
                    "placeholder", PERSONA_INSTRUCTIONS_PLACEHOLDERS[OTHER_PERSONA_VALUE]
                )

                with page.expect_response(is_author_autosave, timeout=AUTOSAVE_TIMEOUT) as back:
                    personalization.select_persona(PINNED_PERSONA_VALUE)
                assert back.value.status == 200, (
                    f"Switching back to {PINNED_PERSONA_LABEL} should autosave via PUT -> 200, "
                    f"got {back.value.status}"
                )
                expect(personalization.user_instructions_textarea).to_have_value(INSTRUCTIONS_TEXT)

            with allure.step("Step 8 - No unexpected console errors were logged"):
                # `/settings/ai-personality` always logs the #1771
                # `disableUnderline` warning; nothing else is tolerated.
                # Known defect: #1771.
                assert not unexpected_console_errors(console_errors), (
                    f"unexpected console errors: {unexpected_console_errors(console_errors)}"
                )

        except BaseException:
            # The body already failed -- restore best-effort so the REAL failure
            # stays the report.
            if original_instructions is not None:
                best_effort(
                    lambda: restore_user_instructions(
                        personalization, PINNED_PERSONA_LABEL, original_instructions
                    ),
                    f"restore {PINNED_PERSONA_LABEL}'s user instructions",
                )
            if original_persona_label:
                best_effort(
                    lambda: restore_persona(personalization, original_persona_label),
                    f"restore the original persona ({original_persona_label})",
                )
            raise
        else:
            # Body passed: leaving text in a shared slot changes what the next
            # run of this spec -- and of ELITEA-2384 -- observes, so a failed
            # restore IS a failure.
            if original_instructions is not None:
                restore_user_instructions(
                    personalization, PINNED_PERSONA_LABEL, original_instructions
                )
            if original_persona_label:
                restore_persona(personalization, original_persona_label)
