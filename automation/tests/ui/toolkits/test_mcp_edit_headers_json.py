"""UI test — modify a Remote MCP's Headers JSON and verify persistence.

TMS: ELITEA-1931 (test-specs/mcp/l1_edit-remote-mcp-modify-headers-json_ELITEA-1931.md)

Types a custom header into the Headers JSON editor on a Remote MCP's detail page,
saves, reloads to confirm server-side persistence, and verifies the header in the
Raw Json view.

No substitution of the system under test is performed: every asserted value is
produced by the product (the rendered CodeMirror content, the update PUT's own
response body, the rendered Raw Json). The only deviation from the case text is
the *test data* — the case assumes a pre-existing Remote MCP, which cannot be
discovered at runtime on this environment (see the AFS § Test Data), so a
disposable MCP is seeded through the real UI create flow and deleted in teardown.

Case-text divergence (asserted against the LIVE product per the reverse-masking
guard, `.agents/role-overrides.md`): step 2's "Headers accordion" does not exist —
`headers` is one schema-driven field of the single **Configuration** section,
which the detail page collapses behind `toolkit-configuration-show-more`.
Expanding that section is what makes the Headers editor reachable.
"""

import json
import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

HEADERS_JSON = '{"X-Custom-Header": "test-value"}'
EXPECTED_HEADERS = {"X-Custom-Header": "test-value"}


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1931_edit-remote-mcp-modify-headers-json.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_edit_headers_json(page, toolkit_api: ToolkitAPI):
    """Custom Headers JSON is accepted, saved, survives reload, and shows in Raw Json."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)

    # Seed a dedicated, disposable Remote MCP (AFS § Test Data:
    # generate-shared-with-cleanup) — same reasoning as the sibling ELITEA-1930
    # (Ssl Verify) spec: ToolkitAPI.list_all_toolkits() returns an empty list on
    # this environment regardless of auth method, so an existing MCP's id cannot
    # be rediscovered at runtime, and writing custom headers is destructive to
    # whatever toolkit would be borrowed. MAX_NAME_LENGTH = 32 truncates the
    # Toolkit Name field client-side — this name is 23 chars.
    toolkit_name = f"autotest_mcp_hdr_{uuid.uuid4().hex[:6]}"

    form.navigate_to_create()
    form.select_remote_mcp_type()
    form.fill_name(toolkit_name)
    # Stored only — this case never clicks Load Tools, so the URL is never dialled.
    form.fill_url("https://mcp.example.com/sse")
    toolkit_id = form.save_and_wait_for_created(project_id)["id"]

    # Console listener — same pattern as the sibling test_mcp_edit_toggle_ssl_verify.py
    # spec: capture "error"-type console messages, filter the two pre-existing React
    # dev-mode warnings tracked in EliteaAI/elitea-testing-public#291, and soft-fail
    # (never silently drop) the known #549 MUI Tabs warning, so a genuine regression
    # in this edit/save/reload flow can't hide behind an already-tracked warning
    # (case Pass criterion: "All steps complete without errors").
    console_messages = []
    soft_failures = []

    def _is_known_291_warning(msg) -> bool:
        text = msg.text
        return (
            'unique "key" prop' in text
            or ("validateDOMNesting" in text and "<p>" in text)
            or ("validateDOMNesting" in text and "%s" in text)
        )

    def _is_known_549_warning(msg) -> bool:
        return "Tabs component is invalid" in msg.text

    page.on(
        "console",
        lambda msg: console_messages.append(msg)
        if msg.type == "error" and not _is_known_291_warning(msg)
        else None,
    )

    def _check_no_new_console_errors(step_label: str) -> None:
        """Split captured console errors: known #549 -> soft; anything else -> hard fail."""
        new_549 = [m for m in console_messages if _is_known_549_warning(m)]
        unexpected = [m for m in console_messages if not _is_known_549_warning(m)]
        for msg in new_549:
            soft_failures.append(
                "Known defect github.com/EliteaAI/elitea-testing-public/issues/549: "
                f"{step_label} — MUI Tabs invalid-value console error: {msg.text!r}"
            )
        assert not unexpected, (
            f"{step_label} — unexpected new console errors beyond the two "
            "pre-existing dev-mode warnings tracked in #291 and the known "
            f"#549 Tabs warning, got: {[m.text for m in unexpected]}"
        )
        console_messages.clear()

    try:
        with allure.step("Step 1 — Open the Remote MCP detail page in Form view"):
            form.navigate_to_detail(toolkit_id, project_id)
            assert form.form_view_toggle.get_attribute("aria-pressed") == "true", (
                "Detail page should load in Form view"
            )
            assert form.get_detail_heading_text() == toolkit_name, (
                f"Detail title should show the toolkit's name, "
                f"got: {form.get_detail_heading_text()!r}"
            )

        with allure.step('Step 2 — Expand the "Headers" section'):
            # DIVERGENCE (AFS § Case-text divergence): the case says "click the
            # Headers accordion". There is no Headers accordion — Headers is a
            # field of the single Configuration section, which the detail page
            # renders collapsed (no toolkit-field-* node exists until it is
            # expanded). Asserting the collapsed baseline first makes the
            # expansion a real, observed transition rather than a blind click.
            assert form.headers_editor.count() == 0, (
                "The Headers editor should not be in the DOM before the "
                "configuration section is expanded"
            )
            form.expand_configuration_section()
            assert form.headers_editor.is_visible(), (
                "Headers editor should be visible once the configuration section is expanded"
            )
            # Expanding is not an edit — the form must still be pristine.
            assert form.detail_save_button.is_disabled(), (
                "Save should still be disabled after merely expanding the "
                "configuration section"
            )

        with allure.step("Step 3 — Verify the Headers JSON editor shows the default {}"):
            assert form.get_headers_json_text() == "{}", (
                f"Headers editor should default to an empty object, "
                f"got: {form.get_headers_json_text()!r}"
            )

        with allure.step(f"Step 4 — Enter valid JSON: {HEADERS_JSON}"):
            form.fill_headers_json(HEADERS_JSON)
            # Read verbatim BEFORE blurring: the editor displays exactly what was
            # typed (CodeMirror's bracket/quote auto-close types over, it does not
            # duplicate); the pretty-print only happens on blur.
            assert form.get_headers_json_text() == HEADERS_JSON, (
                f"Headers editor should display the typed JSON verbatim, "
                f"got: {form.get_headers_json_text()!r}"
            )

        with allure.step("Step 5 — Click Save"):
            # The Headers editor commits on BLUR, not on keystroke (AFS
            # § Automation Hints): with focus still inside it, Save stays
            # disabled. Moving focus out is the same gesture a human makes when
            # reaching for the Save button.
            assert form.detail_save_button.is_disabled(), (
                "Save is expected to still be disabled while focus remains in the "
                "Headers editor (the field commits on blur)"
            )
            form.blur_headers_editor()
            assert not form.detail_save_button.is_disabled(), (
                "Save should be enabled once the blurred Headers value has "
                "dirtied the form"
            )
            # save_and_wait_for_updated() only returns once the PUT resolves with
            # status 200, so reaching this line already proves the update request
            # succeeded. No success toast is rendered on this surface (AFS
            # § Test Steps step 5), so the response body plus Steps 6-7 are the
            # case's "operation completes successfully".
            save_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert save_response.get("id") == toolkit_id, (
                f"Save response should reference the same toolkit id, "
                f"got: {save_response.get('id')!r}"
            )
            saved_headers = save_response.get("settings", {}).get("headers")
            assert saved_headers == EXPECTED_HEADERS, (
                f"Save response should carry the custom header under settings.headers, "
                f"got: {saved_headers!r}"
            )
            _check_no_new_console_errors("Step 5 (Save)")

        with allure.step("Step 6 — Reload the page, expand Headers, verify the JSON persisted"):
            form.reload_and_wait()
            # The configuration section re-collapses on every load.
            form.expand_configuration_section()
            # The product legitimately re-formats the JSON on blur, and a
            # multi-line CodeMirror's text_content() concatenates its line <div>s
            # with no separator — parse and compare the DICT, never the raw string
            # (asserting the string would assert formatting, not persistence).
            persisted = json.loads(form.get_headers_json_text())
            assert persisted == EXPECTED_HEADERS, (
                f"Headers should survive a full page reload (server-side persistence), "
                f"got: {persisted!r}"
            )

        with allure.step("Step 7 — Switch to Raw Json; verify the header in the full config"):
            form.switch_to_raw_json_view()
            raw_json = form.get_raw_json_full()
            raw_headers = raw_json.get("settings", {}).get("headers")
            assert raw_headers == EXPECTED_HEADERS, (
                f"Raw Json settings.headers should carry the custom header, "
                f"got: {raw_headers!r}"
            )
            _check_no_new_console_errors("Step 7 (Raw Json)")

        if soft_failures:
            pytest.fail(
                "Soft assertion(s) failed (known non-blocking product defect, "
                "not test/infrastructure — rest of the flow passed cleanly):\n"
                + "\n".join(soft_failures)
            )
    finally:
        # Not a case step — teardown for the toolkit seeded above.
        try:
            toolkit_api.delete_toolkit(toolkit_id)
        except Exception:
            logger.warning(
                "Failed to delete seeded MCP toolkit id=%s during cleanup", toolkit_id, exc_info=True
            )
