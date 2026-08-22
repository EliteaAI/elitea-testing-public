"""Test for Credential — Test Connection.

Verifies that the credential form's "Test connection" button reports the
truth from the target service in both directions: a success toast
("The connection is OK!") for a working credential, and an inline
field-level error carrying the service's own reason for a broken one.

Test case: ELITEA-1970
AFS: test-specs/toolkits-credentials/l3_credential-test-connection_ELITEA-1970.md

Credential type — declared divergence from the case text: the case names
Github + "a working Github personal access token", but the suite's
``GIT_HUB_TOKEN`` is expired (GitHub itself answers 401 —
elitea-testing-public#1673), so the case's step-3 observable is not
producible on Github today. The flow under test is type-agnostic
(``CredentialForm.jsx`` -> ``useCreateConfiguration.onTestConnection`` ->
``POST /configurations/check_connection/{project}/{type}``), so it is
executed on the credential type this environment DOES hold valid data for:
Jira. See the AFS § Case-text divergence #1; re-pointing at Github once
#1673 is fixed is a one-row edit of the constants below.

No substitution of the system under test: the credential is created through
the real UI form, the connection is tested against the real Jira instance
through the product's own endpoint, and every asserted value comes from the
product — the inline error text is asserted against the failing response's
own ``message`` field rather than a string this test authored.
"""

import logging
import re
import time

import allure
import pytest
from config import settings
from pages.credential_create_page import CredentialCreatePage
from pages.credential_detail_page import CredentialDetailPage
from pages.credentials_list_page import CredentialsListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.credentials,
    pytest.mark.p3,
    pytest.mark.regression,
    pytest.mark.new,
]

# --- The case's vehicle, in one place (see the module docstring) ----------
CREDENTIAL_TYPE = "jira"
SECRET_FIELD_KEY = "api_key"
INVALID_SECRET = "invalid_token_xyz"  # the literal from the case's Test Data

CREATE_RESPONSE_TIMEOUT = 20_000
CHECK_CONNECTION_TIMEOUT = 45_000  # a real round trip to the target service
TOAST_AUTOHIDE_TIMEOUT = 25_000


def _has_valid_test_data() -> bool:
    return bool(settings.jira_base_url and settings.jira_username and settings.jira_api_key)


