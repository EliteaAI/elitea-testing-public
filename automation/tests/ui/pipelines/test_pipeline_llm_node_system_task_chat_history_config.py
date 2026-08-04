"""UI test — Configure LLM Node: System, Task, Chat History.

TMS: ELITEA-2004
(test-specs/pipelines/l2_llm-node-system-task-chat-history-config_ELITEA-2004.md)

Adds an LLM node to a fresh empty pipeline, configures SYSTEM/TASK/CHAT
HISTORY (Type + Value) and the tool-agnostic Input/Output state-variable
selects entirely through the always-inline node config (no click-to-open
action — see AFS Coverage Map row 2), saves, and confirms every value
persists through a full page reload.
"""

import logging

import pytest
import allure

from pages.pipeline_detail_page import PipelineDetailPage
from config import settings

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_SYSTEM_VALUE = "You are a helpful assistant"
_TASK_VALUE = "User Input: {input}"
_CHAT_HISTORY_VALUE = "[]"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2004_llm-node-system-task-chat-history-config.md",
    "onetest-ai Test Case link",
)
def test_llm_node_system_task_chat_history_config(page, pipeline_id):
    """Configure an LLM node's SYSTEM/TASK/CHAT HISTORY + Input/Output; verify persistence."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (node add,
    # field fills, dropdown opens, save, reload) are captured — AFS Expected
    # Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to the pipeline; verify configuration panel + canvas load"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step — a bare
        # /pipelines/all/{id} URL (no query params) 404s (ELITEA-1954 AFS
        # Known Defects); reloading THIS captured URL avoids that.
        assert pipeline_page.configuration_tab.is_visible(), (
            "Configuration panel (General section) should be visible after navigating"
        )

    with allure.step('Step 2 — Add an LLM node via the canvas "+" menu; verify it appears'):
        pipeline_page.add_node("LLM")
        node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert node_id, "LLM node should be present on the canvas with a non-empty data-id"

    with allure.step(
        "Step 3 — Config fields render inline on the node — no click-to-open action needed"
    ):
        assert pipeline_page.llm_node_system_value.is_visible(), (
            "SYSTEM Value field should be visible inline on the canvas card — "
            "no separate click-to-open action needed (live product simplification, "
            "see AFS Coverage Map row 2)"
        )
        assert pipeline_page.llm_node_task_value.is_visible(), "TASK Value field should be visible inline"
        assert pipeline_page.llm_node_chat_history_value.is_visible(), (
            "CHAT HISTORY Value field should be visible inline"
        )
        assert pipeline_page.llm_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.llm_node_output_select.is_visible(), "Output select should be visible inline"
        # The remaining 4 of the case's 9 named sections (Trigger, Toolkits,
        # Interrupt before/after, Structured output) — added to close a gap
        # the first implementation left unasserted despite the AFS Coverage
        # Map claiming full coverage (fix-round finding). All 4 genuinely
        # render for this scenario: the fresh pipeline's first (and only)
        # node auto-becomes the entry point, so Trigger renders
        # (FlowEditor.jsx); Toolkits/Interrupt before/Interrupt after/
        # Structured output are unconditional on the LLM node
        # (LLMNode.jsx / CommonInterruptSettings.jsx).
        assert pipeline_page.entry_point_trigger_select.is_visible(), (
            "Trigger select should be visible — this pipeline's first node "
            "auto-becomes the entry point"
        )
        assert pipeline_page.llm_node_toolkits_select.is_visible(), "Toolkits select should be visible inline"
        assert pipeline_page.is_node_interrupt_before_toggle_visible(node_id), (
            "Interrupt before toggle should be visible inline"
        )
        assert pipeline_page.llm_node_interrupt_after_toggle.is_visible(), (
            "Interrupt after toggle should be visible inline"
        )
        assert pipeline_page.llm_node_structured_output_toggle.is_visible(), (
            "Structured output toggle should be visible inline"
        )

    with allure.step("Step 4 — SYSTEM: Type already 'Fixed' by default; fill Value"):
        default_system_type = pipeline_page.get_llm_node_section_type("system", timeout=UI_ELEMENT_TIMEOUT)
        assert default_system_type == "Fixed", (
            f"SYSTEM Type should default to 'Fixed' with no action needed, got {default_system_type!r}"
        )
        pipeline_page.fill_llm_node_section_value("system", _SYSTEM_VALUE)
        assert pipeline_page.get_llm_node_section_value("system") == _SYSTEM_VALUE, (
            "SYSTEM Value field should reflect the typed text"
        )

    with allure.step("Step 5 — TASK: switch Type to F-String; fill Value"):
        pipeline_page.select_llm_node_section_type("task", "F-String", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_llm_node_section_type("task") == "F-String", (
            "TASK Type select should show 'F-String' after selection"
        )
        pipeline_page.fill_llm_node_section_value("task", _TASK_VALUE)
        assert pipeline_page.get_llm_node_section_value("task") == _TASK_VALUE, (
            "TASK Value field should reflect the typed f-string text"
        )

    with allure.step("Step 6 — CHAT HISTORY: Type already 'Fixed' by default; fill Value"):
        default_chat_history_type = pipeline_page.get_llm_node_section_type(
            "chat_history", timeout=UI_ELEMENT_TIMEOUT
        )
        assert default_chat_history_type == "Fixed", (
            f"CHAT HISTORY Type should default to 'Fixed' with no action needed, "
            f"got {default_chat_history_type!r}"
        )
        pipeline_page.fill_llm_node_section_value("chat_history", _CHAT_HISTORY_VALUE)
        assert pipeline_page.get_llm_node_section_value("chat_history") == _CHAT_HISTORY_VALUE, (
            "CHAT HISTORY Value field should reflect the typed text"
        )

    with allure.step("Step 7 — Set Input combobox to 'input'"):
        pipeline_page.select_llm_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_llm_node_input_value() == "input", (
            "Input select should show 'input' after selection"
        )

    with allure.step("Step 8 — Set Output combobox to 'messages'"):
        pipeline_page.select_llm_node_output_variable("messages", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_llm_node_output_value() == "messages", (
            "Output select should show 'messages' after selection"
        )

    with allure.step("Step 9 — Save; verify 201 + no console errors"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 10 — Reload via the canonical URL; SYSTEM/TASK/CHAT HISTORY/Input/Output persisted"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_llm_node_section_type("system") == "Fixed", (
            "SYSTEM Type should persist as 'Fixed' after reload"
        )
        assert pipeline_page.get_llm_node_section_value("system") == _SYSTEM_VALUE, (
            "SYSTEM Value should persist after reload"
        )
        assert pipeline_page.get_llm_node_section_type("task") == "F-String", (
            "TASK Type should persist as 'F-String' after reload"
        )
        assert pipeline_page.get_llm_node_section_value("task") == _TASK_VALUE, (
            "TASK Value should persist after reload"
        )
        assert pipeline_page.get_llm_node_section_type("chat_history") == "Fixed", (
            "CHAT HISTORY Type should persist as 'Fixed' after reload"
        )
        assert pipeline_page.get_llm_node_section_value("chat_history") == _CHAT_HISTORY_VALUE, (
            "CHAT HISTORY Value should persist after reload"
        )
        # Axis 2 addition (AFS): the case only names SYSTEM/TASK/CHAT HISTORY
        # in its Expected Final State — also assert Input/Output survive,
        # since a regression where they silently reset to empty on reload
        # while the three text sections persisted correctly would otherwise
        # go undetected (same class of gap flagged for the MCP node's
        # Input-mapping values in the ELITEA-1954 AFS).
        assert pipeline_page.get_llm_node_input_value() == "input", (
            "Input should persist as 'input' after reload"
        )
        assert pipeline_page.get_llm_node_output_value() == "messages", (
            "Output should persist as 'messages' after reload"
        )


_WALK_FIXED_VALUE = "Extract these four values from the given input"
_WALK_FSTRING_VALUE = "input: {input}"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2040_pipeline-input-mapping-types-fixed-fstring-variable.md",
    "onetest-ai Test Case link",
)
def test_llm_node_system_type_walks_fixed_fstring_variable(page, pipeline_id):
    """Walk the LLM node's SYSTEM Type through Fixed -> F-String -> Variable.

    TMS: ELITEA-2040 — extend-existing over this file's ELITEA-2004 test
    (test-specs/pipelines/
    lextend_pipeline-input-mapping-types-fixed-fstring-variable_ELITEA-2040.md).
    ELITEA-2004 never selects "Variable"; this test closes that gap: the
    Type select's full 3-option set, the Value field's DOM-widget swap
    (<textarea> -> MUI Select) on entering Variable mode, the Variable
    Value-select's option list (the pipeline's own state variables), and
    Type=Variable/Value=<state var> persistence through Save + reload. Does
    not modify ELITEA-2004's test above.
    """
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step are
    # captured — AFS Expected Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to the pipeline; verify configuration panel + canvas load"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # bare /pipelines/all/{id} 404s (ELITEA-1954
        # AFS Known Defects) — reload THIS captured URL for step 9.
        assert pipeline_page.configuration_tab.is_visible(), (
            "Configuration panel (General section) should be visible after navigating"
        )

    with allure.step('Step 2 — Add an LLM node via the canvas "+" menu; verify it appears'):
        pipeline_page.add_node("LLM")
        node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert node_id, "LLM node should be present on the canvas with a non-empty data-id"

    with allure.step(
        "Step 3 — Open SYSTEM's Type select; confirm exactly Fixed/F-String/Variable are offered"
    ):
        pipeline_page.open_llm_node_section_type_select("system", timeout=UI_ELEMENT_TIMEOUT)
        option_testids = pipeline_page.get_open_listbox_option_testids()
        # DOM order is F-String/Variable/Fixed (FlowEditorConstants.agentTaskTypeOptions,
        # flowEditor.constants.js) — corrected here from the AFS's originally
        # recorded Fixed/F-String/Variable order (implementer Phase-2 exploration;
        # AFS amended in this PR). Asserted as a set — the case's own wording
        # ("Type dropdown offers Fixed/F-String/Variable") is about the option
        # SET being complete, not a specific DOM order.
        assert set(option_testids) == {
            "select-option-fixed",
            "select-option-fstring",
            "select-option-variable",
        }, (
            f"SYSTEM Type select should offer exactly Fixed/F-String/Variable, got {option_testids!r}"
        )
        # Close the popover on the already-default "Fixed" option — a no-op
        # selection (step 4 asserts the default is still 'Fixed').
        pipeline_page.select_open_listbox_option("fixed", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 4 — SYSTEM: Type still 'Fixed' by default; Value field accepts plain text"):
        assert pipeline_page.get_llm_node_section_type("system", timeout=UI_ELEMENT_TIMEOUT) == "Fixed", (
            "SYSTEM Type should default to 'Fixed'"
        )
        pipeline_page.fill_llm_node_section_value("system", _WALK_FIXED_VALUE)
        assert pipeline_page.get_llm_node_section_value("system") == _WALK_FIXED_VALUE, (
            "SYSTEM Value field should accept plain text and reflect the typed value"
        )

    with allure.step("Step 5 — Switch SYSTEM's Type to F-String; Value field allows {variable} syntax"):
        pipeline_page.select_llm_node_section_type("system", "F-String", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_llm_node_section_type("system") == "F-String", (
            "SYSTEM Type select should show 'F-String' after selection"
        )
        pipeline_page.fill_llm_node_section_value("system", _WALK_FSTRING_VALUE)
        assert pipeline_page.get_llm_node_section_value("system") == _WALK_FSTRING_VALUE, (
            "SYSTEM Value field should accept f-string syntax and reflect the typed value"
        )

    with allure.step(
        "Step 6 — Switch SYSTEM's Type to Variable; Value field DOM swaps <textarea> -> MUI Select"
    ):
        before_shape = pipeline_page.get_llm_node_section_value_field_shape(
            "system", timeout=UI_ELEMENT_TIMEOUT
        )
        assert before_shape["tag_name"] == "TEXTAREA", (
            f"SYSTEM Value field should be a <textarea> in F-String mode, got {before_shape!r}"
        )
        pipeline_page.select_llm_node_section_type("system", "Variable", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_llm_node_section_type("system") == "Variable", (
            "SYSTEM Type select should show 'Variable' after selection"
        )
        after_shape = pipeline_page.get_llm_node_section_value_field_shape(
            "system", timeout=UI_ELEMENT_TIMEOUT
        )
        assert after_shape["tag_name"] != "TEXTAREA", (
            f"SYSTEM Value field's DOM element should no longer be the F-String <textarea>, "
            f"got {after_shape!r}"
        )
        combobox = pipeline_page.get_llm_node_section_value_combobox_locator("system")
        assert combobox.get_attribute("role", timeout=UI_ELEMENT_TIMEOUT) == "combobox", (
            "SYSTEM Value field should swap specifically to a MUI Select — its "
            "role='combobox' display element should now be present"
        )

    with allure.step(
        "Step 7 — Open the (now-Select) Value field; option list = pipeline state variables; select 'input'"
    ):
        pipeline_page.open_llm_node_section_variable_value_select("system", timeout=UI_ELEMENT_TIMEOUT)
        variable_option_testids = pipeline_page.get_open_listbox_option_testids()
        assert variable_option_testids == ["select-option-input", "select-option-messages"], (
            f"Variable-mode Value select should offer exactly the pipeline's state variables "
            f"(input, messages), got {variable_option_testids!r}"
        )
        pipeline_page.select_open_listbox_option("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_llm_node_section_variable_value("system") == "input", (
            "SYSTEM Value select should read 'input' after selection"
        )

    with allure.step("Step 8 — Save; verify 201 + no console errors"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step("Step 9 — Reload via the canonical URL; Type=Variable and Value=input persist"):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_llm_node_section_type("system") == "Variable", (
            "SYSTEM Type should persist as 'Variable' after reload"
        )
        assert pipeline_page.get_llm_node_section_variable_value("system") == "input", (
            "SYSTEM Value should persist as 'input' after reload"
        )
