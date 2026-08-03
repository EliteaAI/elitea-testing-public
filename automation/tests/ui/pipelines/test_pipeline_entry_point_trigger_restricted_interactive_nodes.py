"""UI test — Entry Point Node: Trigger Restricted When HITL/Printer/Interrupts Present.

TMS: ELITEA-2008
(test-specs/pipelines/l3_entry-point-trigger-restricted-interactive-nodes_ELITEA-2008.md)

Verifies the entry-point node's Trigger dropdown restricts to Chat-Message-
only whenever the pipeline's LAST-SAVED version contains a Printer node, a
HITL node, or a non-empty interrupt_before/interrupt_after list — and that
the restriction is keyed on the saved YAML, NOT the live unsaved canvas (a
restricting element added but not yet saved has NO effect on the dropdown).
Once saved, the restriction takes effect immediately (no reload needed) and
survives a reload. Removing all restricting elements + Save restores all 3
options.
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


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2008_entry-point-trigger-restricted-interactive-nodes.md",
    "onetest-ai Test Case link",
)
def test_entry_point_trigger_restricted_interactive_nodes(page, pipeline_with_llm_id):
    """Chat-Message-only restriction gates on the SAVED version, for Printer/HITL/interrupts alike."""
    project_id = str(settings.elitea_project_id)
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to the fresh pipeline; verify baseline: all 3 trigger options"):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_llm_id)
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        baseline_options = pipeline_page.get_trigger_options(timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id)
        assert baseline_options == ["Chat Message", "Schedule", "Webhook"], (
            f"Baseline (no restricting elements) should offer all 3 trigger types, got {baseline_options!r}"
        )

    with allure.step('Step 2 — Add a Printer node (unconnected); verify it exists on canvas'):
        pipeline_page.add_node("Printer")
        printer_node_id = pipeline_page.wait_for_node_on_canvas("printer", timeout=UI_ELEMENT_TIMEOUT)
        assert printer_node_id in pipeline_page.get_node_ids(), (
            "Printer node should be present on the canvas after add_node"
        )

    with allure.step(
        "Step 3 — WITHOUT saving, open the Trigger dropdown; verify the restriction does NOT apply yet"
    ):
        # Load-bearing precondition finding (AFS Coverage Map row 4): the
        # restriction is keyed on the pipeline's last-SAVED YAML
        # (`version_details.instructions`), NOT the live unsaved ReactFlow
        # canvas — confirmed via source read of TriggerTypeSelector.jsx's
        # `hasInteractiveElements` useMemo. A literal "add node -> assert
        # restriction" would produce a false negative here.
        pre_save_options = pipeline_page.get_trigger_options(timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id)
        assert pre_save_options == ["Chat Message", "Schedule", "Webhook"], (
            "Restriction should NOT apply before Save — the unsaved Printer node on the live "
            f"canvas has no effect on the Trigger dropdown yet, got {pre_save_options!r}"
        )

    with allure.step("Step 4 — Save the pipeline"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the updated pipeline version"

    with allure.step(
        "Step 5 — Open the Trigger dropdown again; verify ONLY Chat Message is available, "
        "immediately (no reload needed) AND after a reload"
    ):
        post_save_options = pipeline_page.get_trigger_options(timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id)
        assert post_save_options == ["Chat Message"], (
            f"Only Chat Message should be available once the Printer node is saved, got {post_save_options!r}"
        )

        canonical_url = page.url
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        post_reload_options = pipeline_page.get_trigger_options(timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id)
        assert post_reload_options == ["Chat Message"], (
            f"Restriction should survive a reload, got {post_reload_options!r}"
        )

    with allure.step(
        "Step 6 — Remove Printer, add a HITL node instead; Save; verify the same restriction applies"
    ):
        pipeline_page.delete_node(printer_node_id)
        pipeline_page.add_node("Human-in-the-loop")
        hitl_node_id = pipeline_page.wait_for_node_on_canvas("hitl", timeout=UI_ELEMENT_TIMEOUT)
        assert hitl_node_id in pipeline_page.get_node_ids(), (
            "HITL node should be present on the canvas after add_node"
        )

        pipeline_page.save_and_wait_for_update(project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT)
        hitl_options = pipeline_page.get_trigger_options(timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id)
        assert hitl_options == ["Chat Message"], (
            f"Only Chat Message should be available with a saved HITL node present, got {hitl_options!r}"
        )

    with allure.step(
        "Step 7 — Remove HITL; add a second (non-entry-point) node and enable its "
        "'Interrupt before'; Save; verify the same restriction applies"
    ):
        pipeline_page.delete_node(hitl_node_id)
        # CommonInterruptSettings.jsx's "Interrupt before" toggle disables
        # only when the node IS the saved entry point (`entry_point === id`)
        # — a freshly-added Code node never is, so it's enabled regardless of
        # its own canvas connections. ("Interrupt after" was tried first but
        # is unusable here: the pipeline builder auto-wires a new node's
        # output to END, and that toggle disables whenever
        # `transition === END` — confirmed live during this implementation.)
        pipeline_page.add_node("Code")
        code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.toggle_node_interrupt_before(code_node_id, timeout=UI_ELEMENT_TIMEOUT)

        pipeline_page.save_and_wait_for_update(project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT)
        interrupt_options = pipeline_page.get_trigger_options(timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id)
        assert interrupt_options == ["Chat Message"], (
            f"Only Chat Message should be available with a saved non-empty interrupt list, "
            f"got {interrupt_options!r}"
        )

    with allure.step(
        "Step 8 — Remove all HITL/Printer/interrupt configuration; Save; reload; "
        "verify all 3 trigger types are available again"
    ):
        pipeline_page.toggle_node_interrupt_before(code_node_id, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.delete_node(code_node_id)
        assert llm_node_id in pipeline_page.get_node_ids(), (
            "The original entry-point LLM node should still be present after cleanup"
        )

        pipeline_page.save_and_wait_for_update(project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT)

        canonical_url = page.url
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        restored_options = pipeline_page.get_trigger_options(timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id)
        assert restored_options == ["Chat Message", "Schedule", "Webhook"], (
            f"All 3 trigger types should be available again once every restricting element is "
            f"removed and saved, got {restored_options!r}"
        )

    assert not console_errors, (
        f"Exercising the trigger-restriction lifecycle should not introduce console errors: "
        f"{[m.text for m in console_errors]}"
    )
