"""UI test — Pipeline: new pipeline empty canvas, first node and Test Pipeline gate.

TMS: ELITEA-4714
(test-specs/pipelines/l1_pipeline-new-pipeline-empty-canvas-first-node-and-test-gate_ELITEA-4714.md)

Creates a pipeline through the UI and walks the Test Pipeline button's gate: disabled (hard) at every
stage until the first Agent node is configured and saved, enabled afterwards, disabled again once the
nodes are deleted. Tooltip wording is SOFT (collected, reported at the end) per the case; the disabled /
enabled state is hard.

Case-text drift (AFS § Case-text clarifications): Step 8 names ``pipeline-node-summary-primary`` but an
unconfigured card renders only ``pipeline-node-summary`` ("Not configured"); tooltip wording differs
slightly (quotes / trailing period).
"""

import re
import warnings

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipelines_list_page import PipelinesListPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
POST_SAVE_TIMEOUT = 25_000
EMPTY_STATE_TEXT = "Start by adding your first node to the canvas!"
NODE_TYPES = ["Agent", "Code", "Decision", "Human-in-the-loop", "LLM", "MCP", "Printer", "Router",
              "State modifier", "Toolkit"]
TASK_TEXT = "Say hello"


def _soft_tooltip(pp: PipelineDetailPage, expected: str, label: str, soft_failures: list) -> None:
    """Soft check of the Test button tooltip: record a mismatch instead of failing.

    The gate text updates asynchronously after a state change (e.g. right after Save), so re-read
    (each read is a fresh hover) a bounded number of times before recording a mismatch.
    """
    actual = ""
    for _ in range(4):
        actual = pp.read_test_button_tooltip()
        if actual.rstrip(".") == expected.rstrip("."):
            return
    soft_failures.append(f"{label}: tooltip {actual!r} != expected {expected!r}")


