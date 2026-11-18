"""UI tests — Pipeline: node YAML view (scope + two-way sync, validation + invalid YAML).

TMS: ELITEA-4716, ELITEA-4717
(test-specs/pipelines/l2_pipeline-node-yaml-view-scope-sync-and-validation_ELITEA-4716.md)

Two separate tests (their steps differ) sharing one API-seeded pipeline fixture. Case-text drift (AFS
§ Case-text clarifications): the node YAML is a one-item YAML list (``- id: ...``); the button reads
"Discard YAML changes"; ELITEA-4717 "Save is disabled while an error is shown" does not hold on DEV
(Save reflects pipeline dirtiness only) -> the error text and the not-applied rename are asserted instead.
"""

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_TIMEOUT = 20_000
# Node YAML is applied to the pipeline after a 400 ms debounce — expect() polling covers it.
SYNC_TIMEOUT = 10_000

_CASE_URL = (
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/pipelines/{}"
)
CASE_4716_URL = _CASE_URL.format("ELITEA-4716_pipeline-node-yaml-view-scope-and-two-way-sync.md")
CASE_4717_URL = _CASE_URL.format("ELITEA-4717_pipeline-node-yaml-view-validation-and-invalid-yaml-handling.md")

ERR_DUPLICATE = "The name has been used by other nodes, please input a new name!"
ERR_REQUIRED = "Name is required"
ERR_TYPE_CHANGE = "Node type can't be changed in the node YAML."
ERR_INVALID_PREFIX = "Invalid YAML:"

LEAVE_TEXT = (
    "The node YAML has errors, so it wasn't applied. "
    "Fix it, or discard your YAML changes to go back to the last valid version."
)


def _llm_node():
    return {
        "id": "LLM 1", "type": "llm", "input": ["messages"], "output": ["messages"],
        "input_mapping": {
            "system": {"type": "fixed", "value": ""},
            "task": {"type": "fixed", "value": "Say hi"},
            "chat_history": {"type": "fixed", "value": []},
        },
        "transition": "Printer 1",
    }


def _printer_node():
    return {
        "id": "Printer 1", "type": "printer", "input": ["messages"], "output": ["messages"],
        "input_mapping": {"printer": {"type": "fixed", "value": "x"}}, "transition": "END",
    }


def _code_node():
    return {
        "id": "Code 1", "type": "code", "code": {"type": "fixed", "value": '{"x": 1}'},
        "input": ["input"], "output": ["messages"], "transition": "END",
    }


def _seed(pipeline_api, name, description, extra_top_level=None):
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name[:32],
        description=description,
        entry_point="LLM 1",
        nodes=[_llm_node(), _printer_node(), _code_node()],
        extra_top_level=extra_top_level,
    )
    return pipeline["id"]


@pytest.fixture
def node_yaml_pipeline(pipeline_api, request):
    """Pipeline LLM 1 (entry) -> Printer 1 -> END plus Code 1 -> END, with pipeline-level interrupt_before."""
    pid = _seed(
        pipeline_api, f"autotest_nodeyaml_{request.node.name}", "Auto-created for ELITEA-4716/4717",
        extra_top_level={"interrupt_before": ["Printer 1"]},
    )
    yield pid
    try:
        pipeline_api.delete_pipeline(pid)
    except Exception:  # noqa: BLE001 — best-effort cleanup
        pass


def _open_pipeline(page, pp, pipeline_id):
    pp.navigate(pipeline_id)
    pp.dismiss_banner_if_present()
    pp.wait_for_canvas()


def _page_yaml_block(pp, node_id):
    """The page-level Yaml lines of one node block, de-indented to match the node-panel YAML."""
    lines = pp.get_yaml_content().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip() == f"- id: {node_id}")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].lstrip().startswith("- id:") or not lines[i].startswith(" "):
            end = i
            break
    return _dedent_block(lines[start:end])


def _dedent_block(block_lines):
    indent = len(block_lines[0]) - len(block_lines[0].lstrip())
    return "\n".join(ln[indent:] for ln in block_lines).rstrip()


