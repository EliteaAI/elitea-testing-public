"""UI test — Create LLM Model: the ID field is auto-populated from Display Name.

Test case: ELITEA-2409
AFS: test-specs/settings-ai-providers/l3_create-llm-model-id-autopopulated_ELITEA-2409.md

Case-identity note (full write-up in the AFS, reused from ELITEA-2392 — same
root cause, filed as EliteaAI/elitea-testing-public#1250): the TMS case directs
the tester to "Settings -> AI Configuration". No such page or nav item exists;
the real page is "AI Providers" (`/settings/ai-providers`), whose "+" control
opens the AI-provider type picker this case's steps 1-3 walk through.

Case-text drift SPECIFIC to this case (filed as a CLARIFICATION,
EliteaAI/elitea-testing-public#1985): case step 4 says "Verify the ID field is
editable if needed". **It is never editable on this flow, by design** —
`ToolBase.jsx:245` disables `elitea_title` unless `enableEditEliteaTitle` is
set, and that flag comes only from a `prefillId` URL param produced by the
CredentialWarningBanner deep link, never by the AI-Providers "+" flow. Per the
reverse-masking guard (`.agents/testing.md`) the product is correct and the
case text is stale, so this test asserts the LIVE contract — the ID is a
read-only, derived mirror of the Display Name — rather than the stale
hypothesis. The drift is filed, not silently absorbed.

No substitution of the system under test: nothing is mocked, injected or
fabricated. The derivation under test is purely client-side
(`ToolBase.jsx:216-219`), so it is observed by typing into the real form and
reading the real ID input.

Read-only case: nothing is saved, so there is no cleanup and no shared-state
mutation. A dirty form arms a native `beforeunload` dialog, so a dialog
handler is registered before any navigation away.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p2: this suite's l3 maps to p2 (matching the sibling ELITEA-2392 /
      ELITEA-2397 tests in this same folder)
    - regression
    - new: not yet validated on a deployed environment
"""

import logging

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

# The case's own Display Name, and the ID the live product derives from it:
# lowercase, underscore-separated (the case guesses "my-test-model or similar
# slug" — "or similar" covers the underscore form).
DISPLAY_NAME = "My Test Model"
EXPECTED_ID = "my_test_model"


class TestLlmModelIdAutoPopulated:
    """ELITEA-2409 — the create form's ID field mirrors the Display Name."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2409.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1985", "Case-text clarification #1985")
    def test_id_is_auto_populated_and_read_only(self, page):
        """Type a Display Name on the Create LLM Model form and verify the ID
        field auto-populates with its lowercase/underscore derivation, stays
        read-only, and clears when the Display Name clears."""
        providers_page = AIProvidersPage(page)
        form = AiProviderFormPage(page)

        # A dirty create form arms a native beforeunload dialog; accepting it
        # keeps teardown/navigation from blocking every subsequent call.
        page.on("dialog", lambda dialog: dialog.accept())

        with allure.step("Step 1 — Open Settings -> AI Providers, click '+' and pick the LLM Model type"):
            providers_page.navigate()
            expect(providers_page.page_title).to_have_text("AI Providers")
            providers_page.click_create()
            providers_page.click_type_card("llm_model")
            form.wait_for_form()

            # The console axis is scoped to the create form deliberately: the
            # type-picker page logs one already-filed React "unique key" error
            # (#656) that belongs to that page, not to this case's subject.
            # Attaching here keeps the assertion honest and filter-free.
            console_errors = collect_console_errors(page)

            expect(form.display_name_input).to_have_value("")
            # Axis 2 — the before-state. Without it, "the ID matches the slug"
            # could pass on a form that pre-filled the ID from something else.
            expect(form.id_input).to_have_value("")
            expect(form.id_input).to_be_disabled()
            assert not form.is_save_enabled(), "Save must be disabled on a pristine create form"

        with allure.step(f"Step 2 — Type {DISPLAY_NAME!r} into the Display Name field"):
            form.set_display_name(DISPLAY_NAME)
            expect(form.display_name_input).to_have_value(DISPLAY_NAME)

        with allure.step(f"Step 3 — The ID field is auto-populated with {EXPECTED_ID!r}"):
            # Auto-retrying value assertion — the derivation is synchronous and
            # client-side, so no network wait and no sleep.
            expect(form.id_input).to_have_value(EXPECTED_ID)

        with allure.step("Step 4 — The ID field is NOT user-editable (live contract; case drift #1985)"):
            expect(form.id_input).to_be_disabled()

        with allure.step("Axis 2 — Clearing the Display Name clears the derived ID"):
            # The assertion that distinguishes a live binding from a one-shot
            # derivation at first keystroke.
            form.clear_display_name()
            expect(form.display_name_input).to_have_value("")
            expect(form.id_input).to_have_value("")

        with allure.step("Axis 2 — Save stayed disabled throughout; no console errors on the create form"):
            assert not form.is_save_enabled(), "Nothing was submitted — Save must still be disabled"

            # Known defect: #1971 — the project-id-less toolkitTypes 404 fires
            # on project-scope transitions and is unrelated to this flow.
            unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
            assert not unexpected, f"Unexpected console errors on the create form: {unexpected}"
