"""UI test — change the default TTS model (Settings -> AI Providers).

Test case: ELITEA-2407
AFS: test-specs/settings-ai-providers/l3_change-the-default-tts-model_ELITEA-2407.md

Its own spec rather than a third row of `test_change_section_default_model.py`:
the case text matches ELITEA-2403/2405 word for word, but the TTS section holds
ONE model live, so its step 3 ("select a different model") is unsatisfiable
without first creating a second configuration — which drags in a create flow, a
delete teardown and a default restore the other two rows do not have. That is a
difference in STEPS, not in data.

Case-identity note (pre-existing, reused from ELITEA-2392, filed as
EliteaAI/elitea-testing-public#1250): the case says "Settings -> AI
Configuration -> Text to Speech (TTS) section". There is no such page — the
section lives on "AI Providers" (`/settings/ai-providers`). The same
clarification covers step 1 landing on a COLLAPSED accordion (only LLMs
auto-expands, and the accordion's content — including the real Default combobox
— unmounts while collapsed), so the expand is folded into step 1. Asserted as
the live contract per the reverse-masking guard; NOT re-filed.

**This test CREATES, REASSIGNS and DELETES shared, live project state**, and
restores all three: a second TTS configuration is created, the project's default
TTS model is moved twice, and the configuration is deleted. Teardown restores
the default BEFORE deleting — deleting a configuration the project default
still points at leaves the project pointing at something gone, from a spec that
still reports green (`.agents/testing.md` § Teardown-guard ordering).

Declared transit (`.agents/testing.md` § Fidelity policy): the second TTS
configuration is created through the real UI create form a user would use,
because the project has only one TTS model — transit only; every observable the
case asserts (the combobox label, the persisted POST, the badge appearing, the
badge disappearing) is produced by the product. Nothing is mocked, routed,
stubbed or injected. The API is READ as an oracle, never fabricated.

The transit has a second half and it is not optional: creating a TTS
configuration ASSIGNS it as the section default (live contract, measured
2026-08-30 — the same as Vector Storage, the opposite of LLMs). Setup therefore
puts the PRE-EXISTING default back before the case's step 3, or "select a
different model" would re-select what is already selected, fire no request at
all, and the case would pass proving nothing.

Serial only — this spec mutates project-level state and must not run in
parallel with any other AI-Providers spec.

Markers:
    - ui, settings, p2 (this suite's l3 -> p2, matching the merged
      ELITEA-2392 / ELITEA-2397 / ELITEA-2401 siblings), regression, new
"""

import logging
import time

import allure
import pytest
from config import settings
from pages.ai_provider_form_page import AiProviderFormPage
from pages.ai_providers_page import AIProvidersPage
from playwright.sync_api import expect
from utils.ai_provider_teardown import delete_configurations_if_present, restore_section_default_if_moved
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

SECTION_PARAM = "tts"

SEEDED_PROJECT_ID = settings.ai_providers_seeded_project_id

#: The shared AI credential every merged AI-provider create spec uses.
CREDENTIAL_TITLE = "elps"

TMS_CASE_URL = (
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/settings/ai-configuration/"
    "ELITEA-2407_change-the-default-tts-model.md"
)


def _option_value(item: dict) -> str:
    """The Default-selector option value the product builds for *item*
    (``"{name}<<>>{project_id}"``). The two halves of this section's dropdown
    differ in project id — the pre-existing model is shared from project 1 while
    the transit one is local to the active project — so the whole value is taken
    from the response body, never assembled from an assumed project id."""
    return f"{item['name']}<<>>{item['project_id']}"


