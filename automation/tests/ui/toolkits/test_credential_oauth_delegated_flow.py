"""Test for Credential — OAuth-Required Credential Flow (SharePoint Delegated).

Drives the whole SharePoint Delegated lifecycle through the real create form:
the Delegated auth method reveals the OAuth-specific fields, the OAuth Login
button appears, the credential saves with its OAuth settings persisted, and
Login is still there on the saved credential's detail page.

Test case: ELITEA-1981
AFS: test-specs/toolkits-credentials/
     l1_oauth-required-credential-flow-sharepoint-delegated_ELITEA-1981.md

Case-text clarifications (filed as elitea-testing-public#1711 — case text, not
product defects; the live contract is asserted, never the stale wording):

* **Step 5 is ordered too early.** The Login button is NOT revealed by picking
  Delegated: ``CredentialForm.jsx:342`` gates it on ``oauthTokenKey``, derived
  from ``settings.oauth_discovery_endpoint`` (``:168-176``), so it appears the
  moment that field is non-empty. This test asserts BOTH directions — absent
  before the endpoint is filled, visible after — turning the clarification into
  a test-enforced invariant.
* **Saving navigates to ``/credentials/all``**, not to the new credential's
  detail page, so step 8 opens the detail route explicitly.

No substitution of the system under test: the credential is created through the
real UI form against the real backend, and every asserted value comes from the
product (the persisted ``data`` is read off the create response itself).
Placeholder client id/secret are sufficient — nothing here needs a Microsoft
tenant, so this case is immune to the expired ``GIT_HUB_TOKEN`` (#1673).
"""

import logging
import re
import time

import allure
import pytest
from config import settings
from pages.credential_create_page import CredentialCreatePage
from pages.credential_detail_page import CredentialDetailPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.credentials,
    pytest.mark.p1,
    pytest.mark.regression,
    pytest.mark.new,
]

CREDENTIAL_TYPE = "sharepoint"
AUTH_METHOD_APP_ONLY = "app-only"  # the schema default
AUTH_METHOD_DELEGATED = "delegated"  # slug = the option VALUE, lowercased

CLIENT_ID = "placeholder-client-id"
CLIENT_SECRET = "placeholder-client-secret"
SITE_URL = "https://contoso.sharepoint.com/sites/test"
OAUTH_DISCOVERY_ENDPOINT = "https://login.microsoftonline.com/placeholder-tenant"
SCOPES = "Sites.Read.All"

# The three fields the Delegated subsection adds on top of the App-only form.
DELEGATED_TEXT_FIELDS = ("oauth_discovery_endpoint", "scopes")
AUTO_REFRESH_TOKEN_FIELD = "auto_refresh_token"

# ToolBaseProperty.jsx:589 applies a real maxLength (MAX_NAME_LENGTH = 32) to
# the Display Name field, so a longer generated name is silently TRUNCATED by
# the input and every later lookup by name misses, far from the cause.
MAX_DISPLAY_NAME_LENGTH = 32

SAVE_RESPONSE_TIMEOUT = 20_000


def _is_known_518_warning(msg) -> bool:
    """Filter the pre-existing, already-filed, OPEN ``CredentialsList.jsx``
    double-``onRefetch()`` crash (elitea-testing-public#518) — same filter
    established by ``test_credential_create.py``. Saving lands this flow on
    ``/credentials/all``, where that crash reproduces at ~60-75%.
    """
    text = msg.text
    return (
        "Cannot refetch a query that has not been started yet" in text
        or ("above error occurred" in text and "<CredentialsList>" in text)
    )


def _is_known_554_warning(msg) -> bool:
    """Filter the pre-existing, already-filed elitea-testing-public#554 — the
    ``toolkitTypes`` RTK-Query race that builds its URL with an empty projectId
    segment and 404s. Matched by the message's own ``location.url`` rather than
    by "404" alone, so a genuinely new 404 is not masked.
    """
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url


def _is_known_291_warning(msg) -> bool:
    """Filter the pre-existing, already-filed React "missing key prop" /
    validateDOMNesting dev warnings on the credential type surfaces
    (elitea-testing-public#291), as ``test_credential_create.py`` does.
    """
    text = msg.text
    return (
        'unique "key" prop' in text
        or ("validateDOMNesting" in text and "<p>" in text)
        or ("validateDOMNesting" in text and "%s" in text)
    )


