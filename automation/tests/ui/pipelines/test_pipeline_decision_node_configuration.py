"""UI test — Pipeline Decision Node: Configuration and Edge Wiring.

TMS: ELITEA-2034
(test-specs/pipelines/l2_pipeline-decision-node-configuration_ELITEA-2034.md)

Adds a Decision node to a pipeline (alongside two custom state variables and
three Printer nodes, renamed to "bug_responder"/"feature_responder"/
"question_responder", that serve as the Decision's DECISION OUTPUTS targets),
configures Input, Description, and DECISION OUTPUTS (via drag-connect, NOT a
freeform chip field), saves, and confirms every field — plus all three canvas
edges and the two static Output/Default output handle labels — survives a
full page reload.

Step 0 is added ahead of the case's own step 1 (AFS Preconditions/step 0):
the case's precondition text implies state variables and target nodes
already exist, but live behavior requires explicit setup — custom state
variables are NOT built-in (unlike Router's `input`/`messages`) and the
DECISION OUTPUTS field is populated exclusively by dragging a canvas edge
from the node's `Output` handle to an EXISTING, correctly-named target node
(AFS Coverage Map clarification, filed as a case-text CLARIFICATION, not a
defect — the case's overall intent is fully achievable, the wording just
undersells the mechanism; same pattern as the Router AFS's Routes field,
ELITEA-2033).

State-variable existence is verified functionally in Step 3 (both custom
variables must appear as selectable Input options — `select-option-{value}`
testids) rather than by reading the STATE panel's own display-mode row text,
which carries no testid and isn't otherwise touched by this case (locator
policy: testid-only, scope limited to elements the test's code path
actually exercises).
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_DESCRIPTION_TEMPLATE = (
    "Classify this input into one category: - bug_responder: reports a defect "
    "- feature_responder: requests new functionality"
)
_OUTPUT_TARGETS = ["bug_responder", "feature_responder", "question_responder"]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2034_pipeline-decision-node-configuration.md",
    "onetest-ai Test Case link",
)
def test_decision_node_configuration_and_edge_wiring(page, pipeline_id):
    """Configure a Decision node's fields; verify they + their edges persist through Save + reload."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 0 so console errors from every step (state
    # setup, node add/rename, drag-connects, field entry, save, reload) are
    # captured — AFS Expected Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 0 (setup) — add + rename three Printer nodes so they can serve as the "
        "Decision node's DECISION OUTPUTS targets, then add two custom state "
        "variables via the STATE panel"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step (?viewMode=owner already included)

        # Printer nodes are added/renamed BEFORE opening the STATE panel: the
        # panel is a wide side drawer that overlaps the canvas and intercepts
        # the rename's dblclick on nodes that land underneath it (live-hit
        # this session — Playwright reported the STATE panel's own content
        # subtree "intercepts pointer events" on the double-click).
        node_ids_before_printers = set(pipeline_page.get_node_ids())
        target_node_ids = []
        for target_name in _OUTPUT_TARGETS:
            node_ids_before = set(pipeline_page.get_node_ids())
            pipeline_page.add_node("Printer")
            pipeline_page.wait_for_node_count(len(node_ids_before) + 1, timeout=UI_ELEMENT_TIMEOUT)
            new_printer_id = (set(pipeline_page.get_node_ids()) - node_ids_before).pop()
            renamed_id = pipeline_page.edit_node_name(new_printer_id, target_name)
            assert renamed_id == target_name, (
                f"edit_node_name should return the verbatim new name as the node's new "
                f"data-id (got {renamed_id!r} for target {target_name!r})"
            )
            target_node_ids.append(renamed_id)

        node_ids_after_setup = set(pipeline_page.get_node_ids())
        assert set(_OUTPUT_TARGETS).issubset(node_ids_after_setup), (
            f"Renamed target nodes should be on canvas as {_OUTPUT_TARGETS!r}, got {node_ids_after_setup!r}"
        )
        assert len(node_ids_after_setup) == len(node_ids_before_printers) + 3, (
            "Exactly 3 Printer nodes should have been added during setup"
        )

        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.add_state_variable("normalized_issue", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.add_state_variable("metadata_json", timeout=UI_ELEMENT_TIMEOUT)
        # Close the drawer — it overlaps the canvas and would intercept the
        # Decision node's own inline field clicks in later steps (live-hit
        # this session: Playwright reported the STATE panel's content
        # subtree "intercepts pointer events" on the Input select's click).
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 1 — Add a Decision node via canvas '+' button"):
        node_count_before_decision = pipeline_page.get_node_count()
        pipeline_page.add_node("Decision")
        decision_node_id = pipeline_page.wait_for_node_on_canvas("decision", timeout=UI_ELEMENT_TIMEOUT)
        assert decision_node_id, "Decision node should appear on canvas with a non-empty data-id"
        assert pipeline_page.get_node_count() == node_count_before_decision + 1, (
            "Node count should increase by exactly 1 after adding the Decision node"
        )

    with allure.step(
        "Step 2 — Decision node config renders inline on the canvas card "
        "(Input, Description, Decision outputs, Interrupt before/after all present, "
        "no click-to-open action)"
    ):
        assert pipeline_page.decision_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.decision_node_description_input.is_visible(), (
            "Description textarea should be visible inline"
        )
        assert pipeline_page.decision_node_outputs_container.is_visible(), (
            "Decision outputs container should be visible inline"
        )
        # Interrupt before/after — the AFS Coverage Map row 2 claims full
        # ("Interrupt before/after switches") coverage but the first
        # implementation only asserted "after" (fix-round finding). Both are
        # unconditional on the Decision node (CommonInterruptSettings.jsx);
        # "before" is node-id-keyed (ELITEA-2008), not testid-templated per
        # node type — same pattern already used for the Toolkit/LLM node AFSes.
        assert pipeline_page.is_node_interrupt_before_toggle_visible(decision_node_id), (
            "Interrupt before switch should be visible inline"
        )
        assert pipeline_page.decision_node_interrupt_after_toggle.is_visible(), (
            "Interrupt after switch should be visible inline"
        )

    with allure.step("Step 3 — Set Input to the two custom state variables"):
        pipeline_page.select_decision_node_input_variables(
            ["normalized_issue", "metadata_json"], timeout=UI_ELEMENT_TIMEOUT
        )
        input_value = pipeline_page.get_decision_node_input_value()
        assert "normalized_issue" in input_value and "metadata_json" in input_value, (
            f"Input select should show both custom state variables as selected chips, got {input_value!r}"
        )

    with allure.step("Step 4 — Fill Description with the classification prompt"):
        pipeline_page.fill_decision_node_description(_DESCRIPTION_TEMPLATE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_decision_node_description() == _DESCRIPTION_TEMPLATE, (
            "Description textarea should hold the entered classification prompt"
        )

    with allure.step(
        "Step 5 — Wire DECISION OUTPUTS by drag-connecting the Output handle to each "
        "target node; verify chips + immediate canvas edges (before Save)"
    ):
        for target_name in _OUTPUT_TARGETS:
            pipeline_page.connect_nodes(
                decision_node_id, target_name, source_handle="nodes", timeout=UI_ELEMENT_TIMEOUT
            )
            pipeline_page.wait_for_edge_present(decision_node_id, target_name, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.edge_exists(decision_node_id, target_name), (
                f"A {decision_node_id} -> {target_name} edge should render immediately, before Save"
            )
            assert pipeline_page.is_decision_node_output_chip_present(target_name), (
                f"A '{target_name}' chip should appear under Decision outputs immediately after connecting"
            )
        assert pipeline_page.get_decision_node_output_chip_count() == len(_OUTPUT_TARGETS), (
            f"Exactly {len(_OUTPUT_TARGETS)} Decision output chips should be present"
        )

    with allure.step("Step 6 — Save the pipeline; verify no console errors and a 201 Created response"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 7 — Reload via the canonical URL; Input, Description, and DECISION "
        "OUTPUTS all persist"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("decision", timeout=UI_ELEMENT_TIMEOUT)

        input_value_after_reload = pipeline_page.get_decision_node_input_value()
        assert "normalized_issue" in input_value_after_reload and "metadata_json" in input_value_after_reload, (
            f"Input should persist as both custom state variables after reload, got {input_value_after_reload!r}"
        )
        assert pipeline_page.get_decision_node_description() == _DESCRIPTION_TEMPLATE, (
            "Description should persist after reload"
        )
        for target_name in _OUTPUT_TARGETS:
            assert pipeline_page.is_decision_node_output_chip_present(target_name), (
                f"'{target_name}' Decision output chip should persist after reload"
            )
        assert pipeline_page.get_decision_node_output_chip_count() == len(_OUTPUT_TARGETS), (
            f"Exactly {len(_OUTPUT_TARGETS)} Decision output chips should persist after reload"
        )
        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 8 — Verify canvas shows both output handles labeled 'Output' and 'Default output'"
    ):
        assert pipeline_page.decision_node_output_handle.is_visible(), "Output handle should be visible"
        assert pipeline_page.decision_node_output_handle.text_content().strip() == "Output", (
            "Output handle's visible label should read exactly 'Output'"
        )
        assert pipeline_page.decision_node_default_output_handle.is_visible(), (
            "Default output handle should be visible"
        )
        assert pipeline_page.decision_node_default_output_handle.text_content().strip() == "Default output", (
            "Default output handle's visible label should read exactly 'Default output'"
        )

    with allure.step(
        "Step 9 — Verify canvas edges after reload (3 DECISION OUTPUTS edges)"
    ):
        for target_name in _OUTPUT_TARGETS:
            pipeline_page.wait_for_edge_present(decision_node_id, target_name, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.edge_exists(decision_node_id, target_name), (
                f"{decision_node_id} -> {target_name} edge should persist after reload"
            )
