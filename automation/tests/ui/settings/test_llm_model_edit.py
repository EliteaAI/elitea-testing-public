"""UI test — Edit an existing LLM model configuration (Settings -> AI Providers).

Test cases: ELITEA-2396, ELITEA-2413 (extension — the edit survives a reload)
AFS: test-specs/settings-ai-providers/l3_edit-llm-model-configuration_ELITEA-2396.md
AFS: test-specs/settings-ai-providers/lextend_edited-llm-model-name-persists-after-reload_ELITEA-2413.md

ELITEA-2413 (`extend-existing`) adds Step 7. Its steps 1-2 (open an existing
card, change the Display Name, Save) are this spec's Steps 2-5 exactly, and its
step-4 in-section verification is this spec's Step 6 — but read inside the SPA
session that made the edit, so persistence was never proven. The extension is
one real `page.reload()` plus a cold re-read. Its case-text literal "Reload Test
Model" is deliberately NOT used: this spec's per-run generated names are kept
(`toolkit-field-label-input` carries `maxlength="32"` and a fixed literal
collides with leftovers from a failed run) — declared deviation, AFS § Test Data.

Case-identity note (reused from ELITEA-2392, filed as
EliteaAI/elitea-testing-public#1250): "Settings -> AI Configuration -> LLM
Models section" is Settings -> **AI Providers** (`/settings/ai-providers`) ->
the **LLMs** accordion. Not re-filed here.

Declared deviation (AFS § Preconditions): the case says "click on ANY existing
LLM model card". This test edits a model **it created itself** in Setup.
Renaming a shared, live model (e.g. the project Default) would alter what every
other UI test in this suite reads; the behaviour under test — editing an
existing configuration — is identical, and a self-created subject makes the
case safely repeatable.

No substitution of the system under test: the seed model is created through the
real UI create form (transit only — reaching the state the case's step 1
assumes), and the case's own observable, the renamed card in the LLMs section,
is produced entirely by the product. Nothing is mocked, injected or fabricated.

Mutation: one configuration is created and, at the end, deleted in a `finally`
under whichever name is currently live, so a failure between the rename and the
verification still tears down.

Markers:
    - ui, settings, p2 (this suite's l3 -> p2, matching the sibling
      ELITEA-2392 / ELITEA-2397 tests), regression, new
"""

import logging
import re
import time

import allure
import pytest
from pages.ai_provider_form_page import AiProviderFormPage
from pages.ai_providers_page import AIProvidersPage
from playwright.sync_api import expect
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

MODEL_NAME = "gpt-4o"
CREDENTIAL_TITLE = "elps"
CREDENTIAL_LABEL = "ELPS"
DEFAULT_CONTEXT_WINDOW = "128000"
DEFAULT_MAX_OUTPUT_TOKENS = "16000"

#: The LLMs group a custom (non-OpenAI/Anthropic) model lands in — the rename
#: must not move it (ELITEA-2413 Axis 2).
OTHER_PROVIDERS_GROUP = "Other Providers"

EDIT_URL_PATTERN = re.compile(r"/settings/edit-ai-provider/\d+")


def _slug(display_name: str) -> str:
    """The read-only ID the form derives from *display_name* (lowercase,
    underscore-separated — live contract, see ELITEA-2409)."""
    return display_name.lower().replace(" ", "_")