class TestChangeDefaultTtsModel:
    """ELITEA-2407 — reassign the project's default TTS model and verify the
    selector and both cards' Default badges follow."""

    @allure.issue(TMS_CASE_URL, "onetest-ai Test Case ELITEA-2407")
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1250", "Case-text clarification #1250"
    )
    def test_change_default_tts_model(self, page):
        """Select a different default TTS model and verify the change persists,
        the selector updates, the new card gains the Default badge and the
        previous card loses it."""
        providers_page = AIProvidersPage(page)
        form = AiProviderFormPage(page)
        page.on("dialog", lambda dialog: dialog.accept())
        section_header = providers_page.tts_section_header
        combobox = providers_page.tts_default_selector_combobox

        # maxlength="32" with SILENT truncation on the Display Name field
        # (`_surface.md`); "Autotest TTS Probe " is 19 chars, so a 5-digit
        # suffix fits. The model `Name` carries the same suffix so a run never
        # collides with residue a previously-failed run may have left: the
        # option testid is keyed on that `Name`, and two configurations sharing
        # it would make the option locator ambiguous.
        suffix = str(int(time.time()))[-5:]
        transit_display_name = f"Autotest TTS Probe {suffix}"
        transit_model_name = f"tts-1-probe-{suffix}"

        original_default_value = None
        original_default_name = None
        original_total = None
        config_created = False
        default_changed = False
        body_completed = False

        try:
            with allure.step("Step 0a (transit) — Capture the TTS section's pre-existing state"):
                providers_page.navigate()
                providers_page.ensure_project_selected(SEEDED_PROJECT_ID)

                seed_response = providers_page.navigate_and_capture_section_models_response(SECTION_PARAM)
                assert seed_response.status == 200, f"TTS models request failed: {seed_response.status}"
                seed_body = seed_response.json()
                original_total = seed_body["total"]
                assert original_total >= 1, (
                    "The TTS section holds NO configurations, so it is hidden by design and there is no "
                    "pre-existing default for the case to move away from (AFS ELITEA-2407 § Preconditions)."
                )
                original_default_name = seed_body.get("default_model_name")
                assert original_default_name, (
                    "The project's Default TTS model is UNSET. The selector offers no blank option, so this "
                    "test could not restore that state after assigning one — refusing to mutate shared "
                    "project configuration (AFS ELITEA-2407 § Preconditions)."
                )
                original_default_value = (
                    f"{original_default_name}<<>>{seed_body['default_model_project_id']}"
                )
                original_label = next(
                    (
                        i["display_name"]
                        for i in seed_body["items"]
                        if _option_value(i) == original_default_value
                    ),
                    None,
                )
                assert original_label, (
                    f"The reported default {original_default_value!r} is not among the TTS section's own items"
                )
                logger.info(
                    "TTS baseline: %s configuration(s), default=%r (%s)",
                    original_total,
                    original_label,
                    original_default_value,
                )

            with allure.step(f"Step 0b (transit) — Create a second TTS configuration {transit_display_name!r}"):
                # A direct route to the create form: it skips the "+" type
                # picker, whose own React "unique key" console error (#656) is
                # unrelated to this case.
                form.navigate_to_create("tts_model")
                # Settle on a SCHEMA-rendered field before typing: the form
                # renders `toolkit-field-label-input` in its PRE-schema pass
                # too, so the schema re-render can wipe an already-typed value
                # (`_surface.md`, measured on ELITEA-2399).
                form.wait_for_schema_field("name")
                form.set_display_name(transit_display_name)
                form.set_schema_field("name", transit_model_name)
                form.select_saved_credential(CREDENTIAL_TITLE)
                # Both teardown guards set IMMEDIATELY BEFORE the mutation they
                # guard (`.agents/testing.md` § Teardown-guard ordering): the
                # save both creates the configuration AND makes it the section
                # default. A flag set afterwards would leave a window in which a
                # failure skips the restore while the damage is already done.
                config_created = True
                default_changed = True
                form.save_and_return_to_list()

            with allure.step("Step 0c (transit) — Put the pre-existing default back so step 3 is a real change"):
                after_create = providers_page.navigate_and_capture_section_models_response(SECTION_PARAM)
                assert after_create.status == 200, f"TTS models request failed: {after_create.status}"
                after_body = after_create.json()
                assert after_body["total"] == original_total + 1, (
                    f"The transit configuration was not created: TTS total is {after_body['total']}, "
                    f"expected {original_total + 1}"
                )
                # Read the PERSISTED default back rather than assuming the
                # create moved it — and re-select only if it did: re-selecting
                # an already-selected option fires no request at all and would
                # hang the full timeout.
                if after_body["default_model_name"] != original_default_name:
                    providers_page.isolate_section(section_header)
                    providers_page.select_default_configuration(combobox, original_default_value)
                    expect(combobox).to_have_text(original_label)
                default_changed = False

            with allure.step("Step 1 — Open Settings -> AI Providers and expand the TTS section"):
                console_errors = collect_console_errors(page)
                response = providers_page.navigate_and_capture_section_models_response(SECTION_PARAM)
                assert response.status == 200, f"TTS models request failed: {response.status}"
                body = response.json()
                items = body["items"]
                total = body["total"]
                assert total >= 2, (
                    f"The TTS section holds {total} configuration(s); the case needs a DIFFERENT one to "
                    f"select, which the transit create was supposed to provide."
                )
                assert body["default_model_name"] == original_default_name, (
                    f"Setup did not restore the pre-existing default: {body['default_model_name']!r} != "
                    f"{original_default_name!r} — the case's step 3 would not be a real change"
                )
                target_item = next((i for i in items if i["display_name"] == transit_display_name), None)
                assert target_item, (
                    f"The transit configuration {transit_display_name!r} is not offered by the Default selector"
                )
                target_value = _option_value(target_item)

                expect(section_header).to_be_visible()
                expect(section_header).to_have_attribute("aria-expanded", "false")
                # Isolate, not merely expand: the section testid sits on the
                # accordion SUMMARY BUTTON, so cards are not its DOM descendants
                # and a whole-page card query mixes in every other expanded
                # section's cards.
                providers_page.isolate_section(section_header)
                expect(section_header).to_have_attribute("aria-expanded", "true")

            with allure.step(f"Step 2 — Note the currently selected default TTS model ({original_label!r})"):
                expect(combobox).to_have_text(original_label)
                expect(providers_page.card_tier_badge(original_label, "Default")).to_be_visible()
                # Axis 2 — the default is EXCLUSIVE. The case checks the gain
                # (step 5) and the loss (step 6) but never that no THIRD card
                # claims it; "exactly one" is the invariant that catches a
                # badge-keying regression (the defect class behind #1987).
                expect(providers_page.all_default_badges).to_have_count(1)

            with allure.step("Step 3 — Open the Default TTS model dropdown and select a different model"):
                combobox.click()
                expect(providers_page.open_select_options).to_have_count(total)
                expect(providers_page.select_option(original_default_value)).to_have_attribute(
                    "aria-selected", "true"
                )
                expect(providers_page.select_option(target_value)).to_be_visible()
                providers_page.close_open_dropdown()

                logger.info("Default before: %r; selecting %r", original_default_value, target_value)
                default_changed = True
                set_default_response = providers_page.select_default_configuration(combobox, target_value)
                # Axis 2 — steps 4-6 are all DOM reads; a purely optimistic UI
                # update would satisfy every one of them while the server
                # rejected the change. This is the product's own response.
                assert set_default_response.status == 200, (
                    f"Set-default request failed: {set_default_response.status}"
                )

            with allure.step(f"Step 4 — The selector updates to {transit_display_name!r}"):
                expect(combobox).to_have_text(transit_display_name)

            with allure.step(f"Step 5 — The card for {transit_display_name!r} gains the Default badge"):
                expect(providers_page.card_tier_badge(transit_display_name, "Default")).to_be_visible()

            with allure.step(f"Step 6 — The previously default card ({original_label!r}) loses its badge"):
                expect(providers_page.card_badges(original_label)).to_have_count(0)
                expect(providers_page.all_default_badges).to_have_count(1)

            with allure.step("Axis 2 — No console errors before teardown"):
                # Asserted BEFORE the delete: the app re-fetches the deleted
                # record afterwards and logs a 404 (a real duplicate of the open
                # #1666, recorded there rather than re-filed). No filter is
                # added for it — steps 1-6 are clean, and a filter that swallowed
                # that 404 would also swallow a real one.
                # Known defect: #1971 — the project-id-less `toolkitTypes` 404
                # the project switch triggers. URL-keyed and opt-in.
                unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
                assert not unexpected, f"Unexpected console errors: {unexpected}"

            body_completed = True
        finally:
            # Order 1-before-2 is load-bearing, not stylistic: deleting a
            # configuration the project default still points at leaves the
            # project pointing at something gone.
            if default_changed and original_default_value:
                restored = restore_section_default_if_moved(
                    providers_page, SECTION_PARAM, section_header, combobox, original_default_value
                )
                default_changed = False
                if body_completed:
                    assert restored == original_default_name, (
                        f"The TTS default was NOT restored: {restored!r} != {original_default_name!r} — "
                        f"shared project state left altered"
                    )
                elif restored != original_default_name:
                    logger.error(
                        "Teardown left the TTS default at %r instead of %r", restored, original_default_name
                    )

            if config_created:
                final_count = delete_configurations_if_present(
                    providers_page, form, section_header, [transit_display_name]
                )
                if body_completed:
                    assert final_count == original_total, (
                        f"The TTS section was not left as found: {final_count} card(s), expected "
                        f"{original_total} — teardown could not delete the transit configuration"
                    )
