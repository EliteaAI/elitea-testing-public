"""Agent "+ Modules" dropdown opens from the Tools row, lists every module once
and scrolls to a fully visible last module (ELITEA-4789).

Read-only: opens the dropdown on a fresh agent and mutates nothing.

Reference list (case step 7): the case names Settings > General > Default
Modules, but live that list is NOT the agent menu's list (see the AFS
Clarifications). Oracle used instead: rows unique by key and by title, row
count equals the switch count, and a named REQUIRED subset of module keys is
present (a subset, not equality — the module list can grow).

Spec: test-specs/agents/l1_modules-dropdown-opens-lists-all-modules-and-scrolls-to-last_ELITEA-4789.md
"""

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.agents]

TIMEOUT = 10_000

EXPECTED_TOOLS_ROW_ORDER = [
    "agent-add-toolkit-button",
    "agent-add-mcp-button",
    "agent-add-agent-button",
    "agent-add-pipeline-button",
    "agent-add-modules-button",
]

# Keys observed live on DEV; subset assertion because the list may grow.
REQUIRED_MODULE_KEYS = {
    "attachments", "image_generation", "data_analysis", "elitea_builder", "ask_user",
    "planner", "pyodide", "swarm", "lazy_tools_mode",
}
# Platform-settings dependent; checked only for "if present, then once".
OPTIONAL_MODULE_KEYS = {"web_search", "code_mode"}


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "agents/modules/ELITEA-4789_modules-dropdown-opens-lists-all-modules-and-scrolls-to-last-module.md",
    "onetest-ai Test Case link",
)
@pytest.mark.tms("ELITEA-4789")
@pytest.mark.p0
@pytest.mark.regression
def test_modules_dropdown_lists_all_modules_and_scrolls_to_last(page, agent_id):
    detail = AgentDetailPage(page)
    detail.navigate(agent_id)
    detail.dismiss_platform_release_banner_if_present()

    with allure.step("Step 1 — Tools row buttons are in order Toolkit, MCP, Agent, Pipeline, Modules"):
        for loc in (detail.add_toolkit_button, detail.add_mcp_button, detail.add_agent_button,
                    detail.add_pipeline_button, detail.add_modules_button):
            expect(loc).to_be_visible(timeout=TIMEOUT)
        assert detail.tools_row_button_testids_in_x_order() == EXPECTED_TOOLS_ROW_ORDER

    with allure.step("Step 2 — No old MODULES grid and no Show all / Show less control"):
        expect(detail.modules_old_show_all_toggle).to_have_count(0)
        expect(detail.modules_old_grid_header).to_have_count(0)

    with allure.step("Step 3 — Clicking + Modules opens the dropdown with a search field and list"):
        detail.open_modules_menu(timeout=TIMEOUT)
        expect(detail.modules_search_input).to_be_visible(timeout=TIMEOUT)
        expect(detail.modules_search_input).to_have_attribute("placeholder", "Search modules...")
        expect(detail.modules_search_input).to_be_focused()
        expect(detail.add_modules_button).to_have_attribute("aria-haspopup", "menu")
        expect(detail.add_modules_button).to_have_attribute("aria-expanded", "true")
        expect(detail.modules_menu_list.within(detail.modules_menu)).to_be_visible(timeout=TIMEOUT)

    keys = detail.module_row_anatomy()
    with allure.step("Step 4 — Every row shows an icon, name, (i) icon and an on/off switch"):
        assert keys, "dropdown has no module rows"
        for row in keys:
            assert row["svgs"] >= 2, f"{row['key']}: expected module icon + (i) svg, got {row['svgs']}"
            assert row["name"], f"{row['key']}: empty name"
            assert row["info"] == 1, f"{row['key']}: expected 1 (i) icon, got {row['info']}"
            assert row["switches"] == 1, f"{row['key']}: expected 1 switch, got {row['switches']}"

    with allure.step("Step 5 — Mouse wheel scrolls the list to its end; the page does not scroll"):
        m0 = detail.modules_list_metrics()
        assert m0["scrollHeight"] > m0["clientHeight"], (
            f"precondition: list must overflow so scroll steps are meaningful, got {m0}"
        )
        detail.wheel_scroll_modules_list_to_end()
        end = detail.modules_list_metrics()
        assert abs(end["scrollTop"] - (end["scrollHeight"] - end["clientHeight"])) <= 1, end
        assert end["windowScrollY"] == 0, f"page behind scrolled: {end}"

    with allure.step("Step 6 — Last module row is fully visible, not clipped by the dropdown bottom"):
        last = detail.modules_menu_item_box("last")
        lst = detail.modules_menu_list.within(detail.modules_menu).bounding_box()
        menu = detail.modules_menu.bounding_box()
        assert last["y"] + last["height"] <= lst["y"] + lst["height"] + 1, (last, lst)
        assert last["y"] + last["height"] <= menu["y"] + menu["height"] + 1, (last, menu)
        assert last["y"] >= lst["y"] - 1, (last, lst)

    with allure.step("Step 7 — Every module is present exactly once"):
        row_keys = detail.module_menu_item_keys()
        titles = detail.module_menu_item_titles()
        assert len(row_keys) == len(set(row_keys)), f"duplicate module keys: {row_keys}"
        assert len(titles) == len(set(titles)), f"duplicate module titles: {titles}"
        assert len(row_keys) == detail.module_menu_toggle_count()
        missing = REQUIRED_MODULE_KEYS - set(row_keys)
        assert not missing, f"required modules missing from dropdown: {sorted(missing)}"
        unknown_dupes = [k for k in row_keys if k in OPTIONAL_MODULE_KEYS and row_keys.count(k) != 1]
        assert not unknown_dupes, unknown_dupes

    with allure.step("Step 8 — Scrolling back to the top shows the first module below the search field"):
        detail.wheel_scroll_modules_list_to_top()
        top = detail.modules_list_metrics()
        assert top["scrollTop"] == 0, top
        first = detail.modules_menu_item_box("first")
        search = detail.modules_search_input.bounding_box()
        assert first["y"] >= search["y"] + search["height"] - 1, (first, search)

    with allure.step("Step 9 — Escape closes the dropdown"):
        page.keyboard.press("Escape")
        expect(detail.modules_menu).to_have_count(0, timeout=TIMEOUT)
