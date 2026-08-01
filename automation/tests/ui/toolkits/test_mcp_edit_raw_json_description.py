"""UI test — edit a Remote MCP's configuration via the Raw Json editor.

TMS: ELITEA-1927 (test-specs/mcp/l1_edit-remote-mcp-modify-configuration-via-raw-json_ELITEA-1927.md)

Edits the "description" field directly through the Raw Json CodeMirror
editor (per-line edit, not a whole-document select — see
``McpFormPage.fill_raw_json_line``'s docstring for why), saves, verifies the
change reflects in the Form view immediately, then reloads and confirms the
change persisted server-side in both the Form view and the Raw Json view.
"""

import logging
import uuid

import allure
import pytest

from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p0, pytest.mark.regression]

UPDATED_DESCRIPTION = "Updated via raw JSON"

# Raw Json settings keys that must be present (case Step 3). "available_mcp_tools"
# is deliberately NOT asserted here — case text lists it, but the live product
# never renders it (confirmed live on 2 fresh toolkits, consistent with the
# sibling ELITEA-1922 AFS's own exhaustive schema assertions). This is
# case-text drift, not a product defect — CLARIFICATION filed as
# EliteaAI/elitea-testing-public#574. Per AFS Step 3 instruction, only the 8
# real fields are asserted present; "available_mcp_tools" is asserted
# NEITHER present NOR absent — it's a documented clarification, not a
# regression oracle, so a future product change that legitimately adds the
# field back won't break this test.
EXPECTED_SETTINGS_KEYS = {
    "url",
    "timeout",
    "cache_ttl",
    "ssl_verify",
    "enable_caching",
    "selected_tools",
}


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1927_edit-remote-mcp-modify-configuration-via-raw-json.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_edit_raw_json_description(page, toolkit_api: ToolkitAPI):
    """A Remote MCP's description can be edited via Raw Json, saved, and persists after reload."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)

    # Seed a dedicated Remote MCP for this test (AFS § Test Data:
    # generate-shared-with-cleanup). ToolkitAPI.list_all_toolkits() returns
    # an empty list on this environment regardless of auth method
    # (documented quirk, see config.py's remote_github_mcp_toolkit_id
    # comment and
    # .agents/memory/test-automation-engineer/mcp_pipeline_node_toolkit_tool_quirks.md),
    # so there is no reliable read-only way to rediscover an existing
    # toolkit's id at runtime — and editing+saving is inherently
    # destructive to whatever toolkit is used, so per Hard Rule 10 a
    # dedicated, disposable toolkit is seeded rather than mutating a shared
    # leftover (same pattern as test_mcp_view_toggle.py's _seed_mcp_via_ui
    # and the sibling ELITEA-1929 case's shipped implementation).
    form.navigate_to_create()
    form.select_remote_mcp_type()
    # MAX_NAME_LENGTH=32 truncates the Toolkit Name field client-side (see
    # .agents/memory/test-automation-engineer/mcp_toolkit_create_form_implementer_quirks.md)
    # — keep the generated name at or under that limit.
    toolkit_name = f"autotest_mcp_rawjson_{uuid.uuid4().hex[:6]}"
    form.fill_name(toolkit_name)
    form.fill_url("https://mcp.example.com/sse")
    create_response = form.save_and_wait_for_created(project_id)
    toolkit_id = create_response["id"]

    # Console listener — same pattern as test_mcp_edit_toggle_enable_caching.py:
    # capture "error"-type console messages, filter out the two pre-existing
    # React dev-mode warnings already filed as
    # EliteaAI/elitea-testing-public#291 (missing `key` prop in list
    # rendering; invalid `<p>`-in-`<p>` DOM nesting in ToolBaseProperty.jsx's
    # tooltip — the same shared field renderer used on this detail page) and
    # the known #549 MUI Tabs warning (soft-failed, not hard-failed), so a
    # real regression introduced by this raw-json-edit/save/reload flow
    # isn't masked by an expected, already-tracked warning (AFS Step 6 /
    # Expected Results).
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
        text = msg.text
        return "Tabs component is invalid" in text

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

        with allure.step('Step 2 — Click "Raw Json" toggle button; verify JSON editor appears'):
            form.switch_to_raw_json_view()
            assert form.raw_json_editor_content.is_visible(), (
                "Raw Json editor should be visible after switching view"
            )

        with allure.step(
            "Step 3 — Verify JSON contains current config "
            "(name, description, settings with url, timeout, cache_ttl, ssl_verify, "
            "enable_caching, selected_tools)"
        ):
            raw_json = form.get_raw_json()
            assert raw_json.get("name") == toolkit_name, (
                f"Raw Json 'name' should match the toolkit's name, got: {raw_json.get('name')!r}"
            )
            assert "description" in raw_json, "Raw Json should contain a 'description' key"
            settings_obj = raw_json.get("settings", {})
            missing = EXPECTED_SETTINGS_KEYS - settings_obj.keys()
            assert not missing, (
                f"Raw Json 'settings' should contain all expected fields, missing: {missing}"
            )
            # "available_mcp_tools" is deliberately not asserted present or
            # absent here — see EXPECTED_SETTINGS_KEYS comment / AFS Step 3.

        with allure.step(
            'Step 4 — Modify "description" value in the Raw Json editor to '
            f'"{UPDATED_DESCRIPTION}"'
        ):
            # Whole-document select (Ctrl+A / Ctrl+Home+Ctrl+Shift+End) followed
            # by delete did NOT reliably clear the CodeMirror editor in this
            # environment (confirmed live at implementer exploration: left a
            # stray character behind, producing invalid JSON) — per-line edit
            # via fill_raw_json_line is the reliable approach (AFS Step 4
            # automation hint).
            current_description_line = f'"description": {_json_value(raw_json["description"])},'
            new_description_line = f'"description": "{UPDATED_DESCRIPTION}",'
            form.fill_raw_json_line(current_description_line, new_description_line)

            updated_raw_json = form.get_raw_json()
            assert updated_raw_json["description"] == UPDATED_DESCRIPTION, (
                f"Raw Json 'description' should reflect the edit, "
                f"got: {updated_raw_json['description']!r}"
            )
            # get_raw_json() parses the editor's text via json.loads() — a
            # malformed edit would raise json.JSONDecodeError above and fail
            # this step loudly, so reaching this assertion already proves
            # the JSON stayed valid (no "Invalid JSON format" state, which
            # has no data-testid to assert on directly per the testid-only
            # locator policy — Save enabling in Step 5 is the app's own
            # confirmation of this too).

        with allure.step("Step 5 — Verify Save button becomes enabled"):
            assert form.detail_save_button.is_enabled(), (
                "Save button should be enabled once the description edit lands"
            )

        with allure.step("Step 6 — Click Save"):
            save_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert save_response.get("id") == toolkit_id, (
                f"Save response should reference the same toolkit id, got: {save_response.get('id')!r}"
            )
            assert save_response.get("description") == UPDATED_DESCRIPTION, (
                f"Save response should reflect the updated description, "
                f"got: {save_response.get('description')!r}"
            )
            _check_no_new_console_errors("Step 6 (Save)")

        with allure.step(
            'Step 7 — Click "Form" toggle button; verify Description field shows '
            f'"{UPDATED_DESCRIPTION}"'
        ):
            # The page auto-switches back to Form view after Save resolves
            # (confirmed live — a UI side-effect, not a case requirement),
            # but the case step explicitly calls for clicking the Form
            # toggle, so click it regardless of the current view state.
            form.switch_to_form_view()
            assert form.description_input.input_value() == UPDATED_DESCRIPTION, (
                f"Form view Description field should show the updated value, "
                f"got: {form.description_input.input_value()!r}"
            )

        with allure.step(
            "Step 8 — Reload page; verify change persisted in both Form and Raw Json views"
        ):
            form.reload_and_wait()
            assert form.description_input.input_value() == UPDATED_DESCRIPTION, (
                "Form view Description field should still show the updated value after reload "
                "(server-side persistence, not just client state)"
            )
            form.switch_to_raw_json_view()
            reloaded_raw_json = form.get_raw_json()
            assert reloaded_raw_json["description"] == UPDATED_DESCRIPTION, (
                f"Raw Json 'description' should still reflect the updated value after reload, "
                f"got: {reloaded_raw_json['description']!r}"
            )

        if soft_failures:
            pytest.fail(
                "Soft assertion(s) failed (known non-blocking product defect, "
                "not test/infrastructure — rest of the flow passed cleanly):\n"
                + "\n".join(soft_failures)
            )
    finally:
        # Not a case step — teardown for the toolkit seeded above (AFS § Cleanup).
        try:
            toolkit_api.delete_toolkit(toolkit_id)
        except Exception:
            logger.warning(
                "Failed to delete seeded MCP toolkit id=%s during cleanup", toolkit_id, exc_info=True
            )


def _json_value(value) -> str:
    """Render *value* the way the Raw Json editor's own JSON.stringify does.

    Used to reconstruct the exact current line text for
    ``McpFormPage.fill_raw_json_line`` — e.g. ``None`` -> ``null``,
    ``"foo"`` -> ``"foo"`` (already quoted since ``description`` is read
    back as a Python str from ``json.loads()``, so only the ``None`` case
    needs translating here).
    """
    return "null" if value is None else f'"{value}"'
