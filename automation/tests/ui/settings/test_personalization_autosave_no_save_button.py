"""UI test -- personalization settings save automatically: there is no Save
button, and a changed Default persona survives navigating away, coming back,
and a full page reload.

MUTATES SHARED ACCOUNT STATE. `persona` lives on the shared `${TEST_USER}`
record and also drives chat behaviour, so this spec reads the current value
first, never assumes a default, and restores it in a `finally` block -- waiting
for the restore's own autosave round-trip and asserting it landed.

Test case: ELITEA-2387
AFS: test-specs/settings-user-profile/l3_personalization_settings_autosave_no_save_button_ELITEA-2387.md

Case-text drift -- this test asserts the LIVE contract
--------------------------------------------------------
The case says "Settings -> Personalization". `/settings/personalization` renders
the app's global "Page not found" view; "Default Personality" is the
`Default persona` select of the `PERSONA MANAGEMENT` accordion on Settings ->
AI Personality (`/settings/ai-personality`). Everything the case actually
verifies -- no Save button, and the change surviving navigation -- is real.
Clarification: EliteaAI/elitea-testing-public#1960.

Why the PUT is asserted and not merely awaited
----------------------------------------------
"Saved without a Save button" is only proven by the write succeeding. A value
that merely persisted in the SPA store would satisfy the case's step 6 without
anything being saved at all -- so this spec asserts the autosave
`PUT /api/v2/social/author/` returns 200 (the wait signal, never a sleep), and
then re-reads the value after a FULL RELOAD, which is what separates server
persistence from client cache.

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
    AI_PERSONALITY_PATH,
    AUTHOR_SETTINGS_ENDPOINT,
    NOTIFICATIONS_PATH,
    SettingsPersonalizationPage,
)
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
AUTOSAVE_TIMEOUT = 15_000

#: The persona the case asks for.
TARGET_PERSONA_VALUE = "qa"
TARGET_PERSONA_LABEL = "QA"

#: Used only if the account already sits on the case's target -- the change has
#: to be a real change for the persistence assertions to mean anything.
ALTERNATIVE_PERSONA_VALUE = "generic"
ALTERNATIVE_PERSONA_LABEL = "Generic"

#: Per-persona placeholder of the `User instructions` field
#: (`PERSONA_INSTRUCTIONS_PLACEHOLDERS`, `src/common/constants.js`) -- a cheap
#: secondary signal that the persona change reached Formik state rather than
#: only the select's own display.
PERSONA_INSTRUCTIONS_PLACEHOLDERS = {
    "qa": "No custom instructions for the QA persona yet. Type here to add some.",
    "generic": "No custom instructions for the Generic persona yet. Type here to add some.",
}

#: Known defect EliteaAI/elitea-testing-public#1771 -- `/settings/ai-personality`
#: logs a React `disableUnderline` warning on every load, from
#: `StyledInputEnhancer`. Unrelated to autosave and pre-dating this case;
#: filtered by its exact message fragment, so any OTHER console error still fails.
KNOWN_DEFECT_1771_FRAGMENT = "disableUnderline"


def _unexpected(console_errors: list[str]) -> list[str]:
    """Console errors other than the known #1771 `disableUnderline` warning."""
    return [e for e in console_errors if KNOWN_DEFECT_1771_FRAGMENT not in e]


def _is_author_autosave(response) -> bool:
    """Whether *response* is the personalization autosave write."""
    return AUTHOR_SETTINGS_ENDPOINT in response.url and response.request.method == "PUT"


