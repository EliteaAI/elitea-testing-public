"""UI test — Create Embedding Model: required fields must gate Save.

Test case: ELITEA-2410
AFS: test-specs/settings-ai-providers/l3_create-embedding-model-required-field-validation_ELITEA-2410.md

Case-identity note (reused from ELITEA-2392, filed as
EliteaAI/elitea-testing-public#1250): "Settings -> AI Configuration" does not
exist; the real page is "AI Providers" (`/settings/ai-providers`), whose "+"
control opens the type picker this case's step 1 walks through. The card is
labelled "Embedding model". Not re-filed.

**This spec is SANCTIONED-RED on EliteaAI/elitea-testing-public#1984.**
The case is right and the product is wrong. `Name` (the model identifier) is
declared required by the toolkit schema and rendered with the required
asterisk, but `validateRequiredFields` (`toolBase.helpers.js:146`) walks only
the TOP-LEVEL `schema.required` and never the nested `data.required` — so Save
stays enabled with `Name` empty and the configuration is actually created. Per
`.agents/testing.md` § Merge gate (*Analysis-time entry*), the correct expected
behaviour is asserted with `expect.soft()` + a `# Known defect: #1984` comment:
the Display-Name half (which works today) keeps reporting, and the Name half
flips green the day the product is fixed. Nothing is weakened, skipped or
masked.

#1984 was filed against `llm_model` (ELITEA-2408 is its sanctioned-RED spec).
The embedding form is the SAME component one `type` path-param apart, so this
is the second SURFACE of one defect, not a second defect — recorded as a
comment on #1984 rather than a duplicate ticket (`.agents/profile.md` § Bug
filing).

A soft-assert failure IS a pytest FAILURE (`.agents/testing.md`, verified
in-venv 2026-08-22), so `test_name_required_gates_save` is expected to FAIL
until #1984 ships. `test_display_name_required_gates_save` is expected to pass.

No substitution of the system under test: every observable — the Save button's
own `disabled` property, the absence of inline helper text, the card count on
the real list page — is produced by the product. Nothing is mocked, injected or
fabricated.

Mutation: while #1984 is open, the Name-half test really does create a
configuration in the shared project. It is deleted in a `finally`, keyed to a
per-run-suffixed Display Name so cleanup can never touch anyone else's record,
and the cleanup tolerates the record being absent (which is what a fixed #1984
would produce). Deletion is safe here — Embedding Models carries 3 SHARED
configurations, so the created one is never "last in section".

Markers:
    - ui, settings, p2 (this suite's l3 -> p2, matching the sibling
      ELITEA-2392 / ELITEA-2408 tests), regression, new
"""

import logging
import time

import allure
import pytest
from pages.ai_provider_form_page import AiProviderFormPage
from pages.ai_providers_page import AIProvidersPage
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

MODEL_NAME = "text-embedding-3-small"
#: `elitea_title` of the shared AI credential visible in every non-public
#: project (displayed label "ELPS") — picked by title, never by list position.
CREDENTIAL_TITLE = "elps"


