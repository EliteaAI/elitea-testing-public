"""UI test — a HIDDEN secret is absent from the secret-selection dropdown of a
new AI-provider configuration.

Test case: ELITEA-2346
AFS: test-specs/settings-secrets/l3_hidden-secret-absent-from-ai-provider-secret-dropdown_ELITEA-2346.md

Two run-unique secrets are created: one is hidden (the case's subject) and one
stays visible (the CONTROL). The control is what keeps the absence assertion
honest — a dropdown that failed to load renders zero options and would pass a
bare "the hidden secret is not there" check silently. The pre-hide baseline
(the same dropdown listing the secret WHILE it is still visible) is what
attributes its later absence to the hide rather than to it never having been
listed.

Fidelity (`.agents/testing.md` § Fidelity policy): no substitution of any kind.
Every asserted value — the 201/200 responses, the confirmation copy, the
rendered dropdown options — is produced by the live product against the DEV
backend. Nothing is routed, fulfilled, injected or monkeypatched.

Test data: the hidden secret CANNOT be cleaned up — hiding is irreversible via
the UI and no unhide affordance exists — which is exactly why its name is
run-unique (a fixed literal is usable exactly once). The control secret IS
deleted in a mandatory ``finally``. The AI-provider form is never saved, so no
provider configuration is created.

Case-text drift asserted against the LIVE product rather than the case text
(reverse-masking guard, `.agents/role-overrides.md`), filed as clarification
EliteaAI/elitea-testing-public#1906:
  1. "Settings → AI Configuration" does not exist — the section is **AI
     Providers** (`/settings/ai-providers`) and the "+" creates an **AI
     Provider**, not a "model configuration".
  2. The "+" is a TWO-hop flow: create → type picker → type-specific form.
  3. The dropdown requires first switching the ``api_key`` field to **Secret**
     mode; it renders in Password mode and the combobox does not exist until
     the toggle is clicked. The case omits this hop.
  4. The case's literal secret name ``"autotest_secret"`` is replaced by a
     run-unique name — see the Test data note above.

Page-object reuse note (declared): the AI-provider configuration form renders
the SAME shared ``ToolBaseProperty`` / ``SecretField`` components as the
credential forms, with byte-identical derived testids
(``toolkit-field-api_key-input-*``). This test therefore drives those fields
through :class:`CredentialCreatePage`, whose secret-vault methods already own
those selectors, rather than re-declaring them on an AI-providers page object —
one testid, one file (`.agents/conventions.md`). Extracting that block into a
shared ``components/secret_field.py`` component object is the cleaner end
state; it is a refactor of a page object with ~20 merged callers, so it is
flagged to the lead rather than done inside this case's PR (AFS § Automation
Hints raises the same option).

No console-error assertion is made here: it is not part of this case's coverage
map, and the AFS records two known, filed, environment-dependent console
signatures around this flow (#1203 on the Secrets page, #656 on the
*credentials* type picker) that would turn an unrequested assertion into a
sanctioned-RED burden this case never asked for.
"""

import logging
import re
import uuid

import allure
import pytest
from pages.ai_providers_page import AIProvidersPage
from pages.credential_create_page import CredentialCreatePage
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.admin,
    pytest.mark.p2,
    pytest.mark.regression,
    pytest.mark.new,
]

HIDDEN_SECRET_VALUE = "hidden-secret-value-456"
CONTROL_SECRET_VALUE = "visible-secret-value-456"
# open_ai's configuration form is two text fields plus the api_key SecretField —
# the cheapest AI-provider type that carries a secret field.
PROVIDER_TYPE = "open_ai"
SECRET_FIELD_KEY = "api_key"
UI_TIMEOUT = 10_000
ROW_WAIT_TIMEOUT = 15_000