class TestCredentialOAuthDelegatedFlow:
    """ELITEA-1981 — SharePoint Delegated credential: OAuth fields, save, Login."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1981_oauth-required-credential-flow.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1711", "Case-text clarification #1711")
    @allure.title("ELITEA-1981 — SharePoint Delegated credential saves with OAuth fields and keeps Login")
    def test_sharepoint_delegated_credential_oauth_flow(self, page, credential_api):
        """Delegated reveals the OAuth fields, the credential saves with them, and
        Login remains available on the saved credential's detail page."""
        display_name = f"autotest_sp_deleg_{int(time.time())}"
        assert len(display_name) <= MAX_DISPLAY_NAME_LENGTH, (
            f"Generated Display Name {display_name!r} is {len(display_name)} chars, over the field's "
            f"maxLength of {MAX_DISPLAY_NAME_LENGTH} — it would be silently truncated by the input"
        )
        credential_id = None

        console_messages = []

        def _on_console(msg):
            if (
                msg.type in ("error", "warning")
                and not _is_known_291_warning(msg)
                and not _is_known_518_warning(msg)
                and not _is_known_554_warning(msg)
            ):
                console_messages.append(msg)

        create_page = CredentialCreatePage(page)
        detail_page = CredentialDetailPage(page)

        try:
            page.on("console", _on_console)

            with allure.step("Step 1 — Open the Credentials create form for the SharePoint type"):
                # The type-card grid on /credentials/all only renders on a
                # ZERO-credential project (CredentialsList.jsx), so the create
                # route is the stable entry point (_surface.md § Cheap
                # navigation fact). open_type_form settles on the schema-driven
                # form rendering, never on networkidle (unreachable here).
                create_page.open_type_form(CREDENTIAL_TYPE)
                expect(create_page.display_name_input).to_be_visible()
                assert f"/credentials/create-credential/{CREDENTIAL_TYPE}" in page.url, (
                    f"Expected the SharePoint create-credential route, got {page.url}"
                )

            with allure.step("Step 2 — Verify the SharePoint-specific fields are displayed (App-only default)"):
                expect(create_page.field("client_id")).to_be_visible()
                expect(create_page.field("client_secret")).to_be_visible()
                expect(create_page.field("site_url")).to_be_visible()

                # App-only is the schema default, so the Delegated subsection's
                # fields must NOT be rendered yet — that absence is what makes
                # Step 3 a real state change rather than a presence check that
                # would pass even if everything rendered eagerly.
                expect(create_page.auth_radio(AUTH_METHOD_APP_ONLY)).to_be_checked()
                for field_key in DELEGATED_TEXT_FIELDS:
                    expect(create_page.field(field_key)).to_have_count(0)
                expect(create_page.field_checkbox(AUTO_REFRESH_TOKEN_FIELD)).to_have_count(0)

            with allure.step('Step 3 — Select the "Delegated" auth radio'):
                create_page.select_auth_method(AUTH_METHOD_DELEGATED)

                expect(create_page.auth_radio(AUTH_METHOD_DELEGATED)).to_be_checked()
                expect(create_page.auth_radio(AUTH_METHOD_APP_ONLY)).not_to_be_checked()

            with allure.step(
                "Step 4 — Verify the Delegated fields appear: Auto Refresh Token, "
                "Oauth Discovery Endpoint, Scopes"
            ):
                expect(create_page.field_checkbox(AUTO_REFRESH_TOKEN_FIELD)).to_be_visible()
                expect(create_page.field("oauth_discovery_endpoint")).to_be_visible()
                expect(create_page.field("scopes")).to_be_visible()

            with allure.step(
                "Step 5 — Verify the Login button appears next to Test connection "
                "(only once Oauth Discovery Endpoint is filled — clarification #1711)"
            ):
                expect(create_page.test_connection_button).to_be_visible()
                # Case-text clarification #1711: Login is gated on oauthTokenKey
                # (CredentialForm.jsx:342 / :168-176), i.e. on a non-empty
                # oauth_discovery_endpoint — NOT on the Delegated radio. Both
                # directions are asserted so a regression making the button
                # appear unconditionally fails here.
                expect(create_page.oauth_login_button).to_have_count(0)

                create_page.type_into_field("oauth_discovery_endpoint", OAUTH_DISCOVERY_ENDPOINT)

                expect(create_page.oauth_login_button).to_be_visible()
                expect(create_page.test_connection_button).to_be_visible()

            with allure.step("Step 6 — Fill in all remaining required fields"):
                create_page.set_display_name(display_name)
                create_page.type_into_field("client_id", CLIENT_ID)
                create_page.replace_secret_value("client_secret", CLIENT_SECRET)
                create_page.type_into_field("site_url", SITE_URL)
                create_page.type_into_field("scopes", SCOPES)

                expect(create_page.display_name_input).to_have_value(display_name)
                expect(create_page.field("client_id")).to_have_value(CLIENT_ID)
                expect(create_page.secret_native_input("client_secret")).to_have_value(CLIENT_SECRET)
                expect(create_page.field("site_url")).to_have_value(SITE_URL)
                expect(create_page.field("oauth_discovery_endpoint")).to_have_value(
                    OAUTH_DISCOVERY_ENDPOINT
                )
                expect(create_page.field("scopes")).to_have_value(SCOPES)

                assert create_page.is_save_enabled(), (
                    "Save should be enabled once every required field is filled with real keystrokes "
                    "(the button is gated on formik dirty — CredentialsTabBar.jsx:115)"
                )

            with allure.step("Step 7 — Save the credential"):
                with page.expect_response(
                    lambda r: (
                        f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=SAVE_RESPONSE_TIMEOUT,
                ) as save_response_info:
                    create_page.save_button.click()
                save_response = save_response_info.value

                assert save_response.status == 200, (
                    f"Expected 200 from the credential-create POST, got {save_response.status}"
                )
                save_body = save_response.json()
                credential_id = save_body.get("id")
                assert credential_id, f"Expected a numeric id in the create response, got {save_body!r}"
                assert save_body.get("label") == display_name, (
                    f"Expected the created credential's label to be {display_name!r}, "
                    f"got {save_body.get('label')!r}"
                )

                # "Saved with Delegated auth type" — the product exposes that as
                # the persisted Delegated-only settings. The free-text Scopes
                # input is stored as an ARRAY; the response is the oracle.
                saved_data = save_body.get("data") or {}
                assert saved_data.get("scopes") == [SCOPES], (
                    f"Expected the persisted scopes to be the array [{SCOPES!r}] built from the "
                    f"free-text input, got {saved_data.get('scopes')!r}"
                )
                assert saved_data.get("oauth_discovery_endpoint") == OAUTH_DISCOVERY_ENDPOINT, (
                    "Expected the persisted oauth_discovery_endpoint to round-trip, got "
                    f"{saved_data.get('oauth_discovery_endpoint')!r}"
                )
                assert saved_data.get("site_url") == SITE_URL, (
                    f"Expected the persisted site_url to round-trip, got {saved_data.get('site_url')!r}"
                )

                # Clarification #1711: saving navigates to the LIST, not to the
                # new credential's detail page.
                page.wait_for_url(
                    re.compile(r".*/credentials/all/?(\?.*)?$"), timeout=SAVE_RESPONSE_TIMEOUT
                )
                logger.info("Created credential id=%s name=%s", credential_id, display_name)

            with allure.step(
                "Step 8 — Open the saved credential's detail page and verify Login remains available"
            ):
                detail_page.open_by_id(credential_id)

                expect(detail_page.oauth_login_button).to_be_visible()
                expect(detail_page.test_connection_button).to_be_visible()

                # The detail page derives the selected auth subsection from
                # which fields hold values (ToolSection.jsx:58-72) — this is
                # the only observable the product offers for "saved with
                # Delegated auth type".
                expect(detail_page.auth_radio(AUTH_METHOD_DELEGATED)).to_be_checked()
                expect(detail_page.field("oauth_discovery_endpoint")).to_have_value(
                    OAUTH_DISCOVERY_ENDPOINT
                )
                expect(detail_page.field("scopes")).to_have_value(SCOPES)
                assert detail_page.get_display_name() == display_name, (
                    f"Expected the detail page to show {display_name!r} in Display Name, "
                    f"got {detail_page.get_display_name()!r}"
                )

            with allure.step("Side-channel check — no console errors/warnings across the full flow"):
                # Known defects #291 / #518 / #554 are filtered above (all filed,
                # all pre-existing); anything else fails this check for real.
                assert not console_messages, (
                    f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
                )

        finally:
            with allure.step("Cleanup — delete the credential this case created"):
                if credential_id is not None:
                    try:
                        credential_api.delete_credential(int(credential_id))
                        logger.info("Teardown: deleted credential id=%s", credential_id)
                    except Exception as exc:  # noqa: BLE001 — teardown must never mask the verdict
                        logger.warning("Teardown: failed to delete credential %s: %s", credential_id, exc)
