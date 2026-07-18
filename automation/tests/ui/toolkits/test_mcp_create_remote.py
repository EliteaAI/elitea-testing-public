"""UI test — create a Remote MCP toolkit with every field populated.

TMS: ELITEA-1922 (test-specs/mcp/l1_create-remote-mcp-all-fields-populated_ELITEA-1922.md)

Fills every field on the Remote MCP creation form, saves, and verifies every
value is persisted correctly in both the Form view and the Raw Json view of
the resulting detail page.
"""

import logging
import re
import uuid

import pytest

from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from pages.mcp_list_page import McpListPage
import allure

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

TOOLKIT_DESCRIPTION = "Full configuration test MCP"
TOOLKIT_URL = "https://mcp.example.com/sse"
TOOLKIT_HEADERS = '{"Authorization": "Bearer test123"}'
TOOLKIT_CLIENT_ID = "test_client_id"
TOOLKIT_CLIENT_SECRET = "test_secret_value"
TOOLKIT_SCOPES_INPUT = "read,write"
TOOLKIT_TIMEOUT = "600"
TOOLKIT_CACHE_TTL = "120"

# Client Secret is never persisted as plaintext — only as a
# {{secret.<hex>}} reference token in the Raw Json (SecretField.jsx's own
# secretRegex, confirmed at ELITEA-1922 AFS exploration).
SECRET_REFERENCE_RE = re.compile(r"^\{\{secret\.([A-Za-z0-9_]+)\}\}$")

