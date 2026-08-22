"""UI tests — Credential Secret/Password storage toggle and the secret vault
dropdown behind it.

Test cases:
  * ELITEA-1968 — Credential — Secret/Password Storage Toggle
    AFS: test-specs/toolkits-credentials/l1_credential-secret-password-storage-toggle_ELITEA-1968.md
  * ELITEA-1969 — Credential — Create New Project Secret from Secret Toggle
    AFS: test-specs/toolkits-credentials/l1_create-new-project-secret-from-secret-toggle_ELITEA-1969.md

Fidelity (`.agents/testing.md` § Fidelity policy): no substitution of any kind.
Every asserted value — the toggle's ``aria-pressed`` state, the rendered vault
options, the stored ``{{secret.<name>}}`` template, the ``201`` create response,
the post-refresh option count — is produced by the live product against the DEV
backend. Nothing is routed, fulfilled, injected or monkeypatched.

Test data: ELITEA-1968 is fully read-only (the credential form is abandoned
without Save; the ``auth_token`` secret it selects is only read). ELITEA-1969
creates ONE real project secret — its own observable — and deletes it via the
API in a mandatory ``finally`` cleanup, per `.agents/testing.md`
§ Test data strategy.

Case-text divergences asserted against the LIVE product rather than the case
text (reverse-masking guard, `.agents/role-overrides.md`), each filed as a
clarification and detailed in the AFS § Case-text divergence:
  1. The CREATE option reads "New Private Secret" on the acting identity's
     personal project (399), not the case's "New Project Secret" — the label is
     project-scope-dependent (`SecretField.jsx createSecretsOptions`).
  2. ELITEA-1969 step 4 opens a NEW TAB (``window.open(..., '_blank')``), not an
     in-page navigation.
  3. ELITEA-1969 step 6's "+" click is pre-satisfied: the ``?createSecret=1``
     deep link auto-opens the inline create row and disables the "+" button.
  4. ELITEA-1969 step 11's "click Secret toggle again" is not performed — the
     dropdown never closed (known defect #1047's ``skipNextCloseRef``) and
     re-clicking the toggle would clear the field.
"""

import logging
import uuid

import allure
import pytest
from config import settings
from pages.credential_create_page import CredentialCreatePage
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.credentials,
    pytest.mark.p1,
    pytest.mark.regression,
    pytest.mark.new,
]

CREDENTIAL_TYPE = "github"
AUTH_METHOD_TOKEN = "token"
# GitHub's Token auth renders exactly one secret field; its schema property key
# is the testid stem for every handle this module uses.
SECRET_FIELD_KEY = "access_token"

# Read-only: the case names this secret as its test data and project 399
# carries it. Never written to.
EXISTING_SECRET_NAME = "auth_token"

# A literal placeholder — never a real token, never saved (ELITEA-1968 step 7).
PLAINTEXT_TOKEN = "ghp_autotest_placeholder_123"

# The CREATE option's label on the acting identity's PERSONAL project. See the
# module docstring's divergence (1) — the case text says "New Project Secret",
# which is what the same option renders on a team project.
CREATE_OPTION_LABEL_PERSONAL_PROJECT = "New Private Secret"

NEW_SECRET_VALUE = "test_value_123"

UI_TIMEOUT = 10_000
LIST_TIMEOUT = 15_000


