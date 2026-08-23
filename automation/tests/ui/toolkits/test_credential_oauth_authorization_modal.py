"""Test for Credential — OAuth Authorization Modal Invocation.

Clicking Login on a SharePoint Delegated credential opens the "Configuration
OAuth" dialog off a REAL backend handshake, with the server URL and the
backend-prefixed scopes pre-populated, and Cancel closes it without
authorizing anything.

Test case: ELITEA-1982
AFS: test-specs/toolkits-credentials/l1_oauth-authorization-modal-invocation_ELITEA-1982.md

Declared substitution — TRANSIT ONLY (`.agents/testing.md` § Fidelity policy):
the case's PRECONDITION (an existing SharePoint credential with Delegated auth,
an Oauth Discovery Endpoint and Scopes) is seeded through the API rather than
re-driving the create form — that create flow is ELITEA-1981's own subject, not
this case's. Everything this case observes is still produced by the live
product: the dialog opens off a real
``POST /configurations/check_connection/{project}/sharepoint`` (401 +
``requires_authorization``), and the Scope value is asserted against THAT
response's own ``scopes_supported`` rather than against a string this test
authored. No ``route.fulfill``, no injected state.

⚠️ An "authorization attempt" (the case's step-9 Fail criterion) is a POPUP,
not a request this page makes: ``McpAuthModal.onAuthorize`` opens
``window.open('about:blank', '_blank', …)`` and runs the whole handshake inside
it. Step 9 therefore guards on popup absence + the context's page count; the
``check_connection`` count is only a secondary no-new-handshake check.

⚠️ ``McpAuthModal`` renders ``<Dialog keepMounted>``: the dialog is always in
the DOM and a CLOSED instance holds pre-open state (empty ``Server:`` href, a
Scope value without the ``offline_access`` prefix) — i.e. it mimics precisely
the failures steps 5-6 look for. Every open/closed check therefore asserts
VISIBILITY, never a count (see ``OAuthAuthModalPage``).
"""

import logging
import time

import allure
import pytest
from config import settings
from pages.credential_detail_page import CredentialDetailPage
from pages.oauth_auth_modal_page import OAuthAuthModalPage
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
AUTH_METHOD_DELEGATED = "delegated"

CLIENT_ID = "placeholder-client-id"
CLIENT_SECRET = "placeholder-client-secret"
SITE_URL = "https://contoso.sharepoint.com/sites/test"
OAUTH_DISCOVERY_ENDPOINT = "https://login.microsoftonline.com/placeholder-tenant"
SCOPES = "Sites.Read.All"

DIALOG_TITLE = "Configuration OAuth"
DIALOG_MESSAGE = "This MCP server requires OAuth authorization to access its tools."
SCOPE_PLACEHOLDER = "Enter OAuth scopes (space-separated)"
OFFLINE_ACCESS_PREFIX = "offline_access "

# ToolBaseProperty.jsx:589 caps Display Name at MAX_NAME_LENGTH (32).
MAX_DISPLAY_NAME_LENGTH = 32

CHECK_CONNECTION_TIMEOUT = 45_000  # a real OAuth-metadata round trip


def _is_known_554_warning(msg) -> bool:
    """Filter the pre-existing, already-filed elitea-testing-public#554 —
    the ``toolkitTypes`` RTK-Query race that builds its URL with an empty
    projectId segment and 404s. Matched by the message's own ``location.url``
    so a genuinely new 404 is not masked.
    """
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url


def _is_expected_oauth_401(msg) -> bool:
    """Filter the browser's own "Failed to load resource: 401" entry for THIS
    case's ``check_connection`` call.

    Not a defect and not masking: the 401 + ``requires_authorization`` response
    IS the case's oracle — it is what opens the dialog, and step 3 asserts it
    explicitly off the response object. Chromium logs every non-2xx fetch as a
    console error, so the side channel would otherwise fail on the very
    behaviour the case verifies. Matched by the failing resource's own
    ``location.url`` (the check_connection endpoint) plus the 401 status, never
    by "401" alone — any OTHER 401 in the flow still fails this check.
    """
    location_url = (msg.location or {}).get("url", "")
    return "401" in msg.text and "/configurations/check_connection/" in location_url


def _is_known_291_warning(msg) -> bool:
    """Filter the pre-existing, already-filed React "missing key prop" /
    validateDOMNesting dev warnings on the credential surfaces (#291)."""
    text = msg.text
    return (
        'unique "key" prop' in text
        or ("validateDOMNesting" in text and "<p>" in text)
        or ("validateDOMNesting" in text and "%s" in text)
    )


