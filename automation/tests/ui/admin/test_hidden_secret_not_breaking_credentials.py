"""UI test — hiding a secret that an existing credential references does NOT
break that credential, and the hidden secret leaves the secret-selection
dropdown on both the create- and edit-credential forms.

Test case: ELITEA-2345
AFS: test-specs/settings-secrets/l2_hiding-secret-used-by-credential-does-not-break-it_ELITEA-2345.md

The case's step 2 ("identify a secret currently referenced by at least one
credential") is satisfied by BUILDING that relationship inside the test, not by
finding one: hiding is irreversible via the UI and the shared project holds
100+ real, in-use secrets, so hunting for a real referencing secret would mean
permanently hiding production data. The test creates its own run-unique secret,
creates a jira credential whose ``api_key`` references it in Secret mode, and
hides THAT secret.

"The credential still functions" is asserted through the thing that would
actually have broken — its stored auth reference — on two independent,
system-produced observables: the server's own read of
``data.api_key == "{{secret.<name>}}"`` (decisive) and the detail form loading
pristine with Save disabled (nothing silently rewritten client-side).
``credential-form-test-connection-button`` is deliberately NOT the oracle: the
credential points at a fake Jira host, so it would fail regardless of the hide
and could not distinguish "broken by hiding" from "fake host".

The Password-mode fallback the field renders after the hide is asserted as
INTENDED product behaviour, not a defect: ``SecretField.jsx`` computes
``isHiddenSecret = isError || !data?.some(i => i.secret_name === value)`` and
only switches to the Secret tab ``if (isSecret && !isHiddenSecret)``. Pinning
that shape makes an unannounced change to it fail loudly instead of silently.
A related product question — a keystroke in that field would replace the
``{{secret.…}}`` reference with the literal name — is raised for a human
decision as EliteaAI/elitea-testing-public#1907, not asserted here.

Fidelity (`.agents/testing.md` § Fidelity policy): no substitution of any kind.
Every asserted value — the 201/200 responses, the confirmation copy, the
credential's server-side ``data`` block, the rendered dropdown options — is
produced by the live product against the DEV backend. Nothing is routed,
fulfilled, injected or monkeypatched.

Test data: the credential and the CONTROL secret are deleted in a mandatory
``finally``. The hidden secret CANNOT be cleaned up — hiding is irreversible
and no unhide affordance exists — which is why its name is run-unique.

Case-text drift asserted against the LIVE product rather than the case text
(reverse-masking guard, `.agents/role-overrides.md`), filed as clarification
EliteaAI/elitea-testing-public#1905: case step 5 says "Navigate to Settings →
Credentials", but Credentials is not under Settings — it is a top-level route
(``/credentials/all``). Asserting the case's path would assert a screen that
does not exist.

Page-object reuse note (declared): the credential DETAIL route renders the same
shared ``SecretField`` component as the create route, with byte-identical
derived testids. Those secret-vault handles live in exactly one page object
already (:class:`CredentialCreatePage`), so this test drives them through that
object on both routes rather than re-declaring them on
:class:`CredentialDetailPage` — one testid, one file
(`.agents/conventions.md`). Promoting that block to
:class:`CredentialFormFieldsMixin` (the pattern the file already used for
``FIELD_INPUT`` / ``AUTH_METHOD_RADIO``) is the cleaner end state, but it is a
non-additive edit to a page object with ~20 merged callers, so it is flagged to
the lead rather than done inside this case's PR.

No console-error assertion is made here: it is not part of this case's coverage
map, and the AFS records that known filed defect #656 (a React "unique key
prop" console.error from ``CategorySection.jsx``) fires on the
``/credentials/create-credential/<type>`` route on dev builds — an unrequested
assertion would turn this spec into a sanctioned-RED the case never asked for.
"""

import logging
import uuid

import allure
import pytest
from config import settings
from pages.credential_create_page import CredentialCreatePage
from pages.credential_detail_page import CredentialDetailPage
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.admin,
    pytest.mark.p1,
    pytest.mark.regression,
    pytest.mark.new,
]

HIDDEN_SECRET_VALUE = "hidden-secret-value-123"
CONTROL_SECRET_VALUE = "visible-secret-value-123"
# jira's api_key is a SecretField and the rest of the form is three plain text
# inputs — the cheapest credential type that carries a secret field.
CREDENTIAL_TYPE = "jira"
SECRET_FIELD_KEY = "api_key"
# Filler only — never authenticated against anything real (see the module
# docstring on why Test Connection is not this case's oracle).
CREDENTIAL_BASE_URL = "https://example.atlassian.net"
CREDENTIAL_USERNAME = "autotest@example.com"

UI_TIMEOUT = 10_000
ROW_WAIT_TIMEOUT = 15_000


