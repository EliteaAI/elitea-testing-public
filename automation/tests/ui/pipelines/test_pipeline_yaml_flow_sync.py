"""UI test — Pipeline: YAML Editor to Flow Canvas Sync.

TMS: ELITEA-2028
(test-specs/pipelines/l2_yaml-to-flow-sync_ELITEA-2028.md)

Edits a node's `transition` target directly in the YAML editor and verifies
the change is reflected live in the Flow (ReactFlow) canvas as a re-wired
edge, and that the Save button transitions from disabled to enabled —
confirming YAML-editor-driven dirty-state detection (not just
Flow-canvas-driven dirtying, e.g. drag-connect/node-add, which was already
known to work per `discard_button`'s existing docstring).

Precondition setup (AFS § Preconditions / Automation Hints — "Seeding
gotcha") is NOT one of the case's own 5 numbered steps: seeded from
`pipeline_with_llm_id` (single saved LLM node), a second node ("Code 1") is
added via the UI's own `add_node()` and saved once, then the page is
reloaded, BEFORE the case's own steps begin. Seeding the 2-node
precondition via a raw multi-node YAML API call instead leaves
`pipeline_settings` empty and the canvas dirty on first load with zero
edits made — which would silently defeat step 5's disabled->enabled
assertion (confirmed live, see AFS Automation Hints).
"""

import logging

