"""UI test — change a Remote MCP's URL from its detail page and verify persistence.

TMS: ELITEA-1926 (test-specs/mcp/l1_edit-remote-mcp-change-url_ELITEA-1926.md)

Replaces the "Url *" value on a Remote MCP's detail page, saves, reloads to prove
server-side persistence, and confirms the same value in the Raw Json view.

No substitution of the system under test is performed: the asserted URL is read
back from the update PUT's own response body, from the re-rendered form field
after a full page reload, and from the Raw Json view. The only deviation from the
case text is the *test data* — the case assumes a pre-existing Remote MCP, which
cannot be rediscovered at runtime on this environment (see the AFS § Test Data),
so a disposable MCP is seeded through the real UI create flow and deleted in
teardown.
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

ORIGINAL_URL = "https://mcp.example.com/sse"
# Verbatim from the case's Test Data table. Never dialled — nothing in this case
# triggers tool discovery, so the host's reachability is irrelevant.
NEW_URL = "https://new-mcp-server.example.com/sse"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1926_edit-remote-mcp-change-url.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_edit_change_url(page, toolkit_api: ToolkitAPI):
    """A Remote MCP's URL can be edited, saved, and survives a reload — in Form and Raw Json views."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)

    # Seed a dedicated, disposable Remote MCP (AFS § Test Data:
    # generate-shared-with-cleanup) — same reasoning and precedent as the
    # sibling ELITEA-1925 / ELITEA-1927 / ELITEA-1929 specs.
    # MAX_NAME_LENGTH = 32 truncates client-side; this name is 23 chars.
    toolkit_name = f"autotest_mcp_url_{uuid.uuid4().hex[:6]}"

    form.navigate_to_create()
    form.select_remote_mcp_type()
    form.fill_name(toolkit_name)
    form.fill_url(ORIGINAL_URL)
    toolkit_id = form.save_and_wait_for_created(project_id)["id"]

    # Console listener — same pattern as the sibling MCP edit specs: known #291
    # React dev-mode warnings filtered, known #549 MUI Tabs warning soft-failed
    # (never silently dropped), anything else is a hard failure
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

        with allure.step('Step 2 — Note the current value of the "Url *" field'):
            # The detail page renders NO toolkit-field-* node until the
            # configuration section is expanded (found at ELITEA-1923/1924; see
            # the surface digest) — the create form renders them inline, the
            # detail page does not.
            form.expand_configuration_section()
            assert form.url_input.input_value() == ORIGINAL_URL, (
                f"Url field should hold the URL the MCP was created with, "
                f"got: {form.url_input.input_value()!r}"
            )
            assert form.detail_save_button.is_disabled(), (
                "Save should be disabled before anything is edited (baseline for Step 4)"
            )

        with allure.step(f"Step 3 — Clear the Url field and enter {NEW_URL!r}"):
            form.fill_url(NEW_URL)
            assert form.url_input.input_value() == NEW_URL, (
                f"Url field should display the new URL, got: {form.url_input.input_value()!r}"
            )

        with allure.step("Step 4 — Verify the Save button becomes enabled"):
            assert not form.detail_save_button.is_disabled(), (
                "Save should be enabled once the Url field has been edited"
            )

        with allure.step("Step 5 — Click Save"):
            # Returns only on a 200 PUT, so reaching this line proves the update
            # succeeded; the response body is the product's own record of what
            # was stored. There is no success toast on this surface (confirmed
            # live during ELITEA-1925 analysis).
            save_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert save_response.get("id") == toolkit_id, (
                f"Save response should reference the same toolkit id, "
                f"got: {save_response.get('id')!r}"
            )
            assert (save_response.get("settings") or {}).get("url") == NEW_URL, (
                f"Save response settings.url should be the new URL, "
                f"got: {(save_response.get('settings') or {}).get('url')!r}"
            )
            _check_no_new_console_errors("Step 5 (Save)")

        with allure.step('Step 6 — Reload the page; verify the new URL persisted in "Url *"'):
            form.reload_and_wait()
            # The configuration section re-collapses after a reload.
            form.expand_configuration_section()
            assert form.url_input.input_value() == NEW_URL, (
                f"Url field should still show the new URL after a full page reload "
                f"(server-side persistence, not client state), "
                f"got: {form.url_input.input_value()!r}"
            )

        with allure.step('Step 7 — Switch to Raw Json view; verify the "url" field matches'):
            form.switch_to_raw_json_view()
            raw_json = form.get_raw_json()
            raw_url = (raw_json.get("settings") or {}).get("url")
            assert raw_url == NEW_URL, (
                f"Raw Json settings.url should be the updated URL, got: {raw_url!r}"
            )
            _check_no_new_console_errors("Step 7 (Raw Json view)")

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