class TestHiddenSecretNotBreakingCredentials:
    """ELITEA-2345 — hiding a secret referenced by an existing credential
    leaves the credential's stored reference intact, while removing the secret
    from the secret-selection dropdown on both the create- and edit-credential
    forms."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2345_hiding-secret-used-by-credentials.md",
        "onetest-ai Test Case link",
    )
    def test_hiding_secret_used_by_credential_does_not_break_it(self, page, credential_api):
        secrets_page = SecretsPage(page)
        create_page = CredentialCreatePage(page)
        detail_page = CredentialDetailPage(page)
        # The detail route renders the same shared SecretField — see the
        # module docstring's page-object reuse note.
        secret_fields = create_page

        hidden_secret = f"autotest_hidden_{uuid.uuid4().hex[:8]}"
        control_secret = f"autotest_visible_{uuid.uuid4().hex[:8]}"
        credential_name = f"autotest_cred_hidden_{uuid.uuid4().hex[:8]}"
        control_created = False
        credential_id = None

        # Flipping a secret field to Secret mode dirties the form, and a dirtied
        # credential form raises a native `beforeunload` dialog that hangs the
        # next `page.goto()` until it is handled (AFS step 9's warning).
        page.on("dialog", lambda dialog: dialog.accept())

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Secrets; verify the page title"
            ):
                secrets_page.navigate()
                assert secrets_page.page_title.text_content() == "Secrets", (
                    f"Expected page title 'Secrets', got "
                    f"{secrets_page.page_title.text_content()!r}"
                )

            with allure.step(
                "Step 2 — Create the run-unique secret this case will hide, "
                "plus a second run-unique secret that stays VISIBLE as the "
                "control; verify both create POSTs resolve 201 Created"
            ):
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
                "Step 3 — Create a jira credential whose Api Key REFERENCES "
                "the new secret (this realises the case's 'identify a secret "
                "referenced by a credential' by construction); the dropdown "
                "listing the secret BEFORE the hide is the baseline that makes "
                "step 9's absence check meaningful"
            ):
                create_page.open_type_form(CREDENTIAL_TYPE)
                create_page.set_display_name(credential_name)
                create_page.set_base_url(CREDENTIAL_BASE_URL)
                create_page.set_username(CREDENTIAL_USERNAME)

                create_page.secret_toggle(SECRET_FIELD_KEY, "secret").click()
                create_page.open_secret_dropdown(SECRET_FIELD_KEY)
                expect(create_page.saved_secret_option(hidden_secret)).to_have_count(
                    1, timeout=UI_TIMEOUT
                )
                expect(create_page.saved_secret_option(control_secret)).to_have_count(
                    1, timeout=UI_TIMEOUT
                )
                create_page.saved_secret_option(hidden_secret).click()
                # The vault dropdown does not always self-close after a
                # selection (known defect #1047's `skipNextCloseRef`); Escape
                # makes the Save click below unambiguous either way.
                page.keyboard.press("Escape")

                with page.expect_response(
                    lambda r: (
                        f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=ROW_WAIT_TIMEOUT,
                ) as save_info:
                    create_page.save_button.click()
                save_response = save_info.value
                assert save_response.status == 200, (
                    "Expected 200 from the credential-create POST, got "
                    f"{save_response.status}"
                )
                credential_id = save_response.json().get("id")
                if credential_id is None:
                    # The create response is the primary source of the id; fall
                    # back to the server's own list rather than guessing.
                    matches = [
                        c
                        for c in credential_api.list_all_credentials()
                        if c.get("label") == credential_name
                    ]
                    assert len(matches) == 1, (
                        f"Expected exactly one credential labelled {credential_name!r} "
                        f"after creating it, found {len(matches)}"
                    )
                    credential_id = matches[0]["id"]

            with allure.step(
                "Step 4 — Back on Settings -> Secrets, filter to the target "
                "secret and open its three-dot menu -> Hide; verify the "
                "confirmation copy verbatim"
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
                assert secrets_page.alert_dialog_confirm_button.text_content() == "Hide", (
                    "Expected the hide-confirmation dialog's confirm button text "
                    f"'Hide', got {secrets_page.alert_dialog_confirm_button.text_content()!r}"
                )

            with allure.step(
                "Step 5 — Confirm the hide; verify the hide POST resolves 200 "
                "OK (server-side proof, not just DOM removal)"
            ):
                hide_response = secrets_page.confirm_hide()
                assert hide_response.status == 200, (
                    f"Expected 200 from the secret-hide POST, got {hide_response.status}"
                )

            with allure.step(
                "Step 6 — Verify the secret is removed from the Secrets table "
                "(same search filter still applied)"
            ):
                expect(secrets_page.get_row_by_name(hidden_secret)).to_have_count(
                    0, timeout=ROW_WAIT_TIMEOUT
                )

            with allure.step(
                "Step 7 — Open the credential that referenced the hidden "
                "secret (via /credentials/all/<id> — Credentials is a "
                "top-level route, not a Settings child; clarification #1905); "
                "its own field values are intact"
            ):
                detail_page.open_by_id(credential_id)
                expect(detail_page.display_name_input).to_have_value(
                    credential_name, timeout=ROW_WAIT_TIMEOUT
                )
                expect(detail_page.field("base_url")).to_have_value(
                    CREDENTIAL_BASE_URL, timeout=UI_TIMEOUT
                )
                expect(detail_page.field("username")).to_have_value(
                    CREDENTIAL_USERNAME, timeout=UI_TIMEOUT
                )

            with allure.step(
                "Step 8 — Verify the credential still functions: the SERVER's "
                "own read still returns the unchanged {{secret.<name>}} "
                "reference (decisive), the form loads pristine with Save "
                "disabled (nothing rewritten client-side), and the Api Key "
                "field renders the INTENDED Password-mode fallback"
            ):
                stored = credential_api.get_credential(credential_id)
                assert stored["data"]["api_key"] == f"{{{{secret.{hidden_secret}}}}}", (
                    "Hiding the secret must not rewrite the credential's stored "
                    f"reference. Expected '{{{{secret.{hidden_secret}}}}}', got "
                    f"{stored['data']['api_key']!r}"
                )

                expect(detail_page.save_button).to_be_disabled(timeout=UI_TIMEOUT)

                # Intended fallback, source-confirmed (see module docstring):
                # the field drops to Password mode and shows the secret NAME.
                expect(
                    secret_fields.secret_toggle(SECRET_FIELD_KEY, "password")
                ).to_have_attribute("aria-pressed", "true", timeout=UI_TIMEOUT)
                expect(
                    secret_fields.secret_toggle(SECRET_FIELD_KEY, "secret")
                ).to_have_attribute("aria-pressed", "false", timeout=UI_TIMEOUT)
                expect(secret_fields.secret_combobox(SECRET_FIELD_KEY)).to_have_count(0)
                expect(
                    secret_fields.secret_native_input(SECRET_FIELD_KEY)
                ).to_have_value(hidden_secret, timeout=UI_TIMEOUT)

            with allure.step(
                "Step 9a — EDITING a credential: the hidden secret is absent "
                "from the secret-selection dropdown, while the control secret "
                "is still listed (the control is what distinguishes 'hidden' "
                "from 'nothing loaded')"
            ):
                secret_fields.secret_toggle(SECRET_FIELD_KEY, "secret").click()
                secret_fields.open_secret_dropdown(SECRET_FIELD_KEY)
                expect(secret_fields.saved_secret_option(hidden_secret)).to_have_count(
                    0, timeout=UI_TIMEOUT
                )
                expect(secret_fields.saved_secret_option(control_secret)).to_have_count(
                    1, timeout=UI_TIMEOUT
                )
                assert secret_fields.saved_secret_options.count() > 0, (
                    "The edit form's vault dropdown rendered zero saved-secret "
                    "options — the absence assertion above would pass vacuously"
                )
                page.keyboard.press("Escape")

            with allure.step(
                "Step 9b — CREATING a credential: same absence on the create "
                "form (a different route and a different Formik parent, so 9a "
                "does not imply it — the case says 'creating or editing')"
            ):
                create_page.open_type_form(CREDENTIAL_TYPE)
                create_page.secret_toggle(SECRET_FIELD_KEY, "secret").click()
                create_page.open_secret_dropdown(SECRET_FIELD_KEY)
                expect(create_page.saved_secret_option(hidden_secret)).to_have_count(
                    0, timeout=UI_TIMEOUT
                )
                expect(create_page.saved_secret_option(control_secret)).to_have_count(
                    1, timeout=UI_TIMEOUT
                )
                assert create_page.saved_secret_options.count() > 0, (
                    "The create form's vault dropdown rendered zero saved-secret "
                    "options — the absence assertion above would pass vacuously"
                )
        finally:
            if credential_id is not None:
                # Live project data on a shared DEV project — always removed.
                credential_api.delete_credential(credential_id)
            if control_created:
                # The control secret is a live, visible row. The hidden secret
                # cannot be cleaned up: hiding is irreversible and there is no
                # unhide affordance (AFS § Cleanup) — hence the run-unique name.
                secrets_page.navigate()
                secrets_page.type_search(control_secret)
                control_row = secrets_page.get_row_by_name(control_secret)
                if control_row.count() == 1:
                    secrets_page.open_row_actions_menu(control_row)
                    secrets_page.click_delete_menu_item()
                    secrets_page.fill_delete_confirm_name(control_secret)
                    secrets_page.confirm_delete()
