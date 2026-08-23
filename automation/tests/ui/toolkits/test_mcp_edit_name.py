"""UI test — rename a Remote MCP from its detail page and verify the new name propagates.

TMS: ELITEA-1925 (test-specs/mcp/l1_edit-remote-mcp-change-name_ELITEA-1925.md)

Edits the "Toolkit Name *" field on a Remote MCP's detail page, confirms Save and
Discard become enabled, saves, and verifies the new name reaches the detail
header, the MCP list, and the reopened detail page — then renames back to the
original (the case's own step 10 / cleanup of the rename).

No substitution of the system under test is performed: every asserted value is
produced by the product (the update PUT's own response body, the rendered header,
the rendered list, the rendered field). The only deviation from the case text is
the *test data* — the case names a pre-existing "Web Search" MCP, which does not
exist in this project and cannot be rediscovered at runtime (see the AFS
§ Test Data), so a disposable MCP is seeded through the real UI create flow and
deleted in teardown.
"""

import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from pages.mcp_list_page import McpListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

# The detail header (`toolkit-detail-title`) does NOT re-render synchronously
# with the update PUT — an immediate read still returns the pre-save name, and
# the new name lands a few seconds later without any user action (measured
# during this case's live analysis: stale at +0ms, correct and stable at
# +2s/+5s/+10s and across a full reload; see the AFS Step 7 note and the
# surface digest). Hence a retrying web-first assertion with a generous window,
# never a bare text read.
HEADER_REFRESH_TIMEOUT = 20_000


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1925_edit-remote-mcp-change-name.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_edit_change_name(page, toolkit_api: ToolkitAPI):
    """A Remote MCP can be renamed; the new name shows in the header, the list, and on reopen."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    listing = McpListPage(page)

    # Seed a dedicated, disposable Remote MCP (AFS § Test Data:
    # generate-shared-with-cleanup). ToolkitAPI.list_all_toolkits() returns an
    # empty list on this environment regardless of auth method (documented
    # quirk — see config.py's remote_github_mcp_toolkit_id comment), so an
    # existing MCP's id cannot be rediscovered at runtime; and renaming is
    # destructive to whatever toolkit it touches. Same precedent as the sibling
    # ELITEA-1927 / ELITEA-1929 specs.
    suffix = uuid.uuid4().hex[:6]
    # MAX_NAME_LENGTH = 32 truncates the Toolkit Name field client-side — both
    # names below stay under it (26 and 23 chars).
    original_name = f"autotest_mcp_rename_{suffix}"
    renamed_name = f"autotest_renamed_{suffix}"

    form.navigate_to_create()
    form.select_remote_mcp_type()
    form.fill_name(original_name)
    # Stored only — this case never clicks Load Tools, so the URL is never dialled.
    form.fill_url("https://mcp.example.com/sse")
    toolkit_id = form.save_and_wait_for_created(project_id)["id"]

    # Console listener — same pattern as test_mcp_edit_toggle_enable_caching.py /
    # test_mcp_edit_raw_json_description.py: capture "error"-type console
    # messages, filter the two pre-existing React dev-mode warnings tracked in
    # EliteaAI/elitea-testing-public#291, and soft-fail (never silently drop)
    # the known #549 MUI Tabs warning, so a genuine regression in this
    # rename/save flow can't hide behind an already-tracked warning
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
        with allure.step("Step 1 — Open the Remote MCP detail page"):
            form.navigate_to_detail(toolkit_id, project_id)
            assert form.form_view_toggle.get_attribute("aria-pressed") == "true", (
                "Detail page should load in Form view"
            )

        with allure.step("Step 2 — Verify the detail page shows the MCP name"):
            assert form.get_detail_heading_text() == original_name, (
                f"Detail title should show the toolkit's name, "
                f"got: {form.get_detail_heading_text()!r}"
            )
            assert form.name_input.input_value() == original_name, (
                f"Toolkit Name field should hold the toolkit's name, "
                f"got: {form.name_input.input_value()!r}"
            )

        with allure.step('Step 3 — Click into the "Toolkit Name *" field (pristine baseline)'):
            # Baseline for Step 5: on a pristine detail form BOTH buttons are
            # disabled — they gate on `isFormDirtyExcluding`
            # (ToolkitsTabBarContainer.jsx:102-109 and :157-160). Without this
            # baseline, Step 5's "becomes enabled" proves nothing.
            assert form.detail_save_button.is_disabled(), (
                "Save should be disabled on a pristine detail form"
            )
            assert form.detail_discard_button.is_disabled(), (
                "Discard should be disabled on a pristine detail form"
            )

        with allure.step(f"Step 4 — Change the name to {renamed_name!r}"):
            form.fill_name(renamed_name)
            assert form.name_input.input_value() == renamed_name, (
                f"Toolkit Name field should display the updated name, "
                f"got: {form.name_input.input_value()!r}"
            )

        with allure.step("Step 5 — Verify Save and Discard become enabled"):
            assert not form.detail_save_button.is_disabled(), (
                "Save should be enabled once the form is dirty"
            )
            assert not form.detail_discard_button.is_disabled(), (
                "Discard should be enabled once the form is dirty"
            )

        with allure.step("Step 6 — Click Save"):
            # save_and_wait_for_updated() only returns once the PUT resolves
            # with status 200, so reaching this line already proves the update
            # request succeeded. No success toast is rendered on this surface
            # (confirmed live on two probes — see the AFS Step 6 note), so the
            # response body plus the propagation asserted in Steps 7-9 is the
            # case's "confirmation or updated state".
            save_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert save_response.get("id") == toolkit_id, (
                f"Save response should reference the same toolkit id, "
                f"got: {save_response.get('id')!r}"
            )
            assert save_response.get("name") == renamed_name, (
                f"Save response should carry the new name, got: {save_response.get('name')!r}"
            )
            _check_no_new_console_errors("Step 6 (Save)")

        with allure.step("Step 7 — Verify the MCP name updates in the header"):
            expect(form.detail_title).to_have_text(
                renamed_name, timeout=HEADER_REFRESH_TIMEOUT
            )

        with allure.step("Step 8 — Navigate to the MCP list; verify the updated name appears"):
            listing.navigate()
            listing.wait_for_page_load()
            listing.search(renamed_name)
            card_names = listing.get_card_names()
            assert renamed_name in card_names, (
                f"MCP list should show the renamed MCP after searching for it, "
                f"got: {card_names!r}"
            )
            assert original_name not in card_names, (
                f"MCP list should no longer show the old name, got: {card_names!r}"
            )

        with allure.step("Step 9 — Reopen the MCP; verify the name persisted"):
            listing.open_card_by_name(renamed_name)
            assert form.get_detail_heading_text() == renamed_name, (
                f"Reopened detail page should show the new name, "
                f"got: {form.get_detail_heading_text()!r}"
            )
            assert form.name_input.input_value() == renamed_name, (
                f"Reopened Toolkit Name field should hold the new name, "
                f"got: {form.name_input.input_value()!r}"
            )
            _check_no_new_console_errors("Step 9 (reopen from list)")

        with allure.step("Step 10 — Rename back to the original name and save"):
            form.fill_name(original_name)
            revert_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert revert_response.get("name") == original_name, (
                f"Revert response should carry the original name, "
                f"got: {revert_response.get('name')!r}"
            )
            expect(form.detail_title).to_have_text(
                original_name, timeout=HEADER_REFRESH_TIMEOUT
            )
            # Reload to prove the restore is server-side, not client state
            # (same discipline as the sibling ELITEA-1929 spec).
            form.reload_and_wait()
            assert form.name_input.input_value() == original_name, (
                f"Name should read as the original after a full reload, "
                f"got: {form.name_input.input_value()!r}"
            )
            _check_no_new_console_errors("Step 10 (rename back + reload)")

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