class TestHiddenSecretAbsentFromAIProviderDropdown:
    """ELITEA-2346 — hiding a secret removes it from the secret-selection
    dropdown offered when creating a new AI provider, while every still-visible
    secret remains selectable."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2346_hidden-secret-not-in-selection-dropdown.md",
        "onetest-ai Test Case link",
    )
    def test_hidden_secret_absent_from_ai_provider_dropdown(self, page):
        secrets_page = SecretsPage(page)
        ai_providers_page = AIProvidersPage(page)
        # Shared SecretField/ToolBaseProperty handles — see the module
        # docstring's page-object reuse note.
        provider_form = CredentialCreatePage(page)

        hidden_secret = f"autotest_hidden_{uuid.uuid4().hex[:8]}"
        control_secret = f"autotest_visible_{uuid.uuid4().hex[:8]}"
        control_created = False

        # Flipping the api_key field to Secret mode dirties the form, and a
        # dirtied AI-provider form raises a native `beforeunload` dialog that
        # hangs the next `page.goto()` until it is handled (AFS § Cleanup).
        page.on("dialog", lambda dialog: dialog.accept())

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Secrets and create the "
                "run-unique secret this case will hide, plus a second "
                "run-unique secret that stays VISIBLE as the control; verify "
                "both create POSTs resolve 201 Created"
            ):
                secrets_page.navigate()
                assert secrets_page.page_title.text_content() == "Secrets", (
                    f"Expected page title 'Secrets', got "
                    f"{secrets_page.page_title.text_content()!r}"
                )

                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.fill_new_row(hidden_secret, HIDDEN_SECRET_VALUE)
                hidden_create = secrets_page.click_save_button()
                assert hidden_create.status == 201, (
                    "Expected 201 from the secret-create POST for the "
                    f"to-be-hidden secret, got {hidden_create.status}"
                )

                secrets_page.click_add_button()
                expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                secrets_page.fill_new_row(control_secret, CONTROL_SECRET_VALUE)
                control_create = secrets_page.click_save_button()
                assert control_create.status == 201, (
                    "Expected 201 from the secret-create POST for the control "
                    f"secret, got {control_create.status}"
                )
                control_created = True

            with allure.step(
                "Step 2 (baseline, pre-hide) — Open a new AI-provider form's "
                "secret dropdown and verify BOTH secrets are listed while "
                "still visible; without this the later absence cannot be "
                "attributed to the hide"
            ):
                ai_providers_page.navigate()
                expect(ai_providers_page.page_title).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                ai_providers_page.click_create()
                ai_providers_page.click_type_card(PROVIDER_TYPE)
                expect(provider_form.display_name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)

                provider_form.secret_toggle(SECRET_FIELD_KEY, "secret").click()
                provider_form.open_secret_dropdown(SECRET_FIELD_KEY)
                expect(provider_form.saved_secret_option(hidden_secret)).to_have_count(
                    1, timeout=UI_TIMEOUT
                )
                expect(provider_form.saved_secret_option(control_secret)).to_have_count(
                    1, timeout=UI_TIMEOUT
                )
                # Close the dropdown before leaving the route — the form is
                # abandoned, never saved.
                page.keyboard.press("Escape")

            with allure.step(
                "Step 3 — Back on Settings -> Secrets, filter to the target "
                "secret and hide it via the row's three-dot menu; verify the "
                "confirmation copy, the hide POST's 200, and that the secret "
                "leaves the table"
            ):
                secrets_page.navigate()
                secrets_page.type_search(hidden_secret)
                row = secrets_page.get_row_by_name(hidden_secret)
                expect(row).to_have_count(1, timeout=ROW_WAIT_TIMEOUT)

                # DECLARED IMPROVISATION, inherited from ELITEA-2344 and
                # re-confirmed by this case's own analyst session: a plain
                # Playwright .click() on `secret-row-actions-button` does not
                # mount the menu reliably; `open_row_actions_menu()` dispatches
                # the React onClick directly. Tracked as
                # EliteaAI/elitea-testing-public#1222 — do not "simplify" it.
                secrets_page.open_row_actions_menu(row)
                secrets_page.click_hide_menu_item()

                expected_body = (
                    f'Are you sure to hide the secret "{hidden_secret}"? '
                    "Once hidden, the secret will no longer be visible."
                )
                assert secrets_page.get_hide_confirm_text() == expected_body, (
                    f"Expected hide-confirm dialog body {expected_body!r}, got "
                    f"{secrets_page.get_hide_confirm_text()!r}"
                )

                hide_response = secrets_page.confirm_hide()
                assert hide_response.status == 200, (
                    f"Expected 200 from the secret-hide POST, got {hide_response.status}"
                )
                expect(secrets_page.get_row_by_name(hidden_secret)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 4 — Navigate to Settings -> AI Providers and click '+': "
                "the app routes to the Create AI Provider TYPE PICKER (the "
                "case's 'AI Configuration' / one-hop wording is stale — "
                "clarification #1906)"
            ):
                ai_providers_page.navigate()
                expect(ai_providers_page.page_title).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                ai_providers_page.click_create()
                expect(page).to_have_url(
                    re.compile(r"/settings/create-ai-provider"), timeout=UI_TIMEOUT
                )
                expect(ai_providers_page.type_card(PROVIDER_TYPE)).to_be_visible(
                    timeout=UI_TIMEOUT
                )

            with allure.step(
                "Step 5 — Choose the OpenAI provider type; the type-specific "
                "configuration form renders"
            ):
                ai_providers_page.click_type_card(PROVIDER_TYPE)
                expect(page).to_have_url(
                    re.compile(rf"/settings/create-ai-provider/{PROVIDER_TYPE}"),
                    timeout=UI_TIMEOUT,
                )
                expect(provider_form.display_name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)
                expect(provider_form.field("api_base")).to_be_visible(timeout=UI_TIMEOUT)
                expect(provider_form.field(SECRET_FIELD_KEY)).to_be_visible(timeout=UI_TIMEOUT)

            with allure.step(
                "Step 6 — Switch the Api Key field to Secret mode and open the "
                "vault dropdown; both group headers render (positive proof the "
                "menu is open, so step 7's absence check is not read off a "
                "closed menu)"
            ):
                provider_form.secret_toggle(SECRET_FIELD_KEY, "secret").click()
                provider_form.open_secret_dropdown(SECRET_FIELD_KEY)
                expect(provider_form.secret_create_group_header).to_be_visible(
                    timeout=UI_TIMEOUT
                )
                expect(provider_form.secret_saved_group_header).to_be_visible(
                    timeout=UI_TIMEOUT
                )

            with allure.step(
                "Step 7 — Verify the HIDDEN secret does NOT appear in the "
                "dropdown, while the control secret does and the list is "
                "non-empty (the control is what distinguishes 'hidden' from "
                "'nothing loaded')"
            ):
                expect(provider_form.saved_secret_option(hidden_secret)).to_have_count(
                    0, timeout=UI_TIMEOUT
                )
                expect(provider_form.saved_secret_option(control_secret)).to_have_count(
                    1, timeout=UI_TIMEOUT
                )
                assert provider_form.saved_secret_options.count() > 0, (
                    "The vault dropdown rendered zero saved-secret options — the "
                    "absence assertion above would pass vacuously"
                )
        finally:
            if control_created:
                # The control secret is a live, visible row in a shared
                # project — it MUST be removed. The hidden secret cannot be:
                # hiding is irreversible and there is no unhide affordance
                # (AFS § Cleanup), which is why its name is run-unique.
                secrets_page.navigate()
                secrets_page.type_search(control_secret)
                control_row = secrets_page.get_row_by_name(control_secret)
                if control_row.count() == 1:
                    secrets_page.open_row_actions_menu(control_row)
                    secrets_page.click_delete_menu_item()
                    secrets_page.fill_delete_confirm_name(control_secret)
                    secrets_page.confirm_delete()
