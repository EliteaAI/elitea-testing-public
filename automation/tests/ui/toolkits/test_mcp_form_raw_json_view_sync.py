"""UI test — Form ⇄ Raw Json view toggle keeps a Remote MCP's data consistent.

TMS: ELITEA-1948 (test-specs/mcp/l2_mcp-form-raw-json-view-toggle-data-consistency_ELITEA-1948.md)

Reads every field the case names in the Form view, switches to Raw Json and
verifies the serialised values match, edits ``description`` in the Raw Json editor
WITHOUT saving, round-trips Form -> Raw Json to prove the unsaved edit lives in the
shared form model rather than in either view's buffer, then Discards and verifies
BOTH views revert — with nothing persisted (no write request fires at any point).

No substitution of the system under test is performed: every asserted value is
produced by the product (the rendered inputs, the editor's own serialisation, the
rendered buttons, the modal's own text, the browser's real network log). The only
deviation from the case text is the *test data* — the case assumes a pre-existing
Remote MCP, which cannot be discovered at runtime on this environment
(``ToolkitAPI.list_all_toolkits()`` returns an empty list regardless of auth method,
see the AFS § Test Data), so a disposable MCP is seeded through the real UI create
flow and deleted in teardown. That substitution is TRANSIT only: it reaches the
detail page, and the case's own observables all come from the live product there.
"""

import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