@pytest.mark.tms("ELITEA-4716")
@allure.issue(CASE_4716_URL, "onetest-ai Test Case link")
def test_node_yaml_view_scope_and_two_way_sync(page, node_yaml_pipeline):
    """Node YAML is scoped to one node, equals the page Yaml block and syncs both ways; unknown keys persist."""
    page.set_viewport_size({"width": 1600, "height": 1400})
    pp = PipelineDetailPage(page)

    with allure.step("Step 1 — Open the pipeline, click LLM 1 and switch the panel to YAML"):
        _open_pipeline(page, pp, node_yaml_pipeline)
        canonical_url = page.url
        pp.open_node_panel_by_card("LLM 1", timeout=UI_ELEMENT_TIMEOUT)
        pp.open_node_yaml_tab(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 2 — Node YAML shows only the LLM 1 block (no pipeline keys, no other nodes)"):
        node_yaml = pp.node_yaml_text()
        lines = node_yaml.splitlines()
        assert lines[0] == "- id: LLM 1", f"first line should be the list item for LLM 1, got {lines[0]!r}"
        assert sum(1 for ln in lines if ln.startswith("- id:")) == 1, node_yaml
        for key in ("type: llm", "input:", "input_mapping:", "output:", "transition: Printer 1"):
            assert any(ln.strip() == key for ln in lines), f"missing {key!r} in node YAML:\n{node_yaml}"
        for forbidden in ("entry_point:", "nodes:", "state:", "interrupt_before:", "interrupt_after:",
                          "id: Printer 1", "id: Code 1", "custom_note:"):
            assert not any(forbidden in ln for ln in lines), f"{forbidden!r} must not be in node YAML:\n{node_yaml}"

    with allure.step("Step 3 — Page-level Yaml block of LLM 1 is identical to the node YAML"):
        pp.close_node_panel(timeout=UI_ELEMENT_TIMEOUT)
        pp.switch_to_yaml_view()
        page_block = _page_yaml_block(pp, "LLM 1")
        assert page_block == node_yaml.rstrip(), f"page block differs:\n{page_block}\n--- vs node ---\n{node_yaml}"

    with allure.step("Step 4 — Editing the task in node YAML syncs Flow Task field, card summary and Save"):
        pp.switch_to_flow_view()
        pp.wait_for_canvas()
        pp.open_node_panel_by_card("LLM 1", timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.save_button).to_be_disabled()
        pp.open_node_yaml_tab(timeout=UI_ELEMENT_TIMEOUT)
        pp.set_node_yaml_line("value: Say hi", "value: Summarize the input")
        expect(pp.node_card("LLM 1")).to_contain_text("Summarize the input", timeout=SYNC_TIMEOUT)
        expect(pp.save_button).to_be_enabled(timeout=SYNC_TIMEOUT)
        pp.open_node_flow_tab(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.llm_node_task_value).to_have_value("Summarize the input", timeout=SYNC_TIMEOUT)

    with allure.step("Step 5 — Page Yaml LLM 1 block contains the new task value"):
        pp.close_node_panel(timeout=UI_ELEMENT_TIMEOUT)
        pp.switch_to_yaml_view()
        assert "value: Summarize the input" in _page_yaml_block(pp, "LLM 1")

    with allure.step("Step 6 — Changing transition to Code 1 redraws the edge and updates page Yaml"):
        pp.switch_to_flow_view()
        pp.wait_for_canvas()
        pp.open_node_panel_by_card("LLM 1", timeout=UI_ELEMENT_TIMEOUT)
        pp.open_node_yaml_tab(timeout=UI_ELEMENT_TIMEOUT)
        pp.set_node_yaml_line("transition: Printer 1", "transition: Code 1")
        pp.wait_for_edge_present("LLM 1", "Code 1", timeout=SYNC_TIMEOUT)
        assert not pp.edge_exists("LLM 1", "Printer 1"), "old LLM 1 -> Printer 1 edge should be gone"
        pp.close_node_panel(timeout=UI_ELEMENT_TIMEOUT)
        pp.switch_to_yaml_view()
        assert "transition: Code 1" in _page_yaml_block(pp, "LLM 1")
        pp.switch_to_flow_view()
        pp.wait_for_canvas()

    with allure.step("Step 7 — Flow-tab System edit shows in the YAML tab"):
        pp.open_node_panel_by_card("LLM 1", timeout=UI_ELEMENT_TIMEOUT)
        pp.llm_node_system_value.click()
        page.keyboard.insert_text("You are a helpful assistant")
        pp.open_node_yaml_tab(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_yaml_content()).to_contain_text("You are a helpful assistant", timeout=SYNC_TIMEOUT)

    # Step 8 (canvas drag LLM 1 Output -> Printer 1 reflected in node YAML) is NOT automated — AFS
    # § Blocked Steps: after step 6 the 16px Output handle is fully covered by LLM 1's edge source-updater
    # and connect_nodes' bottom sliver by the card's own Box, so no real-mouse "new edge" drag is possible
    # in this layout (dragging the edge's target end only re-routes visually; the app's onReconnect does
    # not write the YAML transition). Not faked via a YAML edit. Reported to the lead as a finding.

    with allure.step("Step 9 — Unknown key survives Save and reload"):
        pp.replace_node_yaml_text(pp.node_yaml_text() + "\n  custom_note: keep_me")
        expect(pp.node_yaml_error()).to_have_count(0)
        expect(pp.save_button).to_be_enabled(timeout=SYNC_TIMEOUT)
        pp.save_and_wait_for_saved(timeout=SAVE_TIMEOUT)
        page.goto(canonical_url)
        pp.dismiss_banner_if_present()
        pp.wait_for_canvas()
        pp.open_node_panel_by_card("LLM 1", timeout=UI_ELEMENT_TIMEOUT)
        pp.open_node_yaml_tab(timeout=UI_ELEMENT_TIMEOUT)
        # The app re-dumps key order, so assert presence rather than position.
        assert "custom_note: keep_me" in pp.node_yaml_text()


@pytest.mark.tms("ELITEA-4717")
@allure.issue(CASE_4717_URL, "onetest-ai Test Case link")
def test_node_yaml_view_validation_and_invalid_yaml(page, node_yaml_pipeline):
    """Invalid names / type changes / YAML are never applied; Fix/Discard guard; Find/Replace/Copy work."""
    page.set_viewport_size({"width": 1600, "height": 1400})
    pp = PipelineDetailPage(page)

    with allure.step("Step 1 — Open the pipeline, click LLM 1, switch the panel to YAML"):
        _open_pipeline(page, pp, node_yaml_pipeline)
        pp.open_node_panel_by_card("LLM 1", timeout=UI_ELEMENT_TIMEOUT)
        pp.open_node_yaml_tab(timeout=UI_ELEMENT_TIMEOUT)
        assert pp.node_yaml_text().splitlines()[0] == "- id: LLM 1"

    with allure.step("Step 2 — Renaming via id updates the card title and the panel Name"):
        pp.set_node_yaml_line("- id: LLM 1", "- id: LLM main")
        expect(pp.node_card("LLM main")).to_be_visible(timeout=SYNC_TIMEOUT)
        expect(pp.node_card("LLM 1")).to_have_count(0)
        expect(pp.node_yaml_error()).to_have_count(0)
        pp.open_node_flow_tab(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_panel_name_input).to_have_value("LLM main")
        pp.open_node_yaml_tab(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 3 — Duplicate id shows the exact error and the rename is not applied"):
        pp.set_node_yaml_line("- id: LLM main", "- id: Code 1")
        expect(pp.node_yaml_error()).to_have_text(ERR_DUPLICATE, timeout=SYNC_TIMEOUT)
        expect(pp.node_card("LLM main")).to_have_count(1)

    with allure.step("Step 4 — Empty id shows 'Name is required'; the card title is unchanged"):
        pp.set_node_yaml_line("- id: Code 1", "- id: ''")
        expect(pp.node_yaml_error()).to_have_text(ERR_REQUIRED, timeout=SYNC_TIMEOUT)
        expect(pp.node_card("LLM main")).to_have_count(1)

    with allure.step("Step 5 — Restoring the id clears the error; a type change is rejected"):
        pp.set_node_yaml_line("- id: ''", "- id: LLM main")
        expect(pp.node_yaml_error()).to_have_count(0, timeout=SYNC_TIMEOUT)
        pp.set_node_yaml_line("type: llm", "type: code")
        expect(pp.node_yaml_error()).to_have_text(ERR_TYPE_CHANGE, timeout=SYNC_TIMEOUT)

    with allure.step("Step 6 — Broken YAML syntax shows an 'Invalid YAML:' error"):
        pp.set_node_yaml_line("type: code", "type: llm")
        expect(pp.node_yaml_error()).to_have_count(0, timeout=SYNC_TIMEOUT)
        pp.set_node_yaml_line("input_mapping:", "input_mapping")
        expect(pp.node_yaml_error()).to_contain_text(ERR_INVALID_PREFIX, timeout=SYNC_TIMEOUT)
        assert (pp.node_yaml_error().text_content() or "").startswith(ERR_INVALID_PREFIX)

    with allure.step("Step 7 — Page Yaml still holds the last valid LLM main block (invalid edit not applied)"):
        pp.switch_to_yaml_view()
        page_yaml = pp.get_yaml_content()
        assert "- id: LLM main" in page_yaml
        assert "input_mapping:" in page_yaml, "invalid edit must not reach the page Yaml"
        pp.switch_to_flow_view()
        pp.wait_for_canvas()
        expect(pp.node_yaml_error()).to_be_visible()

    with allure.step("Step 8 — Switching to Flow with invalid YAML shows the 'Invalid node YAML' modal"):
        pp.node_panel_view_flow_button().click()
        expect(pp.node_yaml_leave_dialog()).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_yaml_leave_dialog()).to_contain_text("Invalid node YAML")
        expect(pp.node_yaml_leave_dialog()).to_contain_text(LEAVE_TEXT)
        expect(pp.node_yaml_leave_fix_button()).to_have_text("Fix")
        # Live label is "Discard YAML changes" (case text says "Changes" — case-text drift).
        expect(pp.node_yaml_leave_discard_button()).to_have_text("Discard YAML changes")

    with allure.step("Step 9 — Fix closes the modal; the YAML tab and error stay"):
        pp.node_yaml_leave_fix_button().click()
        expect(pp.node_yaml_leave_dialog()).to_have_count(0)
        expect(pp.node_yaml_content()).to_be_visible()
        expect(pp.node_yaml_error()).to_contain_text(ERR_INVALID_PREFIX)

    with allure.step("Step 10 — Closing the panel with invalid YAML shows the same modal"):
        pp.node_panel_close_button.click()
        expect(pp.node_yaml_leave_dialog()).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_yaml_leave_dialog()).to_contain_text("Invalid node YAML")

    with allure.step("Step 11 — Discard reverts to the last valid YAML and the error disappears"):
        pp.node_yaml_leave_discard_button().click()
        expect(pp.node_yaml_leave_dialog()).to_have_count(0)
        expect(pp.node_panel_close_button).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)  # panel closed
        expect(pp.node_card("LLM main")).to_have_count(1)
        pp.open_node_panel_by_card("LLM main", timeout=UI_ELEMENT_TIMEOUT)
        pp.open_node_yaml_tab(timeout=UI_ELEMENT_TIMEOUT)
        expect(pp.node_yaml_error()).to_have_count(0)
        node_yaml = pp.node_yaml_text()
        assert node_yaml.splitlines()[0] == "- id: LLM main"
        assert any(ln.strip() == "input_mapping:" for ln in node_yaml.splitlines())

    with allure.step("Step 12 — Ctrl+F opens the find panel; matches are scoped to this node's YAML"):
        pp.node_yaml_content().click()
        page.keyboard.press("Control+f")
        expect(pp.node_yaml_search_panel()).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        page.keyboard.type("transition")
        page.keyboard.press("Enter")
        expected_matches = node_yaml.count("transition")
        expect(pp.node_yaml_search_matches()).to_have_count(expected_matches, timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 13 — Ctrl+H shows the replace controls"):
        # Declared weak (AFS step 12): the replace row already shows at Ctrl+F in this CM6 setup, so this is non-discriminating.
        page.keyboard.press("Control+h")
        expect(pp.node_yaml_replace_button()).to_have_count(1)
        expect(pp.node_yaml_replace_all_button()).to_have_count(1)

    with allure.step("Step 14 — Copy shows the 'Copied' confirmation"):
        pp.node_yaml_copy_button().click()
        expect(pp.node_yaml_copied_message).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