class TestCreateEmbeddingModelRequiredFieldValidation:
    """ELITEA-2410 — an empty required field must disable Save and prevent creation."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2410.md",
        "onetest-ai Test Case link",
    )
    def test_display_name_required_gates_save(self, page):
        """Param A — with Display Name empty (Name + credential filled), Save is
        disabled.

        Walks the gates in order so the assertion cannot pass vacuously: Name
        alone leaves Save disabled, Name + Display Name (still no credential)
        leaves it disabled (Axis 2 — the credential DOES gate Save, i.e. #1984
        is narrow to `name`), adding the credential enables it (Axis 2 —
        positive control), and clearing Display Name disables it again, which
        is the case's own step.
        """
        providers_page = AIProvidersPage(page)
        form = AiProviderFormPage(page)
        page.on("dialog", lambda dialog: dialog.accept())

        with allure.step("Step 1 — Settings -> AI Providers -> '+' -> Embedding model"):
            providers_page.navigate()
            providers_page.click_create()
            providers_page.click_type_card("embedding_model")
            form.wait_for_form()
            # Scoped to the create form on purpose — the type-picker page logs
            # its own already-filed React "unique key" error (#656) which is
            # not this case's subject.
            console_errors = collect_console_errors(page)
            expect(form.save_button).to_be_disabled()

        with allure.step("Step 2A — Fill Name; Display Name and the credential stay empty"):
            form.type_into_field("name", MODEL_NAME)
            expect(form.field("name")).to_have_value(MODEL_NAME)
            expect(form.display_name_input).to_have_value("")
            expect(form.save_button).to_be_disabled()

        with allure.step("Axis 2 — With Display Name AND Name filled but NO credential, Save stays disabled"):
            # Pins that the credential select DOES gate Save on this form, i.e.
            # #1984 is narrow to `name`. Prevents a future over-correcting fix.
            form.set_display_name(f"Autotest Emb 2410 A {str(int(time.time()))[-5:]}")
            expect(form.save_button).to_be_disabled()

        with allure.step("Axis 2 — Positive control: adding the credential enables Save"):
            # Without this, "Save is disabled" would also pass against a form
            # that is simply broken shut.
            form.select_saved_credential(CREDENTIAL_TITLE)
            expect(form.save_button).to_be_enabled()

        with allure.step("Step 3A — Clearing the required Display Name disables Save again"):
            # Clearing goes through real key events; MUI does not commit React
            # onChange on a bare fill("") (`.claude/rules/mui-patterns.md`).
            form.clear_display_name()
            expect(form.display_name_input).to_have_value("")
            expect(form.save_button).to_be_disabled()
            # The auto-derived ID is cleared with it — asserted as the live
            # contract rather than a stale pre-clear value.
            expect(form.id_input).to_have_value("")

        with allure.step("Axis 2 — No console errors on the create form"):
            # Known defect: #1971 — project-id-less toolkitTypes 404, unrelated.
            unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
            assert not unexpected, f"Unexpected console errors on the create form: {unexpected}"

        # Nothing was saved — navigating away discards the form (the dialog
        # handler above accepts the beforeunload prompt).

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2410.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1984", "Known defect #1984")
    def test_name_required_gates_save(self, page):
        """Param B — with Name empty (Display Name + credential filled), Save
        must be disabled and no configuration may be created.

        SANCTIONED-RED on #1984: today Save is enabled and the configuration IS
        created. Both assertions are soft so the whole signature is reported in
        one run instead of stopping at the first.
        """
        providers_page = AIProvidersPage(page)
        form = AiProviderFormPage(page)
        page.on("dialog", lambda dialog: dialog.accept())

        # maxlength="32", silent truncation — "Autotest Emb 2410 B " is 20.
        display_name = f"Autotest Emb 2410 B {str(int(time.time()))[-5:]}"
        initial_card_count = None
        body_completed = False

        try:
            with allure.step("Step 1 — Settings -> AI Providers -> '+' -> Embedding model (fresh form)"):
                providers_page.navigate()
                expect(providers_page.embedding_models_section_header).to_be_visible()
                providers_page.expand_section(providers_page.embedding_models_section_header)
                initial_card_count = providers_page.get_configuration_card_count()
                logger.info("Card count before the attempted create: %s", initial_card_count)

                providers_page.click_create()
                providers_page.click_type_card("embedding_model")
                form.wait_for_form()
                console_errors = collect_console_errors(page)

            with allure.step("Step 2B — Fill Display Name and the credential; leave Name EMPTY"):
                form.set_display_name(display_name)
                form.select_saved_credential(CREDENTIAL_TITLE)
                expect(form.display_name_input).to_have_value(display_name)
                expect(form.field("name")).to_have_value("")

            with allure.step("Step 3B — Save must be disabled while the required Name is empty"):
                # Known defect: #1984 — Save is currently ENABLED. Asserted as
                # the CORRECT expected behaviour, softly, so the rest of the
                # case still runs. Do not weaken it.
                expect.soft(form.save_button).to_be_disabled()

            with allure.step("Axis 2 — There is no inline validation on the empty Name field either"):
                # Records the current absence of inline feedback so #1984's fix
                # can be judged complete rather than partial. Revisit together
                # with the soft assertion above when #1984 closes.
                expect(form.field_helper_text("name")).to_have_count(0)
                expect(form.field("name")).to_have_attribute("aria-invalid", "false")

            with allure.step("Step 4B — Attempting Save must not create a configuration"):
                if form.is_save_enabled():
                    # #1984's severe half: the record is really persisted.
                    form.save_and_return_to_list()
                else:
                    # The behaviour the case expects (i.e. #1984 fixed) —
                    # Save cannot be clicked; return to the list to count.
                    providers_page.navigate()

                providers_page.embedding_models_section_header.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )
                providers_page.expand_section(providers_page.embedding_models_section_header)
                # Known defect: #1984 — the count currently grows by one.
                expect.soft(providers_page.configuration_cards).to_have_count(initial_card_count)

            with allure.step("Axis 2 — No console errors before teardown"):
                # Asserted BEFORE the delete: the app re-fetches the deleted
                # record and logs a 404 during teardown (AFS § Cleanup).
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
