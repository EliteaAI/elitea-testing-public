"""UI test — Create a new Embedding Model configuration (Settings -> AI Providers).

Test case: ELITEA-2398
AFS: test-specs/settings-ai-providers/l3_create-embedding-model-configuration_ELITEA-2398.md

Case-identity note (reused from ELITEA-2392, filed as
EliteaAI/elitea-testing-public#1250): "Settings -> AI Configuration" does not
exist. The real page is "AI Providers" (`/settings/ai-providers`), whose
**Embedding Models** accordion this case exercises; the type-picker card is
labelled "Embedding model" (lowercase `m`). Not re-filed.

No substitution of the system under test: the configuration is created through
the real "+" -> Embedding model -> Save flow, and every observable (the card,
its status text, the Default selector's option list) is produced by the
product. The only API involvement is READING the product's own
`section=embedding` models response as an oracle for the ACTIVE PROJECT ID —
never fabricating any asserted value. The project id matters: the Default
selector keys its options `{model_name}<<>>{project_id}`, and this case's model
`name` deliberately duplicates an existing SHARED model (project 1), so a
project-scoped option testid is the only one that proves the NEW record rather
than passing vacuously on the shared one (`_surface.md`).

**This test MUTATES shared, live project configuration**: it creates a real
Embedding Model configuration, deleted in a `finally`. Deletion is safe here —
the Embedding Models section carries 3 SHARED configurations, so the created
one is never "last in section" (`CredentialsControls.jsx`'s `isLastInSection`
guard, which makes the same cleanup impossible for Vector Storage).

The project's own Default embedding model is deliberately NOT changed: step 9
asserts option INCLUSION only, as the case asks, and the dropdown is dismissed
with Escape.

Markers:
    - ui, settings, p2 (this suite's l3 -> p2, matching the sibling
      ELITEA-2392 / ELITEA-2395 / ELITEA-2397 tests), regression, new
"""

import logging
import re
import time

import allure
import pytest
from pages.ai_provider_form_page import AiProviderFormPage
from pages.ai_providers_page import AIProvidersPage, project_id_from_models_response
from playwright.sync_api import expect
from utils.ai_provider_teardown import delete_configurations_if_present
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

#: The case's own model identifier. It duplicates an existing SHARED embedding
#: model's name by design — see the module docstring on why that is safe.
MODEL_NAME = "text-embedding-3-small"
#: `elitea_title` of the shared AI credential present in every non-public
#: project (displayed label "ELPS") — picked by title, never by list position.
CREDENTIAL_TITLE = "elps"
CREDENTIAL_LABEL = "ELPS"

CREATE_PICKER_URL_PATTERN = re.compile(r"/settings/create-ai-provider(\?|$)")
CREATE_EMBEDDING_FORM_URL_PATTERN = re.compile(r"/settings/create-ai-provider/embedding_model")


def _slug(display_name: str) -> str:
    """The read-only ID the form derives from *display_name* (lowercase,
    underscore-separated — live contract, pinned by ELITEA-2409)."""
    return display_name.lower().replace(" ", "_")


