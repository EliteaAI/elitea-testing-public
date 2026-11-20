"""Remote MCP test result — Copy markdown / Copy text icons visible, clickable, toast-confirmed (ELITEA-4759).

Spec: test-specs/mcp/l1_mcp-test-result-copy-markdown-and-copy-text-icons-toast_ELITEA-4759.md
"""

import allure
import pytest
from pages.toolkit_detail_page import ToolkitDetailPage
from pages.toolkit_test_settings_page import ToolkitTestSettingsPage
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.ui, pytest.mark.mcp, pytest.mark.p1, pytest.mark.regression]

T = 15_000
RUN_TIMEOUT = 90_000
TOAST_DISMISS_TIMEOUT = 20_000
TOOL = "Read wiki structure"
REPO = "AsyncFuncAI/deepwiki-open"


@pytest.mark.tms("ELITEA-4759")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/"
    "ELITEA-4759_mcp-test-result-copy-markdown-and-copy-text-actions.md",
    "onetest-ai Test Case link",
)
def test_mcp_test_result_copy_icons_show_tooltip_and_toast(page: Page, mcp_toolkit_with_tools):
    """Both copy icons are visible under the MCP tool result; tooltips and click toasts match."""
    page.set_viewport_size({"width": 1600, "height": 1400})
    detail = ToolkitDetailPage(page)
    settings = ToolkitTestSettingsPage(page)
    mcp_id = mcp_toolkit_with_tools["id"]

    with allure.step("Step 1 — Open the MCP detail page; the Test button is visible"):
        detail.navigate(f"/mcps/all/{mcp_id}")
        expect(detail.test_button).to_be_visible(timeout=T)

    with allure.step("Step 2 — Click Test; the Test Toolkit page opens with the MCP tool list"):
        detail.open_test_surface(timeout=T)
        expect(settings.start_search).to_be_visible(timeout=T)
        expect(settings.get_tool_chips()).to_have_count(3, timeout=T)

    with allure.step("Step 3 — Select Read wiki structure; Model and Run Test are shown"):
        settings.get_tool_chip(TOOL).click()
        expect(settings.tool_select).to_contain_text(TOOL, timeout=T)
        expect(settings.run_tool_button).to_be_visible(timeout=T)
        expect(settings.model_selector_name).to_be_visible(timeout=T)

    with allure.step("Step 4 — Run Test; the result shows read_wiki_structure"):
        settings.fill_param_field("repoName", REPO)
        settings.run_tool(timeout=T)
        result = settings.wait_for_tool_result(timeout=RUN_TIMEOUT)
        assert "read_wiki_structure" in result, f"Result should mention read_wiki_structure, got: {result[:200]!r}"

    with allure.step("Step 5 — Copy markdown and Copy text icons are visible and enabled"):
        assert settings.is_result_copy_icon_enabled("markdown", timeout=T), "Copy markdown icon not enabled"
        assert settings.is_result_copy_icon_enabled("text", timeout=T), "Copy text icon not enabled"

    with allure.step("Step 6 — Hover the Copy markdown icon; tooltip 'Copy markdown'"):
        assert settings.hover_result_copy_icon("markdown", timeout=T) == "Copy markdown"

    with allure.step("Step 7 — Click Copy markdown; toast 'Markdown copied to clipboard.'"):
        toast = settings.click_result_copy_icon("markdown", timeout=T)
        assert toast == "Markdown copied to clipboard.", f"Unexpected toast: {toast!r}"
        expect(settings.toast_message).to_have_count(0, timeout=TOAST_DISMISS_TIMEOUT)

    with allure.step("Step 8 — Hover the Copy text icon; tooltip 'Copy text'"):
        assert settings.hover_result_copy_icon("text", timeout=T) == "Copy text"

    with allure.step("Step 9 — Click Copy text; toast 'Text copied to clipboard.'"):
        toast = settings.click_result_copy_icon("text", timeout=T)
        assert toast == "Text copied to clipboard.", f"Unexpected toast: {toast!r}"