class TestCredentialOAuthAuthorizationModal:
    """ELITEA-1982 — the Configuration OAuth dialog: contents and Cancel."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1982_credential-oauth-authorization-modal-invocation.md",
        "onetest-ai Test Case link",
    )
    @allure.title("ELITEA-1982 — Login opens the Configuration OAuth dialog; Cancel closes it without action")
    def test_oauth_authorization_modal_invocation(self, page, credential_api):
        """Login opens the dialog with the server URL and backend scopes
        pre-populated; Cancel dismisses it without any authorization request."""
        display_name = f"autotest_sp_oauth_{int(time.time())}"
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
                and not _is_known_554_warning(msg)
                and not _is_expected_oauth_401(msg)
            ):
                console_messages.append(msg)

        # The case's Fail criterion for step 9 is "Cancel triggers an
        # authorization attempt". An authorization attempt is NOT a
        # check_connection call — `McpAuthModal.onAuthorize`
        # (McpAuthModal.jsx:244-258) opens a popup with
        # `window.open('about:blank', '_blank', …)` and then runs
        # `McpAuthFlowHelpers.startMcpAuthFlow`, whose whole handshake
        # (authorize / token / registration) happens INSIDE that popup and is
        # therefore invisible to this page's request listener. So the popup is
        # the direct, unconditional guard: `window.open` is the first thing
        # `onAuthorize` does after its `storageKey` check, and `storageKey =
        # tokenStorageKey || serverUrl` is truthy in the credential flow, so
        # any authorization attempt necessarily produces one.
        popups = []

        def _on_popup(popup_page):
            popups.append(popup_page)

        page.on("popup", _on_popup)

        # Secondary axis (kept as a no-new-backend-handshake guard, NOT as the
        # authorization guard it was mistaken for): every check_connection
        # request this page makes.
        check_connection_requests = []

        def _on_request(request):
            if "/configurations/check_connection/" in request.url:
                check_connection_requests.append(request.url)

        detail_page = CredentialDetailPage(page)
        modal = OAuthAuthModalPage(page)

        try:
            with allure.step(
                "Precondition — seed the SharePoint Delegated credential via API "
                "(declared TRANSIT substitution: the create flow is ELITEA-1981's subject)"
            ):
                seeded = credential_api.create_credential(
                    {
                        "type": CREDENTIAL_TYPE,
                        "elitea_title": display_name,
                        "label": display_name,
                        "data": {
                            "client_id": CLIENT_ID,
                            "client_secret": CLIENT_SECRET,
                            "site_url": SITE_URL,
                            "oauth_discovery_endpoint": OAUTH_DISCOVERY_ENDPOINT,
                            "scopes": [SCOPES],
                        },
                        "shared": False,
                    }
                )
                credential_id = seeded.get("id")
                assert credential_id, f"Expected a numeric id for the seeded credential, got {seeded!r}"
                logger.info("Seeded credential id=%s name=%s", credential_id, display_name)

            page.on("console", _on_console)
            page.on("request", _on_request)

            with allure.step("Step 1 — Open the existing SharePoint Delegated credential"):
                detail_page.open_by_id(credential_id)

                assert detail_page.get_credential_id_from_url() == str(credential_id), (
                    f"Detail page URL should carry credential id {credential_id}, got {page.url}"
                )
                # The precondition, asserted rather than assumed: the product
                # derives the auth subsection from the persisted field values
                # (ToolSection.jsx:58-72).
                expect(detail_page.auth_radio(AUTH_METHOD_DELEGATED)).to_be_checked()
                expect(detail_page.field("oauth_discovery_endpoint")).to_have_value(
                    OAUTH_DISCOVERY_ENDPOINT
                )
                expect(detail_page.field("scopes")).to_have_value(SCOPES)

            with allure.step('Step 2 — Verify the Login button is present next to "Test connection"'):
                expect(detail_page.oauth_login_button).to_be_visible()
                expect(detail_page.test_connection_button).to_be_visible()

            with allure.step('Step 3 — Click Login → the "Configuration OAuth" dialog appears'):
                with page.expect_response(
                    lambda r: (
                        f"/configurations/check_connection/{settings.elitea_project_id}/{CREDENTIAL_TYPE}"
                        in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=CHECK_CONNECTION_TIMEOUT,
                ) as auth_response_info:
                    detail_page.oauth_login_button.click()
                auth_response = auth_response_info.value

                # The dialog is opened by the REAL handshake — asserting the
                # status explicitly means a silent 200 (or any other path into
                # the dialog) cannot pass.
                assert auth_response.status == 401, (
                    f"Expected 401 from check_connection for an unauthorized OAuth credential, "
                    f"got {auth_response.status}"
                )
                auth_body = auth_response.json()
                assert auth_body.get("requires_authorization") is True, (
                    f"Expected requires_authorization=true in the check_connection body, got {auth_body!r}"
                )

                modal.wait_for_open()
                expect(modal.dialog).to_be_visible()
                expect(modal.dialog_title).to_have_text(DIALOG_TITLE)

            with allure.step("Step 4 — Verify the dialog's OAuth-authorization message"):
                expect(modal.dialog_description).to_have_text(DIALOG_MESSAGE)

            with allure.step('Step 5 — Verify "Server:" shows the Oauth Discovery Endpoint as a link'):
                expect(modal.server_link).to_be_visible()
                expect(modal.server_link).to_have_text(OAUTH_DISCOVERY_ENDPOINT)
                expect(modal.server_link).to_have_attribute("href", OAUTH_DISCOVERY_ENDPOINT)

            with allure.step('Step 6 — Verify Scope is pre-populated with "offline_access" + the scopes'):
                # The product is the oracle: the prefix is BACKEND-sourced
                # (resource_metadata.scopes_supported), not a UI concat, so the
                # expected value is read off the very response that opened the
                # dialog — while the literal prefix the case asks about is
                # asserted explicitly.
                resource_metadata = (auth_body.get("auth_metadata") or {}).get("resource_metadata") or {}
                supported_scopes = resource_metadata.get("scopes_supported")
                assert supported_scopes, (
                    "Expected the check_connection response to carry "
                    f"auth_metadata.resource_metadata.scopes_supported, got {auth_body!r}"
                )
                expected_scope_value = " ".join(supported_scopes)

                expect(modal.scope_input).to_have_value(expected_scope_value)
                assert expected_scope_value.startswith(OFFLINE_ACCESS_PREFIX), (
                    f"Expected the dialog's scopes to be prefixed with {OFFLINE_ACCESS_PREFIX!r}, "
                    f"got {expected_scope_value!r}"
                )
                assert SCOPES in expected_scope_value, (
                    f"Expected the credential's own scope {SCOPES!r} to be part of the dialog's "
                    f"pre-populated scopes, got {expected_scope_value!r}"
                )

            with allure.step("Step 7 — Verify the Scope placeholder when the field is empty"):
                modal.clear_scope()

                expect(modal.scope_input).to_have_value("")
                expect(modal.scope_input).to_have_attribute("placeholder", SCOPE_PLACEHOLDER)

            with allure.step("Step 8 — Verify Cancel and Authorize are present"):
                expect(modal.cancel_button).to_be_visible()
                expect(modal.authorize_button).to_be_visible()
                # Authorize is ENABLED in this configuration (the server
                # advertises an authorization endpoint and needs no client
                # secret) — asserted so a metadata regression that leaves the
                # button dead cannot pass unnoticed.
                expect(modal.authorize_button).to_be_enabled()
                # The Client Id / Client Secret inputs are conditional
                # (needClientId / needsClientSecret) and do not render here, so
                # the dialog holds exactly one input: Scope.
                expect(modal.inputs).to_have_count(1)

            with allure.step("Step 9 — Click Cancel → the dialog closes without taking any action"):
                requests_before_cancel = len(check_connection_requests)
                assert requests_before_cancel == 1, (
                    "Expected exactly one check_connection request (step 3's) before Cancel, got "
                    f"{check_connection_requests!r}"
                )
                # Nothing has authorized yet — the baseline the Fail criterion
                # is measured against.
                assert popups == [], (
                    f"An authorization popup opened before Cancel was even clicked: "
                    f"{[p.url for p in popups]!r}"
                )
                pages_before_cancel = len(page.context.pages)

                modal.click_cancel()

                # keepMounted: the dialog stays in the DOM, so "closed" is a
                # visibility assertion, never to_have_count(0).
                expect(modal.dialog).not_to_be_visible()

                # THE case's Fail criterion: "Cancel triggers an authorization
                # attempt". `onAuthorize`'s first act is opening the auth popup,
                # so an authorization attempt is exactly one new page in this
                # context. Both axes are read AFTER the dialog is confirmed
                # hidden, so the event has had its chance to fire; the page
                # count is a synchronous re-read that does not depend on event
                # timing at all.
                assert popups == [], (
                    "Cancel must not trigger an authorization attempt, but an OAuth popup "
                    f"was opened: {[p.url for p in popups]!r}"
                )
                assert len(page.context.pages) == pages_before_cancel, (
                    "Cancel must not trigger an authorization attempt, but the browser "
                    f"context gained a page: {pages_before_cancel} -> {len(page.context.pages)} "
                    f"({[p.url for p in page.context.pages]!r})"
                )
                # Secondary: Cancel also starts no new backend handshake.
                assert len(check_connection_requests) == requests_before_cancel, (
                    "Cancel must not start a new backend handshake, but new check_connection "
                    f"requests fired: {check_connection_requests[requests_before_cancel:]!r}"
                )

            with allure.step("Side-channel check — no console errors/warnings across the full flow"):
                # Known defects #291 / #554 are filtered above (both filed, both
                # pre-existing), as is the browser's console entry for this
                # case's OWN expected check_connection 401 (the oracle step 3
                # asserts). Anything else fails this check for real.
                assert not console_messages, (
                    f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
                )

        finally:
            # If the step-9 guard ever fires, an OAuth popup is left open and
            # would outlive this test; close it so the next test starts clean.
            page.remove_listener("popup", _on_popup)
            for leaked in popups:
                try:
                    leaked.close()
                except Exception as exc:  # noqa: BLE001 — teardown must never mask the verdict
                    logger.warning("Teardown: failed to close leaked OAuth popup: %s", exc)

            with allure.step("Cleanup — delete the seeded credential"):
                if credential_id is not None:
                    try:
                        credential_api.delete_credential(int(credential_id))
                        logger.info("Teardown: deleted credential id=%s", credential_id)
                    except Exception as exc:  # noqa: BLE001 — teardown must never mask the verdict
                        logger.warning("Teardown: failed to delete credential %s: %s", credential_id, exc)
