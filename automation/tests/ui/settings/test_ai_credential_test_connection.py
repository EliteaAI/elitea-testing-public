"""UI test — AI-provider credential: Test connection error, then success (Settings -> AI Providers).

Test case: ELITEA-2415
AFS: test-specs/settings-ai-providers/l1_test-connection-error-then-success-for-ai-credential_ELITEA-2415.md

Case-identity note (AFS § Case-identity note): there is no "Credentials" item in
the settings drawer. The case's "Settings -> Credentials" is the **AI Credentials**
half of Settings -> AI Providers (`/settings/ai-providers`), whose "+" flow is
`/settings/create-ai-provider/{type}` and renders the SAME `CredentialForm.jsx`
the toolkit-credentials routes render. Same nonexistent-"AI Configuration"-page
drift already tracked by #1250 / #1772 / #1906 / #1982 — not re-filed.

Case-text divergence (non-blocking, AFS § Case-text divergence): the case names
the error text only by example ("e.g. 'Connection failed' or 'Invalid API key'").
The product renders the **backend's own** message verbatim, so this spec asserts
the carry-through invariant — the inline text EQUALS the failing response body's
own `message` — plus a category regex, exactly as merged ELITEA-1970/1980 do.
No literal wording is pinned.

Why this is a NEW spec rather than an extension of
`tests/ui/toolkits/test_credential_test_connection.py` (ELITEA-1970): that spec
runs the opposite direction (success then failure) on the toolkit-credential
vehicle and never re-tests after a fix. ELITEA-2415's subject is the AI-provider
vehicle plus the RECOVERY direction — a failure whose indicators must CLEAR once
the credential is corrected in the same form session.

No substitution of the system under test (AFS § Fidelity Declaration): no
`page.route`, no `route.fulfill`, no `page.evaluate` writing app state, no
monkeypatch, no API-seeded precondition. Both `check_connection` round trips are
real calls to the real backend, which really calls the real LLM gateway, and every
asserted string is read off the response body that produced it. The valid secret
is real environment test data (`ELITEA_API_TOKEN`, which authenticates against
Elitea's own OpenAI-compatible gateway) — never logged, never asserted on by
value, only typed.

**Nothing is created and nothing is saved**: the case ends with the form still
unsaved, so there is no teardown and no shared-state pollution.

Markers:
    - ui, credentials, p1, regression, new
"""

import logging
import re
import time

import allure
import pytest
from config import settings
from pages.ai_provider_form_page import AiProviderFormPage
from pages.ai_providers_page import AIProvidersPage
from pages.settings_drawer_page import SettingsDrawerPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.credentials,
    pytest.mark.p1,
    pytest.mark.regression,
    pytest.mark.new,
]

# --- The case's vehicle, in ONE block (the ELITEA-1970 convention) --------
CREDENTIAL_TYPE = "open_ai"
SECRET_FIELD_KEY = "api_key"
BASE_FIELD_KEY = "api_base"
#: Elitea's own OpenAI-compatible gateway — `ELITEA_API_TOKEN` authenticates
#: against it (verified out-of-band, `_surface.md` § A VALID OpenAI-compatible
#: credential exists in the suite's own test data), which is what makes the
#: case's SUCCESS half producible by the real system with no substitution.
API_BASE = "https://dev.elitea.ai/llm/v1"
INVALID_API_KEY = "sk-invalid-key-xyz-2415"

#: The Display Name input carries a real maxLength (MAX_NAME_LENGTH,
#: EliteaUI/src/common/constants.js) — an over-long generated name is silently
#: TRUNCATED by the field, and every later lookup by name then misses far from
#: the cause. Same guard as ELITEA-1970.
MAX_DISPLAY_NAME_LENGTH = 32

#: The failing message's CATEGORY, not its wording — the wording is the
#: gateway's and is asserted by equality against the response body instead.
AUTH_FAILURE_PATTERN = re.compile(r"authentication failed", re.IGNORECASE)

CHECK_CONNECTION_TIMEOUT = 45_000  # a real round trip to the real LLM gateway
UI_ELEMENT_TIMEOUT = 10_000
FORM_URL_PATTERN = re.compile(r"/settings/create-ai-provider/open_ai")


def _check_connection_matcher(response) -> bool:
    return (
        f"/configurations/check_connection/{settings.elitea_project_id}/{CREDENTIAL_TYPE}" in response.url
        and response.request.method == "POST"
    )