@pytest.mark.credentials
class TestCredentialSecretPasswordToggle:
    """Secret/Password storage toggle on a GitHub credential's Token field."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "toolkits-credentials/ELITEA-1968_credential-secret-password-storage-toggle.md",
        "onetest-ai Test Case link",
    )
    def test_secret_password_storage_toggle(self, page):
        """ELITEA-1968 — the Secret/Password toggle switches a credential's
        token field between a vault-backed secret select and a masked plaintext
        input, and both modes hold the value they are given.

        Read-only: nothing is created, saved or deleted.
        """
        create_page = CredentialCreatePage(page)

        with allure.step(
            "Step 1 — Open the Github credential create form and select Token "
            "auth; the Access Token field renders"
        ):
            create_page.open_type_form(CREDENTIAL_TYPE)
            create_page.select_auth_method(AUTH_METHOD_TOKEN)
            expect(create_page.field(SECRET_FIELD_KEY)).to_be_visible(timeout=UI_TIMEOUT)
            expect(create_page.secret_native_input(SECRET_FIELD_KEY)).to_be_visible(
                timeout=UI_TIMEOUT
            )

        with allure.step(
            "Step 2 — The Secret/Password toggle is present beside the token field"
        ):
            secret_button = create_page.secret_toggle(SECRET_FIELD_KEY, "secret")
            password_button = create_page.secret_toggle(SECRET_FIELD_KEY, "password")
            expect(secret_button).to_be_visible(timeout=UI_TIMEOUT)
            expect(password_button).to_be_visible(timeout=UI_TIMEOUT)
            # The field opens in Password mode (SecretField's own default) —
            # pinning it makes step 3's flip unambiguous.
            expect(password_button).to_have_attribute("aria-pressed", "true")
            expect(secret_button).to_have_attribute("aria-pressed", "false")

        with allure.step(
            "Step 3 — Click 'Secret': the field becomes a vault select and its "
            "dropdown lists SAVED SECRETS from the Elitea Secret vault"
        ):
            secret_button.click()
            # Both sides of the exclusive pair — a toggle that lights both
            # buttons is exactly the "does not switch modes" failure the case
            # names, and a one-sided check cannot see it.
            expect(secret_button).to_have_attribute("aria-pressed", "true")
            expect(password_button).to_have_attribute("aria-pressed", "false")
            # The two modes are mutually exclusive: the native password input
            # must be GONE, not merely hidden behind the select.
            expect(create_page.secret_native_input(SECRET_FIELD_KEY)).to_have_count(0)
            expect(create_page.secret_combobox(SECRET_FIELD_KEY)).to_be_visible(
                timeout=UI_TIMEOUT
            )

            create_page.open_secret_dropdown(SECRET_FIELD_KEY)
            expect(create_page.secret_saved_group_header).to_be_visible(
                timeout=UI_TIMEOUT
            )
            # The group header's underlying string is "Saved Secrets"; the
            # all-caps rendering is CSS `text-transform` only, and `to_have_text`
            # reads textContent, not the transformed form.
            expect(create_page.secret_saved_group_header).to_have_text("Saved Secrets")
            saved_option_count = create_page.saved_secret_options.count()
            assert saved_option_count >= 1, (
                "Expected at least one saved secret in the vault dropdown "
                f"(precondition), got {saved_option_count}"
            )

        with allure.step(
            "Step 4 — The same dropdown carries a CREATE section with the "
            "create-a-secret option (label is project-scope-dependent — see the "
            "module docstring's divergence 1)"
        ):
            expect(create_page.secret_create_group_header).to_be_visible(
                timeout=UI_TIMEOUT
            )
            expect(create_page.secret_create_group_header).to_have_text("Create")
            expect(create_page.secret_create_option).to_be_visible(timeout=UI_TIMEOUT)
            expect(create_page.secret_create_option).to_have_text(
                CREATE_OPTION_LABEL_PERSONAL_PROJECT
            )

        with allure.step(
            f"Step 5 — Select the saved secret {EXISTING_SECRET_NAME!r}: its NAME "
            "is displayed while the {{secret.<name>}} template is what the field "
            "stores"
        ):
            option = create_page.saved_secret_option(EXISTING_SECRET_NAME)
            expect(option).to_have_count(1, timeout=UI_TIMEOUT)
            option.click()
            combobox = create_page.secret_combobox(SECRET_FIELD_KEY)
            expect(combobox).to_have_text(EXISTING_SECRET_NAME, timeout=UI_TIMEOUT)
            # The dropdown closes on selection — asserted, because a select that
            # stays open after a pick is the "selected secret is not displayed"
            # failure shape the case names.
            expect(create_page.secret_saved_group_header).to_have_count(0)

        with allure.step(
            "Step 6 — Switch to 'Password': the select is replaced by a masked "
            "plaintext input, cleared by the mode switch"
        ):
            password_button.click()
            expect(password_button).to_have_attribute("aria-pressed", "true")
            expect(secret_button).to_have_attribute("aria-pressed", "false")
            expect(create_page.secret_combobox(SECRET_FIELD_KEY)).to_have_count(0)
            native_input = create_page.secret_native_input(SECRET_FIELD_KEY)
            expect(native_input).to_be_visible(timeout=UI_TIMEOUT)
            expect(native_input).to_have_attribute("type", "password")
            # Product behaviour: SecretField.handleToggleTab clears the value on
            # every mode switch. Pinning it makes step 7's "value is accepted"
            # unambiguous — the typed text, never a leftover.
            expect(native_input).to_have_value("")

        with allure.step(
            "Step 7 — Type a token directly: the value is accepted and stays masked"
        ):
            create_page.set_access_token(PLAINTEXT_TOKEN)
            native_input = create_page.secret_native_input(SECRET_FIELD_KEY)
            expect(native_input).to_have_value(PLAINTEXT_TOKEN, timeout=UI_TIMEOUT)
            # "displayed as masked (hidden) text" — the input must still be a
            # password field, not merely hold the value.
            expect(native_input).to_have_attribute("type", "password")

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "toolkits-credentials/ELITEA-1969_credential-create-new-project-secret-from-secret-toggle.md",
        "onetest-ai Test Case link",
    )
    def test_create_new_project_secret_from_secret_toggle(self, page, api):
        """ELITEA-1969 — the credential form's CREATE option lands on the
        Secrets settings page with the create row open; the secret created there
        becomes selectable in the credential form's saved-secrets list once the
        dropdown's refresh button reconciles its cached list.

        Creates ONE real project secret (the case's own observable) and deletes
        it via the API in a mandatory ``finally`` cleanup.
        """
        create_page = CredentialCreatePage(page)
        secret_name = f"autotest_new_secret_{uuid.uuid4().hex[:8]}"
        created = False

        try:
            with allure.step(
                "Step 1 — Open the Github credential create form and select "
                "Token auth; the Access Token field renders"
            ):
                create_page.open_type_form(CREDENTIAL_TYPE)
                create_page.select_auth_method(AUTH_METHOD_TOKEN)
                expect(create_page.field(SECRET_FIELD_KEY)).to_be_visible(
                    timeout=UI_TIMEOUT
                )

            with allure.step(
                "Step 2 — Click 'Secret' on the toggle and open the vault dropdown"
            ):
                create_page.secret_toggle(SECRET_FIELD_KEY, "secret").click()
                expect(create_page.secret_combobox(SECRET_FIELD_KEY)).to_be_visible(
                    timeout=UI_TIMEOUT
                )
                create_page.open_secret_dropdown(SECRET_FIELD_KEY)

            with allure.step(
                "Step 3 — The dropdown shows both a CREATE section and a SAVED "
                "SECRETS list; record the saved-option count as the baseline"
            ):
                expect(create_page.secret_create_group_header).to_have_text(
                    "Create", timeout=UI_TIMEOUT
                )
                expect(create_page.secret_create_option).to_be_visible(
                    timeout=UI_TIMEOUT
                )
                expect(create_page.secret_saved_group_header).to_have_text(
                    "Saved Secrets", timeout=UI_TIMEOUT
                )
                baseline_option_count = create_page.saved_secret_options.count()
                assert baseline_option_count >= 1, (
                    "Expected at least one saved secret in the vault dropdown "
                    f"(precondition), got {baseline_option_count}"
                )
                logger.info("Baseline saved-secret options: %s", baseline_option_count)

            with allure.step(
                "Step 4 — Click the create-a-secret option: the Secrets settings "
                "page opens in a NEW TAB (divergence 2 — window.open, not an "
                "in-page navigation)"
            ):
                with page.context.expect_page() as popup_info:
                    create_page.secret_create_option.click()
                secrets_tab = popup_info.value
                # The router strips ?createSecret=1 shortly after handling it,
                # so assert on the URL captured at open time.
                popup_url = secrets_tab.url
                assert "/settings/secrets" in popup_url, (
                    f"Expected the popup to open the Secrets settings page, got {popup_url!r}"
                )
                assert "createSecret=1" in popup_url, (
                    "Expected the popup URL to carry the createSecret=1 deep-link "
                    f"query, got {popup_url!r}"
                )

            secrets_page = SecretsPage(secrets_tab)

            with allure.step(
                "Step 5 — The Secrets page shows a table with exactly the "
                "columns Name, Value and Actions"
            ):
                expect(secrets_page.secret_row.first).to_be_visible(
                    timeout=LIST_TIMEOUT
                )
                expect(secrets_page.column_header("name")).to_have_text(
                    "Name", timeout=UI_TIMEOUT
                )
                expect(secrets_page.column_header("secretValue")).to_have_text("Value")
                expect(secrets_page.column_header("actions")).to_have_text("Actions")
                # Bi-directional: the case names exactly three columns, so a
                # fourth is a failure a presence-only check cannot see.
                expect(secrets_page.column_headers()).to_have_count(3)

            with allure.step(
                "Step 6 — The inline create row is already open (divergence 3 — "
                "the createSecret=1 deep link auto-invokes the '+' action and "
                "the '+' button is disabled while a row is editable)"
            ):
                expect(secrets_page.name_input).to_be_visible(timeout=LIST_TIMEOUT)
                expect(secrets_page.value_input).to_be_visible(timeout=UI_TIMEOUT)
                expect(secrets_page.add_button).to_be_disabled(timeout=UI_TIMEOUT)

            with allure.step(
                f"Step 7 — Fill Name {secret_name!r} and Value into the new row"
            ):
                secrets_page.fill_new_row(secret_name, NEW_SECRET_VALUE)
                expect(secrets_page.name_input).to_have_value(secret_name)
                expect(secrets_page.value_input).to_have_value(NEW_SECRET_VALUE)

            with allure.step(
                "Step 8 — Click the checkmark: the create POST resolves 201 and "
                "the add button re-enables"
            ):
                response = secrets_page.click_save_button(timeout=LIST_TIMEOUT)
                assert response.status == 201, (
                    f"Expected 201 from the secret-create POST, got {response.status}"
                )
                created = True
                expect(secrets_page.add_button).to_be_enabled(timeout=LIST_TIMEOUT)

            with allure.step(
                f"Step 9 — {secret_name!r} is listed in the secrets table"
            ):
                row = secrets_page.get_row_by_name(secret_name)
                expect(row).to_have_count(1, timeout=LIST_TIMEOUT)
                expect(secrets_page.get_row_name_cell(row)).to_have_text(secret_name)

            with allure.step(
                "Step 10 — Back on the credential form tab: still on the create "
                "form, still in Secret mode"
            ):
                page.bring_to_front()
                assert f"/credentials/create-credential/{CREDENTIAL_TYPE}" in page.url, (
                    f"Expected to return to the credential create form, got {page.url!r}"
                )
                expect(
                    create_page.secret_toggle(SECRET_FIELD_KEY, "secret")
                ).to_have_attribute("aria-pressed", "true")

            with allure.step(
                "Step 11 — The saved-secrets dropdown is still open (divergence "
                "4 — it never closed) and its cached list is STALE: the new "
                "secret is absent and the count still equals the baseline"
            ):
                expect(create_page.secret_saved_group_header).to_be_visible(
                    timeout=UI_TIMEOUT
                )
                # Asserting the staleness is what gives step 12's refresh click
                # its meaning — without it, steps 12-13 would pass on a list
                # that had already reconciled by itself.
                expect(create_page.saved_secret_option(secret_name)).to_have_count(0)
                assert create_page.saved_secret_options.count() == baseline_option_count, (
                    "Expected the cached saved-secrets list to be unchanged before "
                    f"the refresh (baseline {baseline_option_count}), got "
                    f"{create_page.saved_secret_options.count()}"
                )

            with allure.step(
                "Step 12 — Click the refresh button in the SAVED SECRETS header"
            ):
                refresh_button = create_page.secret_refresh_button(SECRET_FIELD_KEY)
                expect(refresh_button).to_be_visible(timeout=UI_TIMEOUT)
                refresh_button.click()

            with allure.step(
                f"Step 13 — {secret_name!r} now appears in the saved-secrets "
                "list, and the list grew by exactly one"
            ):
                new_option = create_page.saved_secret_option(secret_name)
                expect(new_option).to_have_count(1, timeout=LIST_TIMEOUT)
                expect(new_option).to_have_text(secret_name)
                expect(create_page.saved_secret_options).to_have_count(
                    baseline_option_count + 1, timeout=LIST_TIMEOUT
                )
        finally:
            # Cleanup (not an AFS case step — mandatory, runs regardless of
            # outcome): step 8 persists a real secret into shared live project
            # data. Same API-delete pattern as
            # test_secret_create_inline_checkmark_x_cancel.py's teardown.
            if created:
                delete_response = api.delete(
                    f"/secrets/secret/default/{settings.elitea_project_id}/{secret_name}"
                )
                assert delete_response.status_code == 204, (
                    f"Cleanup failed: expected 204 deleting {secret_name!r}, got "
                    f"{delete_response.status_code} {delete_response.text}"
                )
