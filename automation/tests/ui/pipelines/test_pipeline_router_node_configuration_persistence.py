"""UI test — Pipeline Router Node: Configuration Persistence.

TMS: ELITEA-2033
(test-specs/pipelines/l2_router-node-configuration-persistence_ELITEA-2033.md)

Adds a Router node to a pipeline pre-seeded with two Printer target nodes
named "approve"/"reject" (via ``PipelineAPI.create_pipeline_with_nodes()``,
sidestepping a fragile UI-rename detour — nodes added through the "Add node"
menu get a type-prefixed default name like "Printer 1", not the case's
literal test data; see the AFS's Axis 2 addition), configures its Condition
(Jinja template), Routes (both targets), and Input entirely through the
node's inline panel, saves, and verifies every field AND the Routes canvas
edges persist through a real hard reload: Condition/Routes are corroborated
by both the Flow-view fields and the YAML view independently; Input is
verified via its Flow-view chip alone (not cross-checked against YAML).

Known defect #1036 (isolated, non-blocking to Steps 1-5/7/9's Routes checks):
selecting "END" in the Router node's Default output field is a silent no-op
on a freshly-added node — confirmed live via 3 independent reads (immediate,
after an extra settle wait, and the actual Save PUT payload + API refetch),
all show `default_output: ''` even though the display continues to show
"END" and a (client-only, unpersisted) canvas edge is drawn. Root cause
(source-confirmed): RouterNode.jsx displays `yamlNode?.default_output ||
'END'` as a fallback for the freshly-initialized empty value; MUI's own
`SelectInput.js` (`handleItemClick`) only fires `onChange` when the clicked
option's value differs from the Select's current `value` prop — since the
prop is already the fallback string "END", clicking the "END" option is a
no-op indistinguishable (from the DOM alone) from a successful selection.
Per this suite's reverse-masking-guard convention, the Default-output
assertions are written as the CORRECT expected behavior (not weakened) and
deferred to the end of the test so the unaffected assertions (Condition,
Routes, Input persistence; Save; Routes edges) still run and prove
correctness on every execution — see the final allure step.
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

_CONDITION_JINJA = "{% if 'yes' in input %}approve{% else %}reject{% endif %}"
_INPUT_STATE_VAR = "input"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2033_pipeline-router-node-configuration.md",
    "onetest-ai Test Case link",
)
@allure.issue(
    "https://github.com/EliteaAI/elitea-testing-public/issues/1036",
    "Known defect #1036 — Default output 'END' selection no-ops on a fresh node",
)
def test_router_node_configuration_persistence(page, pipeline_with_route_targets_id):
    """Configure a Router node's panel fields end-to-end; verify persistence."""
    pipeline_id = pipeline_with_route_targets_id
    project_id = str(settings.elitea_project_id)

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
    soft_failures: list[str] = []

    with allure.step('Step 1 — Create a pipeline and add a Router node via "Add node" → "Router"'):
        # "Create a pipeline" is satisfied by the pipeline_with_route_targets_id
        # fixture (provides the case's own precondition — two existing node
        # ids, "approve"/"reject", for the Router node to route to); the
        # Router node itself is added fresh here, per the case's own step 1.
        pipeline_page = _navigate_to_canvas(page, pipeline_id)
        pipeline_page.add_node("Router")
        router_id = pipeline_page.wait_for_node_on_canvas("router", timeout=UI_ELEMENT_TIMEOUT)
        assert router_id, "Router node should have a non-empty data-id after being added"
        canonical_url = page.url  # captured for the reload step (Step 8) — bare
        # /pipelines/all/{id} without query params 404s (ELITEA-1954 Known Defect)

    with allure.step(
        "Step 2 — Verify Router node panel shows Condition/Routes/Input/Default output"
    ):
        # CLARIFICATION (AFS Coverage Map row 2): the Flow-view canvas renders
        # the Router node's full config always inline/expanded — no
        # click-to-open action exists (same finding as every other node type
        # explored on this surface: MCP/LLM/HITL).
        assert pipeline_page.router_node_condition_input.is_visible(), (
            "Condition textarea should be visible inline"
        )
        assert pipeline_page.router_node_routes_select.is_visible(), "Routes select should be visible inline"
        assert pipeline_page.router_node_input_select.is_visible(), "Input select should be visible inline"
        assert pipeline_page.router_node_default_output_select.is_visible(), (
            "Default output select should be visible inline"
        )

    with allure.step("Step 3 — Enter Jinja condition template"):
        pipeline_page.set_router_condition(_CONDITION_JINJA, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_router_condition() == _CONDITION_JINJA, (
            "Condition textarea should read back the typed Jinja template verbatim"
        )

    with allure.step('Step 4 — Routes: add route values "approve", "reject"'):
        # CLARIFICATION (AFS Coverage Map row 4): "route values" are existing
        # node ids selected from a combobox, not free-typed strings — the
        # pipeline_with_route_targets_id fixture pre-seeds them so the case's
        # literal test data ("approve"/"reject") matches real node ids.
        pipeline_page.select_router_routes(["approve", "reject"], timeout=UI_ELEMENT_TIMEOUT)
        routes_text = pipeline_page.get_router_routes()
        assert "approve" in routes_text and "reject" in routes_text, (
            f"Routes select should show both 'approve' and 'reject' chips, got {routes_text!r}"
        )

    with allure.step('Step 5 — Set Input combobox to state variable "input"'):
        pipeline_page.select_router_input(_INPUT_STATE_VAR, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_router_input() == _INPUT_STATE_VAR, (
            f"Input select should show a removable '{_INPUT_STATE_VAR}' chip after selection"
        )

    with allure.step(
        'Step 6 — Default output: verify out-of-the-box display default; set to "END" '
        "(interaction performed per the case; persistence proof deferred — see final step)"
    ):
        # Pre-interaction observation (AFS Step 6 clarification, corrected —
        # see module docstring / final step): the display already shows
        # "END" with zero interaction (a client-side fallback), and neither
        # the YAML nor a canvas edge reflect a persisted value yet.
        assert pipeline_page.get_router_default_output() == "END", (
            "Default output should display 'END' before any interaction (client-side fallback)"
        )
        assert not pipeline_page.edge_exists(router_id, "END"), (
            "No Default-output edge should exist yet — the display default is a "
            "display-only fallback, not a persisted/drawn value"
        )

        # The interaction the case's own step 6 calls for. Per Known defect
        # #1036 this specific click is a no-op on a fresh node (see module
        # docstring) — performed here regardless, exactly as a real user
        # would, and NOT worked around (e.g. by selecting a different value
        # first) — working around it would mask the defect.
        pipeline_page.select_router_default_output("END", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 7 — Save pipeline; verify no errors"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 8 — Reload — verify Condition text, Routes values, and Input persist "
        "(Default output persistence is the deferred Known-defect check — final step)"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("router", timeout=UI_ELEMENT_TIMEOUT)

        # Source 1 — Flow-view inline fields
        assert pipeline_page.get_router_condition() == _CONDITION_JINJA, "Condition should persist after reload"
        routes_text_after_reload = pipeline_page.get_router_routes()
        assert "approve" in routes_text_after_reload and "reject" in routes_text_after_reload, (
            f"Routes should persist after reload, got {routes_text_after_reload!r}"
        )
        assert pipeline_page.get_router_input() == _INPUT_STATE_VAR, "Input should persist after reload"

        # Source 2 — YAML view (independent corroboration, per AFS Axis 2 —
        # a single-source read can't distinguish stale client state from
        # genuinely persisted backend state).
        pipeline_page.switch_to_yaml_view()
        yaml_content_after_reload = pipeline_page.get_yaml_content()
        assert "condition:" in yaml_content_after_reload, "YAML should show the condition key"
        assert "approve" in yaml_content_after_reload and "reject" in yaml_content_after_reload, (
            "YAML should show both route target ids"
        )
        pipeline_page.switch_to_flow_view()

    with allure.step("Step 9 — Verify canvas shows Routes edges to the approve/reject target nodes"):
        pipeline_page.fit_view()
        assert pipeline_page.edge_exists(router_id, "approve"), (
            "A Routes edge from the Router node to 'approve' should exist on canvas after reload"
        )
        assert pipeline_page.edge_exists(router_id, "reject"), (
            "A Routes edge from the Router node to 'reject' should exist on canvas after reload"
        )

    with allure.step(
        "Known-defect check (deferred, #1036) — Default output 'END' should have persisted "
        "through Save and reload, matching the case's own step 6/8/9 expectations"
    ):
        # Deferred to the end (same precedent as
        # test_agent_management.py::test_edit_agent_instructions's Known
        # defect #538 side-channel) so the unaffected assertions above
        # (Condition/Routes/Input persistence, Save, Routes edges) still run
        # and prove correctness on every execution, regardless of this
        # known, isolated, already-filed defect. Each of the 3 checks below
        # is collected independently via the pytest-native soft_failures/
        # pytest.fail() idiom (mirrors test_fork_agent_to_different_project.py
        # and the sanctioned-RED "closed-set" convention, .agents/testing.md
        # § Merge gate) rather than three plain asserts — a plain assert on
        # the first check alone would short-circuit the block and leave the
        # other two never actually executed on any given run.
        if "default_output: END" not in yaml_content_after_reload:
            soft_failures.append(
                "Known defect #1036: Default output should show 'END' in the reloaded YAML — "
                "selecting the already-displayed 'END' option on a freshly-added Router node's "
                "Default output select is a silent no-op (MUI's Select suppresses onChange "
                "because its `value` prop already equals 'END' via RouterNode.jsx's display-only "
                "fallback), so `default_output` is never actually persisted. Confirmed via the "
                "Save PUT payload and a direct API refetch both showing default_output: '' "
                "immediately after the same selection this test just performed."
            )
        if pipeline_page.get_router_default_output() != "END":
            soft_failures.append(
                "Default output should display 'END' after reload (this assertion alone would "
                "pass vacuously even with the defect present — the display always falls back "
                "to 'END' for an empty value; see the YAML assertion above for the real proof)"
            )
        if not pipeline_page.edge_exists(router_id, "END"):
            soft_failures.append(
                "Known defect #1036: the Default-output edge should exist on canvas after "
                "reload — it does not."
            )
        # NOT a discriminating check for #1036 (source-verified,
        # parsePipeline.helpers.js's handleRouterNode, lines ~190-210): when
        # `default_output` is falsy the parser's `else` branch still
        # synthesizes an edge with the IDENTICAL id/testid shape
        # (`{id}default_output---END`) as the truthy branch produces for a
        # genuinely-persisted "END" — so this edge_exists() check passes
        # whether or not #1036 has shipped a fix, exactly like the display
        # assertion above. Kept (not removed) because it still exercises a
        # real testid on the case's own executed code path; the YAML
        # assertion above remains the only assertion in this block that
        # actually discriminates the defect.

    if soft_failures:
        pytest.fail(
            "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1036 "
            "(Default output 'END' selection no-ops on a freshly-added Router node — Steps "
            "1-5/7/9's Condition/Routes/Input/Save/Routes-edges checks above passed cleanly):\n"
            + "\n".join(soft_failures)
        )