@pytest.mark.skipif(
    not settings.elitea_api_token,
    reason=(
        "ELITEA_API_TOKEN must be set in .env.test — the case's step-7 precondition is a "
        "credential that genuinely authenticates, which cannot be faked"
    ),
)
@allure.title("ELITEA-2415 — AI credential Test connection: inline error, then success after correction")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "settings/ai-configuration/ELITEA-2415_test-connection-button-shows-error-for-invalid-or-expired-cr.md",
    "onetest-ai Test Case link",
)
def test_ai_credential_test_connection_error_then_success(page):
    """Invalid api_key -> inline field error + form stays open; corrected key ->
    success toast AND every failure indicator cleared."""
    providers_page = AIProvidersPage(page)
    drawer = SettingsDrawerPage(page)
    form = AiProviderFormPage(page)
    # The form is left dirty and unsaved on purpose (the case never saves), so a
    # navigate-away confirm must not wedge teardown.
    page.on("dialog", lambda dialog: dialog.accept())

    display_name = f"autotest_2415_conn_{int(time.time())}"
    assert len(display_name) <= MAX_DISPLAY_NAME_LENGTH, (
        f"Generated Display Name {display_name!r} is {len(display_name)} chars, over the field's "
        f"maxLength of {MAX_DISPLAY_NAME_LENGTH} — it would be silently truncated by the input"
    )

    with allure.step("Step 1 — Navigate to Settings -> AI Providers (the case's 'Settings -> Credentials')"):
        providers_page.navigate()
        expect(providers_page.page_title).to_have_text("AI Providers")
        # The case's target section — the AI Credentials half of this page.
        expect(providers_page.ai_credentials_section_header).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        # The drawer agrees this is where we are — state read off the product's
        # own `data-active` attribute, not a CSS class.
        expect(drawer.nav_item("ai-providers")).to_have_attribute("data-active", "true")

    with allure.step("Step 2 — Click '+' and choose the OpenAI provider type"):
        providers_page.click_create()
        expect(providers_page.type_card(CREDENTIAL_TYPE)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        providers_page.click_type_card(CREDENTIAL_TYPE)
        expect(page).to_have_url(FORM_URL_PATTERN)
        form.wait_for_form()
        # Settle on a SCHEMA-ONLY field: `wait_for_form` returns on the
        # pre-schema render, and the schema re-render that follows WIPES
        # anything typed in the gap (`_surface.md`, AiProviderFormPage docs).
        form.wait_for_schema_field(BASE_FIELD_KEY)
        expect(form.secret_native_input(SECRET_FIELD_KEY)).to_be_visible()

    with allure.step(f"Step 3 — Fill Display Name, Api Base and the INVALID Api Key {INVALID_API_KEY!r}"):
        expect(form.save_button).to_be_disabled()

        form.set_display_name(display_name)
        # Read-back guard: `fill()`-style writes into these MUI controlled
        # inputs can reach the backend EMPTY while the DOM looks right
        # (`_surface.md` § Typing into these forms).
        expect(form.display_name_input).to_have_value(display_name)
        # The ID mirrors the Display Name (ELITEA-2409's subject).
        expect(form.id_input).to_have_value(display_name)

        form.set_schema_field(BASE_FIELD_KEY, API_BASE)
        expect(form.field(BASE_FIELD_KEY)).to_have_value(API_BASE)

        form.fill_secret_field(SECRET_FIELD_KEY, INVALID_API_KEY)
        expect(form.secret_native_input(SECRET_FIELD_KEY)).to_have_value(INVALID_API_KEY)

        # The form now considers the record complete — without this, "Test
        # connection is enabled" below would prove nothing about the form
        # having accepted the input.
        expect(form.save_button).to_be_enabled()

    with allure.step("Step 4 — Click 'Test connection' with the invalid credential"):
        expect(form.test_connection_button).to_be_enabled()

        with page.expect_response(_check_connection_matcher, timeout=CHECK_CONNECTION_TIMEOUT) as fail_info:
            form.test_connection_button.click()
        fail_response = fail_info.value

        assert fail_response.status == 400, (
            f"Expected 400 from check_connection with an invalid api_key, got {fail_response.status}"
        )
        fail_body = fail_response.json()
        assert fail_body.get("success") is False, (
            f"Expected success=false in the failing check_connection body, got {fail_body!r}"
        )
        service_message = fail_body.get("message")
        assert service_message, (
            f"Expected the failing check_connection body to carry a message, got {fail_body!r}"
        )
        logger.info("check_connection rejected the invalid key: %s", service_message)

    with allure.step("Step 5 — A user-facing error is shown inline, carrying the service's own reason"):
        key_helper = form.field_helper_text(SECRET_FIELD_KEY)
        base_helper = form.field_helper_text(BASE_FIELD_KEY)

        # Both fields light up: `extractInformationFromCredentialError` maps an
        # authentication message onto the secret key AND falls back to every
        # `*url*` key. Pinning only one would pass while the other silently
        # changed (AFS Axis 2).
        expect(key_helper).to_be_visible()
        expect(base_helper).to_be_visible()
        # The product is the oracle: the rendered text is asserted against the
        # response body that produced it, never against a wording this test
        # authored.
        expect(key_helper).to_have_text(service_message)
        expect(base_helper).to_have_text(service_message)
        assert AUTH_FAILURE_PATTERN.search(service_message), (
            f"Expected an authentication-category failure reason, got {service_message!r}"
        )

        expect(form.secret_native_input(SECRET_FIELD_KEY)).to_have_attribute("aria-invalid", "true")
        expect(form.field(BASE_FIELD_KEY)).to_have_attribute("aria-invalid", "true")

        # The typed secret must never be echoed back in full — the product
        # masks it (`sk-inval***********2415`), and a regression that stops
        # masking is a real credential leak this assertion catches.
        expect(key_helper).not_to_contain_text(INVALID_API_KEY)

        # The case's Fail criterion: no success feedback for an invalid
        # credential — and the error is INLINE, not the global banner.
        expect(form.success_toast()).to_have_count(0)
        expect(form.api_error_message).to_have_count(0)

    with allure.step("Step 6 — The form remains open for correction (no redirect, values retained)"):
        expect(page).to_have_url(FORM_URL_PATTERN)
        expect(form.save_button).to_be_visible()
        expect(form.discard_button).to_be_visible()
        expect(form.secret_native_input(SECRET_FIELD_KEY)).to_have_value(INVALID_API_KEY)
        expect(form.field(BASE_FIELD_KEY)).to_have_value(API_BASE)
        expect(form.display_name_input).to_have_value(display_name)

    with allure.step("Step 7 — Correct the Api Key and click 'Test connection' again"):
        form.fill_secret_field(SECRET_FIELD_KEY, settings.elitea_api_token)
        # The secret's VALUE is never asserted, logged or screenshotted — only
        # that the field now holds a different secret, and (below) its effect.
        corrected_length = len(form.secret_native_input(SECRET_FIELD_KEY).input_value())
        assert corrected_length == len(settings.elitea_api_token), (
            f"The Api Key field should hold the corrected secret "
            f"({len(settings.elitea_api_token)} chars), it holds {corrected_length}"
        )
        assert corrected_length != len(INVALID_API_KEY), (
            "The corrected secret happens to be the same length as the invalid one — "
            "this test cannot then tell the two apart without asserting the secret itself"
        )

        with page.expect_response(_check_connection_matcher, timeout=CHECK_CONNECTION_TIMEOUT) as ok_info:
            form.test_connection_button.click()
        ok_response = ok_info.value

        assert ok_response.status == 200, (
            f"Expected 200 from check_connection with the corrected api_key, got {ok_response.status}"
        )
        assert ok_response.json() == {"success": True}, (
            f"Expected a successful check_connection body, got {ok_response.json()!r}"
        )

    with allure.step("Step 8 — The success indicator appears AND the failure indicators cleared"):
        # Read inside this step: MUI auto-hides the toast.
        expect(form.success_toast()).to_be_visible()
        expect(form.toast_message).to_have_text("The connection is OK!")

        # The recovery half of the case: a stale inline error next to a success
        # toast would be a contradictory UI, and is exactly what a recovery flow
        # regresses into (AFS Axis 2).
        expect(form.field_helper_text(SECRET_FIELD_KEY)).to_have_count(0)
        expect(form.field_helper_text(BASE_FIELD_KEY)).to_have_count(0)
        expect(form.secret_native_input(SECRET_FIELD_KEY)).not_to_have_attribute("aria-invalid", "true")
        expect(form.field(BASE_FIELD_KEY)).not_to_have_attribute("aria-invalid", "true")
        expect(form.api_error_message).to_have_count(0)
