"""UI test — delete a Remote MCP via the three-dot menu's type-to-confirm dialog.

TMS: ELITEA-1947 (test-specs/mcp/l3_delete-remote-mcp_ELITEA-1947.md)

Creates a Remote MCP through the UI create flow, navigates to the MCP list
and opens its detail page via a REAL list-card click (not the create flow's
own post-save redirect), deletes it through the three-dot menu -> Delete ->
type-to-confirm dialog, and verifies both the immediate list-absence and the
post-reload persisted absence.

Step-order caveat (AFS § Known Defects Found / Automation Hints, load-bearing
for correctness, not just style): the step 8 redirect-to-list assertion only
lands reliably when the detail page was reached via a list->card-click
navigation — DeleteToolkitButton.jsx's confirm handler does
``window.history.length > 1 ? navigate(-1) : navigate(MCPsWithTab)``, so
staying on the create flow's own post-save detail page and deleting from
there redirects to ``/mcps/create`` instead. This test therefore implements
steps 2-3 as real navigations rather than shortcutting via the create
response.
"""

import logging

import allure
import pytest

from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from pages.mcp_list_page import McpListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p3, pytest.mark.regression, pytest.mark.new]

# Fixed literal name — required verbatim by the delete-confirm dialog's exact-text
# assertions (case text hardcodes "autotest_mcp_to_delete" in both the dialog body
# and the type-to-confirm field), so this can't be uuid-suffixed like sibling MCP
# tests (e.g. ELITEA-1922's autotest_mcp_full_{uuid}).
TOOLKIT_NAME = "autotest_mcp_to_delete"
TOOLKIT_URL = "https://mcp.example.com/sse"


