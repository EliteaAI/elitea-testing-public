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


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "agents/modules/ELITEA-4790_module-switches-persist-after-save-on-top-ordering-and-discard-restores.md",
    "onetest-ai Test Case link",
)
@pytest.mark.tms("ELITEA-4790")
@pytest.mark.p0
@pytest.mark.regression
def test_module_switches_persist_after_save_on_top_and_discard_restores(page, agent_id):
    """ELITEA-4790. Module A = pyodide; Module B = last row that is not code_mode
    (code_mode opens a warning dialog and closes the dropdown — AFS Clarification 2).
    The fresh ``agent_id`` agent has all modules OFF and is deleted by the fixture,
    so no cleanup step is needed.
    """
    detail = AgentDetailPage(page)
    detail.navigate(agent_id)
    detail.dismiss_platform_release_banner_if_present()
    module_a = "pyodide"

    with allure.step("Step 1 — Open Modules: A and B OFF (baseline recorded), Save and Discard disabled"):
        detail.open_modules_menu(timeout=TIMEOUT)
        keys = detail.module_menu_item_keys()
        assert module_a in keys, f"module {module_a} missing from dropdown: {keys}"
        # DEV defaults a fresh agent to elitea_builder + ask_user ON (AFS drift) -> baseline-relative.
        baseline = set(detail.module_on_keys())
        candidates = [k for k in keys if k not in baseline | {module_a, "code_mode"}]
        assert candidates, f"no non-warning OFF module available for Module B: {keys}"
        module_b = candidates[-1]
        assert module_a not in baseline, f"{module_a} must start OFF, baseline ON={sorted(baseline)}"
        expect(detail.save_button).to_be_disabled(timeout=TIMEOUT)
        expect(detail.discard_button).to_be_disabled(timeout=TIMEOUT)

    with allure.step("Step 2 — Switch Module A ON: dropdown stays open, Save and Discard enabled"):
        detail.toggle_module(module_a)
        expect(detail.module_toggle(module_a)).to_be_checked(timeout=TIMEOUT)
        expect(detail.modules_menu).to_have_count(1)
        expect(detail.save_button).to_be_enabled(timeout=TIMEOUT)
        expect(detail.discard_button).to_be_enabled(timeout=TIMEOUT)

    with allure.step("Step 3 — Scroll and switch Module B ON: dropdown stays open"):
        detail.wheel_scroll_modules_list_to_end()
        detail.toggle_module(module_b)
        expect(detail.module_toggle(module_b)).to_be_checked(timeout=TIMEOUT)
        expect(detail.modules_menu).to_be_visible()

    with allure.step("Step 4 — Escape and Save: Save and Discard become disabled"):
        page.keyboard.press("Escape")
        expect(detail.modules_menu).to_have_count(0, timeout=TIMEOUT)
        detail.click_save()
        expect(detail.save_button).to_be_disabled(timeout=15_000)
        expect(detail.discard_button).to_be_disabled(timeout=15_000)

    def assert_on_modules_on_top():
        row_keys = detail.module_menu_item_keys()
        on = detail.module_on_keys()
        assert set(on) == baseline | {module_a, module_b}, f"ON modules: {on}"
        assert set(row_keys[: len(on)]) == set(on), f"ON modules not on top: {row_keys}, ON={on}"
        assert all(not detail.module_is_on(k) for k in row_keys[len(on):]), "OFF row above/among ON rows"

    with allure.step("Step 5 — Reload: Module A and B are ON and listed above all OFF modules"):
        page.reload()
        detail.wait_for_page_load()
        detail.dismiss_platform_release_banner_if_present()
        expect(detail.save_button).to_be_disabled(timeout=TIMEOUT)
        expect(detail.discard_button).to_be_disabled(timeout=TIMEOUT)
        detail.open_modules_menu(timeout=TIMEOUT)
        assert_on_modules_on_top()

    with allure.step("Step 6 — Switch Module A OFF and close the dropdown: Save and Discard enabled"):
        detail.toggle_module(module_a)
        expect(detail.module_toggle(module_a)).not_to_be_checked(timeout=TIMEOUT)
        page.keyboard.press("Escape")
        expect(detail.modules_menu).to_have_count(0, timeout=TIMEOUT)
        expect(detail.save_button).to_be_enabled(timeout=TIMEOUT)
        expect(detail.discard_button).to_be_enabled(timeout=TIMEOUT)

    with allure.step("Step 7 — Discard (confirm dialog): changes discarded, Save and Discard disabled"):
        detail.click_discard()
        detail.confirm_discard()
        expect(detail.save_button).to_be_disabled(timeout=TIMEOUT)
        expect(detail.discard_button).to_be_disabled(timeout=TIMEOUT)

    with allure.step("Step 8 — Open Modules: Module A and B still ON at the top"):
        detail.open_modules_menu(timeout=TIMEOUT)
        assert_on_modules_on_top()

    with allure.step("Step 9 — Cleanup: switch A and B OFF and Save; reload shows all OFF"):
        detail.toggle_module(module_a)
        detail.toggle_module(module_b)
        page.keyboard.press("Escape")
        expect(detail.modules_menu).to_have_count(0, timeout=TIMEOUT)
        detail.click_save()
        expect(detail.save_button).to_be_disabled(timeout=15_000)
        page.reload()
        detail.wait_for_page_load()
        detail.dismiss_platform_release_banner_if_present()
        detail.open_modules_menu(timeout=TIMEOUT)
        assert set(detail.module_on_keys()) == baseline, "A and B must be OFF, baseline unchanged"
