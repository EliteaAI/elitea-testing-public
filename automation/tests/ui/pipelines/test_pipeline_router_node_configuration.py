"""UI test — Pipeline Router Node: Configuration, persistence and edge wiring.

TMS: ELITEA-2033
(test-specs/pipelines/l2_pipeline-router-node-configuration_ELITEA-2033.md)

Adds two Printer nodes renamed ``approve`` / ``reject`` (Routes is a picklist of
existing node ids, not a freeform field), adds a Router node, configures its
Condition / Routes / Input (under Advanced) / Default output, saves, reloads and
verifies every field plus the canvas edges persist.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_CONDITION = "{% if 'yes' in input %}approve{% else %}reject{% endif %}"
_TARGETS = ["approve", "reject"]
_ROUTER_ID = "Router 1"
_DEFAULT_OUTPUT_SOURCE = f"{_ROUTER_ID}default_output"  # source handle id in the edge testid


@pytest.mark.tms("ELITEA-2033")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2033_pipeline-router-node-configuration.md",
    "onetest-ai Test Case link",
)
def test_router_node_configuration_and_persistence(page, pipeline_id):
    """Configure a Router node; verify fields and edges persist through Save + reload."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 0 (setup) — add two Printer nodes and rename them 'approve' and 'reject'"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        canonical_url = page.url
        for target_name in _TARGETS:
            node_ids_before = set(pipeline_page.get_node_ids())
            pipeline_page.add_node("Printer")
            pipeline_page.wait_for_node_type_count("printer", 1, timeout=UI_ELEMENT_TIMEOUT)
            new_id = (set(pipeline_page.get_node_ids()) - node_ids_before - {"END"}).pop()
            renamed = pipeline_page.edit_node_name(new_id, target_name)
            assert renamed == target_name, f"Rename should yield {target_name!r}, got {renamed!r}"
        assert set(_TARGETS).issubset(set(pipeline_page.get_node_ids())), (
            f"Target nodes {_TARGETS!r} should exist on canvas, got {pipeline_page.get_node_ids()!r}"
        )

    with allure.step("Step 1 — Add a Router node via '+ Node'; card 'Router 1' appears"):
        pipeline_page.add_node("Router")
        router_id = pipeline_page.wait_for_node_on_canvas("router", timeout=UI_ELEMENT_TIMEOUT)
        assert router_id == _ROUTER_ID, f"Router node should be named {_ROUTER_ID!r}, got {router_id!r}"
        assert pipeline_page.node_card(_ROUTER_ID).is_visible(), "Router 1 card should be visible on canvas"

    with allure.step("Step 2 — Open the Router 1 panel; Condition, Routes, Default output, Input are shown"):
        pipeline_page.open_node_panel_by_card(_ROUTER_ID, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.router_node_condition_input.is_visible(), "Condition should be visible"
        assert pipeline_page.router_node_routes_select.is_visible(), "Routes should be visible"
        assert pipeline_page.router_node_default_output_select.is_visible(), "Default output should be visible"
        # Input lives in the collapsed-by-default Advanced section (case-text drift, not a defect).
        pipeline_page.expand_router_node_advanced_section(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.router_node_input_select.is_visible(), "Input should be visible under Advanced"

    with allure.step("Step 3 — Enter the Jinja condition"):
        pipeline_page.fill_router_node_condition(_CONDITION, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_router_node_condition() == _CONDITION, "Condition should accept the Jinja template"

    with allure.step("Step 4 — Add routes 'approve' and 'reject'; edges render immediately"):
        pipeline_page.select_router_node_routes(_TARGETS, timeout=UI_ELEMENT_TIMEOUT)
        routes_text = pipeline_page.get_router_node_routes_value()
        assert routes_text == "approvereject", f"Routes should show both values, got {routes_text!r}"
        for target_name in _TARGETS:
            pipeline_page.wait_for_edge_present(_ROUTER_ID, target_name, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.edge_exists(_ROUTER_ID, target_name), (
                f"{_ROUTER_ID} -> {target_name} edge should render before Save"
            )

    with allure.step("Step 5 — Set Input to 'input'"):
        pipeline_page.select_router_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_router_node_input_value() == "input", "Input should be 'input'"

    with allure.step("Step 6 — Set Default output to END"):
        pipeline_page.select_router_node_default_output("END", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_router_node_default_output_value() == "END", "Default output should read END"

    with allure.step("Step 7 — Save the pipeline without errors"):
        pipeline_page.close_node_panel(timeout=UI_ELEMENT_TIMEOUT)
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"
        # The Default output -> END edge appears on Save, without a reload.
        pipeline_page.wait_for_edge_present(_DEFAULT_OUTPUT_SOURCE, "END", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.edge_exists(_DEFAULT_OUTPUT_SOURCE, "END"), (
            f"{_ROUTER_ID} default output -> END edge should appear after Save (before reload)"
        )

    with allure.step("Step 8 — Reload; reopen Router 1; all four fields are restored"):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("router", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.open_node_panel_by_card(_ROUTER_ID, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_router_node_condition() == _CONDITION, "Condition should persist"
        assert pipeline_page.get_router_node_routes_value() == "approvereject", "Routes should persist"
        assert pipeline_page.get_router_node_default_output_value() == "END", "Default output should persist"
        pipeline_page.expand_router_node_advanced_section(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_router_node_input_value() == "input", "Input should persist"

    with allure.step("Step 9 — Canvas edges Router 1 -> approve / reject / END exist after reload"):
        for target_name in _TARGETS:
            pipeline_page.wait_for_edge_present(_ROUTER_ID, target_name, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.edge_exists(_ROUTER_ID, target_name), (
                f"{_ROUTER_ID} -> {target_name} edge should persist after reload"
            )
        pipeline_page.wait_for_edge_present(_DEFAULT_OUTPUT_SOURCE, "END", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.edge_exists(_DEFAULT_OUTPUT_SOURCE, "END"), (
            f"{_ROUTER_ID} default output -> END edge should persist after reload"
        )
        assert not console_errors, f"Flow should not produce console errors: {console_errors}"