import allure
import pytest
import yaml
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2028_pipeline-yaml-to-flow-sync.md",
    "onetest-ai Test Case link",
)
def test_yaml_edit_transition_syncs_to_flow_canvas_and_enables_save(page, pipeline_with_llm_id):
    """A YAML transition edit re-wires the Flow edge and enables Save."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before setup so console errors / failed requests from every
    # step (node add, save, reload, view switches, the edit itself) are
    # captured — AFS Expected Results require "zero console errors, zero
    # failed network requests, throughout".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
    failed_requests = []
    page.on("response", lambda resp: failed_requests.append(resp) if resp.status >= 400 else None)

    # --- Setup (not a case step, see AFS Preconditions / Automation Hints —
    # "Seeding gotcha"): satisfy the "pipeline with >= 2 nodes" precondition
    # via the UI's own add_node(), Save once, then reload, so Save/Discard
    # start genuinely disabled before the case's step 1 begins.
    pipeline_page.navigate(pipeline_with_llm_id)
    pipeline_page.wait_for_canvas()
    canonical_url = page.url  # captured for the reload below (?viewMode=owner already included)

    pipeline_page.add_node("Code")
    code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
    assert code_node_id, "Code node should appear on canvas with a non-empty data-id"

    pipeline_page.save_and_wait_for_update(project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT)

    page.goto(canonical_url)
    pipeline_page.wait_for_detail_page_load()
    pipeline_page.wait_for_canvas()
    pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
    baseline_node_count = pipeline_page.get_node_count()
    baseline_edge_count = pipeline_page.get_edge_count()

    # Positive control (not one of the case's 5 numbered steps): prove the
    # exact-testid template `edge_testid_present()` relies on actually
    # detects a REAL edge before Step 4 leans on its NEGATIVE form ("the old
    # edge testid is gone"). Without this, a wrong guessed testid format
    # (`rf__edge-xy-edge__{source}---{target}`) would make edge_testid_present()
    # return False both before AND after the edit — Step 4's "not
    # edge_testid_present(...)" assertion would then pass vacuously, having
    # never actually observed a real edge testid to lose. Checked here, while
    # still on the Flow canvas (post-setup baseline, before the view switch
    # in Step 1), against the pre-edit LLM 1 -> END edge that setup itself
    # establishes.
    assert pipeline_page.edge_testid_present("LLM 1", "EliteAPipelineEnd"), (
        "Sanity check failed: edge_testid_present() should detect the real, "
        "pre-edit LLM 1 -> END edge on the Flow canvas baseline. If this "
        "fails, the exact-testid template itself is wrong, and Step 4's "
        "negative ('edge testid is gone') assertion would be meaningless."
    )

    with allure.step("Step 1 — Confirm default view is Flow, then switch to Yaml view"):
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Pipeline detail page should default to the Flow view"
        )
        pipeline_page.switch_to_yaml_view()
        pipeline_page.yaml_editor.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.yaml_editor.is_visible(), "YAML CodeMirror editor should become visible"

        # Captured here (post-setup, before the edit) so step 5 can prove the
        # disabled->enabled transition is CAUSED by the YAML edit, not a
        # pre-existing always-on dirty state (AFS Automation Hints —
        # confirmed live that an improperly-seeded pipeline can render with
        # Save/Discard permanently enabled with zero edits made). Nothing
        # between this capture and the edit itself (a view switch) dirties
        # the form.
        save_enabled_before_edit = pipeline_page.is_save_enabled()
        discard_enabled_before_edit = pipeline_page.is_discard_enabled()
        pre_edit_yaml = pipeline_page.get_yaml_content()
        pre_edit_transition_end_count = pre_edit_yaml.count("transition: END")
        assert pre_edit_transition_end_count == 2, (
            "Before the edit, exactly 2 nodes (LLM 1 and Code 1) should transition to END, "
            f"got {pre_edit_transition_end_count} in: {pre_edit_yaml!r}"
        )

    with allure.step("Step 2 — Edit the LLM node's transition target in the YAML editor: END → Code 1"):
        pipeline_page.edit_yaml_line("transition: END", f"transition: {code_node_id}")

        post_edit_yaml = pipeline_page.get_yaml_content()
        assert f"transition: {code_node_id}" in post_edit_yaml, (
            f"YAML content should contain the new transition target {code_node_id!r} after the edit: "
            f"{post_edit_yaml!r}"
        )
        assert post_edit_yaml.count("transition: END") == pre_edit_transition_end_count - 1, (
            "Editing the LLM node's transition should reduce 'transition: END' occurrences by exactly 1 "
            f"(Code 1's own trailing transition: END line stays untouched): {post_edit_yaml!r}"
        )

    with allure.step("Step 3 — Switch back to Flow view"):
        pipeline_page.switch_to_flow_view()
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Flow view (ReactFlow canvas) should become visible after switching back"
        )

    with allure.step("Step 4 — Verify the canvas reflects the updated edge; structure re-wired, not re-created"):
        # switch_to_flow_view() already settles ~1s (ReactFlow layout/edge
        # re-render is not instant, confirmed live) — within the AFS's
        # confirmed 1-1.5s window, no additional wait needed here.
        assert pipeline_page.edge_exists("LLM 1", code_node_id), (
            f"An edge from 'LLM 1' to {code_node_id!r} should exist on the canvas after the YAML edit"
        )
        assert not pipeline_page.edge_testid_present("LLM 1", "EliteAPipelineEnd"), (
            "The previous LLM 1 -> END edge testid should be gone — the same edge element re-targets "
            "to Code 1, it isn't left behind alongside a new one"
        )
        assert pipeline_page.get_node_count() == baseline_node_count, (
            "Node count should be unchanged by the YAML edit (structure re-wired, not re-created)"
        )
        assert pipeline_page.get_edge_count() == baseline_edge_count, (
            "Edge count should be unchanged by the YAML edit (LLM 1->Code 1 replaces LLM 1->END; "
            "Code 1->END is untouched)"
        )

    with allure.step(
        "Step 5 — Verify Save becomes enabled, confirming the disabled->enabled transition "
        "caused by the YAML edit (not a pre-existing always-on dirty state)"
    ):
        assert not save_enabled_before_edit, (
            "Save should have been disabled at the clean post-setup baseline, before the YAML edit"
        )
        assert not discard_enabled_before_edit, (
            "Discard should have been disabled at the clean post-setup baseline, before the YAML edit"
        )
        assert pipeline_page.is_save_enabled(), "Save should be enabled after the YAML-editor-driven edit"

    assert not console_errors, f"No console errors expected at any step: {console_errors}"
    assert not failed_requests, f"No failed network requests expected at any step: {failed_requests}"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2067_pipeline-yaml-editor-edit-and-save.md",
    "onetest-ai Test Case link",
)
def test_yaml_edit_persists_after_save_and_reload(page, pipeline_with_llm_id):
    """A YAML `output:` edit reflects in the Flow node config, enables Save, and survives reload.

    TMS: ELITEA-2067
    (test-specs/pipelines/lextend_pipeline-yaml-editor-edit-and-save_ELITEA-2067.md)

    Extends the YAML<->Flow sync coverage this file already establishes (ELITEA-2028) one stage
    further: that test proves a YAML edit reflects on the canvas AND enables Save, but never
    clicks Save nor reloads. This test edits a different field (the LLM node's `output:` list,
    the case's own worked example — "change a node's output variable name"), verifies the change
    reflected in the node's own inline config panel (not the canvas edge), then clicks Save and
    reloads to prove the edit round-trips through a full browser reload, not just in-memory
    client state.

    The `pipeline_with_llm_id` fixture (single LLM node -> END, `output: []`, never saved in this
    session) is ALREADY the clean baseline this case needs — unlike ELITEA-2028's own test, no
    second node / prior Save is required to establish a disabled Save/Discard starting point.
    """
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before step 1 so console errors / failed requests from every step (the edit,
    # view switches, save, reload) are captured — AFS Expected Results require "zero console
    # errors, zero failed network requests, throughout".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
    failed_requests = []
    page.on("response", lambda resp: failed_requests.append(resp) if resp.status >= 400 else None)

    pipeline_page.navigate(pipeline_with_llm_id)
    pipeline_page.wait_for_canvas()
    canonical_url = page.url  # captured for the step-7 reload (ELITEA-1954 404-on-bare-URL gotcha)

    with allure.step("Step 1 — Open the pipeline; switch to Yaml view"):
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Pipeline detail page should default to the Flow view"
        )
        pipeline_page.switch_to_yaml_view()
        pipeline_page.yaml_editor.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.yaml_editor.is_visible(), "YAML CodeMirror editor should become visible"

        # Captured here (post-navigate, before the edit) so step 5 can prove the
        # disabled->enabled transition is CAUSED by the YAML edit, not a pre-existing
        # always-on dirty state (mirrors ELITEA-2028's own proven pattern).
        save_enabled_before_edit = pipeline_page.is_save_enabled()
        discard_enabled_before_edit = pipeline_page.is_discard_enabled()
        pre_edit_yaml = pipeline_page.get_yaml_content()
        assert "output: []" in pre_edit_yaml, (
            f"Before the edit, the LLM node's output should be the fixture's empty list: {pre_edit_yaml!r}"
        )

    with allure.step(
        "Step 2/3 — Click into the editor and make a valid edit: change the LLM node's "
        "output variable from [] to [messages]"
    ):
        # Step 2 ("click into the editor, cursor placed") has no independent DOM signal to assert
        # against beyond the edit itself succeeding — folded into edit_yaml_line()'s own
        # click+Home+Shift+End sequence (AFS Coverage Map row 2 disposition).
        pipeline_page.edit_yaml_line("output: []", "output: [messages]")

        post_edit_yaml = pipeline_page.get_yaml_content()
        assert "output: [messages]" in post_edit_yaml, (
            f"YAML content should contain the new output variable after the edit: {post_edit_yaml!r}"
        )
        assert "output: []" not in post_edit_yaml, (
            f"The old empty-output value should be gone, not merely appended alongside: {post_edit_yaml!r}"
        )

    with allure.step("Step 4 — Switch to Flow view; verify the change is reflected in node configuration"):
        pipeline_page.switch_to_flow_view()
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Flow view (ReactFlow canvas) should become visible after switching back"
        )
        assert pipeline_page.get_llm_node_output_value() == "messages", (
            "The LLM node's inline Output field should reflect the YAML-editor-driven change"
        )

    with allure.step(
        "Step 5 — Verify Save becomes enabled, confirming the disabled->enabled transition "
        "caused by the YAML edit (not a pre-existing always-on dirty state)"
    ):
        assert not save_enabled_before_edit, (
            "Save should have been disabled at the clean pre-edit baseline"
        )
        assert not discard_enabled_before_edit, (
            "Discard should have been disabled at the clean pre-edit baseline"
        )
        assert pipeline_page.is_save_enabled(), "Save should be enabled after the YAML-editor-driven edit"

    with allure.step("Step 6 — Click Save; verify the pipeline saves without errors"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"

    with allure.step("Step 7 — Reload; switch to Yaml view; verify the edit persisted"):
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()

        pipeline_page.switch_to_yaml_view()
        pipeline_page.yaml_editor.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        post_reload_yaml = pipeline_page.get_yaml_content()
        # Parsed, not a literal-string match against what was TYPED: the server round-trips the
        # flow-style `output: [messages]` this test typed back as standard block-style YAML
        # (`output:\n  - messages`) — confirmed live this session, correct/expected YAML
        # serialization behavior, not a defect (reverse-masking guard — assert the live contract,
        # not the input's literal shape).
        post_reload_parsed = yaml.safe_load(post_reload_yaml)
        llm_node = next(n for n in post_reload_parsed["nodes"] if n["id"] == "LLM 1")
        assert llm_node["output"] == ["messages"], (
            f"The output edit should still be present after a full page reload, got: {llm_node['output']!r}"
        )

    assert not console_errors, f"No console errors expected at any step: {console_errors}"
    assert not failed_requests, f"No failed network requests expected at any step: {failed_requests}"