# Test-chosen: the case names no data. The ORIGINAL must be NON-EMPTY so step 9's
# revert is an observable value coming back rather than a revert-to-empty (an
# absent description serialises as JSON `null` while the Form input reads "").
ORIGINAL_DESCRIPTION = "Original description for view sync case"
UPDATED_DESCRIPTION = "Modified via Raw Json"
DISCARD_WARNING_TEXT = "Are you sure you want to discard changes?"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1948_mcp-form-raw-json-view-toggle-data-consistency.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
class TestMcpFormRawJsonViewSync:
    """Form ⇄ Raw Json view toggle on a Remote MCP's detail page."""

    def test_form_raw_json_view_sync_and_discard(self, page, toolkit_api: ToolkitAPI):
        """Both views project the same model; an unsaved edit survives the round trip and Discard reverts both."""
        project_id = str(settings.elitea_project_id)
        form = McpFormPage(page)

        # Seed a dedicated, disposable Remote MCP (AFS § Test Data:
        # generate-shared-with-cleanup) — same pattern as the sibling
        # ELITEA-1927/1928 specs. MAX_NAME_LENGTH = 32 truncates the Toolkit Name
        # field client-side; this name is 27 chars.
        toolkit_name = f"autotest_mcp_viewsync_{uuid.uuid4().hex[:6]}"

        form.navigate_to_create()
        form.select_remote_mcp_type()
        form.fill_name(toolkit_name)
        form.fill_description(ORIGINAL_DESCRIPTION)
        # Stored only — this case never clicks Load Tools, so the URL is never dialled.
        form.fill_url("https://mcp.example.com/sse")
        toolkit_id = form.save_and_wait_for_created(project_id)["id"]

        # Console listener registered AFTER seeding: /mcps/create emits the
        # already-tracked React `key` warning (EliteaAI/elitea-testing-public#656)
        # from the type picker, which is scaffolding for this case, not its
        # surface. The detail page itself is clean, so anything captured from here
        # on is a real regression in the flow under test (case Pass criterion:
        # "All steps complete without errors").
        console_messages = []
        page.on(
            "console",
            lambda msg: console_messages.append(msg) if msg.type == "error" else None,
        )

        # Absence-of-write guard for "without saving" (step 6) and the Expected
        # Final State: a UI revert alone would not prove the discard was
        # server-side inert rather than a save-then-restore. Registered before the
        # detail page is even opened, so it genuinely spans every moment in which
        # a write could have fired.
        write_requests = []
        page.on(
            "request",
            lambda request: write_requests.append(f"{request.method} {request.url}")
            if request.method in ("PUT", "POST", "PATCH", "DELETE")
            and f"/tool/prompt_lib/{project_id}" in request.url
            else None,
        )

        try:
            with allure.step("Step 1 — Open the Remote MCP detail page in Form view"):
                form.navigate_to_detail(toolkit_id, project_id)
                assert form.form_view_toggle.get_attribute("aria-pressed") == "true", (
                    "Detail page should load in Form view"
                )
                assert form.raw_json_view_toggle.get_attribute("aria-pressed") == "false", (
                    "Raw Json view should not be active on load"
                )
                assert form.get_detail_heading_text() == toolkit_name, (
                    f"Detail title should show the toolkit's name, "
                    f"got: {form.get_detail_heading_text()!r}"
                )
                # Pristine baseline — both buttons gate on `isFormDirtyExcluding`
                # (ToolkitsTabBarContainer.jsx), so this is the product's own "the
                # form is clean" signal and is what makes the Expected Final
                # State's "without any unsaved modifications" testable in step 9.
                assert form.detail_save_button.is_disabled(), (
                    "Save should be disabled on a pristine detail form"
                )
                assert form.detail_discard_button.is_disabled(), (
                    "Discard should be disabled on a pristine detail form"
                )

            with allure.step(
                "Step 2 — Note Toolkit Name, Description, Url, Timeout, Cache TTL, "
                "Enable Caching and Ssl Verify"
            ):
                # Name and Description render INLINE on the detail page (through
                # NameDescriptionInput.jsx); every schema-driven `toolkit-field-*`
                # element is COLLAPSED and absent from the DOM until the
                # configuration section is expanded.
                form_name = form.name_input.input_value()
                form_description = form.description_input.input_value()
                form.expand_configuration_section()
                form_url = form.url_input.input_value()
                form_timeout = form.timeout_input.input_value()
                form_cache_ttl = form.cache_ttl_input.input_value()
                form_enable_caching = form.is_enable_caching_checked()
                form_ssl_verify = form.is_ssl_verify_checked()

                assert form_name == toolkit_name, (
                    f"Toolkit Name should hold the seeded name, got: {form_name!r}"
                )
                assert form_description == ORIGINAL_DESCRIPTION, (
                    f"Description should hold the seeded original value, "
                    f"got: {form_description!r}"
                )
                assert form_url, "Url should hold the seeded value, got an empty string"
                assert form_timeout, "Timeout should render a value, got an empty string"
                assert form_cache_ttl, "Cache TTL should render a value, got an empty string"

            with allure.step("Step 3 — Click the 'Raw Json' toggle"):
                form.switch_to_raw_json_view()
                expect(form.raw_json_editor_content).to_be_visible()
                assert form.raw_json_view_toggle.get_attribute("aria-pressed") == "true", (
                    "Raw Json toggle should be active after switching"
                )
                assert form.form_view_toggle.get_attribute("aria-pressed") == "false", (
                    "Form toggle should be inactive while Raw Json view is shown"
                )
                # The two views SWAP — they do not co-exist. The Form inputs are
                # unmounted, not hidden, so a hidden-but-present duplicate form
                # (which would make the cross-view assertions vacuous) fails here.
                expect(form.name_input).to_have_count(0)

            with allure.step("Step 4 — Verify the JSON values match the Form values"):
                # get_raw_json_full(), never get_raw_json(): CodeMirror virtualises
                # this ~200-line payload and a single text_content() read silently
                # truncates it.
                raw_json = form.get_raw_json_full()
                settings_block = raw_json["settings"]
                assert raw_json["name"] == form_name, (
                    f"JSON 'name' should match the Form's Toolkit Name, "
                    f"got: {raw_json['name']!r} vs {form_name!r}"
                )
                assert raw_json["description"] == form_description, (
                    f"JSON 'description' should match the Form's Description, "
                    f"got: {raw_json['description']!r} vs {form_description!r}"
                )
                assert settings_block["url"] == form_url, (
                    f"JSON 'settings.url' should match the Form's Url, "
                    f"got: {settings_block['url']!r} vs {form_url!r}"
                )
                # Numeric fields serialise as JSON numbers while the Form inputs
                # read them back as strings — compare on the rendered form.
                assert str(settings_block["timeout"]) == form_timeout, (
                    f"JSON 'settings.timeout' should match the Form's Timeout, "
                    f"got: {settings_block['timeout']!r} vs {form_timeout!r}"
                )
                assert str(settings_block["cache_ttl"]) == form_cache_ttl, (
                    f"JSON 'settings.cache_ttl' should match the Form's Cache TTL, "
                    f"got: {settings_block['cache_ttl']!r} vs {form_cache_ttl!r}"
                )
                assert settings_block["enable_caching"] == form_enable_caching, (
                    f"JSON 'settings.enable_caching' should match the Form's checkbox, "
                    f"got: {settings_block['enable_caching']!r} vs {form_enable_caching!r}"
                )
                assert settings_block["ssl_verify"] == form_ssl_verify, (
                    f"JSON 'settings.ssl_verify' should match the Form's checkbox, "
                    f"got: {settings_block['ssl_verify']!r} vs {form_ssl_verify!r}"
                )

            with allure.step(
                f"Step 5 — Modify 'description' to {UPDATED_DESCRIPTION!r} in the Raw Json view"
            ):
                # get_raw_json_full() leaves the editor's scrollable ancestor at the
                # BOTTOM; the target line would be virtualised out of the DOM
                # without this.
                form.scroll_raw_json_to_top()
                form.fill_raw_json_line(
                    f'"description": "{ORIGINAL_DESCRIPTION}",',
                    f'"description": "{UPDATED_DESCRIPTION}",',
                )
                # Assert the PARSED value, never the raw line text: CodeMirror
                # auto-indents the retyped line, which leaves the JSON valid but
                # changes the literal characters.
                assert form.get_raw_json_full()["description"] == UPDATED_DESCRIPTION, (
                    "Raw Json 'description' should reflect the edit, got: "
                    f"{form.get_raw_json_full()['description']!r}"
                )
                # Proves the edit entered the SHARED form model rather than merely
                # painting text into the editor buffer — without this, steps 6-8
                # could pass on a UI that just echoes CodeMirror back.
                assert not form.detail_save_button.is_disabled(), (
                    "Save should become enabled once the raw-JSON edit dirties the form"
                )
                assert not form.detail_discard_button.is_disabled(), (
                    "Discard should become enabled once the raw-JSON edit dirties the form"
                )

            with allure.step("Step 6 — Click the 'Form' toggle without saving"):
                form.switch_to_form_view()
                assert form.form_view_toggle.get_attribute("aria-pressed") == "true", (
                    "Form toggle should be active after switching back"
                )
                expect(form.description_input).to_be_visible()
                expect(form.raw_json_editor_content).to_have_count(0)

            with allure.step("Step 7 — Verify the Form view shows the updated description"):
                expect(form.description_input).to_have_value(UPDATED_DESCRIPTION)
                expect(form.name_input).to_have_value(toolkit_name)
                assert not form.detail_save_button.is_disabled(), (
                    "Save should still be enabled — the edit is unsaved"
                )

            with allure.step("Step 8 — Click 'Raw Json' again; the modification is retained"):
                form.switch_to_raw_json_view()
                expect(form.name_input).to_have_count(0)
                assert form.get_raw_json_full()["description"] == UPDATED_DESCRIPTION, (
                    "Raw Json should retain the unsaved change after the round trip, got: "
                    f"{form.get_raw_json_full()['description']!r}"
                )

            with allure.step("Step 9 — Click Discard and verify BOTH views revert"):
                # Discard is a two-step gesture: the first click only raises a
                # confirmation modal (absent from the case text — clarification
                # #1718, third case to hit it). Nothing reverts until it is
                # confirmed, asserted here so a future product change that
                # silently reverts on the first click cannot pass unnoticed.
                form.click_discard()
                assert DISCARD_WARNING_TEXT in form.get_discard_confirm_message(), (
                    f"Discard should raise the discard-changes warning modal, "
                    f"got: {form.get_discard_confirm_message()!r}"
                )
                assert form.get_raw_json_full()["description"] == UPDATED_DESCRIPTION, (
                    "Raw Json should still hold the edited value while the "
                    "confirmation modal is open"
                )
                form.confirm_discard()

                # Raw Json view reverts (the view is unchanged by the discard —
                # only the model is).
                assert form.raw_json_view_toggle.get_attribute("aria-pressed") == "true", (
                    "Confirming the discard should not switch views"
                )
                assert form.get_raw_json_full()["description"] == ORIGINAL_DESCRIPTION, (
                    "Raw Json view should show the original description after the "
                    f"discard, got: {form.get_raw_json_full()['description']!r}"
                )

                # ...and so does the Form view.
                form.switch_to_form_view()
                expect(form.description_input).to_have_value(ORIGINAL_DESCRIPTION)
                expect(form.name_input).to_have_value(toolkit_name)

            with allure.step(
                "Expected Final State — both views show the original values with no "
                "unsaved modifications, and nothing was persisted"
            ):
                assert form.detail_save_button.is_disabled(), (
                    "Save should be disabled again once the changes are discarded"
                )
                assert form.detail_discard_button.is_disabled(), (
                    "Discard should be disabled again once the changes are discarded"
                )
                assert write_requests == [], (
                    "Toggling views, editing raw JSON and discarding must not write "
                    f"anything to the server, but these requests fired: {write_requests!r}"
                )
                assert not console_messages, (
                    "Unexpected console errors on the MCP detail page, got: "
                    f"{[m.text for m in console_messages]}"
                )
        finally:
            # Not a case step — teardown for the toolkit seeded above.
            try:
                toolkit_api.delete_toolkit(toolkit_id)
            except Exception:
                logger.warning(
                    "Failed to delete seeded MCP toolkit id=%s during cleanup",
                    toolkit_id,
                    exc_info=True,
                )