class TestPersonalizationAutosaveNoSaveButton:
    """ELITEA-2387 -- personalization settings save automatically."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2387_personalization-settings-save-automatically-without-a-save-button.md",
        "onetest-ai Test Case link",
    )
    def test_personalization_autosave_no_save_button(self, page):
        """Settings -> AI Personality exposes no Save button; changing the
        Default persona fires an autosave PUT that returns 200, and the new
        value is still shown after navigating to Notifications and back, and
        after a full page reload. The original persona is restored afterwards."""
        personalization = SettingsPersonalizationPage(page)
        console_errors = collect_console_errors(page)
        original_persona_label = None

        try:
            with allure.step("Step 1 - Open Settings -> AI Personality and read the current persona"):
                personalization.open_settings_tab("ai-personality")
                expect(page).to_have_url(f"{settings.app_base_url}{AI_PERSONALITY_PATH}")
                expect(personalization.nav_item("ai-personality")).to_have_attribute(
                    "data-active", "true"
                )
                expect(personalization.persona_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # The select renders a beat after the route does -- an element
                # wait, never a sleep.
                personalization.wait_for_persona_select()

                original_persona_label = personalization.get_persona()
                assert original_persona_label, "Could not read the current Default persona"
                logger.info("Original persona: %r", original_persona_label)

                # The change must be a real change, whatever the last session left.
                if original_persona_label == TARGET_PERSONA_LABEL:
                    target_value, target_label = (
                        ALTERNATIVE_PERSONA_VALUE,
                        ALTERNATIVE_PERSONA_LABEL,
                    )
                else:
                    target_value, target_label = TARGET_PERSONA_VALUE, TARGET_PERSONA_LABEL
                allure.attach(
                    f"original={original_persona_label!r} target={target_label!r}",
                    name="persona under test",
                )

            with allure.step("Step 2 - Verify there is no Save button on the page"):
                # Absence assertions are first-class references (canon #511
                # extension): if a Save button ever appears here, the case's
                # premise -- that these settings autosave -- has stopped holding.
                expect(personalization.save_buttons()).to_have_count(0)
                expect(personalization.page_save_buttons()).to_have_count(0)

            with allure.step(f"Step 3 - Change Default persona to {target_label}"):
                with page.expect_response(
                    _is_author_autosave, timeout=AUTOSAVE_TIMEOUT
                ) as autosave:
                    personalization.select_persona(target_value)
                autosave_response = autosave.value
                assert autosave_response.status == 200, (
                    f"Autosave PUT {autosave_response.url} returned "
                    f"{autosave_response.status}, expected 200"
                )
                expect(personalization.persona_select_combobox).to_have_text(target_label)
                # Beyond the case: the per-persona placeholder proves the change
                # reached Formik state, not just the select's display.
                expect(personalization.user_instructions_textarea).to_have_attribute(
                    "placeholder", PERSONA_INSTRUCTIONS_PLACEHOLDERS[target_value]
                )

            with allure.step("Step 4 - Navigate away to Settings -> Notifications"):
                personalization.go_to_settings_tab("notifications")
                expect(page).to_have_url(f"{settings.app_base_url}{NOTIFICATIONS_PATH}")
                expect(personalization.nav_item("notifications")).to_have_attribute(
                    "data-active", "true"
                )

            with allure.step("Step 5 - Navigate back to Settings -> AI Personality"):
                personalization.go_to_settings_tab("ai-personality")
                expect(page).to_have_url(f"{settings.app_base_url}{AI_PERSONALITY_PATH}")
                personalization.wait_for_persona_select()

            with allure.step(
                f"Step 6 - Verify Default persona still shows {target_label} "
                "(auto-saved without an explicit save action)"
            ):
                expect(personalization.persona_select_combobox).to_have_text(target_label)

            with allure.step(
                "Step 7 (beyond the case) - Verify the value survives a full page reload, "
                "which separates server persistence from the SPA store"
            ):
                page.reload()
                personalization.wait_for_persona_select()
                expect(personalization.persona_select_combobox).to_have_text(target_label)

            with allure.step("Step 8 - Verify no unexpected console errors were logged"):
                # `/settings/ai-personality` always logs the #1771
                # `disableUnderline` warning; nothing else is tolerated.
                # Known defect: #1771.
                assert not _unexpected(console_errors), (
                    f"unexpected console errors: {_unexpected(console_errors)}"
                )

        finally:
            if original_persona_label and personalization.get_persona() != original_persona_label:
                with allure.step(
                    f"Teardown - Restore the original persona ({original_persona_label})"
                ):
                    original_value = original_persona_label.strip().lower()
                    with page.expect_response(
                        _is_author_autosave, timeout=AUTOSAVE_TIMEOUT
                    ) as restore:
                        personalization.select_persona(original_value)
                    assert restore.value.status == 200, (
                        "Failed to restore the original persona -- shared account state is "
                        f"left on a different value (restore PUT returned {restore.value.status})"
                    )
                    expect(personalization.persona_select_combobox).to_have_text(
                        original_persona_label
                    )
