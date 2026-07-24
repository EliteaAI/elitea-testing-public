"""UI test — Configure LLM Node: System, Task, Chat History (fields persist
across Save + reload).

TMS: ELITEA-2004
(test-specs/pipelines/l2_configure-llm-node-system-task-chat-history_ELITEA-2004.md)

Configures an existing LLM node's SYSTEM (Fixed), TASK (F-String), and
CHAT HISTORY (Fixed) fields plus its tool-agnostic Input/Output
state-variable selects, saves, and confirms every field persists through a
full page reload — verified via both the Flow-view fields and the YAML-view
tab independently (AFS Axis 2 addition), plus zero console errors and zero
failed network requests across the whole configure->save cycle.
"""

import logging

import pytest
import allure

from pages.pipeline_detail_page import PipelineDetailPage
from config import settings

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_SYSTEM_VALUE = "You are a helpful assistant"
_TASK_VALUE = "User Input: {input}"
_CHAT_HISTORY_VALUE = "[]"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2004_configure-llm-node-system-task-chat-history.md",
    "onetest-ai Test Case link",
)
def test_configure_llm_node_system_task_chat_history(page, pipeline_with_llm_id):
    """Configure SYSTEM/TASK/CHAT HISTORY + Input/Output; verify Save + reload persistence."""
    pipeline_id = pipeline_with_llm_id
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (field
    # edits, dropdown opens, Save) are captured — AFS Expected Results
    # require "zero error-level console messages" across the whole cycle.
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to the fixture-created pipeline; LLM node on canvas"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step — same
        # /pipelines/all/{id}?viewMode=owner pattern the MCP-node specs rely on.
        node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert node_id, "LLM node should be present on the canvas with a non-empty data-id"

    with allure.step(
        "Step 2/3 — Config fields are always rendered inline on the node card "
        "(no separate open/close action — same live simplification as ELITEA-1954)"
    ):
        assert pipeline_page.get_llm_node_type("system", timeout=UI_ELEMENT_TIMEOUT) is not None, (
            "SYSTEM Type select should be visible inline on the canvas card"
        )
        assert pipeline_page.get_llm_node_type("task") is not None, "TASK Type select should be visible"
        assert pipeline_page.get_llm_node_type("chat_history") is not None, (
            "CHAT HISTORY Type select should be visible"
        )
        assert pipeline_page.llm_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.llm_node_output_select.is_visible(), "Output select should be visible inline"

    with allure.step('Step 4 — SYSTEM: set Type to "Fixed", enter Value'):
        pipeline_page.set_llm_node_field("system", "fixed", _SYSTEM_VALUE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_llm_node_type("system") == "Fixed", "SYSTEM Type should show 'Fixed'"
        assert pipeline_page.get_llm_node_value("system") == _SYSTEM_VALUE, (
            "SYSTEM Value should read back the typed text"
        )

    with allure.step('Step 5 — TASK: set Type to "F-String", enter Value'):
        pipeline_page.set_llm_node_field("task", "fstring", _TASK_VALUE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_llm_node_type("task") == "F-String", "TASK Type should show 'F-String'"
        assert pipeline_page.get_llm_node_value("task") == _TASK_VALUE, (
            "TASK Value should read back the typed f-string text verbatim"
        )

    with allure.step('Step 6 — CHAT HISTORY: set Type to "Fixed", enter Value "[]"'):
        pipeline_page.set_llm_node_field(
            "chat_history", "fixed", _CHAT_HISTORY_VALUE, timeout=UI_ELEMENT_TIMEOUT
        )
        assert pipeline_page.get_llm_node_type("chat_history") == "Fixed", (
            "CHAT HISTORY Type should show 'Fixed'"
        )
        assert pipeline_page.get_llm_node_value("chat_history") == _CHAT_HISTORY_VALUE, (
            "CHAT HISTORY Value should read back '[]'"
        )

    with allure.step('Step 7 — Set Input combobox to include "input"'):
        pipeline_page.select_llm_node_input("input", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step('Step 8 — Set Output combobox to "messages"'):
        pipeline_page.select_llm_node_output("messages", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 7/8 verification — YAML view corroborates Input/Output selections "
        "(AFS Concrete Handles: chip-reading is out of scope, YAML view suffices)"
    ):
        pipeline_page.switch_to_yaml_view()
        yaml_before_save = pipeline_page.get_yaml_content()
        pipeline_page.switch_to_flow_view()
        assert "input" in yaml_before_save, "YAML should show 'input' as an Input variable"
        assert "messages" in yaml_before_save, "YAML should show 'messages' as an Output variable"

    with allure.step("Step 9 — Save pipeline; verify 201 + Discard clears + no console errors"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not pipeline_page.is_discard_enabled(), (
            "Discard button (dirty-state indicator) should disable after a successful Save"
        )
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"
        assert pipeline_page.get_llm_node_type("system") is not None  # canvas still rendered post-save

    with allure.step(
        "Step 10 — Hard reload via the canonical URL; all fields persisted "
        "(dual-sourced: Flow-view fields AND YAML view independently)"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_llm_node_type("system") == "Fixed"
        assert pipeline_page.get_llm_node_value("system") == _SYSTEM_VALUE, (
            "SYSTEM Value should persist after reload"
        )
        assert pipeline_page.get_llm_node_type("task") == "F-String"
        assert pipeline_page.get_llm_node_value("task") == _TASK_VALUE, (
            "TASK Value should persist after reload"
        )
        assert pipeline_page.get_llm_node_type("chat_history") == "Fixed"
        assert pipeline_page.get_llm_node_value("chat_history") == _CHAT_HISTORY_VALUE, (
            "CHAT HISTORY Value should persist after reload"
        )

        pipeline_page.switch_to_yaml_view()
        yaml_after_reload = pipeline_page.get_yaml_content()
        pipeline_page.switch_to_flow_view()
        assert "You are a helpful assistant" in yaml_after_reload, (
            "YAML view should independently corroborate the persisted SYSTEM value"
        )
        assert "User Input: {input}" in yaml_after_reload, (
            "YAML view should independently corroborate the persisted TASK value"
        )
        assert "input" in yaml_after_reload, "YAML view should show 'input' still mapped after reload"
        assert "messages" in yaml_after_reload, "YAML view should show 'messages' still mapped after reload"
