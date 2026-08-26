"""UI test — toggle a Remote MCP's Ssl Verify checkbox off and verify persistence.

TMS: ELITEA-1930 (test-specs/mcp/l1_edit-remote-mcp-toggle-ssl-verify_ELITEA-1930.md)

Unchecks the "Ssl Verify" checkbox on a Remote MCP's detail page, saves, reloads
to confirm server-side persistence, and verifies the boolean value in the Raw
Json view.

No substitution of the system under test is performed: every asserted value is
produced by the product (the rendered checkbox, the update PUT's own response
body, the rendered Raw Json). The only deviation from the case text is the *test
data* — the case assumes a pre-existing Remote MCP, which cannot be discovered at
runtime on this environment (see the AFS § Test Data), so a disposable MCP is
seeded through the real UI create flow and deleted in teardown.
"""

import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1930_edit-remote-mcp-toggle-ssl-verify.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_edit_toggle_ssl_verify(page, toolkit_api: ToolkitAPI):
    """Ssl Verify can be unchecked, saved, and survives reload; Raw Json shows boolean false."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)

    # Seed a dedicated, disposable Remote MCP (AFS § Test Data:
    # generate-shared-with-cleanup) — same reasoning as the sibling ELITEA-1929
    # (Enable Caching) spec: ToolkitAPI.list_all_toolkits() returns an empty list
    # on this environment regardless of auth method, so an existing MCP's id
    # cannot be rediscovered at runtime, and flipping ssl_verify is destructive
    # to whatever toolkit is used. Ssl Verify defaults to checked on creation
    # (AFS-confirmed live), matching this case's stated precondition.
    # MAX_NAME_LENGTH = 32 truncates the Toolkit Name field client-side — this
    # name is 23 chars.
    toolkit_name = f"autotest_mcp_ssl_{uuid.uuid4().hex[:6]}"

    form.navigate_to_create()
    form.select_remote_mcp_type()
    form.fill_name(toolkit_name)
    # Stored only — this case never clicks Load Tools, so the URL is never dialled.
    form.fill_url("https://mcp.example.com/sse")
    toolkit_id = form.save_and_wait_for_created(project_id)["id"]

    # Console listener — same pattern as the sibling test_mcp_edit_name.py /
    # test_mcp_edit_toggle_enable_caching.py specs: capture "error"-type console
    # messages, filter the two pre-existing React dev-mode warnings tracked in
    # EliteaAI/elitea-testing-public#291, and soft-fail (never silently drop) the
    # known #549 MUI Tabs warning, so a genuine regression in this toggle/save/
    # reload flow can't hide behind an already-tracked warning (case Pass
    # criterion: "All steps complete without errors").
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

        with allure.step(
            'Step 2 — Note the current state of the "Ssl Verify" checkbox (checked by default)'
        ):
            # The detail page renders NO toolkit-field-* element until the
            # configuration section is expanded (unlike the create form, which
            # renders them inline) — expanding is an ordinary user gesture, not a
            # substitution: the value read below is still the one the product
            # loaded from the server.
            form.expand_configuration_section()
            assert form.is_ssl_verify_checked(), (
                "Ssl Verify should be checked by default on a freshly created Remote MCP"
            )
            # Pristine baseline for Step 3/4: expanding the section must not
            # dirty the form, so Save is still gated off here (both buttons gate
            # on `isFormDirtyExcluding`, ToolkitsTabBarContainer.jsx:150,158-161).
            assert form.detail_save_button.is_disabled(), (
                "Save should still be disabled after merely expanding the "
                "configuration section — expanding is not an edit"
            )

        with allure.step('Step 3 — Click "Ssl Verify" to uncheck it'):
            form.click_ssl_verify_checkbox()
            assert not form.is_ssl_verify_checked(), (
                "Ssl Verify should be unchecked after clicking"
            )
            assert not form.detail_save_button.is_disabled(), (
                "Save should be enabled once the form is dirty"
            )

        with allure.step("Step 4 — Click Save"):
            # save_and_wait_for_updated() only returns once the PUT resolves with
            # status 200 (see its expect_response filter), so reaching this line
            # already proves the update request succeeded. No success toast is
            # rendered on this surface (confirmed live — see the AFS Step 4 note),
            # so the response body plus Steps 5-6 are the case's "operation
            # completes successfully".
            save_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert save_response.get("id") == toolkit_id, (
                f"Save response should reference the same toolkit id, "
                f"got: {save_response.get('id')!r}"
            )
            saved_ssl_verify = save_response.get("settings", {}).get("ssl_verify")
            assert saved_ssl_verify is False, (
                f"Save response should carry settings.ssl_verify as the boolean False, "
                f"got: {saved_ssl_verify!r} ({type(saved_ssl_verify).__name__})"
            )
            _check_no_new_console_errors("Step 4 (Save)")

        with allure.step('Step 5 — Reload the page; verify "Ssl Verify" is still unchecked'):
            form.reload_and_wait()
            # The configuration section re-collapses on every load — expanding is
            # required again, not just on first load.
            form.expand_configuration_section()
            assert not form.is_ssl_verify_checked(), (
                "Ssl Verify should remain unchecked after a full page reload "
                "(server-side persistence, not just client state)"
            )

        with allure.step('Step 6 — Switch to Raw Json; verify "ssl_verify": false (boolean)'):
            form.switch_to_raw_json_view()
            # get_raw_json() (not get_raw_json_full()): this toolkit has no
            # discovered tools, so the payload is ~376 chars — far below the
            # CodeMirror virtualization threshold that truncates long documents.
            raw_json = form.get_raw_json()
            ssl_verify_value = raw_json.get("settings", {}).get("ssl_verify")
            assert ssl_verify_value is False, (
                f"Raw Json settings.ssl_verify should be the boolean False, "
                f"got: {ssl_verify_value!r} ({type(ssl_verify_value).__name__})"
            )
            _check_no_new_console_errors("Step 6 (Raw Json)")

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