class TestEditLlmModelConfiguration:
    """ELITEA-2396 — edit an existing LLM model configuration in place."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2396.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ai-configuration/ELITEA-2413_editing-an-existing-configuration-persists-after-page-reload.md",
        "onetest-ai Test Case link (ELITEA-2413)",
    )
    def test_edit_llm_model_display_name(self, page):
        """Open an existing LLM model card, verify the edit form is
        pre-populated and inert while pristine, rename it, verify the LLMs
        section reflects the new name in place (no duplicate, no orphan), and
        verify the rename survives a full page reload (ELITEA-2413)."""
        providers_page = AIProvidersPage(page)
        form = AiProviderFormPage(page)
        page.on("dialog", lambda dialog: dialog.accept())

        # `toolkit-field-label-input` carries maxlength="32" (ToolBase.jsx's
        # MAX_NAME_LENGTH) — the field silently truncates beyond it, so the
        # per-run suffix is trimmed to keep the LONGER of the two names
        # ("Autotest LLM Model Edited " = 26 chars) inside the limit.
        suffix = str(int(time.time()))[-5:]
        seed_display_name = f"Autotest LLM Model {suffix}"
        edited_display_name = f"Autotest LLM Model Edited {suffix}"
        live_display_name = seed_display_name
        initial_card_count = None
        body_completed = False

        try:
            with allure.step(f"Step 0 (Setup) — Create the seed model {seed_display_name!r} through the UI"):
                providers_page.navigate()
                expect(providers_page.llms_section_header).to_be_visible()
                initial_card_count = providers_page.get_configuration_card_count()

                # Transit only: a direct route to the create form (skips the
                # type picker, whose own React "unique key" console error #656
                # is unrelated to this case).
                form.navigate_to_create("llm_model")
                form.set_display_name(seed_display_name)
                form.type_into_field("name", MODEL_NAME)
                form.select_saved_credential(CREDENTIAL_TITLE)
                form.save_and_return_to_list()
                expect(providers_page.card_for_model(seed_display_name)).to_have_count(1)
                seeded_card_count = providers_page.get_configuration_card_count()
                assert seeded_card_count == initial_card_count + 1, (
                    f"Seed did not add exactly one card: {seeded_card_count} vs {initial_card_count}"
                )

            with allure.step("Step 1 — The LLMs section is rendered and holds the seed card"):
                expect(providers_page.llms_section_header).to_be_visible()
                expect(providers_page.card_for_model(seed_display_name)).to_be_visible()
                console_errors = collect_console_errors(page)

            with allure.step("Step 2 — Click the model's card; its edit form opens"):
                providers_page.open_model_card(seed_display_name)
                form.wait_for_form()
                expect(page).to_have_url(EDIT_URL_PATTERN)
                logger.info("Editing configuration id %s", form.configuration_id_from_url())

            with allure.step("Step 3 — The edit form is pre-populated and inert while pristine"):
                expect(form.display_name_input).to_have_value(seed_display_name)
                expect(form.id_input).to_have_value(_slug(seed_display_name))
                expect(form.id_input).to_be_disabled()
                expect(form.field("name")).to_have_value(MODEL_NAME)
                expect(form.field("context_window")).to_have_value(DEFAULT_CONTEXT_WINDOW)
                expect(form.field("max_output_tokens")).to_have_value(DEFAULT_MAX_OUTPUT_TOKENS)
                expect(form.credential_select_combobox).to_have_text(CREDENTIAL_LABEL)
                # Axis 2 — the dirty-state contract. Step 5 is meaningless if
                # Save was clickable all along.
                expect(form.save_button).to_be_disabled()
                expect(form.discard_button).to_be_disabled()

            with allure.step(f"Step 4 — Change the Display Name to {edited_display_name!r}"):
                form.set_display_name(edited_display_name)
                live_display_name = edited_display_name
                expect(form.display_name_input).to_have_value(edited_display_name)
                expect(form.save_button).to_be_enabled()
                expect(form.discard_button).to_be_enabled()
                # Live behaviour (AFS § Known Defects, observation not filed):
                # the disabled ID field re-derives from the new label.
                expect(form.id_input).to_have_value(_slug(edited_display_name))

            with allure.step("Step 5 — Click Save; the app returns to the AI Providers list"):
                form.save_and_return_to_list()
                expect(providers_page.llms_section_header).to_be_visible()

            with allure.step("Step 6 — The LLMs section reflects the updated Display Name in place"):
                expect(providers_page.card_for_model(edited_display_name)).to_have_count(1)
                # Axis 2 — an UPDATE, not a create-and-orphan: the old name is
                # gone and the section did not grow.
                expect(providers_page.card_for_model(seed_display_name)).to_have_count(0)
                expect(providers_page.configuration_cards).to_have_count(initial_card_count + 1)

            with allure.step("Step 7 (ELITEA-2413) — The rename survives a full page reload"):
                # ELITEA-2413's own subject: proof the write reached the SERVER,
                # not just the client's re-render of its own mutation response.
                # Every assertion above runs inside the SPA session that made the
                # edit, so a write the server accepted and silently dropped would
                # still go green.
                reload_response = providers_page.reload_and_capture_llm_response()
                assert reload_response.status == 200, (
                    f"LLM models request after reload failed: {reload_response.status}"
                )
                # Accordion content UNMOUNTS on collapse — a collapsed LLMs
                # section reads as "the card is missing" (AFS § Automation Hints).
                expect(providers_page.llms_section_header).to_have_attribute(
                    "aria-expanded", "true", timeout=UI_ELEMENT_TIMEOUT
                )
                expect(providers_page.card_for_model(edited_display_name)).to_have_count(1)
                # Axis 2 — the case's own parenthetical, "(not the previous
                # name)": a server that persisted a COPY under the new name
                # while leaving the original row intact would pass a bare
                # presence check. The unchanged total catches the same failure
                # from the other side (rename implemented as create).
                expect(providers_page.card_for_model(seed_display_name)).to_have_count(0)
                expect(providers_page.configuration_cards).to_have_count(initial_card_count + 1)
                # Axis 2 — a rename must not disturb the server-derived provider
                # grouping or the credential link; both are re-derived from the
                # server on reload, so this is exactly what a cold read can check
                # and an in-session re-render cannot.
                expect(providers_page.card_in_group(OTHER_PROVIDERS_GROUP, edited_display_name)).to_have_count(1)
                expect(providers_page.card_for_model(edited_display_name)).to_contain_text("OK •")

            with allure.step("Axis 2 — No console errors before teardown"):
                # Asserted BEFORE the delete: the app re-fetches the deleted
                # record afterwards and logs a 404 (AFS ELITEA-2395).
                # Known defect: #1971 — project-id-less toolkitTypes 404.
                unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
                assert not unexpected, f"Unexpected console errors: {unexpected}"

            body_completed = True
        finally:
            # Look the name up rather than assume which of the two is live, so
            # a failure between steps 4 and 6 still tears down.
            final_count = _delete_model_if_present(
                providers_page, form, [live_display_name, seed_display_name, edited_display_name]
            )
            if body_completed and final_count is not None and initial_card_count is not None:
                assert final_count == initial_card_count, (
                    f"Cleanup did not restore the LLMs card count: {final_count} != {initial_card_count}"
                )


def _delete_model_if_present(providers_page: AIProvidersPage, form: AiProviderFormPage, candidate_names: list[str]):
    """Delete whichever of *candidate_names* is currently on the AI Providers
    list, and return the resulting card count (``None`` if teardown failed)."""
    try:
        providers_page.navigate()
        providers_page.llms_section_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        for name in dict.fromkeys(candidate_names):
            if providers_page.card_for_model(name).count() == 0:
                continue
            providers_page.open_model_card(name)
            form.wait_for_form()
            form.delete_current_configuration(name)
            providers_page.navigate()
            providers_page.llms_section_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            expect(providers_page.card_for_model(name)).to_have_count(0)
        return providers_page.get_configuration_card_count()
    except Exception:  # noqa: BLE001 - teardown must never mask the test's own failure
        logger.exception("Teardown failed to delete the configuration(s) %r", candidate_names)
        return None