# The Form view's Client Secret <input> DOM value is the BARE hex id, not
# the full {{secret.<hex>}} wrapper — confirmed live during implementer
# Phase 4 (the AFS's step-15 text describing the Form view as also showing
# the full reference-token wrapper does not match the live product; a
# reverse-masking-guard CLARIFICATION was filed rather than asserting the
# stale case text, see AFS § Known Defects). Cross-checking this bare hex
# against the hex embedded in the Raw Json's reference token (step 16) is
# what actually proves it's the secret-reference id and not a coincidental
# non-plaintext string.
SECRET_HEX_RE = re.compile(r"^[0-9a-f]{32}$")


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1922_create-remote-mcp-all-fields-populated.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_create_remote_mcp_all_fields_populated(page, toolkit_api: ToolkitAPI):
    """Create a Remote MCP toolkit filling every field; verify Form + Raw Json."""
    # Toolkit Name input carries MAX_NAME_LENGTH=32 (EliteaUI src/common/constants.js) —
    # silently truncates anything longer. Keep the generated name comfortably under it.
    toolkit_name = f"autotest_mcp_full_{uuid.uuid4().hex[:6]}"
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    created_id: int | None = None

    # A dirty, unsaved form triggers a native beforeunload confirm dialog if
    # the harness ever navigates away mid-test (e.g. a failure path) —
    # auto-accept it so such a navigation never hangs (ELITEA-1922 AFS
    # § Automation Hints).
    page.on("dialog", lambda dialog: dialog.accept())

    try:
        with allure.step("Step 1 — Navigate to MCP creation page; verify type picker"):
            form.navigate_to_create()
            assert form.remote_mcp_type_card.is_visible(), (
                "Remote MCP type card should be visible on the type-picker page"
            )

        with allure.step("Step 2 — Select Remote MCP type; verify create form loads"):
            form.select_remote_mcp_type()
            assert "/mcps/create/mcp" in page.url, f"Expected the Remote MCP form URL, got: {page.url}"
            assert form.name_input.is_visible(), "Toolkit Name field should be visible on the create form"

        with allure.step("Step 3 — Fill Toolkit Name"):
            form.fill_name(toolkit_name)
            assert form.name_input.input_value() == toolkit_name

        with allure.step("Step 4 — Fill Description"):
            form.fill_description(TOOLKIT_DESCRIPTION)
            assert form.description_input.input_value() == TOOLKIT_DESCRIPTION

        with allure.step("Step 5 — Fill Url"):
            form.fill_url(TOOLKIT_URL)
            assert form.url_input.input_value() == TOOLKIT_URL

        with allure.step("Step 6 — Expand Headers editor and enter JSON"):
            form.fill_headers_json(TOOLKIT_HEADERS)
            headers_text = form.get_headers_json_text()
            assert '"Authorization"' in headers_text and "Bearer test123" in headers_text, (
                f"Headers editor should show the typed JSON, got: {headers_text!r}"
            )

        with allure.step("Step 7 — Fill Client Id"):
            form.fill_client_id(TOOLKIT_CLIENT_ID)
            assert form.client_id_input.input_value() == TOOLKIT_CLIENT_ID

        with allure.step("Step 8 — Fill Client Secret (Password view)"):
            form.fill_client_secret(TOOLKIT_CLIENT_SECRET)
            assert form.get_client_secret_value() == TOOLKIT_CLIENT_SECRET

        with allure.step("Step 9 — Fill Scopes"):
            form.fill_scopes(TOOLKIT_SCOPES_INPUT)
            # The field cosmetically reformats "read,write" -> "read, write"
            # on input — assert the meaningful content survived, not exact
            # string equality against the pre-reformat value (AFS Axis 2).
            scopes_value = form.get_scopes_value()
            assert "read" in scopes_value and "write" in scopes_value, (
                f"Scopes field should contain both scopes, got: {scopes_value!r}"
            )

        with allure.step("Step 10 — Change Timeout 300 -> 600"):
            form.fill_timeout(TOOLKIT_TIMEOUT)
            assert form.timeout_input.input_value() == TOOLKIT_TIMEOUT

        with allure.step("Step 11 — Verify Enable Caching is checked by default"):
            assert form.is_enable_caching_checked(), "Enable Caching should be checked by default"

        with allure.step("Step 12 — Change Cache TTL 300 -> 120"):
            form.fill_cache_ttl(TOOLKIT_CACHE_TTL)
            assert form.cache_ttl_input.input_value() == TOOLKIT_CACHE_TTL

        with allure.step("Step 13 — Verify Ssl Verify checked by default, then uncheck it"):
            assert form.is_ssl_verify_checked(), "Ssl Verify should be checked by default"
            form.click_ssl_verify_checkbox()
            assert not form.is_ssl_verify_checked(), "Ssl Verify should be unchecked after click"

        with allure.step("Step 14 — Click Save; verify 201 + navigation to detail page"):
            save_response = form.save_and_wait_for_created(project_id)
            created_id = save_response["id"]
            assert isinstance(created_id, int), f"Save response should include a numeric id: {save_response!r}"
            assert f"/mcps/all/{created_id}" in page.url, (
                f"Should navigate to the new MCP's detail page, got: {page.url}"
            )

        with allure.step("Step 15 — Verify Form view shows every persisted value"):
            assert toolkit_name in form.get_detail_heading_text()
            assert form.name_input.input_value() == toolkit_name
            assert form.description_input.input_value() == TOOLKIT_DESCRIPTION
            assert form.url_input.input_value() == TOOLKIT_URL
            assert form.client_id_input.input_value() == TOOLKIT_CLIENT_ID
            scopes_value = form.get_scopes_value()
            assert "read" in scopes_value and "write" in scopes_value
            assert form.timeout_input.input_value() == TOOLKIT_TIMEOUT
            assert form.cache_ttl_input.input_value() == TOOLKIT_CACHE_TTL
            assert form.is_enable_caching_checked(), "Enable Caching should remain checked"
            assert not form.is_ssl_verify_checked(), "Ssl Verify should remain unchecked"

            # Client Secret must never round-trip as plaintext — only the
            # bare secret-reference hex id (security-relevant behavior, AFS
            # Axis 2 addition). Match the hex-id shape, not just
            # "!= plaintext" — a bare inequality check would pass on an
            # empty or garbage render just as easily as on the correct
            # secret-reference value. The Form view's DOM value is the bare
            # hex (not the {{secret.<hex>}} wrapper the Raw Json uses — see
            # SECRET_HEX_RE comment); step 16 cross-checks this same hex
            # against the Raw Json's reference token to prove it's really
            # the secret-reference id, not a coincidental hex-shaped string.
            secret_value = form.get_client_secret_value()
            assert SECRET_HEX_RE.match(secret_value), (
                f"Client Secret field must show the bare secret-reference hex id, "
                f"never plaintext — got: {secret_value!r}"
            )
            assert TOOLKIT_CLIENT_SECRET not in secret_value

        with allure.step("Step 16 — Switch to Raw Json view; verify every persisted value"):
            form.switch_to_raw_json_view()
            raw = form.get_raw_json()

            assert raw["name"] == toolkit_name
            assert raw["description"] == TOOLKIT_DESCRIPTION
            assert raw["type"] == "mcp"

            mcp_settings = raw["settings"]
            assert mcp_settings["url"] == TOOLKIT_URL
            assert mcp_settings["headers"] == {"Authorization": "Bearer test123"}
            assert mcp_settings["client_id"] == TOOLKIT_CLIENT_ID
            assert mcp_settings["scopes"] == ["read", "write"], (
                f"Scopes should persist as an array, got: {mcp_settings['scopes']!r}"
            )
            # timeout/cache_ttl persist as JSON STRINGS, not numbers — the
            # live product's actual schema, confirmed at ELITEA-1922 AFS
            # exploration (case text doesn't specify a type).
            assert mcp_settings["timeout"] == "600"
            assert isinstance(mcp_settings["timeout"], str)
            assert mcp_settings["cache_ttl"] == "120"
            assert isinstance(mcp_settings["cache_ttl"], str)
            assert mcp_settings["enable_caching"] is True
            assert mcp_settings["ssl_verify"] is False

            client_secret_json = mcp_settings["client_secret"]
            secret_match = SECRET_REFERENCE_RE.match(client_secret_json)
            assert secret_match, (
                f"client_secret in Raw Json must be a {{{{secret.<hex>}}}} reference token, "
                f"never plaintext — got: {client_secret_json!r}"
            )
            assert TOOLKIT_CLIENT_SECRET not in client_secret_json

            # Cross-check: the Form view's bare hex (step 15) and the Raw
            # Json's wrapped reference token must carry the SAME hex id —
            # proves the Form view value is genuinely the secret-reference
            # id, not just a coincidentally hex-shaped string.
            assert secret_match.group(1) == secret_value, (
                f"Form view Client Secret hex ({secret_value!r}) should match the "
                f"Raw Json reference token's hex ({secret_match.group(1)!r})"
            )

    finally:
        # Not a case step — cleanup for the persistent server-side toolkit
        # this test creates (AFS § Cleanup).
        if created_id is not None:
            try:
                toolkit_api.delete_toolkit(created_id)
            except Exception:
                logger.warning("Failed to delete MCP toolkit id=%s during cleanup", created_id, exc_info=True)


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1921_create-remote-mcp-minimal-required-fields.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_create_remote_mcp_minimal_required_fields(page, toolkit_api: ToolkitAPI):
    """Create a Remote MCP toolkit filling only the required fields (Name + Url).

    Distinct scenario from ``test_create_remote_mcp_all_fields_populated``:
    the Save-button disabled->enabled gating on a minimal form, the
    minimal-fields create + persist round-trip (every other field left at
    its schema default), and the "Remote" type badge on the MCP list card
    — none of which the all-fields test touches (TMS: ELITEA-1921).
    """
    # Toolkit Name input carries MAX_NAME_LENGTH=32 (EliteaUI src/common/constants.js) —
    # silently truncates anything longer. "autotest_remote_mcp_minimal" is
    # already 27 characters, so a 4-hex-char suffix (NOT the 6-hex-char
    # pattern above) keeps the generated name at exactly 32 chars — one more
    # hex digit would silently truncate (AFS Test Data).
    toolkit_name = f"autotest_remote_mcp_minimal_{uuid.uuid4().hex[:4]}"
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    list_page = McpListPage(page)
    created_id: int | None = None

    # A dirty, unsaved form triggers a native beforeunload confirm dialog if
    # the harness ever navigates away mid-test — auto-accept it (same
    # pattern as test_create_remote_mcp_all_fields_populated above).
    page.on("dialog", lambda dialog: dialog.accept())

    try:
        with allure.step("Step 1 — Navigate to MCP creation page; verify type picker URL"):
            form.navigate_to_create()
            assert "/mcps/create" in page.url, f"Expected the MCP type-picker URL, got: {page.url}"

        with allure.step("Step 2 — Verify Local (empty-state) and Remote (card) sections are shown"):
            assert form.local_empty_state.is_visible(), "Local MCP empty-state message should be visible"
            assert "Still no local MCP available" in (form.local_empty_state.text_content() or ""), (
                "Local section should show the 'no local MCP' empty-state copy"
            )
            assert form.remote_mcp_type_card.is_visible(), "Remote MCP type card should be visible"
            assert "Remote MCP" in (form.remote_mcp_type_card.text_content() or ""), (
                "Remote section card should be labelled 'Remote MCP'"
            )

        with allure.step("Step 3 — Select Remote MCP type; verify create form loads"):
            form.select_remote_mcp_type()
            assert "/mcps/create/mcp" in page.url, f"Expected the Remote MCP form URL, got: {page.url}"
            assert form.name_input.is_visible(), "Toolkit Name field should be visible on the create form"

        with allure.step("Step 4 — Verify Save is disabled on the pristine, untouched form"):
            assert form.is_save_button_disabled(), "Save should be disabled before any field is filled"

        with allure.step("Step 5 — Fill Toolkit Name"):
            form.fill_name(toolkit_name)
            assert form.name_input.input_value() == toolkit_name

        with allure.step("Step 6 — Fill Url"):
            form.fill_url(TOOLKIT_URL)
            assert form.url_input.input_value() == TOOLKIT_URL

        with allure.step("Step 7 — Verify Save becomes enabled once both required fields are filled"):
            # Do NOT additionally assert an intermediate "disabled after only
            # one field" state here — Save's enabled/disabled toggle is
            # dirty-based, not required-field-completeness-based (flips on
            # the first touched field), so that stricter reading flakes.
            # Client-side Yup validation still correctly blocks submission of
            # an incomplete form regardless (AFS Test Steps step 7 note,
            # CLARIFICATION EliteaAI/elitea-testing-public#633).
            assert not form.is_save_button_disabled(), "Save should be enabled once Name and Url are both filled"

        with allure.step("Step 8 — Click Save; verify 201 + navigation to detail page"):
            save_response = form.save_and_wait_for_created(project_id)
            created_id = save_response["id"]
            assert isinstance(created_id, int), f"Save response should include a numeric id: {save_response!r}"
            assert f"/mcps/all/{created_id}" in page.url, (
                f"Should navigate to the new MCP's detail page, got: {page.url}"
            )

        with allure.step("Step 9 — Verify detail page shows the persisted name and the two filled fields"):
            assert toolkit_name in form.get_detail_heading_text()
            assert form.name_input.input_value() == toolkit_name
            assert form.url_input.input_value() == TOOLKIT_URL

        with allure.step("Step 10 — Navigate to MCP list; verify the card carries a 'Remote' type badge"):
            list_page.navigate()
            badge_text = list_page.get_card_type_badge_text(toolkit_name)
            assert badge_text == "Remote", f"Expected the 'Remote' type badge, got: {badge_text!r}"

    finally:
        # Not a case step — cleanup for the persistent server-side toolkit
        # this test creates (AFS § Cleanup).
        if created_id is not None:
            try:
                toolkit_api.delete_toolkit(created_id)
            except Exception:
                logger.warning("Failed to delete MCP toolkit id=%s during cleanup", created_id, exc_info=True)
