"""Test for Credential — Error States.

Verifies that the credentials UI reports its three error states with a
specific, human-readable reason and without leaking implementation detail:

* an invalid token -> "Test connection" surfaces the service's own auth
  failure inline on the offending form field;
* an unreachable Base Url -> the credential still SAVES, and testing it
  surfaces a connection error;
* a non-existent credential id in the URL -> the app's shared not-found page;
* none of those messages carries a raw stack trace.

Test case: ELITEA-1980
AFS: test-specs/toolkits-credentials/l2_credential-error-states_ELITEA-1980.md

Vehicle: the **Github** credential type with Token auth. Github's schema
requires only ``base_url`` and both scenarios here want *invalid* input, so
this spec needs no valid external test data at all — it is immune to
elitea-testing-public#1673 (the expired ``GIT_HUB_TOKEN``) and has no
``pytest.skip`` path.

No substitution of the system under test: the credential is created through
the real UI form, both failures are produced by the product's own
``check_connection`` round trip against the real (and really unreachable)
targets, the 404 is a real backend 404, and every asserted message is
asserted against the response body that produced it rather than against a
string this test authored.
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
from pages.not_found_page import NotFoundPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.credentials,
    pytest.mark.p2,
    pytest.mark.regression,
    pytest.mark.new,
]

# --- The case's Test Data, in one place -----------------------------------
CREDENTIAL_TYPE = "github"
AUTH_METHOD = "token"
SECRET_FIELD_KEY = "access_token"
URL_FIELD_KEY = "base_url"
INVALID_TOKEN = "invalid_token_xyz"
# RFC 2606 reserved TLD — can never resolve, so the failure is a property of
# the address itself rather than of this machine's network.
UNREACHABLE_BASE_URL = "http://unreachable.example.invalid"
NON_EXISTENT_CREDENTIAL_ID = "99999"

# The Display Name input carries a real maxLength (MAX_NAME_LENGTH,
# EliteaUI/src/common/constants.js, applied at ToolBaseProperty.jsx:589 for
# k === 'label'): an over-long generated name is silently TRUNCATED by the
# field, so the create response carries a different label than this test typed
# and every later lookup-by-name misses, far from the cause (cost ELITEA-1970
# a run).
MAX_DISPLAY_NAME_LENGTH = 32

CREATE_RESPONSE_TIMEOUT = 20_000
CHECK_CONNECTION_TIMEOUT = 45_000
DETAIL_RESPONSE_TIMEOUT = 20_000

# Markers of a raw stack trace / exception dump leaking into a user-facing
# message (the case's Fail criterion). Matched case-insensitively.
STACK_TRACE_MARKERS = (
    "traceback",
    "most recent call last",
    'file "',
    ", line ",
    " at 0x",
    "<class '",
    "raise ",
)
# A user-facing message is a sentence, not a dump.
MAX_USER_FACING_MESSAGE_LENGTH = 200


def _assert_user_friendly(message: str, where: str) -> None:
    """Assert *message* reads like a user-facing sentence, not a stack trace."""
    assert message.strip(), f"{where}: expected a non-empty error message, got {message!r}"
    lowered = message.lower()
    for marker in STACK_TRACE_MARKERS:
        assert marker not in lowered, (
            f"{where}: error message exposes internal detail ({marker!r} found) — "
            f"the case requires user-friendly text, got {message!r}"
        )
    assert "\n" not in message.strip(), (
        f"{where}: error message spans multiple lines, which is how a stack trace "
        f"reaches a user — got {message!r}"
    )
    assert len(message) <= MAX_USER_FACING_MESSAGE_LENGTH, (
        f"{where}: error message is {len(message)} chars, over the "
        f"{MAX_USER_FACING_MESSAGE_LENGTH}-char sanity bound for a user-facing "
        f"sentence — got {message!r}"
    )


def _check_connection_response(page, action):
    """Run *action* and return the check_connection response it triggers."""
    with page.expect_response(
        lambda r: (
            f"/configurations/check_connection/{settings.elitea_project_id}/{CREDENTIAL_TYPE}"
            in r.url
            and r.request.method == "POST"
        ),
        timeout=CHECK_CONNECTION_TIMEOUT,
    ) as response_info:
        action()
    return response_info.value


@allure.title("ELITEA-1980 — Credential error states: bad token, unreachable host, bad id")
def test_credential_error_states(page, credential_api):
    """Every credential error state reports a specific, stack-trace-free reason."""
    display_name = f"autotest_cred_err_{int(time.time())}"
    assert len(display_name) <= MAX_DISPLAY_NAME_LENGTH, (
        f"Generated Display Name {display_name!r} is {len(display_name)} chars, over the "
        f"field's maxLength of {MAX_DISPLAY_NAME_LENGTH} — it would be silently truncated "
        f"by the input and every later lookup by name would miss"
    )
    credential_id = None
    # The strings the PRODUCT produced in this run, checked together in step 6.
    observed_messages: list[tuple[str, str]] = []

    create_page = CredentialCreatePage(page)
    list_page = CredentialsListPage(page)
    detail_page = CredentialDetailPage(page)
    not_found_page = NotFoundPage(page)

    try:
        with allure.step(f"Step 1 — Fill the {CREDENTIAL_TYPE} create form with the invalid token"):
            create_page.open_type_form(CREDENTIAL_TYPE)
            create_page.set_display_name(display_name)
            assert create_page.display_name_input.input_value() == display_name, (
                f"Display Name field should read {display_name!r} after filling, got "
                f"{create_page.display_name_input.input_value()!r} — a mismatch here means "
                f"the field's maxLength ({MAX_DISPLAY_NAME_LENGTH}) truncated the name"
            )

            create_page.select_auth_method(AUTH_METHOD)
            create_page.set_access_token(INVALID_TOKEN)

            # The case's step-1 expected result: "Credential form accepts the
            # input" — the field holds exactly what was typed, and the form is
            # in a submittable state.
            expect(create_page.secret_native_input(SECRET_FIELD_KEY)).to_have_value(INVALID_TOKEN)
            assert create_page.base_url_input.input_value() == settings.github_base_url, (
                f"Github's Base Url should carry its schema default "
                f"{settings.github_base_url!r}, got {create_page.base_url_input.input_value()!r}"
            )
            assert create_page.is_save_enabled(), (
                "Save should be enabled once Display Name, Base Url and the token are filled"
            )

        with allure.step("Step 2 — Click 'Test connection' with the invalid token"):
            expect(create_page.test_connection_button).to_be_enabled()
            auth_response = _check_connection_response(
                page, lambda: create_page.test_connection_button.click()
            )

            assert auth_response.status == 400, (
                f"Expected 400 from check_connection with an invalid token, got {auth_response.status}"
            )
            auth_body = auth_response.json()
            assert auth_body.get("success") is False, (
                f"Expected success=false in the failing check_connection body, got {auth_body!r}"
            )
            auth_message = auth_body.get("message")
            assert auth_message, (
                f"Expected the failing check_connection body to carry a message, got {auth_body!r}"
            )

            # The case's "error message ... with a specific failure reason": the
            # offending field goes invalid and renders the SERVICE's own reason.
            # The field is Base Url, not the token field: with nothing in the
            # message mapping to a Github schema key,
            # credentialError.helpers.js#extractInformationFromCredentialError
            # falls back to assigning the message to every *url* key (AFS
            # § Case-text divergence #1). A mapping change fails here, loudly.
            expect(create_page.field(URL_FIELD_KEY)).to_have_attribute("aria-invalid", "true")
            auth_helper = create_page.field_helper_text(URL_FIELD_KEY)
            expect(auth_helper).to_be_visible()
            # Expected text is the response body's own message — the product is
            # the oracle, so this catches the UI dropping or mangling the reason
            # without pinning a backend wording.
            expect(auth_helper).to_have_text(auth_message)

            # "Specific failure reason" means the category is named, not just
            # that some text appeared.
            assert re.search(r"authentication failed", auth_message, re.IGNORECASE), (
                f"Expected the invalid-token failure to name an authentication failure, "
                f"got {auth_message!r}"
            )
            # No success feedback for a failing credential.
            expect(create_page.success_toast()).to_have_count(0)

            observed_messages.append(("Step 2 (invalid token)", auth_message))

        with allure.step(f"Step 3 — Set an unreachable Base Url ({UNREACHABLE_BASE_URL}) and Save"):
            # set_base_url() appends (click + press_sequentially); the field already
            # holds Github's schema default, so clear it first.
            create_page.clear_base_url()
            create_page.set_base_url(UNREACHABLE_BASE_URL)
            assert create_page.base_url_input.input_value() == UNREACHABLE_BASE_URL, (
                f"Base Url should read {UNREACHABLE_BASE_URL!r} after filling, got "
                f"{create_page.base_url_input.input_value()!r}"
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

            # The case's step-3 expected result: the credential IS saved — an
            # unreachable host is not a validation failure.
            assert create_response.status == 200, (
                f"Expected 200 from the credential-create POST (an unreachable Base Url must "
                f"still save), got {create_response.status}"
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
            expect(list_page.card_by_name(display_name)).to_have_count(1)
            logger.info("Created credential id=%s name=%s", credential_id, display_name)

        with allure.step("Step 4 — Open the saved credential and click 'Test connection'"):
            list_page.click_credential_card(display_name)
            detail_page.wait_for_page_load()
            assert detail_page.get_credential_id_from_url() == str(credential_id), (
                f"Detail page URL should carry the created credential id {credential_id}, got {page.url}"
            )

            conn_response = _check_connection_response(
                page, lambda: detail_page.test_connection_button.click()
            )

            assert conn_response.status == 400, (
                f"Expected 400 from check_connection against an unreachable host, got "
                f"{conn_response.status}"
            )
            conn_body = conn_response.json()
            assert conn_body.get("success") is False, (
                f"Expected success=false in the failing check_connection body, got {conn_body!r}"
            )
            conn_message = conn_body.get("message")
            assert conn_message, (
                f"Expected the failing check_connection body to carry a message, got {conn_body!r}"
            )

            # The case's "timeout or connection refused" is a CATEGORY claim —
            # the product answers fast and explicitly rather than hanging (AFS
            # § Case-text divergence #2), so the category is what is asserted.
            assert re.search(r"connection error|unable to reach|timeout|refused", conn_message, re.IGNORECASE), (
                f"Expected the unreachable-host failure to name a connection problem, "
                f"got {conn_message!r}"
            )

            expect(detail_page.field(URL_FIELD_KEY)).to_have_attribute("aria-invalid", "true")
            conn_helper = detail_page.field_helper_text(URL_FIELD_KEY)
            expect(conn_helper).to_be_visible()
            expect(conn_helper).to_have_text(conn_message)
            expect(detail_page.success_toast()).to_have_count(0)

            observed_messages.append(("Step 4 (unreachable host)", conn_message))

        with allure.step(
            f"Step 5 — Open a credential detail URL with the non-existent id {NON_EXISTENT_CREDENTIAL_ID}"
        ):
            # The not-found state renders only AFTER the detail GET resolves;
            # until then the route shows an empty editable form. Settle on the
            # product's own response, never on a timer (AFS § divergence #3).
            with page.expect_response(
                lambda r: (
                    f"/configurations/configuration/{settings.elitea_project_id}/"
                    f"{NON_EXISTENT_CREDENTIAL_ID}" in r.url
                    and r.request.method == "GET"
                ),
                timeout=DETAIL_RESPONSE_TIMEOUT,
            ) as missing_response_info:
                not_found_page.open_route(f"/credentials/all/{NON_EXISTENT_CREDENTIAL_ID}")
            missing_response = missing_response_info.value

            assert missing_response.status == 404, (
                f"Expected 404 for a non-existent credential id, got {missing_response.status}"
            )

            not_found_page.wait_for_not_found()
            not_found_text = not_found_page.get_not_found_text()
            assert re.search(r"page not found", not_found_text, re.IGNORECASE), (
                f"Expected the shared not-found state to name the condition, got {not_found_text!r}"
            )
            # ...and the app does NOT leave a blank, editable credential form
            # behind on a route whose entity does not exist.
            expect(detail_page.save_button).to_have_count(0)

            observed_messages.append(("Step 5 (non-existent id)", not_found_text))

        with allure.step("Step 6 — Every error message is user-friendly, with no raw stack traces"):
            assert len(observed_messages) == 3, (
                f"Expected an error message from each of steps 2, 4 and 5, got {observed_messages!r}"
            )
            for where, message in observed_messages:
                _assert_user_friendly(message, where)
            logger.info("Error messages verified user-friendly: %s", observed_messages)

    finally:
        if credential_id:
            try:
                credential_api.delete_credential(credential_id)
                logger.info("Teardown: deleted credential id=%s", credential_id)
            except Exception as exc:  # noqa: BLE001 — teardown must never mask the verdict
                logger.warning("Teardown: failed to delete credential %s: %s", credential_id, exc)
