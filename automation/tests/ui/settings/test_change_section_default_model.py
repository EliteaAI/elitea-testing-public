"""UI test — change the default Image Generation / ASR model
(Settings -> AI Providers).

Test cases: ELITEA-2403 (Image Generation), ELITEA-2405 (Speech Recognition /
ASR)
AFS: test-specs/settings-ai-providers/l3_change-section-default-model_ELITEA-2403.md

One parameterized test, one row per TMS case: the two cases are identical in
actions, order and assertions and differ only in which section they act on.
The TTS sibling (ELITEA-2407) is deliberately NOT a row here — the TTS section
holds one model live, so its "select a different model" needs a transit create
and a delete teardown these two do not have. Different STEPS, so its own spec
(`test_change_default_tts_model.py`).

Case-identity note (pre-existing, reused from ELITEA-2392, filed as
EliteaAI/elitea-testing-public#1250): both cases say "Settings -> AI
Configuration -> <X> section". There is no such page — the sections live on
"AI Providers" (`/settings/ai-providers`). Asserted as the live contract per
the reverse-masking guard; NOT re-filed. The same clarification covers step 1
landing on a COLLAPSED accordion (only LLMs auto-expands, and the accordion's
content — including the real Default combobox — unmounts while collapsed), so
the expand is folded into step 1 below.

**This test MUTATES shared, live project configuration.** Selecting an option
persists immediately (`POST /configurations/models/{project_id}` -> 200; there
is no Save button and no confirmation), and the section's Default model is
project-level state every other user and every later spec reads. The default is
reassigned and restored, and the restore is ASSERTED — a green-but-damaging
spec is precisely what an N x green gate cannot catch
(`.agents/testing.md` § Teardown-guard ordering). Nothing is created or deleted.

Fidelity (`.agents/testing.md` § Fidelity policy): nothing is mocked, stubbed,
routed or injected. The section's own `...&section={param}` response is READ as
the oracle for the current default and for the alternative to select — every
asserted value is produced by the product, and no model name is hardcoded (the
model set is shared from project 1 and mutable).

Serial only — these rows mutate project-level state and must not run in
parallel with each other or with any other AI-Providers spec.

Markers:
    - ui, settings, p2 (this suite's l3 -> p2, matching the merged
      ELITEA-2392 / ELITEA-2397 / ELITEA-2401 siblings), regression, new
"""

import logging

import allure
import pytest
from config import settings
from pages.ai_providers_page import AIProvidersPage, pick_alternative_llm_model
from playwright.sync_api import expect
from utils.ai_provider_teardown import restore_section_default_if_moved
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

SEEDED_PROJECT_ID = settings.ai_providers_seeded_project_id

TMS_CASE_URL = (
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/settings/ai-configuration/{}"
)

SECTION_ROWS = [
    pytest.param(
        "ELITEA-2403",
        "Image Generation",
        "image_generation",
        "image_generation_section_header",
        "image_generation_default_selector_combobox",
        "ELITEA-2403_change-the-default-image-generation-model.md",
        id="ELITEA-2403-image-generation",
    ),
    pytest.param(
        "ELITEA-2405",
        "Speech Recognition (ASR)",
        "asr",
        "asr_section_header",
        "asr_default_selector_combobox",
        "ELITEA-2405_change-the-default-asr-model.md",
        id="ELITEA-2405-asr",
    ),
]


def _option_value(item: dict) -> str:
    """The Default-selector option value the product builds for *item*
    (``"{name}<<>>{project_id}"`` — the model's OWN project id, not the active
    one: these models are shared from project 1)."""
    return f"{item['name']}<<>>{item['project_id']}"