@pytest.mark.tms("ELITEA-4714")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-4714_pipeline-new-pipeline-empty-canvas-first-node-and-test-pipeline-gate.md",
    "onetest-ai Test Case link",
)
def test_new_pipeline_empty_canvas_first_node_and_test_gate(page, agent_id, agent_api, pipeline_api):
    """New pipeline: empty canvas -> first Agent node (entrypoint) -> Test gate flips -> delete all -> empty again."""
    agent_name = agent_api.get_agent(agent_id)["name"]
    soft_failures: list[str] = []
    created_id = None
    # Tall viewport: the DEV corner banner otherwise covers the node panel footer (AFS Preconditions).
    page.set_viewport_size({"width": 1366, "height": 1400})

    try:
        with allure.step("Step 1 — Pipelines list -> '+ Pipeline': editor opens on the empty canvas"):
            list_page = PipelinesListPage(page)
            list_page.navigate()
            list_page.dismiss_banner_if_present()
            list_page.click_create_pipeline()
            pp = PipelineDetailPage(page)
            expect(pp.empty_state).to_be_visible(timeout=30_000)
            expect(pp.empty_state).to_contain_text(EMPTY_STATE_TEXT)
            expect(pp.empty_state_add_node_button).to_be_visible()
            assert re.fullmatch(r"Pipeline \d+", pp.get_name()), (
                f"Name should be pre-filled 'Pipeline N', got {pp.get_name()!r}"
            )

        with allure.step("Step 2 — Test Pipeline is disabled before the first save"):
            expect(pp.test_pipeline_button).to_be_disabled()
            _soft_tooltip(pp, "Save the pipeline to test it", "Step 2", soft_failures)

        with allure.step("Step 3 — Save: still disabled, tooltip asks for a connected node"):
            pp.save_button.click()
            page.wait_for_url(re.compile(r"/pipelines/all/\d+"), timeout=30_000)
            created_id = int(re.search(r"/pipelines/all/(\d+)", page.url).group(1))
            expect(pp.empty_state).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(pp.test_pipeline_button).to_be_disabled()
            _soft_tooltip(pp, "Add and configure at least one node connected to End.", "Step 3", soft_failures)

        with allure.step("Step 4 — Add Node lists the 10 node types"):
            pp.empty_state_add_node_button.click()
            expect(pp.node_type_selector).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert pp.node_type_menu_labels() == NODE_TYPES, "Node-type selector should list the 10 types in order"

        with allure.step("Step 5 — Escape closes the selector; empty-state card remains"):
            page.keyboard.press("Escape")
            expect(pp.node_type_menu_items()).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
            expect(pp.empty_state).to_be_visible()

        with allure.step("Step 6 — Re-open, click outside: selector closes"):
            pp.empty_state_add_node_button.click()
            expect(pp.node_type_selector).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            pp.click_outside_menus()
            expect(pp.node_type_menu_items()).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
            expect(pp.empty_state).to_be_visible()

        with allure.step("Step 7 — Select Agent: Agent 1 is the entrypoint, END exists but is not connected"):
            pp.empty_state_add_node_button.click()
            expect(pp.node_type_selector).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            pp.select_add_node_menu_item("agent")
            expect(pp.empty_state).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
            expect(pp.node_entrypoint_badge("Agent 1")).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
            node_ids = set(pp.get_node_ids())
            assert {"Agent 1", "END"} <= node_ids, f"Canvas should hold Agent 1 and END, got {node_ids}"
            assert pp.get_edge_count() == 0, "END must NOT be connected before the node is configured"

        with allure.step("Step 8 — Agent 1 card summary reads 'Not configured'"):
            expect(pp.node_summary("Agent 1")).to_contain_text("Not configured", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 9 — Test Pipeline disabled; tooltip asks to select an agent"):
            expect(pp.test_pipeline_button).to_be_disabled()
            _soft_tooltip(pp, 'Configure node "Agent 1": Select an agent', "Step 9", soft_failures)

        with allure.step("Step 10 — Pick the agent in the node panel"):
            pp.open_agent_node_picker(timeout=UI_ELEMENT_TIMEOUT)
            pp.pick_agent_node_application(agent_name, timeout=UI_ELEMENT_TIMEOUT)
            pp.wait_for_agent_node_agent_value(agent_name, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 11 — Test Pipeline still disabled; tooltip asks for the task input"):
            expect(pp.test_pipeline_button).to_be_disabled()
            _soft_tooltip(pp, 'Configure node "Agent 1": Fill in the required input: task', "Step 11", soft_failures)

        with allure.step("Step 12 — Set Task and Save: Agent 1 gets connected to END"):
            pp.fill_agent_node_input_mapping_value(TASK_TEXT, timeout=UI_ELEMENT_TIMEOUT)
            pp.save_and_wait_for_saved(timeout=POST_SAVE_TIMEOUT)
            expect(pp.node_summary_primary("Agent 1")).to_have_text(agent_name, timeout=UI_ELEMENT_TIMEOUT)
            expect(pp.node_summary_secondary("Agent 1")).to_have_text(TASK_TEXT, timeout=UI_ELEMENT_TIMEOUT)
            expect(pp.node_entrypoint_badge("Agent 1")).to_have_count(1)
            pp.wait_for_edge("Agent 1", "EliteAPipelineEnd", timeout=POST_SAVE_TIMEOUT)  # END node's internal edge id
            pp.expect_edge_count(1)  # Agent 1 is connected to END after the configured save

        with allure.step("Step 13 — Test Pipeline is ENABLED"):
            expect(pp.test_pipeline_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 14 — Drag from Agent 1's Output handle onto empty canvas: connection dropdown"):
            pp.drag_output_handle_to_empty_canvas("Agent 1")
            expect(pp.connection_dropdown_menu).to_be_visible()
            expect(pp.connection_dropdown_create).to_be_visible()

        with allure.step("Step 15 — '+ Create new node' -> Printer: Printer 1 connected from Agent 1"):
            pp.connection_dropdown_create.click()
            expect(pp.node_type_menu_items().first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            pp.select_add_node_menu_item("printer")
            pp.wait_for_edge_present("Agent 1", "Printer 1", timeout=UI_ELEMENT_TIMEOUT)
            assert "Printer 1" in pp.get_node_ids(), "Printer 1 should be on the canvas"

        with allure.step("Step 16 — Delete Agent 1: removed; Test Pipeline disabled, entry-point tooltip"):
            pp.delete_node("Agent 1", timeout=UI_ELEMENT_TIMEOUT)
            expect(pp.node_summary("Agent 1")).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
            assert "Agent 1" not in pp.get_node_ids(), "Agent 1 should be gone from the canvas"
            expect(pp.test_pipeline_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)
            _soft_tooltip(pp, "Set an entry point to test the pipeline.", "Step 16", soft_failures)

        with allure.step("Step 17 — Delete Printer 1: the empty-state card returns"):
            pp.delete_node("Printer 1", timeout=UI_ELEMENT_TIMEOUT)
            expect(pp.empty_state).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(pp.empty_state).to_contain_text(EMPTY_STATE_TEXT)
            expect(pp.empty_state_add_node_button).to_be_visible()

        if soft_failures:
            # Tooltip wording is SOFT per the case/AFS: record it, never fail the test on it.
            report = "Soft tooltip checks differ from case wording:\n" + "\n".join(soft_failures)
            allure.attach(report, name="soft tooltip mismatches", attachment_type=allure.attachment_type.TEXT)
            warnings.warn(report, stacklevel=1)
    finally:
        if created_id is not None:
            try:
                pipeline_api.delete_pipeline(created_id)
            except Exception as exc:  # cleanup must not mask the test verdict
                allure.attach(str(exc), name="pipeline cleanup failed")
