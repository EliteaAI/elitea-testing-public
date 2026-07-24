"""UI test — Pipeline HITL Node: Configuration and Router Mapping.

TMS: ELITEA-2014
(test-specs/pipelines/l2_hitl-node-config-router-mapping_ELITEA-2014.md)

Adds a Human-in-the-loop node to a pipeline, configures its Input, USER
MESSAGE (Type + Value with an f-string token), all three ROUTER MAPPING
routes (APPROVE/EDIT/REJECT), and EDIT STATE KEY entirely through the
node's inline panel (Select onValueChange), NOT via canvas edge-dragging —
a distinct code path from the already-merged PIPE-031
(test_pipeline_nodes.py::test_add_human_in_the_loop_node_and_connect_to_end),
which only ever drags the approve handle to END and never touches USER
MESSAGE / EDIT STATE KEY / the EDIT route. Saves and verifies every field
persists through a real hard reload, corroborated by both the Flow-view
fields and the YAML view.

Two real execution-order dependencies (both source-confirmed in the AFS,
neither a defect) mean this test's action order differs from the case's
literal step numbering: USER MESSAGE Type must be F-String before the
Input select is usable (HITLNode.jsx:58), and EDIT STATE KEY must be
non-empty before the EDIT route select is usable (HITLNode.jsx:244-248).
allure.step labels below keep the case's own step numbers for traceability
even where execution order differs.
"""

import logging