class TestCreateEmbeddingModelConfiguration:
    """ELITEA-2398 — create an Embedding Model configuration."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2398.md",
        "onetest-ai Test Case link",
    )
    def test_create_embedding_model_configuration(self, page):
        """Create an Embedding Model through the UI, verify its card appears in
        the Embedding Models section with an OK status, and verify the section's
        Default selector offers it — without reassigning the project default."""
        providers_page = AIProvidersPage(page)
        form = AiProviderFormPage(page)
        page.on("dialog", lambda dialog: dialog.accept())

        # `toolkit-field-label-input` carries maxlength="32" and truncates
        # SILENTLY, so the per-run suffix is trimmed to keep the whole name
        # inside the limit ("Autotest Embedding Model " = 25 + 5 = 30).
        suffix = str(int(time.time()))[-5:]
        display_name = f"Autotest Embedding Model {suffix}"
        initial_card_count = None
        body_completed = False

        try:
            with allure.step("Step 1 — Open Settings -> AI Providers and capture the Embedding baseline"):
                response = providers_page.navigate_and_capture_section_models_response("embedding")
                assert response.status == 200, f"Embedding models request failed: {response.status}"
                project_id = project_id_from_models_response(response)
                logger.info("Active project id (from the product's own request): %s", project_id)

                expect(providers_page.page_title).to_have_text("AI Providers")
                expect(providers_page.embedding_models_section_header).to_be_visible()
                providers_page.isolate_section(providers_page.embedding_models_section_header)
                initial_card_count = providers_page.get_configuration_card_count()
                # The section's current Default, as the product renders it —
                # captured so step 9 can prove creation did not reassign it.
                initial_default_label = providers_page.embedding_models_default_selector_combobox.text_content()
                logger.info("Baseline: %s cards, Default=%r", initial_card_count, initial_default_label)

            with allure.step("Step 2 — Click '+' in the AI Providers header"):
                providers_page.click_create()
                expect(page).to_have_url(CREATE_PICKER_URL_PATTERN)

            with allure.step("Step 3 — Select the 'Embedding model' provider type"):
                providers_page.click_type_card("embedding_model")
                form.wait_for_form()
                # Settle on the SCHEMA render, not merely the shell — the
                # re-render that follows the schema GET wipes anything typed
                # in the gap (`_surface.md`).
                form.wait_for_schema_field("name")
                expect(page).to_have_url(CREATE_EMBEDDING_FORM_URL_PATTERN)
                # Console axis scoped to the create form and everything after
                # it; the type-picker page's own React "unique key" error
                # (#656) belongs to that page, not to this case's subject.
                console_errors = collect_console_errors(page)
                expect(form.save_button).to_be_disabled()

            with allure.step(f"Steps 4-5 — Fill Display Name {display_name!r}"):
                form.set_display_name(display_name)
                expect(form.display_name_input).to_have_value(display_name)
                # Axis 2 — the read-only auto-derived ID contract (ELITEA-2409
                # pinned it for llm_model; asserting it here proves it is
                # form-wide rather than type-specific).
                expect(form.id_input).to_have_value(_slug(display_name))
                expect(form.id_input).to_be_disabled()

            with allure.step(f"Step 6a — Fill Name (model identifier) {MODEL_NAME!r}"):
                form.set_schema_field("name", MODEL_NAME)
                expect(form.field("name")).to_have_value(MODEL_NAME)
                # Axis 2 — the credential is the last required gate. Without
                # this before-state, "Save is enabled" proves nothing about the
                # form knowing the record is complete.
                expect(form.save_button).to_be_disabled()

            with allure.step(f"Step 6b — Select the saved AI credential {CREDENTIAL_LABEL!r}"):
                form.select_saved_credential(CREDENTIAL_TITLE)
                expect(form.credential_select_combobox).to_have_text(CREDENTIAL_LABEL)
                expect(form.save_button).to_be_enabled()

            with allure.step("Step 7 — Save; the app returns to the AI Providers list"):
                form.save_and_return_to_list()
                expect(providers_page.embedding_models_section_header).to_be_visible()
                providers_page.isolate_section(providers_page.embedding_models_section_header)

            with allure.step("Step 8 — The new card is in the Embedding Models section"):
                # Axis 2 — a CREATE, not a silent overwrite of the same-named
                # shared model: the name deliberately collides, so identity has
                # to be proven rather than assumed.
                expect(providers_page.configuration_cards).to_have_count(initial_card_count + 1)
                card = providers_page.card_for_model(display_name)
                expect(card).to_be_visible()
                expect(card).to_contain_text("OK •")

            with allure.step("Step 9 — The Default embedding model dropdown offers the new model"):
                # Axis 2 — creation must not silently reassign the project's
                # Default embedding model.
                expect(providers_page.embedding_models_default_selector_combobox).to_have_text(initial_default_label)

                providers_page.embedding_models_default_selector_combobox.click()
                # Project-scoped on purpose: `select-option-text-embedding-3-small<<>>1`
                # (the shared model) and `...<<>>{project_id}` (this one) coexist.
                option = providers_page.select_option(f"{MODEL_NAME}<<>>{project_id}")
                expect(option).to_be_visible()
                # In this section the option is LABELLED with the Display Name
                # while it is KEYED by the model identifier.
                expect(option).to_have_text(display_name)
                expect(option).to_have_attribute("aria-selected", "false")
                providers_page.close_open_dropdown()

            with allure.step("Axis 2 — No console errors before teardown"):
                # Asserted BEFORE the delete: the app re-fetches the deleted
                # record afterwards and logs a 404 (AFS § Cleanup).
                # Known defect: #1971 — project-id-less toolkitTypes 404.
                unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
                assert not unexpected, f"Unexpected console errors: {unexpected}"

            body_completed = True
        finally:
            final_count = delete_configurations_if_present(
                providers_page, form, providers_page.embedding_models_section_header, [display_name]
            )
            if body_completed and final_count is not None and initial_card_count is not None:
                assert final_count == initial_card_count, (
                    f"Cleanup did not restore the card count: {final_count} != {initial_card_count}"
                )
