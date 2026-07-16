"""UI test — edit a Remote MCP's Enable Caching toggle and verify persistence.

TMS: ELITEA-1929 (test-specs/mcp/l1_edit-remote-mcp-toggle-enable-caching_ELITEA-1929.md)

Toggles the "Enable Caching" checkbox on a Remote MCP's detail page off, saves,
reloads to confirm server-side persistence, verifies the boolean value in the
Raw Json view, then re-enables and re-saves (this doubles as the test's own
cleanup — see AFS § Cleanup).
"""

import logging
import uuid

import allure
import pytest

from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1929_edit-remote-mcp-toggle-enable-caching.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_edit_toggle_enable_caching(page, toolkit_api: ToolkitAPI):
    """Enable Caching can be unchecked, saved, and survives reload; re-checking restores it."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)

    # Seed a dedicated Remote MCP for this test (AFS § Cleanup, option 3):
    # ToolkitAPI.list_all_toolkits() returns an empty list on this environment
    # regardless of auth method (documented quirk, see config.py's
    # remote_github_mcp_toolkit_id comment and
    # .agents/memory/test-automation-engineer/mcp_pipeline_node_toolkit_tool_quirks.md),
    # so there is no reliable read-only way to discover an existing Remote
    # MCP's id — seeding via the UI create flow (same helper pattern as
    # test_mcp_view_toggle.py's _seed_mcp_via_ui) is the stable choice here,
    # not a hardcoded leftover toolkit id from a prior manual session.
    # Enable Caching defaults to checked on creation (AFS-confirmed live),
    # matching this case's stated precondition.
    form.navigate_to_create()
    form.select_remote_mcp_type()
    # MAX_NAME_LENGTH=32 truncates the Toolkit Name field client-side (see
    # .agents/memory/test-automation-engineer/mcp_toolkit_create_form_implementer_quirks.md)
    # — keep the generated name at or under that limit.
    toolkit_name = f"autotest_mcp_caching_{uuid.uuid4().hex[:6]}"
    form.fill_name(toolkit_name)
    form.fill_url("https://mcp.example.com/sse")
    create_response = form.save_and_wait_for_created(project_id)
    toolkit_id = create_response["id"]

    # Console listener — same pattern as test_mcp_attach_via_tools_section.py /
    # test_skill_tag_filter.py: capture "error"-type console messages, filter
    # out the two pre-existing React dev-mode warnings already filed as
    # EliteaAI/elitea-testing-public#291 (missing `key` prop in list
    # rendering on the /mcps/create type-picker; invalid `<p>`-in-`<p>` DOM
    # nesting from ToolBaseProperty.jsx's InfoTooltip — the latter also
    # fires on this case's detail page since ToolBaseProperty.jsx is the
    # same shared field renderer, confirmed live during this fix pass), so a
    # real regression introduced by this toggle/save/reload flow isn't
    # masked by an expected, already-tracked warning (AFS Step 4 / Expected
    # Results).
    #
    # A THIRD console error was discovered live while implementing this
    # check (not documented in the AFS or #291): "MUI: The `value` provided
    # to the Tabs component is invalid" — reproduces on every detail-page
    # load, traced to ConfigurationTab.jsx/StyledTabs.jsx, no functional
    # impact on this case's assertions. Filed as
    # EliteaAI/elitea-testing-public#549. Per the no-defect-masking policy
    # this is NOT silently filtered like the #291 warnings — it's tracked as
    # a soft failure (pytest-native expect.soft() equivalent, same pattern
    # as test_skill_agent_interaction.py) so it stays visible without
    # blocking the rest of the flow. Anything else is a genuinely new,
    # hard-failing regression.
    console_messages = []
    soft_failures = []

    def _is_known_291_warning(msg) -> bool:
        text = msg.text
        return (
            'unique "key" prop' in text
            or ("validateDOMNesting" in text and "<p>" in text)
            # Chromium/Playwright collapses the printf-style %s placeholders
            # differently across builds — the raw un-substituted template is
            # also matched so the filter doesn't depend on that formatting.
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
        with allure.step(
            "Step 1 — Open the Remote MCP detail page in Form view"
        ):
            form.navigate_to_detail(toolkit_id, project_id)
            assert form.form_view_toggle.get_attribute("aria-pressed") == "true", (
                "Detail page should load in Form view"
            )
            assert form.get_detail_heading_text() == toolkit_name, (
                f"Detail title should show the toolkit's name, "
                f"got: {form.get_detail_heading_text()!r}"
            )

        with allure.step(
            'Step 2 — Note current state of "Enable Caching" checkbox (checked by default)'
        ):
            assert form.is_enable_caching_checked(), (
                "Enable Caching should be checked by default"
            )

        with allure.step('Step 3 — Click "Enable Caching" to uncheck it'):
            form.click_enable_caching_checkbox()
            assert not form.is_enable_caching_checked(), (
                "Enable Caching should be unchecked after clicking"
            )

        with allure.step("Step 4 — Click Save"):
            # save_and_wait_for_updated() only returns once the PUT response
            # resolves with status 200 (see its expect_response filter) — a
            # non-200 or unmatched response raises a timeout, so reaching
            # this point already proves the save succeeded. Step 6 (Raw Json)
            # is the authoritative check of the persisted boolean value.
            save_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert save_response.get("id") == toolkit_id, (
                f"Save response should reference the same toolkit id, got: {save_response.get('id')!r}"
            )
            _check_no_new_console_errors("Step 4 (Save)")

        with allure.step(
            'Step 5 — Reload page; verify "Enable Caching" is still unchecked'
        ):
            form.reload_and_wait()
            assert not form.is_enable_caching_checked(), (
                "Enable Caching should remain unchecked after a full page reload "
                "(server-side persistence, not just client state)"
            )

        with allure.step(
            'Step 6 — Switch to Raw Json view; verify "enable_caching": false (boolean)'
        ):
            form.switch_to_raw_json_view()
            raw_json = form.get_raw_json()
            enable_caching_value = raw_json.get("settings", {}).get("enable_caching")
            assert enable_caching_value is False, (
                f"Raw Json settings.enable_caching should be the boolean False, "
                f"got: {enable_caching_value!r} ({type(enable_caching_value).__name__})"
            )

        with allure.step(
            "Step 7 — Switch back to Form view; re-enable caching and save again"
        ):
            form.switch_to_form_view()
            assert not form.is_enable_caching_checked(), (
                "Enable Caching should still be unchecked before re-toggling"
            )
            form.click_enable_caching_checkbox()
            assert form.is_enable_caching_checked(), (
                "Enable Caching should be checked again after re-clicking"
            )
            resave_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert resave_response.get("id") == toolkit_id, (
                f"Second save response should reference the same toolkit id, "
                f"got: {resave_response.get('id')!r}"
            )
            # Confirm the restored state survives too — same "trust the
            # server, not just client state" discipline as Step 5.
            form.reload_and_wait()
            assert form.is_enable_caching_checked(), (
                "Enable Caching should be checked again after reload — cleanup restored "
                "the toolkit's original state"
            )
            _check_no_new_console_errors("Step 7 (re-Save + reload)")

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