import allure
import pytest
from config import settings

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_USER_MESSAGE_PREFIX = "Please review this: "
_USER_MESSAGE_STATE_VAR = "input"
_USER_MESSAGE_EXPECTED_VALUE = "Please review this: {input}"
_EDIT_STATE_KEY_VALUE = "messages"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2014_pipeline-hitl-node-configuration-and-router-mapping.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p2
def test_hitl_node_config_router_mapping(page, pipeline_with_llm_id):
    """Configure a HITL node's panel fields end-to-end; verify persistence."""
    pipeline_id = pipeline_with_llm_id
    project_id = str(settings.elitea_project_id)

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Create a pipeline and add a Human-in-the-loop node"):
        # "Create a pipeline" is satisfied by the pipeline_with_llm_id fixture
        # (already provides the case's own precondition — an LLM node as a
        # valid HITL route target); the HITL node itself is added fresh here,
        # per the case's own step 1.
        pipeline_page = _navigate_to_canvas(page, pipeline_id)
        pipeline_page.add_node("Human-in-the-loop")
        hitl_id = pipeline_page.wait_for_node_on_canvas("hitl", timeout=UI_ELEMENT_TIMEOUT)
        assert hitl_id, "Human-in-the-loop node should have a non-empty data-id after being added"
        canonical_url = page.url  # captured for the reload step (Step 8) — bare
        # /pipelines/all/{id} without query params 404s (ELITEA-1954 Known Defect)

    with allure.step(
        "Step 2 — Click HITL node — panel shows Input/USER MESSAGE/ROUTER MAPPING/EDIT STATE KEY"
    ):
        # CLARIFICATION (AFS Coverage Map row 2): the Flow-view canvas renders
        # the HITL node's full config always inline/expanded — no click-to-open
        # action exists (same finding as ELITEA-1954/ELITEA-2004). The
        # observable ("all sections visible") is still asserted here.
        assert pipeline_page.hitl_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.hitl_node_user_message_type_select.is_visible(), (
            "USER MESSAGE Type select should be visible inline"
        )
        assert pipeline_page.hitl_node_user_message_value_input.is_visible(), (
            "USER MESSAGE Value field should be visible inline"
        )
        for action in ("approve", "edit", "reject"):
            assert pipeline_page.is_hitl_router_route_visible(action, timeout=UI_ELEMENT_TIMEOUT), (
                f"ROUTER MAPPING {action.upper()} Route select should be visible inline"
            )
        assert pipeline_page.hitl_node_edit_state_key_select.is_visible(), (
            "EDIT STATE KEY Value select should be visible inline"
        )

    with allure.step(
        "Step 4 — USER MESSAGE: set Type to F-String (executed before Step 3 — "
        "see module docstring on execution order)"
    ):
        assert pipeline_page.is_hitl_input_select_disabled(timeout=UI_ELEMENT_TIMEOUT), (
            "Input select should be disabled by default (USER MESSAGE Type starts as Fixed, "
            "not F-String) — HITLNode.jsx:58"
        )
        pipeline_page.select_hitl_user_message_type("fstring", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_hitl_user_message_type() == "F-String", (
            "USER MESSAGE Type select should show 'F-String' after selection"
        )
        assert not pipeline_page.is_hitl_input_select_disabled(timeout=UI_ELEMENT_TIMEOUT), (
            "Input select should become enabled once USER MESSAGE Type is F-String"
        )
        pipeline_page.type_hitl_user_message_value(
            _USER_MESSAGE_PREFIX, _USER_MESSAGE_STATE_VAR, timeout=UI_ELEMENT_TIMEOUT
        )
        assert pipeline_page.get_hitl_user_message_value() == _USER_MESSAGE_EXPECTED_VALUE, (
            f"USER MESSAGE Value should read {_USER_MESSAGE_EXPECTED_VALUE!r} after typing "
            f"the prefix and inserting the f-string token via the autocomplete popper"
        )

    with allure.step("Step 3 — Set Input combobox with relevant state variables"):
        pipeline_page.select_hitl_input(_USER_MESSAGE_STATE_VAR, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_hitl_input_values() == _USER_MESSAGE_STATE_VAR, (
            f"Input select should show a removable '{_USER_MESSAGE_STATE_VAR}' chip after selection"
        )

    with allure.step(
        "Step 5 — ROUTER MAPPING: verify REJECT's out-of-the-box default; configure APPROVE"
    ):
        # Pre-interaction DOM read (AFS Test Steps 5): a freshly-added HITL
        # node ships with routes.reject == END before any click at all.
        assert pipeline_page.get_hitl_router_route("reject") == "END", (
            "REJECT route should default to 'END' before any interaction"
        )
        pipeline_page.select_hitl_router_route("approve", "LLM 1", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_hitl_router_route("approve") == "LLM 1", (
            "APPROVE route should show 'LLM 1' after selection"
        )

    with allure.step(
        "Step 6 — Set EDIT STATE KEY Value (must precede the EDIT route — see "
        "module docstring on execution order)"
    ):
        assert pipeline_page.is_hitl_edit_route_select_disabled(timeout=UI_ELEMENT_TIMEOUT), (
            "EDIT route select should be disabled while EDIT STATE KEY is empty — HITLNode.jsx:244-248"
        )
        pipeline_page.select_hitl_edit_state_key(_EDIT_STATE_KEY_VALUE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_hitl_edit_state_key() == _EDIT_STATE_KEY_VALUE, (
            f"EDIT STATE KEY Value select should show '{_EDIT_STATE_KEY_VALUE}' after selection"
        )
        assert not pipeline_page.is_hitl_edit_route_select_disabled(timeout=UI_ELEMENT_TIMEOUT), (
            "EDIT route select should become enabled immediately after EDIT STATE KEY is set"
        )

    with allure.step(
        "Step 5 (continued) — ROUTER MAPPING: verify EDIT excludes END; configure EDIT route"
    ):
        # Axis 2 addition (AFS): EDIT's option list deliberately excludes END
        # (HITLNode.jsx:49-52, editRouteOptions) — an Edit route must lead
        # somewhere that continues the flow, unlike APPROVE/REJECT.
        pipeline_page.open_hitl_router_route_select("edit", timeout=UI_ELEMENT_TIMEOUT)
        edit_options = set(pipeline_page.get_open_listbox_option_names())
        assert "END" not in edit_options, f"EDIT route options should never include END, got {edit_options!r}"
        assert "LLM 1" in edit_options, f"EDIT route options should include 'LLM 1', got {edit_options!r}"
        pipeline_page.select_open_listbox_option("LLM 1", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_hitl_router_route("edit") == "LLM 1", (
            "EDIT route should show 'LLM 1' after selection"
        )

    with allure.step("Step 7 — Save pipeline; verify no errors and edges reflect the routes"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"
        pipeline_page.fit_view()
        assert pipeline_page.edge_exists(hitl_id, "LLM 1", handle_suffix="approve"), (
            "An APPROVE edge from the HITL node to 'LLM 1' should exist on canvas after Save"
        )
        assert pipeline_page.edge_exists(hitl_id, "LLM 1", handle_suffix="edit"), (
            "An EDIT edge from the HITL node to 'LLM 1' should exist on canvas after Save"
        )

    with allure.step(
        "Step 8 — Reload — verify USER MESSAGE, all three ROUTER MAPPING routes, "
        "and EDIT STATE KEY persist"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("hitl", timeout=UI_ELEMENT_TIMEOUT)

        # Source 1 — Flow-view inline fields
        assert pipeline_page.get_hitl_input_values() == _USER_MESSAGE_STATE_VAR, (
            "Input chip should persist after reload"
        )
        assert pipeline_page.get_hitl_user_message_type() == "F-String", (
            "USER MESSAGE Type should persist as 'F-String' after reload"
        )
        assert pipeline_page.get_hitl_user_message_value() == _USER_MESSAGE_EXPECTED_VALUE, (
            "USER MESSAGE Value should persist after reload"
        )
        assert pipeline_page.get_hitl_router_route("approve") == "LLM 1", (
            "APPROVE route should persist as 'LLM 1' after reload"
        )
        assert pipeline_page.get_hitl_router_route("edit") == "LLM 1", (
            "EDIT route should persist as 'LLM 1' after reload"
        )
        assert pipeline_page.get_hitl_router_route("reject") == "END", (
            "REJECT route should persist as 'END' after reload"
        )
        assert pipeline_page.get_hitl_edit_state_key() == _EDIT_STATE_KEY_VALUE, (
            "EDIT STATE KEY should persist after reload"
        )

        # Source 2 — YAML view (independent corroboration, per AFS Axis 2:
        # a single-source read can't distinguish stale client state from
        # genuinely persisted backend state).
        pipeline_page.switch_to_yaml_view()
        yaml_content = pipeline_page.get_yaml_content()
        assert "edit_state_key: messages" in yaml_content, "YAML should show edit_state_key: messages"
        assert "approve: LLM 1" in yaml_content, "YAML should show routes.approve: LLM 1"
        assert "edit: LLM 1" in yaml_content, "YAML should show routes.edit: LLM 1"
        assert "reject: END" in yaml_content, "YAML should show routes.reject: END"
        assert "type: fstring" in yaml_content, "YAML should show user_message.type: fstring"
        assert _USER_MESSAGE_EXPECTED_VALUE in yaml_content, (
            "YAML should show the exact user_message.value string"
        )