@pytest.mark.skipif(
    not _has_valid_test_data(),
    reason=(
        "JIRA_BASE_URL / JIRA_USERNAME / JIRA_API_KEY must be set in .env.test — "
        "the case's precondition is a WORKING credential, which cannot be faked"
    ),
)
@allure.title("ELITEA-1970 — Credential Test connection: success toast vs inline error")
def test_credential_test_connection(page, credential_api):
    """Valid credentials -> success toast; invalid secret -> inline field error."""
    # Kept under the product's MAX_NAME_LENGTH (32, common/constants.js): the
    # Display Name input carries a real maxLength, so a longer name is silently
    # TRUNCATED by the field rather than rejected.
    display_name = f"autotest_cred_conn_{int(time.time())}"
    credential_id = None

    create_page = CredentialCreatePage(page)
    list_page = CredentialsListPage(page)
    detail_page = CredentialDetailPage(page)

    try:
        with allure.step(f"Step 1 — Create the {CREDENTIAL_TYPE} credential {display_name!r} with a valid secret"):
            create_page.open_type_form(CREDENTIAL_TYPE)
            create_page.set_display_name(display_name)
            assert create_page.display_name_input.input_value() == display_name, (
                f"Display Name field should read {display_name!r} after filling, got "
                f"{create_page.display_name_input.input_value()!r}"
            )
            create_page.set_base_url(settings.jira_base_url)
            create_page.set_username(settings.jira_username)
            create_page.set_api_key(settings.jira_api_key)

            assert create_page.is_save_enabled(), (
                "Save should be enabled once Display Name, Base Url, Username and Api Key are filled"
            )

            with page.expect_response(
                lambda r: (
                    f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                    and r.request.method == "POST"
                ),
                timeout=CREATE_RESPONSE_TIMEOUT,
            ) as create_response_info:
                create_page.save_button.click()
            create_response = create_response_info.value

            assert create_response.status == 200, (
                f"Expected 200 from the credential-create POST, got {create_response.status}"
            )
            create_body = create_response.json()
            credential_id = create_body.get("id")
            assert credential_id, "Expected a numeric id in the create response"
            assert create_body.get("label") == display_name, (
                f"Expected created credential label {display_name!r}, got {create_body.get('label')!r}"
            )
            assert create_body.get("elitea_title") == display_name, (
                f"Expected created credential elitea_title {display_name!r}, "
                f"got {create_body.get('elitea_title')!r}"
            )
            page.wait_for_url(
                re.compile(r".*/credentials/all/?(\?.*)?$"), timeout=CREATE_RESPONSE_TIMEOUT
            )
            logger.info("Created credential id=%s name=%s", credential_id, display_name)

        with allure.step("Step 2 — Open the credential detail page"):
            list_page.click_credential_card(display_name)
            detail_page.wait_for_page_load()

            assert detail_page.get_credential_id_from_url() == str(credential_id), (
                f"Detail page URL should carry the created credential id {credential_id}, got {page.url}"
            )
            assert detail_page.get_display_name() == display_name, (
                f"Detail page should show {display_name!r} in the Display Name field"
            )
            expect(detail_page.secret_native_input(SECRET_FIELD_KEY)).to_be_visible()

        with allure.step("Step 3 — Click 'Test connection' with the valid credential"):
            expect(detail_page.test_connection_button).to_be_enabled()

            with page.expect_response(
                lambda r: (
                    f"/configurations/check_connection/{settings.elitea_project_id}/{CREDENTIAL_TYPE}"
                    in r.url
                    and r.request.method == "POST"
                ),
                timeout=CHECK_CONNECTION_TIMEOUT,
            ) as ok_response_info:
                detail_page.test_connection_button.click()
            ok_response = ok_response_info.value

            assert ok_response.status == 200, (
                f"Expected 200 from check_connection with valid credentials, got {ok_response.status}"
            )
            assert ok_response.json() == {"success": True}, (
                f"Expected a successful check_connection body, got {ok_response.json()!r}"
            )

            # The success indicator the case names: a SUCCESS-severity toast
            # carrying the exact message. Severity is read off the product's
            # own data-severity attribute, not a CSS class.
            expect(detail_page.success_toast()).to_be_visible()
            expect(detail_page.toast_message).to_have_text("The connection is OK!")

            # ...and no failure indicator anywhere.
            expect(detail_page.secret_field_helper_text(SECRET_FIELD_KEY)).to_have_count(0)
            expect(detail_page.secret_native_input(SECRET_FIELD_KEY)).to_have_attribute(
                "aria-invalid", "false"
            )
            expect(detail_page.api_error_message).to_have_count(0)

            # The toast auto-hides; awaiting that (real product behaviour, no
            # sleep) gives step 5 a clean baseline for its "no success toast"
            # assertion.
            expect(detail_page.success_toast()).to_have_count(0, timeout=TOAST_AUTOHIDE_TIMEOUT)

        with allure.step(f"Step 4 — Replace the secret with the invalid value {INVALID_SECRET!r}"):
            detail_page.replace_secret_value(SECRET_FIELD_KEY, INVALID_SECRET)

            expect(detail_page.secret_native_input(SECRET_FIELD_KEY)).to_have_value(INVALID_SECRET)

        with allure.step("Step 5 — Click 'Test connection' again with the invalid secret"):
            with page.expect_response(
                lambda r: (
                    f"/configurations/check_connection/{settings.elitea_project_id}/{CREDENTIAL_TYPE}"
                    in r.url
                    and r.request.method == "POST"
                ),
                timeout=CHECK_CONNECTION_TIMEOUT,
            ) as fail_response_info:
                detail_page.test_connection_button.click()
            fail_response = fail_response_info.value

            assert fail_response.status == 400, (
                f"Expected 400 from check_connection with an invalid secret, got {fail_response.status}"
            )
            fail_body = fail_response.json()
            assert fail_body.get("success") is False, (
                f"Expected success=false in the failing check_connection body, got {fail_body!r}"
            )
            service_message = fail_body.get("message")
            assert service_message, (
                f"Expected the failing check_connection body to carry a message, got {fail_body!r}"
            )

            # The case's "failure/error indicator ... in the token field": the
            # field goes invalid AND renders the service's own reason. The
            # expected text is the response body's own message — the product
            # is the oracle, so this catches the UI dropping or mangling the
            # reason without pinning a backend wording (AFS § divergence #2).
            expect(detail_page.secret_native_input(SECRET_FIELD_KEY)).to_have_attribute(
                "aria-invalid", "true"
            )
            helper = detail_page.secret_field_helper_text(SECRET_FIELD_KEY)
            expect(helper).to_be_visible()
            expect(helper).to_have_text(service_message)

            # The error is inline, not the global banner — and no success
            # toast is raised for invalid credentials (the case's Fail criterion).
            expect(detail_page.api_error_message).to_have_count(0)
            expect(detail_page.success_toast()).to_have_count(0)

    finally:
        if credential_id:
            try:
                credential_api.delete_credential(credential_id)
                logger.info("Teardown: deleted credential id=%s", credential_id)
            except Exception as exc:  # noqa: BLE001 — teardown must never mask the verdict
                logger.warning("Teardown: failed to delete credential %s: %s", credential_id, exc)
