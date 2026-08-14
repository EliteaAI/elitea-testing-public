"""UI test — MCP list page view toggle (Card <-> Table).

TMS: ELITEA-1944 (test-specs/mcp/l1_mcp-dashboard-view-toggle-card-table_ELITEA-1944.md)

Verifies the MCP list page's Card/Table view toggle: Card view is the
default active layout, clicking Table view switches the layout (URL,
aria-pressed, columns, row content), and clicking Card view restores the
original card layout with the same MCPs.
"""

import logging
import uuid
from urllib.parse import parse_qs, urlparse

import allure
import pytest

from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from pages.mcp_list_page import McpListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]


def _seed_mcp_via_ui(page) -> int:
    """Create a minimal Remote MCP through the UI create flow; return its id.

    Toolkits created via the raw REST API never show up in this
    environment's MCP list (the ``tools/prompt_lib/{project}`` list endpoint
    returns ``{"rows": [], "total": 0}`` even for toolkits that individually
    exist by id — a documented environment quirk, see
    ``.agents/memory/test-automation-engineer/mcp_pipeline_node_toolkit_tool_quirks.md``),
    so seeding for THIS test must go through the UI form to be visible to
    the list page under test. Called only when the project is genuinely
    empty (see :meth:`McpListPage.has_any_mcp`) — read-only-by-default
    (Hard Rule 10) otherwise reuses whatever MCPs already exist.
    """
    form = McpFormPage(page)
    # McpListPage.has_any_mcp() already left the page on /mcps/create.
    form.select_remote_mcp_type()
    form.fill_name(f"autotest_mcp_toggle_{uuid.uuid4().hex[:6]}")
    form.fill_url("https://mcp.example.com/sse")
    save_response = form.save_and_wait_for_created(str(settings.elitea_project_id))
    return save_response["id"]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1944_mcp-dashboard-view-toggle-card-table.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_dashboard_view_toggle_card_table(page, toolkit_api: ToolkitAPI):
    """MCP list page supports switching between Card and Table view layouts."""
    list_page = McpListPage(page)
    seeded_mcp_id: int | None = None

    try:
        # Precondition (AFS § Preconditions): at least one MCP must exist.
        # Not a case step — reuse existing MCPs when present, seed only if
        # the project is genuinely empty.
        if not list_page.has_any_mcp():
            seeded_mcp_id = _seed_mcp_via_ui(page)
            logger.info("Seeded MCP toolkit %s — project had zero MCPs", seeded_mcp_id)

        with allure.step("Step 1 — Navigate to MCP list page; verify it loads with no ?view= param"):
            list_page.navigate()
            assert "MCPs" in page.title(), f"Page title should reference MCPs, got: {page.title()!r}"
            parsed = urlparse(page.url)
            assert parsed.path.rstrip("/").endswith("/mcps/all"), (
                f"Expected the MCP list page URL, got: {page.url}"
            )
            assert parsed.query == "", (
                f"A fresh, unvisited navigation should carry no ?view= query param, got: {page.url}"
            )

        with allure.step(
            'Step 2 — Verify the "Small View Toggler" group is visible with '
            "Table view and Card list view buttons"
        ):
            assert list_page.table_view_button.is_visible(), "Table view button should be visible"
            assert list_page.table_view_button.is_enabled(), "Table view button should be enabled"
            assert list_page.card_view_button.is_visible(), "Card list view button should be visible"
            assert list_page.card_view_button.is_enabled(), "Card list view button should be enabled"

        with allure.step("Step 3 — Verify Card list view button is pressed (active) by default"):
            assert list_page.is_card_view_active(), (
                "Card view should be the default active layout on a fresh page load"
            )
            assert not list_page.is_table_view_active(), (
                "Table view should NOT be active while Card view is the default"
            )

        with allure.step("Step 4 — Verify MCPs are displayed in card format by default"):
            card_count = list_page.get_card_count()
            assert card_count > 0, "At least one MCP card should be visible by default"
            original_card_names = list_page.get_card_names()
            assert len(original_card_names) == card_count, (
                f"Every visible card should expose a name, got {len(original_card_names)} "
                f"names for {card_count} cards"
            )

        with allure.step("Step 5 — Click the Table view button; verify URL + aria-pressed state"):
            list_page.switch_to_table_view()
            assert parse_qs(urlparse(page.url).query).get("view") == ["table"], (
                f"URL should reflect ?view=table after switching, got: {page.url}"
            )
            assert list_page.is_table_view_active(), (
                "Table view should be active after clicking the Table view button"
            )
            assert not list_page.is_card_view_active(), (
                "Card view should no longer be active after switching to Table view"
            )

        with allure.step("Step 6 — Verify MCPs display in table/list format"):
            assert list_page.get_card_count() == 0, (
                "MCP cards should no longer be visible once Table view is active"
            )
            visible_headers = list_page.get_visible_table_column_headers()
            expected_headers = [label for _, label in McpListPage.TABLE_COLUMNS]
            assert list(visible_headers) == expected_headers, (
                f"All table column headers should be visible, got: {visible_headers}"
            )
            visible_row_names = list_page.get_visible_table_row_names(original_card_names)
            assert set(visible_row_names) == set(original_card_names), (
                f"Every MCP shown in Card view should also appear as a table row, "
                f"expected {original_card_names}, found {visible_row_names}"
            )

        with allure.step("Step 7 — Click the Card list view button; verify URL + aria-pressed state"):
            list_page.switch_to_card_view()
            assert parse_qs(urlparse(page.url).query).get("view") == ["cards"], (
                f"URL should reflect ?view=cards after switching back, got: {page.url}"
            )
            assert list_page.is_card_view_active(), (
                "Card view should be active again after clicking the Card list view button"
            )
            assert not list_page.is_table_view_active(), (
                "Table view should no longer be active after switching back to Card view"
            )

        with allure.step(
            "Step 8 — Verify MCPs display back in card format with the same names as Step 4"
        ):
            restored_card_names = list_page.get_card_names()
            assert set(restored_card_names) == set(original_card_names), (
                f"Card view should restore the same MCPs after the round trip, "
                f"expected {original_card_names}, got {restored_card_names}"
            )
    finally:
        # Not a case step — cleanup for the MCP seeded above when the
        # project was empty (AFS § Cleanup: seeded data needs its own
        # teardown; pre-existing MCPs are reused and never touched).
        if seeded_mcp_id is not None:
            try:
                toolkit_api.delete_toolkit(seeded_mcp_id)
            except Exception:
                logger.warning("Failed to delete seeded MCP toolkit id=%s during cleanup", seeded_mcp_id, exc_info=True)
