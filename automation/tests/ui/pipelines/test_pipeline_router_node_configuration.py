"""UI test — Pipeline Router Node: Configuration and Edge Wiring.

TMS: ELITEA-2033
(test-specs/pipelines/l2_pipeline-router-node-configuration_ELITEA-2033.md)

Adds a Router node to a pipeline (alongside two Printer nodes, renamed to
"approve"/"reject", that serve as the Router's route targets), configures
Condition (Jinja), Routes, Input, and Default output, saves, and confirms
every field — plus all three canvas edges (two "routes" edges and one
"default output" edge) — survives a full page reload.

Step 0 is added ahead of the case's own step 1 (AFS Preconditions/step 0):
the case's precondition text implies target nodes named "approve"/"reject"
already exist, but live behavior requires an explicit setup action — the
Routes combobox is a picklist of EXISTING pipeline node ids (+ a literal
"END" option), NOT a freeform/creatable tag field (AFS Coverage Map
clarification, filed as a case-text CLARIFICATION, not a defect — the case's
overall intent is fully achievable, the wording just undersells the
mechanism).

Known defect: https://github.com/EliteaAI/elitea-testing-public/issues/1036
— "Default output" is a MUI `<Select>` whose displayed value on a fresh
Router node already shows "END" via a client-side fallback
(`yamlNode?.default_output || 'END'` in RouterNode.jsx); MUI's own
`SelectInput.js` only fires `onChange` when the clicked option's value
DIFFERS from the Select's current `value` prop, so clicking "END" — this
AFS's own step 6 instruction, deliberately chosen to "re-confirm the
already-selected option" — is a silent no-op: `default_output` never gets
written, the canvas edge never renders, and neither survives Save+reload.
The rest of the Router node's config (Condition, Routes, Input, both routes
edges, Save, reload) is unaffected and asserted normally. Soft-asserted via
this project's `soft_failures`/`pytest.fail()` shape (`edge_testid_present()`
returns a plain bool, not a Locator/Page/APIResponse, so
`expect.soft()` doesn't apply — precedent:
`test_fork_agent_to_different_project.py` #570).
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

_CONDITION_TEMPLATE = "{% if 'yes' in input %}approve{% else %}reject{% endif %}"


@pytest.mark.blocked(reason="Known product defect - blocked by issue #1036")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2033_pipeline-router-node-configuration.md",
    "onetest-ai Test Case link",
)
def test_router_node_configuration_and_edge_wiring(page, pipeline_id):
    """Configure a Router node's fields; verify they + their edges persist through Save + reload."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 0 so console errors from every step (node add,
    # rename, dropdown opens, field entry, save, reload) are captured — AFS
    # Expected Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    # pytest has no built-in expect.soft() for a plain bool (Playwright's
    # Python expect.soft() only supports Page/Locator/APIResponse —
    # edge_testid_present() returns bool). This list is the pytest-native
    # equivalent (precedent: test_fork_agent_to_different_project.py #570):
    # record known-defect #1036 failures here instead of raising immediately,
    # so the rest of the flow (steps 7-9's unaffected assertions) still runs
    # and reports; the test fails at the very end via pytest.fail() if
    # anything landed here — the defect is never masked.
    soft_failures = []

    with allure.step(
        "Step 0 (setup) — add two Printer nodes and rename them to 'approve'/'reject' "
        "so they can serve as the Router's route targets"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step (?viewMode=owner already included)

        node_ids_before_first_printer = set(pipeline_page.get_node_ids())
        pipeline_page.add_node("Printer")
        pipeline_page.wait_for_node_count(len(node_ids_before_first_printer) + 1, timeout=UI_ELEMENT_TIMEOUT)
        printer_1_id = (set(pipeline_page.get_node_ids()) - node_ids_before_first_printer).pop()

        node_ids_before_second_printer = set(pipeline_page.get_node_ids())
        pipeline_page.add_node("Printer")
        pipeline_page.wait_for_node_count(len(node_ids_before_second_printer) + 1, timeout=UI_ELEMENT_TIMEOUT)
        printer_2_id = (set(pipeline_page.get_node_ids()) - node_ids_before_second_printer).pop()

        approve_node_id = pipeline_page.edit_node_name(printer_1_id, "approve")
        reject_node_id = pipeline_page.edit_node_name(printer_2_id, "reject")

        assert approve_node_id == "approve" and reject_node_id == "reject", (
            "edit_node_name should return the verbatim new name as the node's new "
            f"data-id (got approve={approve_node_id!r}, reject={reject_node_id!r})"
        )
        node_ids_after_setup = set(pipeline_page.get_node_ids())
        assert {"approve", "reject"}.issubset(node_ids_after_setup), (
            f"Renamed target nodes should be on canvas as 'approve'/'reject', got {node_ids_after_setup!r}"
        )

    with allure.step("Step 1 — Add a Router node via canvas '+' button"):
        node_count_before_router = pipeline_page.get_node_count()
        pipeline_page.add_node("Router")
        router_node_id = pipeline_page.wait_for_node_on_canvas("router", timeout=UI_ELEMENT_TIMEOUT)
        assert router_node_id, "Router node should appear on canvas with a non-empty data-id"
        assert pipeline_page.get_node_count() == node_count_before_router + 1, (
            "Node count should increase by exactly 1 after adding the Router node"
        )
        default_output_edge_source = f"{router_node_id}default_output"

    with allure.step(
        "Step 2 — Router node config renders inline on the canvas card "
        "(Condition, Routes, Input, Default output all present, no click-to-open action)"
    ):
        assert pipeline_page.router_node_condition_input.is_visible(), (
            "Condition textarea should be visible inline"
        )
        assert pipeline_page.router_node_routes_select.is_visible(), (
            "Routes select should be visible inline"
        )
        assert pipeline_page.router_node_input_select.is_visible(), (
            "Input select should be visible inline"
        )
        assert pipeline_page.router_node_default_output_select.is_visible(), (
            "Default output select should be visible inline"
        )

    with allure.step("Step 3 — Enter the Jinja Condition template"):
        pipeline_page.fill_router_node_condition(_CONDITION_TEMPLATE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_router_node_condition() == _CONDITION_TEMPLATE, (
            "Condition textarea should hold the entered Jinja template"
        )

    with allure.step(
        "Step 4 — Select Routes 'approve' and 'reject'; verify chips + immediate "
        "canvas edges (before Save)"
    ):
        pipeline_page.select_router_node_routes(["approve", "reject"], timeout=UI_ELEMENT_TIMEOUT)
        routes_value = pipeline_page.get_router_node_routes_value()
        assert "approve" in routes_value and "reject" in routes_value, (
            f"Routes field should show both 'approve' and 'reject' chips, got {routes_value!r}"
        )
        pipeline_page.wait_for_edge(router_node_id, "approve", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.wait_for_edge(router_node_id, "reject", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.edge_testid_present(router_node_id, "approve"), (
            f"A {router_node_id} -> approve edge should render immediately, before Save"
        )
        assert pipeline_page.edge_testid_present(router_node_id, "reject"), (
            f"A {router_node_id} -> reject edge should render immediately, before Save"
        )

    with allure.step("Step 5 — Set Input to state variable 'input'"):
        pipeline_page.select_router_node_input_variable("input", timeout=UI_ELEMENT_TIMEOUT)
        assert "input" in pipeline_page.get_router_node_input_value(), (
            "Input select should show 'input' as a selected chip"
        )

    with allure.step(
        "Step 6 — Set Default output to 'END'; verify the distinct default-output edge"
    ):
        pipeline_page.select_router_node_default_output("END", timeout=UI_ELEMENT_TIMEOUT)
        # Always true regardless of the known defect below — the SingleSelect
        # displays "END" via a client-side fallback (`|| 'END'`) even when no
        # real selection has been committed, so this checks genuine on-screen
        # text, not persistence (persistence is what #1036 breaks).
        assert pipeline_page.get_router_node_default_output_value() == "END", (
            "Default output select should show 'END' after selection"
        )
        # Known defect: #1036 — clicking "END" while it's already the
        # displayed value never fires RouterNode.jsx's handleDefaultOutput
        # (MUI SelectInput.js only calls onChange when the clicked value
        # differs from the Select's current `value` prop), so the edge is a
        # silent no-op. See module docstring for the full root cause.
        try:
            pipeline_page.wait_for_edge(default_output_edge_source, "END", timeout=UI_ELEMENT_TIMEOUT)
        except AssertionError:
            soft_failures.append(
                "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1036: "
                f"default-output edge {default_output_edge_source} -> END did not render "
                "immediately after selecting Default output = END on a fresh Router node"
            )

    with allure.step("Step 7 — Save the pipeline; verify no console errors and a 201 Created response"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 8 — Reload via the canonical URL; Condition, Routes, Input, and "
        "Default output all persist"
    ):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("router", timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_router_node_condition() == _CONDITION_TEMPLATE, (
            "Condition should persist after reload"
        )
        routes_value_after_reload = pipeline_page.get_router_node_routes_value()
        assert "approve" in routes_value_after_reload and "reject" in routes_value_after_reload, (
            f"Routes chips should persist after reload, got {routes_value_after_reload!r}"
        )
        assert "input" in pipeline_page.get_router_node_input_value(), (
            "Input should persist as 'input' after reload"
        )
        # Always true regardless of #1036 — see the same-shape comment at
        # Step 6 (the "|| 'END'" display fallback applies post-reload too).
        assert pipeline_page.get_router_node_default_output_value() == "END", (
            "Default output should persist as 'END' after reload"
        )
        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 9 — Verify canvas edges after reload (2 routes edges + 1 default-output edge)"
    ):
        pipeline_page.wait_for_edge(router_node_id, "approve", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.wait_for_edge(router_node_id, "reject", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.edge_testid_present(router_node_id, "approve"), (
            f"{router_node_id} -> approve edge should persist after reload"
        )
        assert pipeline_page.edge_testid_present(router_node_id, "reject"), (
            f"{router_node_id} -> reject edge should persist after reload"
        )
        # Known defect: #1036 (see Step 6) — since default_output was never
        # actually written client-side, it was never persisted by Save
        # either, so the edge cannot survive a reload (the app's YAML->canvas
        # parser only draws this edge when default_output is truthy).
        try:
            pipeline_page.wait_for_edge(default_output_edge_source, "END", timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.edge_testid_present(default_output_edge_source, "END"), (
                f"{router_node_id} -> END default-output edge should persist after reload"
            )
        except AssertionError:
            soft_failures.append(
                "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1036: "
                f"default-output edge {default_output_edge_source} -> END did not persist "
                "after Save + reload"
            )

    if soft_failures:
        pytest.fail(
            "Soft assertion(s) failed (known isolated product defect, not "
            "test/infrastructure — rest of the flow, Condition/Routes/Input/"
            "routes-edges/Save/reload, passed cleanly):\n" + "\n".join(soft_failures)
        )
