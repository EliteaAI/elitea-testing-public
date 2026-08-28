"""UI test -- the Default persona dropdown lists exactly the seven documented
personas, and picking one autosaves and sticks (ELITEA-2381).

AFS: test-specs/settings-user-profile/
l3_default-personality-dropdown-options_ELITEA-2381.md

MUTATES SHARED ACCOUNT STATE. `persona` lives on the shared `${TEST_USER}`
record and drives chat behaviour, so this spec reads the current value first,
never assumes a default, and restores it afterwards -- asserting the restore's
own autosave landed. Route-guarded, strict on the success path, best-effort on
the failure path, so teardown can never replace the real failure in the report.

Case-text drift -- this spec asserts the LIVE contract
------------------------------------------------------
Three divergences, all *case-text stale, product correct*; none is weakened
toward the stale text (reverse-masking guard), and each is filed as a
clarification rather than a defect:

1. The case title says "six documented options" while its own step table lists
   **seven** (steps 4-10), and the live dropdown renders exactly those seven --
   `PERSONA_OPTIONS`, `EliteaUI` `src/common/constants.js`. Seven is asserted.
   Clarification: EliteaAI/elitea-testing-public#1963.
2. "Personalization -> GENERAL section" does not exist. The Default persona
   select is in the `PERSONA MANAGEMENT` accordion of Settings -> AI
   Personality (`/settings/ai-personality`); `GENERAL` on
   `/settings/preferences` carries the Theme toggle only.
   Clarification: EliteaAI/elitea-testing-public#1960.
3. Step 12 "click outside to trigger autosave" is not this control's mechanism:
   `handlePersonaChange` calls `onAutoSaveRequested` directly, so the PUT fires
   on selection. The step is still executed (it is a harmless no-op) so the
   case's flow is honoured, and what it asserts is that the click did not
   collapse the section.

No substitutions: every asserted value is produced by the running app -- the
option rows are read from the live DOM, the save outcome from the real
`PUT /api/v2/social/author/` response, and the final value after a real reload.

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
    unexpected_console_errors,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

#: The option set the case enumerates, in the DOM order `PERSONA_OPTIONS`
#: defines (`EliteaUI` `src/common/constants.js`). Order is asserted as well as
#: membership: a reordering is a real, user-visible change the case would
#: otherwise miss.
EXPECTED_PERSONA_OPTIONS = [
    ("generic", "Generic"),
    ("qa", "QA"),
    ("nerdy", "Nerdy"),
    ("quirky", "Quirky"),
    ("cynical", "Cynical"),
    ("none", "None"),
    ("bare", "Bare"),
]

#: The persona the case selects at step 11.
TARGET_PERSONA_VALUE = "nerdy"
TARGET_PERSONA_LABEL = "Nerdy"

#: Used only when the account already sits on the case's target -- the change
#: has to be a real change for the persistence assertions to mean anything.
ALTERNATIVE_PERSONA_VALUE = "generic"
ALTERNATIVE_PERSONA_LABEL = "Generic"


class TestDefaultPersonalityOptions:
    """ELITEA-2381 -- the Default persona dropdown's option set."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/user-profile/ELITEA-2381_default-personality-dropdown-shows-all-six-documented-option.md",
        "onetest-ai Test Case link",
    )
    def test_default_personality_dropdown_options(self, page):
        """The Default persona list renders exactly the seven documented personas
        in order, marks the current one, and selecting a different one autosaves
        (PUT 200), updates the display and survives a full page reload."""
        personalization = SettingsPersonalizationPage(page)
        console_errors = collect_console_errors(page)
        original_persona_label = None

        try:
            with allure.step("Step 1 - Open Settings -> AI Personality"):
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

            with allure.step("Step 2 - Click the Default Personality dropdown"):
                personalization.open_persona_options(timeout=UI_ELEMENT_TIMEOUT)
                expect(personalization.persona_option("generic")).to_be_visible()

            with allure.step(
                "Steps 3-10 - The list contains exactly the seven documented "
                "personas, in order, with the current one marked"
            ):
                # Count first: a per-option presence check alone passes when an
                # EIGHTH option appears, and the case's subject is the option set.
                expect(personalization.persona_options()).to_have_count(
                    len(EXPECTED_PERSONA_OPTIONS)
                )
                assert personalization.get_persona_option_labels() == [
                    label for _, label in EXPECTED_PERSONA_OPTIONS
                ], (
                    "The Default persona list should render the documented personas in "
                    f"order; got {personalization.get_persona_option_labels()}"
                )

                for value, label in EXPECTED_PERSONA_OPTIONS:
                    option = personalization.persona_option(value)
                    expect(option).to_be_visible()
                    expect(option).to_contain_text(label)

                # The list reflects live state rather than a static menu.
                for _, label in EXPECTED_PERSONA_OPTIONS:
                    expected_state = "true" if label == original_persona_label else "false"
                    actual_state = personalization.persona_option_selected_state(
                        label.strip().lower()
                    )
                    assert actual_state == expected_state, (
                        f"Option {label!r} should report data-selected={expected_state!r} "
                        f"while the account persona is {original_persona_label!r}, got "
                        f"{actual_state!r}"
                    )

            with allure.step(f"Step 11 - Select a different personality ({target_label})"):
                # The list is already open (step 2), so the option is clicked
                # directly rather than through `select_persona()`.
                with page.expect_response(is_author_autosave, timeout=AUTOSAVE_TIMEOUT) as autosave:
                    personalization.persona_option(target_value).click()
                autosave_response = autosave.value
                assert autosave_response.status == 200, (
                    f"Selecting a persona should autosave via PUT -> 200, got "
                    f"{autosave_response.status} from {autosave_response.url}"
                )

            with allure.step(
                "Step 12 - Click outside to trigger autosave (a no-op for this "
                "control -- the PUT already landed at step 11)"
            ):
                # NOT the accordion header: clicking that collapses PERSONA
                # MANAGEMENT (confirmed live). Pinning `aria-expanded` here stops
                # a future refactor from silently changing what this step does.
                personalization.click_neutral_content_area()
                # PERSONA MANAGEMENT is a one-item `BasicAccordion` whose summary
                # carries no testid of its own, so "still expanded" is observed
                # through the section's CONTENT: collapsing hides the body
                # (`visibility: hidden`) rather than unmounting it, so a visible
                # select is proof the section did not collapse.
                expect(personalization.persona_select_combobox).to_be_visible()
                expect(personalization.user_instructions_textarea).to_be_visible()

            with allure.step(f"Step 13 - The dropdown shows {target_label}"):
                expect(personalization.persona_select_combobox).to_have_text(target_label)

            with allure.step(
                "Step 14 (beyond the case) - The selection survives a full page "
                "reload, which separates server persistence from the SPA store"
            ):
                page.reload()
                personalization.wait_for_persona_select()
                expect(personalization.persona_select_combobox).to_have_text(target_label)

            with allure.step("Step 15 - No unexpected console errors were logged"):
                # `/settings/ai-personality` always logs the #1771
                # `disableUnderline` warning; nothing else is tolerated.
                # Known defect: #1771.
                assert not unexpected_console_errors(console_errors), (
                    f"unexpected console errors: {unexpected_console_errors(console_errors)}"
                )

        except BaseException:
            # The body already failed. Restore best-effort and let the REAL
            # failure propagate.
            if original_persona_label:
                best_effort(
                    lambda: restore_persona(personalization, original_persona_label),
                    f"restore the original persona ({original_persona_label})",
                )
            raise
        else:
            # Body passed: a failed restore IS a failure -- it leaks shared
            # account state onto every other spec reading this persona.
            if original_persona_label:
                restore_persona(personalization, original_persona_label)
