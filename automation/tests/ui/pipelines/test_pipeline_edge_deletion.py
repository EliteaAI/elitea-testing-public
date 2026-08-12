"""UI test — Pipeline: Edge Deletion.

TMS: ELITEA-2032
(test-specs/pipelines/l2_pipeline-edge-deletion_ELITEA-2032.md)

Seeds a pipeline ``LLM 1 -> Printer 1 -> END`` (the edge under test already
exists), clicks the ``LLM 1 -> Printer 1`` edge to select it, deletes it via
the Delete key + confirmation dialog, and confirms the edge is gone, the
source node's ``transition`` resets to the literal ``END`` (not an
empty/absent value), and the deletion survives Save + full page reload.

Case-text drift (AFS Preconditions, filed as
EliteaAI/elitea-testing-public#1136, clarification, same root cause as
ELITEA-2031's sibling finding): the case's Step 5 expects "the source
node's transition field is cleared / empty" — there is no visible
"transition field" in the node config panel to read. The verifiable
equivalent, confirmed live: the source node's underlying ``transition``
YAML property resets to the literal value ``END`` (every node always has
SOME transition, defaulting to the terminal END state).
"""

import re

import allure
import pytest
from components.mui import Dialog

from tests.ui.pipelines.helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000


def _extract_node_yaml_block(yaml_text: str, node_id: str) -> str:
    """Return the YAML lines belonging to *node_id*'s list item, from its
    ``- id: <node_id>`` line up to (but excluding) the next top-level
    ``- id:`` line or end of text.

    Line-based rather than a single backtracking regex, to stay readable
    and tolerant of the exact quoting/whitespace the product's YAML
    serializer emits on save+reload (may differ from the raw
    ``yaml.dump()`` text used to seed the pipeline via the API).
    """
    lines = yaml_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"-\s*id:\s*['\"]?{re.escape(node_id)}['\"]?\s*$", line.strip()):
            start = i
            break
    assert start is not None, f"'{node_id}' node id line not found in YAML:\n{yaml_text}"

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"-\s*id:", lines[j].strip()):
            end = j
            break
    return "\n".join(lines[start:end])


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2032_pipeline-edge-deletion.md",
    "onetest-ai Test Case link",
)
def test_delete_edge_resets_source_transition_and_persists(page, pipeline_llm_printer_connected):
    """Deleting the LLM 1 -> Printer 1 edge removes it, resets LLM 1's
    transition to END, and the removal persists after Save + reload."""
    with allure.step("Step 1 — Navigate to the pipeline's canvas"):
        pipeline_page = _navigate_to_canvas(page, pipeline_llm_printer_connected)
        assert pipeline_page.edge_exists("LLM 1", "Printer 1"), (
            "Seeded LLM 1 -> Printer 1 edge should exist on first canvas load"
        )
        edge_count_before = pipeline_page.get_edge_count()
        assert edge_count_before == 2, (
            f"Canvas should show 2 seeded edges (LLM 1->Printer 1, Printer 1->END), "
            f"got {edge_count_before}"
        )

    with allure.step("Step 2 — Click the LLM 1 -> Printer 1 edge to select it"):
        edge = pipeline_page.get_edge_locator("LLM 1", "Printer 1")
        # The default auto-layout places LLM 1 directly above Printer 1 with
        # no gap, so the edge's rendered path is near-zero-length and its
        # bounding-box center (what a coordinate-based click(force=True)
        # would target) falls under the node cards themselves, which paint
        # on top of edges in ReactFlow's stacking order — a coordinate click
        # lands on the node, not the edge. Dispatching a native MouseEvent
        # directly on the edge's own SVG <g> element (SVGElement has no
        # .click() method, unlike the MUI-overlay evaluate("el =>
        # el.click()") escape hatch in .claude/rules/mui-patterns.md — a
        # synthetic bubbling MouseEvent is the SVG equivalent) targets the
        # correct element regardless of what visually overlaps it, since
        # ReactFlow binds its edge onClick handler to this same
        # <g class="react-flow__edge"> group.
        edge.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
        classes = edge.get_attribute("class") or ""
        assert "selected" in classes.split(), (
            f"Edge should gain the 'selected' CSS class after clicking, got class='{classes}'"
        )

    with allure.step(
        "Step 3 — Delete the edge via the Delete key; confirm the 'Delete confirmation' dialog"
    ):
        # The embedded chat input auto-focuses on canvas load and stays
        # focused through our synthetic edge-click (a real user click
        # naturally blurs it; our dispatchEvent-based click, needed to reach
        # the edge under the overlapping nodes above, does not). The app's
        # delete-key handler (useKeyPress + isInputDOMNode,
        # useDeleteItems.hooks.js) intentionally no-ops while an <input>/
        # <textarea> is focused — confirmed live: pressing Delete with the
        # chat textarea still focused leaves no dialog. Blur it explicitly
        # first, matching what a real click elsewhere on the page would do.
        page.evaluate("document.activeElement && document.activeElement.blur()")
        page.keyboard.press("Delete")
        dialog = Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)
        dialog_text = dialog.text_content() or ""
        assert "Delete confirmation" in dialog_text, (
            f"Confirmation dialog should show 'Delete confirmation', got: {dialog_text!r}"
        )
        Dialog.click_button(dialog, "Delete")
        pipeline_page.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 4 — Verify the edge is removed from canvas"):
        assert not pipeline_page.edge_exists("LLM 1", "Printer 1"), (
            "LLM 1 -> Printer 1 edge should no longer exist after deletion"
        )
        edge_count_after = pipeline_page.get_edge_count()
        assert edge_count_after == 1, (
            f"Edge count should be exactly 1 after deletion (only Printer 1->END remains, "
            f"the sibling edge should not have been taken along), got {edge_count_after}"
        )

    with allure.step(
        "Step 5 — Verify LLM 1's transition resets to the literal 'END' "
        "(no empty/absent 'transition field' exists to read)"
    ):
        pipeline_page.switch_to_yaml_view()
        yaml_text = pipeline_page.get_yaml_content()
        llm1_block = _extract_node_yaml_block(yaml_text, "LLM 1")
        assert re.search(r"transition:\s*END\b", llm1_block), (
            f"LLM 1's transition should reset to 'END' after the edge deletion; "
            f"node block:\n{llm1_block}"
        )
        pipeline_page.switch_to_flow_view()

    with allure.step("Step 6 — Save — verify edge removal persists after reload"):
        assert pipeline_page.save_button.is_enabled(), (
            "Save button should be enabled after the delete (unsaved-change state)"
        )
        pipeline_page.save_button.click()
        pipeline_page.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
        page.reload()
        pipeline_page.wait_for_canvas()

        assert not pipeline_page.edge_exists("LLM 1", "Printer 1"), (
            "LLM 1 -> Printer 1 edge should still be gone after Save + reload"
        )
        # AFS drift (discovered during implementation, see module docstring
        # and test-specs/pipelines/l2_pipeline-edge-deletion_ELITEA-2032.md
        # § Implementer amendment): pipeline_settings is saved empty ({}) —
        # confirmed via the Save PUT response — so the canvas always
        # re-derives nodes/edges purely from the YAML `transition` fields on
        # load, never from a cached layout. LLM 1's transition resets to the
        # literal END (Step 5), so a FRESH load renders that as a real
        # LLM 1 -> END edge, on top of the pre-existing Printer 1 -> END
        # edge — 2 edges total, not 1. The AFS's own precondition documents
        # the identical rule elsewhere ("every node always has SOME
        # transition, defaulting to END") but Step 6's edge-count assertion
        # didn't carry it forward; corrected here.
        # edge_exists()'s own docstring flags it unreliable for the END node
        # (real internal target id is "EliteAPipelineEnd", not "END") —
        # edge_testid_present() checks the exact DOM testid instead, same
        # tool ELITEA-2028's AFS uses for the identical END-target case.
        assert pipeline_page.edge_testid_present("LLM 1", "EliteAPipelineEnd"), (
            "LLM 1 should reconnect to END on reload (its transition resets to END, "
            "and the canvas re-derives edges purely from YAML transitions on load)"
        )
        assert pipeline_page.get_edge_count() == 2, (
            f"Edge count should be 2 after reload (LLM 1->END, Printer 1->END — LLM 1's "
            f"reset transition renders as a real edge on a fresh load), "
            f"got {pipeline_page.get_edge_count()}"
        )
