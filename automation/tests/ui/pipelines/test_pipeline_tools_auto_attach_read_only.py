"""UI test — Pipeline: tools selected in nodes auto-attach to the read-only TOOLS section.

TMS: ELITEA-4718
(test-specs/pipelines/l1_pipeline-tools-selected-in-nodes-auto-attach-read-only-tools_ELITEA-4718.md)

Case-text drift (AFS § Known Defects): Discard only exists on a saved pipeline, so the new pipeline is saved
once after the shared attachment is built (Steps 8-9 run on the saved pipeline); the saved YAML keeps an empty
``input_mapping: {}`` key after the clear (asserted as "no entries", not "no key"); TOOLS is hidden while a
node panel is open, so it is re-expanded before every read.
"""

import re

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipelines_list_page import PipelinesListPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p0, pytest.mark.regression]

T = 15_000
EMPTY_TEXT = "Tools you select in nodes will appear here."


@pytest.mark.tms("ELITEA-4718")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-4718_pipeline-tools-selected-in-nodes-auto-attach-and-read-only-tools-section.md",
    "onetest-ai Test Case link",
)
def test_tools_selected_in_nodes_auto_attach_and_read_only_tools(page, artifact_toolkit, agent_id, agent_api,
                                                                 pipeline_api):
    """Node pickers attach to TOOLS (shared, 'Used by'), clear detaches, Discard restores, saved YAML is clean."""
    tk = artifact_toolkit["name"]
    agent_name = agent_api.get_agent(agent_id)["name"]
    created_id = None
    page.set_viewport_size({"width": 1600, "height": 1400})

    try:
        pp = PipelineDetailPage(page)

        with allure.step("Step 1 — New pipeline: TOOLS shows the placeholder and no add buttons"):
            list_page = PipelinesListPage(page)
            list_page.navigate()
            list_page.dismiss_banner_if_present()
            list_page.click_create_pipeline()
            expect(pp.toolkits_section).to_be_visible(timeout=30_000)
            expect(pp.tools_section_empty).to_have_text(EMPTY_TEXT)
            expect(pp.add_toolkit_button).to_have_count(0)
            expect(pp.add_mcp_button).to_have_count(0)
            expect(pp.add_agent_button).to_have_count(0)
            expect(pp.add_pipeline_button).to_have_count(0)

        with allure.step("Step 2 — Add a Toolkit node; its picker lists project toolkits with search + Create new"):
            pp.empty_state_add_node_button.click()
            expect(pp.node_type_selector).to_be_visible(timeout=T)
            pp.select_add_node_menu_item("toolkit")
            pp.open_toolkit_node_by_card("Toolkit 1", timeout=T)
            pp.open_toolkit_node_picker(timeout=T)
            expect(pp.toolkit_node_picker_menu).to_be_visible()
            expect(pp.toolkit_node_picker_search).to_be_visible()
            expect(pp.toolkit_node_picker_create_new).to_be_visible()
            expect(pp.toolkit_picker_option_named(tk)).to_have_count(1)
            row_texts = pp.get_toolkit_picker_row_texts()
            assert any(tk in t for t in row_texts), f"Fixture toolkit {tk!r} missing from picker rows {row_texts}"

        with allure.step("Step 3 — Select the toolkit and a tool: ONE TOOLS card, Used by Toolkit 1, Show tools"):
            pp.select_toolkit_node_toolkit(tk, timeout=T)
            expect(pp.toolkit_node_toolkit_select).to_contain_text(tk, timeout=T)
            pp.select_toolkit_node_tool("create_file", timeout=T)
            pp.expand_tools_section(timeout=T)
            expect(pp.toolkit_card).to_have_count(1, timeout=T)
            card = pp.tool_card_named(tk).first
            expect(card).to_contain_text("Show tools", timeout=T)
            expect(pp.tool_card_used_by_chips(tk)).to_have_text(["Toolkit 1"], timeout=T)

        with allure.step("Step 4 — Second Toolkit node: its picker marks the toolkit 'In use'"):
            pp.close_node_panel(timeout=T)
            pp.add_node("Toolkit", timeout=T)
            pp.open_toolkit_node_by_card("Toolkit 2", timeout=T)
            pp.open_toolkit_node_picker(timeout=T)
            expect(pp.toolkit_picker_in_use_marker(tk)).to_have_count(1, timeout=T)
            expect(pp.toolkit_picker_option_named(tk).first).to_contain_text("In use")

        with allure.step("Step 5 — Select the same toolkit in Toolkit 2: still ONE card, Used by both nodes"):
            pp.select_toolkit_node_toolkit(tk, timeout=T)
            expect(pp.toolkit_node_toolkit_select).to_contain_text(tk, timeout=T)
            pp.expand_tools_section(timeout=T)
            expect(pp.toolkit_card).to_have_count(1, timeout=T)
            expect(pp.tool_card_used_by_chips(tk)).to_have_text(["Toolkit 1", "Toolkit 2"], timeout=T)
            # Case-text drift: Discard needs a saved pipeline; persist the attachment once here.
            pp.save_button.click()
            page.wait_for_url(re.compile(r"/pipelines/all/\d+"), timeout=30_000)
            created_id = int(re.search(r"/pipelines/all/(\d+)", page.url).group(1))
            expect(pp.save_button).to_be_disabled(timeout=30_000)
            pp.expand_tools_section(timeout=T)
            expect(pp.toolkit_card).to_have_count(1, timeout=T)
            expect(pp.tool_card_used_by_chips(tk)).to_have_text(["Toolkit 1", "Toolkit 2"], timeout=T)

        with allure.step("Step 6 — Clicking a 'Used by' name selects that node and opens its panel"):
            for node in ("Toolkit 1", "Toolkit 2"):
                pp.expand_tools_section(timeout=T)
                pp.click_used_by_chip(tk, node, timeout=T)
                expect(pp.node_panel_name_input).to_have_value(node, timeout=T)

        with allure.step("Step 7 — Clear on Toolkit 2: the entry stays, Used by Toolkit 1 only"):
            pp.open_toolkit_node_by_card("Toolkit 2", timeout=T)
            pp.clear_toolkit_node_toolkit(timeout=T)
            pp.expand_tools_section(timeout=T)
            expect(pp.toolkit_card).to_have_count(1, timeout=T)
            expect(pp.tool_card_used_by_chips(tk)).to_have_text(["Toolkit 1"], timeout=T)

        with allure.step("Step 8 — Clear on Toolkit 1: entry disappears, placeholder returns, Discard enabled"):
            pp.open_toolkit_node_by_card("Toolkit 1", timeout=T)
            pp.clear_toolkit_node_toolkit(timeout=T)
            pp.expand_tools_section(timeout=T)
            expect(pp.toolkit_card).to_have_count(0, timeout=T)
            expect(pp.tools_section_empty).to_have_count(1, timeout=T)
            expect(pp.discard_button).to_be_enabled(timeout=T)

        with allure.step("Step 9 — Discard: both nodes select the toolkit again, card back Used by both"):
            dialog = pp.start_discard(timeout=T)
            expect(dialog).to_contain_text("discard changes")
            pp.confirm_discard(timeout=T)
            pp.expand_tools_section(timeout=T)
            expect(pp.toolkit_card).to_have_count(1, timeout=T)
            expect(pp.tool_card_used_by_chips(tk)).to_have_text(["Toolkit 1", "Toolkit 2"], timeout=T)
            for node in ("Toolkit 1", "Toolkit 2"):
                pp.open_toolkit_node_by_card(node, timeout=T)
                expect(pp.toolkit_node_toolkit_select).to_contain_text(tk, timeout=T)

        with allure.step("Step 10 — Clear both, Save, YAML view: no toolkit_name / tool / mapped params"):
            # Control: the page YAML carries the keys BEFORE the clear, so a clean read afterwards is not vacuous.
            pp.close_node_panel(timeout=T)
            pp.switch_to_yaml_view()
            pp.wait_for_page_yaml_rendered()
            before = pp.get_yaml_node_blocks()
            assert before["Toolkit 1"].get("toolkit_name") == tk, f"Control: toolkit_name missing before clear: {before}"
            assert before["Toolkit 1"].get("tool") == "create_file", f"Control: tool missing before clear: {before}"
            pp.switch_to_flow_view()
            for node in ("Toolkit 1", "Toolkit 2"):
                pp.open_toolkit_node_by_card(node, timeout=T)
                pp.clear_toolkit_node_toolkit(timeout=T)
            pp.close_node_panel(timeout=T)
            pp.save_and_wait_for_saved(timeout=30_000)
            expect(pp.save_button).to_be_disabled(timeout=T)
            pp.switch_to_yaml_view()
            pp.wait_for_page_yaml_rendered()
            after = pp.get_yaml_node_blocks()
            for node in ("Toolkit 1", "Toolkit 2"):
                block = after[node]
                assert block.get("type") == "toolkit", f"{node} block missing/changed: {block}"
                assert "toolkit_name" not in block, f"{node} still has toolkit_name: {block}"
                assert "tool" not in block, f"{node} still has tool: {block}"
                assert not block.get("input_mapping"), f"{node} still has input_mapping entries: {block}"
            pp.switch_to_flow_view()

        with allure.step("Step 11 — Agent node picker groups rows under Agents and Pipelines"):
            pp.add_node("Agent", timeout=T)
            pp.open_agent_node_picker(timeout=T)
            expect(pp.agent_node_picker_menu).to_be_visible()
            expect(pp.agent_node_picker_create_agent).to_be_visible()
            expect(pp.agent_node_picker_create_pipeline).to_be_visible()
            for group in ("Agents", "Pipelines"):
                expect(pp.PICKER_GROUP_TITLE.within(pp.agent_node_picker_menu, group)).to_have_count(1, timeout=T)

        with allure.step("Step 12 — Select an agent: TOOLS card with version 'base', Used by Agent 1"):
            pp.pick_agent_node_application(agent_name, timeout=T)
            pp.wait_for_agent_node_agent_value(agent_name, timeout=T)
            pp.expand_tools_section(timeout=T)
            card = pp.tool_card_named(agent_name).first
            expect(card).to_be_visible(timeout=T)
            expect(card.locator(pp.TOOLKIT_CARD_USED_BY)).to_have_text(["Agent 1"], timeout=T)
            expect(pp.tool_card_version.first).to_have_text("base", timeout=T)
    finally:
        if created_id is not None:
            try:
                pipeline_api.delete_pipeline(created_id)
            except Exception as exc:  # cleanup must not mask the test verdict
                allure.attach(str(exc), name="pipeline cleanup failed")