def _delete_stale_mcp_if_present(page, toolkit_api: ToolkitAPI, name: str) -> None:
    """Defensive pre-check: delete a leftover MCP named *name* from a prior aborted run.

    AFS § Test Data flags that this case's fixed literal name is NOT verified
    unique across runs — a run that fails between create (step 1) and
    confirmed delete (step 7) would leave a stale MCP with this exact name
    for the next run, which would break this test's dialog-text assertions
    (two same-named cards) or its list-absence assertions.

    ``ToolkitAPI.list_all_toolkits()``/``list_toolkits()`` is a CONFIRMED
    BROKEN discovery path on this environment — it always returns
    ``{"rows": [], "total": 0}`` regardless of params, a different (and
    always-empty) endpoint than the one ``/mcps/all`` itself renders from
    (see
    ``.agents/memory/test-automation-engineer/mcp_pipeline_node_toolkit_tool_quirks.md``).
    A UI-based list-check is therefore the only reliable discovery path here
    — deletion itself uses the raw API (delete-by-id IS confirmed reliable,
    unaffected by the listing quirk) rather than repeating the full UI
    delete-confirm flow this test itself already exercises.
    """
    list_page = McpListPage(page)
    if not list_page.has_any_mcp():
        return
    if name not in list_page.get_card_names():
        return
    logger.warning("Found stale MCP %r from a prior aborted run — deleting via API before test", name)
    list_page.open_card_by_name(name)
    stale_id = McpFormPage(page).get_toolkit_id_from_url()
    toolkit_api.delete_toolkit(stale_id)


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1947_delete-remote-mcp.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
@pytest.mark.blocked
def test_delete_remote_mcp(page, toolkit_api: ToolkitAPI):
    """A Remote MCP can be permanently deleted via the three-dot menu's type-to-confirm dialog."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    list_page = McpListPage(page)

    _delete_stale_mcp_if_present(page, toolkit_api, TOOLKIT_NAME)

    created_id: int | None = None
    try:
        with allure.step("Step 1 — Create a Remote MCP named 'autotest_mcp_to_delete'"):
            form.navigate_to_create()
            form.select_remote_mcp_type()
            form.fill_name(TOOLKIT_NAME)
            form.fill_url(TOOLKIT_URL)
            save_response = form.save_and_wait_for_created(project_id)
            created_id = save_response["id"]
            assert isinstance(created_id, int), (
                f"Save response should include a numeric id: {save_response!r}"
            )
            assert f"/mcps/all/{created_id}" in page.url, (
                f"Should navigate to the new MCP's detail page, got: {page.url}"
            )

        with allure.step("Step 2 — Navigate to the MCP list; verify the created MCP appears"):
            list_page.navigate()
            assert TOOLKIT_NAME in list_page.get_card_names(), (
                f"{TOOLKIT_NAME!r} should appear in the MCP list after creation"
            )

        with allure.step("Step 3 — Click the MCP's card from the list to open its detail page"):
            # Load-bearing ordering (module docstring / AFS § Known Defects
            # Found): a REAL list->card-click navigation, not the create
            # flow's own post-save redirect, is required for step 8's
            # redirect assertion to be reliable.
            list_page.open_card_by_name(TOOLKIT_NAME)
            form.wait_for_page_load()
            assert f"/mcps/all/{created_id}" in page.url, (
                f"Should be on the MCP's detail page after the card click, got: {page.url}"
            )
            assert form.name_input.input_value() == TOOLKIT_NAME

        with allure.step("Step 4 — Click the three-dot actions menu button; verify menu opens"):
            form.open_controls_menu()
            menu_text = form.get_controls_menu_text()
            for expected_item in ("Export", "Fork", "Copy link", "Pin to top", "Delete"):
                assert expected_item in menu_text, (
                    f"Controls menu should show {expected_item!r}, got: {menu_text!r}"
                )

        with allure.step("Step 5 — Click the 'Delete' menu item; verify the confirmation dialog opens"):
            form.click_delete_menu_item()
            assert form.delete_confirm_dialog.is_visible(), "Delete confirmation dialog should open"

        with allure.step("Step 6 — Verify the confirmation dialog's content"):
            dialog_text = form.get_delete_confirm_dialog_text()
            assert "Delete confirmation" in dialog_text, (
                f"Dialog title should read 'Delete confirmation', got: {dialog_text!r}"
            )
            expected_body = (
                f"Are you sure to delete the {TOOLKIT_NAME}? Enter the name to complete the action."
            )
            assert expected_body in dialog_text, (
                f"Dialog body should read {expected_body!r}, got: {dialog_text!r}"
            )
            assert form.delete_confirm_name_input.is_visible(), "Name field should be present"
            # Axis 2 addition (AFS) — type-to-confirm safety gate: Delete starts disabled.
            assert not form.is_delete_confirm_button_enabled(), (
                "Delete button should be disabled before the exact name is typed"
            )

        with allure.step("Step 7 — Type the exact name; click Delete; verify the 204 response"):
            form.fill_delete_confirm_name(TOOLKIT_NAME)
            # Axis 2 addition (AFS) — Delete only enables once the typed name matches exactly.
            assert form.is_delete_confirm_button_enabled(), (
                "Delete button should enable once the typed name matches exactly"
            )
            form.confirm_delete(project_id, created_id)

        with allure.step("Step 8 — Verify redirect to the MCP list page"):
            assert page.url.rstrip("/").endswith("/mcps/all"), (
                f"Should redirect to the MCP list page after confirming deletion, got: {page.url}"
            )

        with allure.step("Step 9 — Verify the MCP no longer appears in the list"):
            list_page.wait_for_page_load()
            assert TOOLKIT_NAME not in list_page.get_card_names(), (
                f"{TOOLKIT_NAME!r} should no longer appear in the MCP list after deletion"
            )

        with allure.step("Step 10 — Reload the page; verify the deletion persisted"):
            list_page.reload_and_wait()
            assert TOOLKIT_NAME not in list_page.get_card_names(), (
                f"{TOOLKIT_NAME!r} should still be absent from the MCP list after a full page reload"
            )

        # This case's own steps 5-7 ARE the cleanup (AFS § Cleanup) — clear
        # created_id so the finally block below doesn't attempt a redundant
        # delete-by-id against an already-deleted toolkit.
        created_id = None

    finally:
        # Not a case step — safety-net cleanup only fires if the test failed
        # before its own delete steps (5-7) completed.
        if created_id is not None:
            try:
                toolkit_api.delete_toolkit(created_id)
            except Exception:
                logger.warning(
                    "Failed to delete MCP toolkit id=%s during cleanup", created_id, exc_info=True
                )