class TestChangeSectionDefaultModel:
    """ELITEA-2403 / 2405 — reassign a section's default model and verify the
    selector and both cards' Default badges follow."""

    @pytest.mark.parametrize(
        "tms_id, section_label, section_param, header_field, combobox_field, case_file", SECTION_ROWS
    )
    def test_change_section_default_model(
        self, page, tms_id, section_label, section_param, header_field, combobox_field, case_file
    ):
        """Select a different default model for the section and verify the
        change persists, the selector updates, the new card gains the Default
        badge and the previous card loses it."""
        allure.dynamic.issue(TMS_CASE_URL.format(case_file), f"onetest-ai Test Case {tms_id}")
        allure.dynamic.issue(
            "https://github.com/EliteaAI/elitea-testing-public/issues/1250",
            "Case-text clarification #1250",
        )
        providers_page = AIProvidersPage(page)
        section_header = getattr(providers_page, header_field)
        combobox = getattr(providers_page, combobox_field)

        original_default_value = None
        original_default_name = None
        default_changed = False
        body_completed = False

        try:
            with allure.step(f"Step 1 — Open Settings -> AI Providers and expand the {section_label} section"):
                providers_page.navigate()
                providers_page.ensure_project_selected(SEEDED_PROJECT_ID)
                console_errors = collect_console_errors(page)

                response = providers_page.navigate_and_capture_section_models_response(section_param)
                assert response.status == 200, f"{section_label} models request failed: {response.status}"
                body = response.json()
                items = body["items"]
                total = body["total"]
                # The case's real precondition: without a SECOND configuration
                # its step 3 ("select a different model") is a no-op and the
                # whole case passes vacuously.
                assert total >= 2, (
                    f"The {section_label} section holds {total} configuration(s); the case needs a DIFFERENT "
                    f"one to select (AFS ELITEA-2403 § Preconditions)."
                )
                original_default_name = body.get("default_model_name")
                assert original_default_name, (
                    f"The project's Default {section_label} model is UNSET. The selector offers no blank "
                    f"option, so this test could not restore that state after assigning one — refusing to "
                    f"mutate shared project configuration (AFS ELITEA-2403 § Preconditions)."
                )
                original_default_value = f"{original_default_name}<<>>{body['default_model_project_id']}"
                original_label = next(
                    (i["display_name"] for i in items if _option_value(i) == original_default_value), None
                )
                assert original_label, (
                    f"The reported default {original_default_value!r} is not among the section's own items"
                )

                expect(section_header).to_be_visible()
                expect(section_header).to_have_attribute("aria-expanded", "false")
                # Isolate, not merely expand: the section testid sits on the
                # accordion SUMMARY BUTTON, so cards are not its DOM descendants
                # and a whole-page card query mixes in every other expanded
                # section's cards.
                providers_page.isolate_section(section_header)
                expect(section_header).to_have_attribute("aria-expanded", "true")

            with allure.step(f"Step 2 — Note the currently selected default model ({original_label!r})"):
                expect(combobox).to_have_text(original_label)
                expect(providers_page.card_tier_badge(original_label, "Default")).to_be_visible()
                # Axis 2 — the default is EXCLUSIVE. The case checks the gain
                # (step 5) and the loss (step 6) but never that no THIRD card
                # claims it; "exactly one" is the invariant that catches a
                # badge-keying regression (the defect class behind #1987).
                expect(providers_page.all_default_badges).to_have_count(1)

            with allure.step("Step 3 — Open the Default dropdown and select a different model"):
                target_item = pick_alternative_llm_model(items, original_default_value)
                target_value = _option_value(target_item)
                target_label = target_item["display_name"]

                combobox.click()
                expect(providers_page.open_select_options).to_have_count(total)
                expect(providers_page.select_option(original_default_value)).to_have_attribute(
                    "aria-selected", "true"
                )
                providers_page.close_open_dropdown()

                logger.info("Default before: %r; selecting %r", original_default_value, target_value)
                # Teardown guard set IMMEDIATELY BEFORE the mutation it guards
                # (`.agents/testing.md` § Teardown-guard ordering) — the window
                # between "the POST fired" and "the flag says it did" is a
                # window in which a failure skips the restore while the damage
                # is already done.
                default_changed = True
                set_default_response = providers_page.select_default_configuration(combobox, target_value)
                # Axis 2 — steps 4-6 are all DOM reads; a purely optimistic UI
                # update would satisfy every one of them while the server
                # rejected the change. This is the product's own response.
                assert set_default_response.status == 200, (
                    f"Set-default request failed: {set_default_response.status}"
                )

            with allure.step(f"Step 4 — The selector updates to {target_label!r}"):
                expect(combobox).to_have_text(target_label)

            with allure.step(f"Step 5 — The card for {target_label!r} gains the Default badge"):
                expect(providers_page.card_tier_badge(target_label, "Default")).to_be_visible()

            with allure.step(f"Step 6 — The previously default card ({original_label!r}) loses its badge"):
                expect(providers_page.card_badges(original_label)).to_have_count(0)
                # Axis 2 — still exactly one, now on the other card.
                expect(providers_page.all_default_badges).to_have_count(1)

            with allure.step("Axis 2 — No console errors across the flow"):
                # Known defect: #1971 — the project-id-less `toolkitTypes` 404
                # the project switch triggers. URL-keyed and opt-in.
                unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
                assert not unexpected, f"Unexpected console errors: {unexpected}"

            body_completed = True
        finally:
            if default_changed and original_default_value:
                restored = restore_section_default_if_moved(
                    providers_page, section_param, section_header, combobox, original_default_value
                )
                default_changed = False
                if body_completed:
                    # The restore is an assertion, not a hope — a spec that
                    # leaves the project's default moved still reports green.
                    assert restored == original_default_name, (
                        f"The {section_label} default was NOT restored: {restored!r} != "
                        f"{original_default_name!r} — shared project state left altered"
                    )
                elif restored != original_default_name:
                    logger.error(
                        "Teardown left the %s default at %r instead of %r",
                        section_label,
                        restored,
                        original_default_name,
                    )
