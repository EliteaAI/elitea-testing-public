"""UI test — Pipeline with Toolkit Node: configuration and persistence.

TMS: ELITEA-2010
(test-specs/pipelines/l2_pipeline-toolkit-node-configuration-persistence_ELITEA-2010.md)

Attaches a toolkit to a bare pipeline via the Tools section, adds a Toolkit
node to the canvas, configures it with the attached toolkit + one of its
tools, sets the resulting Input-mapping (F-String value with a state-variable
placeholder), configures the tool-agnostic Input/Output selects, saves, and
confirms every field survives a full page reload — verified via both the
Flow-view canvas and the YAML tab.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000
ATTACH_RESPONSE_TIMEOUT = 15_000

# search_index's one required Input-mapping parameter (raw schema key, lowercase
# — matches the dynamic testid suffix, not the capitalized display label "Query").
_QUERY_PARAM = "query"
_QUERY_FSTRING_VALUE = "{input} error"

# AFS Test Step 2 — the exact toast text confirmed live during analysis.
_TOOLKIT_ATTACH_TOAST_TEXT = "The toolkit has been successfully added to the pipeline."


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2010_pipeline-with-toolkit-node.md",
    "onetest-ai Test Case link",
)
@allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1025", "Known defect #1025")
def test_pipeline_toolkit_node_configuration_persistence(page, pipeline_id, artifact_toolkit):
    """Configure a Toolkit node end-to-end; verify persistence through save + reload.

    Known defect #1025 (isolated, non-blocking): the YAML tab's CodeMirror
    editor silently truncates long node YAML — its own scroll container
    reports zero overflow (``scrollHeight == clientHeight``) yet stops
    rendering partway through this case's Toolkit node (confirmed via a
    direct API fetch that the real persisted YAML is complete and correct;
    this is a display-only bug in the YAML tab, not a persistence bug). The
    fields the truncation hits (``tool``/``toolkit_name``/``output``) are
    checked last, in their own deferred step, so the flow-view persistence
    proof (steps 1-11's canvas assertions) and the YAML fields that DO
    render (``type``/``fstring``/the literal Query value) still run and pass
    regardless — same deferred-known-defect scoping precedent as
    ``test_agent_management.test_edit_agent_instructions`` (#538).
    """
    toolkit_name = artifact_toolkit["name"]
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step are
    # captured — AFS Expected Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to the bare pipeline; verify configuration panel loads"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        canonical_url = page.url  # captured for the reload step (bare /pipelines/all/{id}
        # with no query params 404s — same known-defect note as ELITEA-1954's test)
        assert pipeline_page.configuration_tab.is_visible(), (
            "Configuration panel (General section) should be visible after navigating"
        )

    with allure.step(
        "Step 2 — Attach the toolkit via '+ Toolkit'; verify 201 + toast + toolkit card"
    ):
        popper = pipeline_page.open_toolkit_popper(timeout=UI_ELEMENT_TIMEOUT)
        attach_response = pipeline_page.select_toolkit_in_popper(
            popper, toolkit_name, project_id, timeout=ATTACH_RESPONSE_TIMEOUT
        )
        assert attach_response is not None, "Toolkit attach should return the persisted response"
        expect(pipeline_page.toolkit_attach_toast_message).to_have_text(
            _TOOLKIT_ATTACH_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT
        )
        assert pipeline_page.is_toolkit_attached(toolkit_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"Toolkit {toolkit_name!r} should appear as a card in the Tools section"
        )

    with allure.step("Step 3 — Add a Toolkit node via 'Add node' -> 'Toolkit'"):
        pipeline_page.wait_for_canvas()
        pipeline_page.add_node("Toolkit")
        node_id = pipeline_page.wait_for_node_on_canvas("toolkit", timeout=UI_ELEMENT_TIMEOUT)
        assert node_id, "Toolkit node should be present on the canvas with a non-empty data-id"
        # Canvas is heavily zoomed-out by default (test-specs/pipelines/_surface.md
        # "Canvas is heavily zoomed-out by default"): at the default zoom level the
        # node's lower fields render close enough to the ReactFlow Controls panel's
        # fixed bottom-left position that clicks there resolve against the
        # panel's own Fit-View button instead of the node's own fields (confirmed
        # live). Zoom in first, per that digest's guidance.
        pipeline_page.zoom_in_up_to(10)
        pipeline_page.fit_view()

    with allure.step(
        "Step 4 — Inspect the fresh node's panel: Toolkit/Input/Output/Interrupt/"
        "Structured-output visible; Tool and Input-mapping not yet rendered"
    ):
        assert pipeline_page.toolkit_node_toolkit_select.is_visible(), (
            "Toolkit node's Toolkit select should be visible inline on the canvas card"
        )
        assert pipeline_page.get_toolkit_node_toolkit_value(timeout=UI_ELEMENT_TIMEOUT) == "", (
            "Toolkit select should be empty on a freshly-added node"
        )
        assert pipeline_page.toolkit_node_input_select.is_visible(), (
            "Toolkit node's tool-agnostic Input select should be visible"
        )
        assert pipeline_page.toolkit_node_output_select.is_visible(), (
            "Toolkit node's tool-agnostic Output select should be visible"
        )
        assert pipeline_page.interrupt_before_switch.is_visible(), (
            "Interrupt before switch should be visible"
        )
        assert pipeline_page.interrupt_after_switch.is_visible(), (
            "Interrupt after switch should be visible"
        )
        assert pipeline_page.structured_output_switch.is_visible(), (
            "Structured output switch should be visible"
        )
        # Tool select and both Input-mapping sections are gated on a Toolkit
        # (then Tool) being selected first — not merely empty, not rendered
        # at all yet (AFS Coverage Map row 3 pre/post split).
        assert pipeline_page.toolkit_node_tool_select.count() == 0, (
            "Tool select should not render before a Toolkit is selected"
        )
        assert pipeline_page.toolkit_node_input_mapping_required_heading.count() == 0, (
            "Input mapping (required) heading should not render before a Tool is selected"
        )
        assert pipeline_page.toolkit_node_input_mapping_optional_heading.count() == 0, (
            "Input mapping (optional) heading should not render before a Tool is selected"
        )
        # AFS step 4: "Interrupt before / after switches (disabled — entry-point
        # nodes can't have Interrupt before)" — this pipeline's sole real node
        # auto-became the entry point, so the switch is disabled. Confirmed live
        # that Playwright's is_disabled() correctly reflects the underlying
        # <input disabled> despite the testid sitting on the wrapping
        # MuiButtonBase-root span, not the <input> itself.
        assert pipeline_page.interrupt_before_switch.is_disabled(), (
            "Interrupt before switch should be disabled for an entry-point node"
        )

    with allure.step("Step 5 — Select the attached toolkit; Toolkit combobox shows its name"):
        pipeline_page.select_toolkit_node_toolkit(toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_toolkit_node_toolkit_value(timeout=UI_ELEMENT_TIMEOUT) == toolkit_name, (
            f"Toolkit select should show {toolkit_name!r} after selection"
        )
        assert pipeline_page.toolkit_node_tool_select.is_visible(), (
            "Tool select should appear once a Toolkit is selected"
        )
        assert pipeline_page.get_toolkit_node_tool_value(timeout=UI_ELEMENT_TIMEOUT) == "", (
            "Tool select should still be empty right after the Toolkit is selected"
        )

    with allure.step(
        "Step 6 — Select 'search_index'; Input-mapping (required 1) + (optional 9) appear"
    ):
        pipeline_page.select_toolkit_node_tool("search_index", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_toolkit_node_tool_value(timeout=UI_ELEMENT_TIMEOUT) == "search_index", (
            "Tool select should show 'search_index' after selection"
        )
        assert pipeline_page.is_toolkit_node_input_mapping_section_visible(1, timeout=UI_ELEMENT_TIMEOUT), (
            "'Input mapping (required 1)' section should appear for search_index's 1 required param"
        )
        assert pipeline_page.is_toolkit_node_input_mapping_optional_section_visible(
            9, timeout=UI_ELEMENT_TIMEOUT
        ), "'Input mapping (optional 9)' section should appear for search_index's 9 optional params"
        assert pipeline_page.is_toolkit_node_input_mapping_value_visible(
            _QUERY_PARAM, timeout=UI_ELEMENT_TIMEOUT
        ), "Query Value field should be visible"

    with allure.step("Step 7 — Set the Query mapping's Type to F-String"):
        pipeline_page.select_toolkit_node_input_mapping_type(
            _QUERY_PARAM, "fstring", timeout=UI_ELEMENT_TIMEOUT
        )
        assert (
            pipeline_page.get_toolkit_node_input_mapping_type_value(_QUERY_PARAM, timeout=UI_ELEMENT_TIMEOUT)
            == "F-String"
        ), "Query mapping's Type combobox should show 'F-String'"

    with allure.step(
        "Step 8 — Type the Query mapping's Value ('{input} error'); no new console errors"
    ):
        pipeline_page.fill_toolkit_node_input_mapping_value(
            _QUERY_PARAM, _QUERY_FSTRING_VALUE, timeout=UI_ELEMENT_TIMEOUT
        )
        assert (
            pipeline_page.get_toolkit_node_input_mapping_value(_QUERY_PARAM) == _QUERY_FSTRING_VALUE
        ), f"Query Value field should read exactly {_QUERY_FSTRING_VALUE!r}"
        assert not console_errors, f"Typing the F-string value should not introduce console errors: {console_errors}"

    with allure.step("Step 9 — Set the tool-agnostic Input and Output selects"):
        pipeline_page.select_toolkit_node_input("input", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_toolkit_node_input_value(timeout=UI_ELEMENT_TIMEOUT) == "input", (
            "Input select should show exactly 'input'"
        )
        pipeline_page.select_toolkit_node_output("messages", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_toolkit_node_output_value(timeout=UI_ELEMENT_TIMEOUT) == "messages", (
            "Output select should show exactly 'messages'"
        )

    with allure.step("Step 10 — Save; verify 201 + no console errors"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 11 — Reload via the canonical URL; every field persists "
        "(Flow-view canvas AND YAML tab both confirm it)"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("toolkit", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_toolkit_node_toolkit_value(timeout=UI_ELEMENT_TIMEOUT) == toolkit_name, (
            f"Toolkit should persist as {toolkit_name!r} after reload"
        )
        assert pipeline_page.get_toolkit_node_tool_value(timeout=UI_ELEMENT_TIMEOUT) == "search_index", (
            "Tool should persist as 'search_index' after reload"
        )
        assert pipeline_page.is_toolkit_node_input_mapping_section_visible(1, timeout=UI_ELEMENT_TIMEOUT), (
            "Input mapping (required 1) section should still be present after reload"
        )
        assert (
            pipeline_page.get_toolkit_node_input_mapping_type_value(_QUERY_PARAM, timeout=UI_ELEMENT_TIMEOUT)
            == "F-String"
        ), "Query mapping's Type should persist as 'F-String' after reload"
        assert (
            pipeline_page.get_toolkit_node_input_mapping_value(_QUERY_PARAM) == _QUERY_FSTRING_VALUE
        ), "Query mapping's Value should persist after reload"
        assert pipeline_page.get_toolkit_node_input_value(timeout=UI_ELEMENT_TIMEOUT) == "input", (
            "Input select should persist as 'input' after reload"
        )
        assert pipeline_page.get_toolkit_node_output_value(timeout=UI_ELEMENT_TIMEOUT) == "messages", (
            "Output select should persist as 'messages' after reload"
        )

        # Second, independent verification source — the YAML tab — per this
        # project's existing "Save/reload persistence" pattern
        # (test_yaml_content_reflects_pipeline) and this case's own AFS.
        pipeline_page.switch_to_yaml_view()
        yaml_content = pipeline_page.get_yaml_content()
        yaml_lower = yaml_content.lower()
        assert "type: toolkit" in yaml_lower, f"YAML should show 'type: toolkit', got: {yaml_content}"
        assert "input:" in yaml_lower and "- input" in yaml_lower, (
            f"YAML should show the tool-agnostic 'input:' state var as '- input', got: {yaml_content}"
        )
        assert "fstring" in yaml_lower, f"YAML should show the fstring mapping type, got: {yaml_content}"
        assert _QUERY_FSTRING_VALUE in yaml_content, (
            f"YAML should show the literal Query value {_QUERY_FSTRING_VALUE!r}, got: {yaml_content}"
        )
        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"

    with allure.step(
        "Side-channel check — YAML tab shows the Toolkit node's tool/toolkit_name/"
        "output keys (Known defect #1025, deferred: the YAML tab's CodeMirror "
        "editor silently truncates long node YAML before reaching these keys — "
        "confirmed via a direct API fetch that the real persisted YAML is "
        "complete and correct, so this is a display-only bug, not a persistence "
        "regression. Checked last so the flow-view + partial-YAML persistence "
        "proof above runs and passes regardless.)"
    ):
        assert "tool: search_index" in yaml_lower, (
            f"YAML should show 'tool: search_index' — see #1025, got: {yaml_content}"
        )
        assert f"toolkit_name: {toolkit_name}" in yaml_content, (
            f"YAML should show toolkit_name: {toolkit_name} — see #1025, got: {yaml_content}"
        )
        assert "output:" in yaml_lower and "- messages" in yaml_lower, (
            f"YAML should show the tool-agnostic 'output:' state var as "
            f"'- messages' — see #1025, got: {yaml_content}"
        )
        # AFS Expected Results: "No console errors at any step" — this is the
        # final step of the test, so this closes out the global check for the
        # side-channel step itself (the #1025 YAML-truncation defect is a
        # display-only rendering bug, unrelated to console errors, and does not
        # exempt this step from the same no-console-errors expectation).
        assert not console_errors, f"Side-channel check should not introduce console errors: {console_errors}"
