"""UI Test for ELITEA-2078 — Chat: Pipeline Flow Editor – Add LLM Node,
Discard Changes, and Verify Node is Removed.

Verifies that adding an LLM node to the in-chat pipeline canvas's Flow
Editor and then clicking Discard removes the unsaved node and reverts the
canvas to its last saved state — one layer deeper than the sibling
ELITEA-2076 spec (which only ever dirtied the header form's Name/
Description fields): this case dirties the Flow GRAPH itself.

Spec: test-specs/chat-interface/l2_pipeline-flow-editor-add-llm-node-discard-changes_ELITEA-2078.md

Setup replicates the case's own stated precondition ("the 'test-pipeline'
canvas is open with 'Configuration' and 'Flow Editor' tabs, following
ELITEA-2077") live, the same way ELITEA-2079's spec already does — ELITEA-
2077 is not yet automated as a standalone spec in this batch.

New page-object surface: none. Every method/testid this case touches
already exists — composes `ChatPage` (canvas entry point) +
`PipelineCanvasPage` (canvas chrome: title/subtitle/tabs/discard) +
`PipelineDetailPage` (Flow Editor: add-node menu, node count/ids, view
toggle) on the SAME ``page``, identical composition pattern to
``test_pipeline_discard_changes_clears_canvas.py`` (ELITEA-2076),
``test_pipeline_create_save_basic_configuration.py`` (ELITEA-2077), and
``test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py`` (ELITEA-2079).

Uses the testid-based Add Node menu methods (``get_add_node_menu_items()``/
``select_add_node_menu_item()``, ELITEA-2030) rather than the older
``add_node()`` helper, which still chains a raw CSS handle + role-based
menuitem lookup (kept only for its existing ELITEA-2079 caller).

Findings (AFS § Axis 2 / § Known Defects): none — this flow behaves exactly
as the case describes. Live-confirmed this session (pipeline id 9423,
version id 9734): Discard is gated on the Flow graph's own dirty state
(``PipelineEditor.jsx``'s ``totalDirty = isDirty || isYamlDirty``, via
``EditorPanel``'s ``useIsPipelineYamlCodeDirty()``), reverts the graph via
a purely client-side Redux reset (zero network calls between add-node and
post-discard), and the Add Node menu's 11-item set matches the case's own
list exactly.
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from pages.pipeline_canvas_page import PipelineCanvasPage
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat.pipeline_flow_editor_discard_llm_node")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.pipelines, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
CANVAS_TIMEOUT = 30_000  # ReactFlow's FlowWrapper is lazy-loaded (React.lazy/Suspense)

PIPELINE_NAME = "test-pipeline"
PIPELINE_DESCRIPTION = "A test pipeline for conversation"

# Confirmed live this session (source-traced to AddNodeMenu.jsx's
# getVisibleNodeTypes(), which filters FlowEditorConstants.PipelineNodeTypes
# down by excluding DeprecatedConstants.DeprecatedOrInvisibleNode) — matches
# the case's own Step 5 list one-for-one.
EXPECTED_NODE_TYPE_LABELS = {
    "Agent", "MCP", "Code", "Printer", "Custom", "Router",
    "Decision", "State modifier", "Human-in-the-loop", "Toolkit", "LLM",
}


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as the sibling pipeline-canvas specs (ELITEA-2076/2077/2079)
    — an unrelated toolkit/secrets panel probe that fires on every page
    load in this local environment, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestPipelineFlowEditorDiscardLlmNode:
    """ELITEA-2078: Chat – Pipeline Flow Editor – Add LLM Node, Discard
    Changes, and Verify Node is Removed (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2078_chat-pipeline-flow-editor-add-llm-node-discard-changes-and-verify-node-is-removed.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_add_llm_node_discard_changes_removes_node(
        self, page, conversation_id, pipeline_api,
    ):
        """Add an LLM node in the Flow Editor, then Discard, and verify the
        canvas reverts to only the End node.

        Steps (AFS
        test-specs/chat-interface/l2_pipeline-flow-editor-add-llm-node-discard-changes_ELITEA-2078.md):
        Setup (not a numbered case step — AFS § Preconditions live
        replication of ELITEA-2077): open the fixture-created conversation,
        + menu -> Pipelines -> + Create New Pipeline, fill Name/
        Description, Save (create-mode) -> canvas transitions to edit mode.
        1. Verify the canvas is open with Configuration/Flow Editor tabs.
        2. Click the Flow Editor tab.
        3. Verify Flow/Yaml sub-tabs, Flow active, only End node visible.
        4. Click "+ Add node".
        5. Verify the menu's 11 node types.
        6. Click "LLM".
        7. Verify the LLM node appears, visible and selectable.
        8. Click Discard; verify the confirmation dialog appears.
        9. Confirm Discard.
        10. Verify only the End node remains.
        """
        chat = ChatPage(page)
        pipeline_canvas = PipelineCanvasPage(page)
        pipeline_detail = PipelineDetailPage(page)

        pipeline_id = None
        console_messages = []
        write_requests = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        def _on_response(resp):
            # AFS § Network Behavior / Coverage Map row 9: Discard is a purely
            # client-side Redux reset — zero POST/PUT calls should fire once
            # this listener is attached (right after Setup's own create-mode
            # Save, which is awaited and off-list before we get here).
            if resp.request.method in ("POST", "PUT"):
                write_requests.append(f"{resp.request.method} {resp.url}")

        page.on("console", _on_console)
        page.on("response", _on_response)

        try:
            with allure.step(
                "Setup — open the fixture-created conversation; + menu -> "
                "Pipelines -> + Create New Pipeline; fill Name/Description; "
                "Save (create-mode) -> canvas transitions to edit mode "
                "(AFS § Preconditions, replicating ELITEA-2077)"
            ):
                chat.navigate_to_chat(conversation_id=conversation_id)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                chat.open_create_new_pipeline_canvas(timeout=NAVIGATION_TIMEOUT)
                pipeline_detail.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                pipeline_detail.fill_form(name=PIPELINE_NAME, description=PIPELINE_DESCRIPTION)

                with page.expect_response(
                    lambda r: r.request.method in ("POST", "PUT")
                    and "/applications/prompt_lib/" in r.url
                ) as create_resp_info, page.expect_response(
                    lambda r: r.request.method == "POST"
                    and "/participants/prompt_lib/" in r.url
                ) as add_participant_resp_info:
                    pipeline_detail.save_button.click()
                create_response = create_resp_info.value
                assert create_response.status == 201, (
                    f"Pipeline-creation request should resolve 201, got "
                    f"{create_response.status} for {create_response.url}"
                )
                created_pipeline = create_response.json()
                pipeline_id = created_pipeline.get("id")
                assert pipeline_id, (
                    f"Expected a numeric pipeline id in the creation "
                    f"response, got: {created_pipeline!r}"
                )
                # The create-mode Save also synchronously triggers
                # usePipelineCreation.js's onPipelineCreated -> addNewParticipants(),
                # which POSTs the new pipeline onto the conversation as a
                # PIPELINES participant (chat.api.js's addParticipantIntoConversation).
                # Await it explicitly so it can't race into the write-request
                # log below — it belongs to Setup's own precondition-replication
                # traffic, not to the Steps 4-9 add-node/discard flow.
                add_participant_response = add_participant_resp_info.value
                assert add_participant_response.status in (200, 201), (
                    f"Pipeline-as-participant request should resolve "
                    f"200/201, got {add_participant_response.status} for "
                    f"{add_participant_response.url}"
                )
                # Setup's own create-mode Save (+ its participant-add side
                # effect, now settled above) are legitimate POSTs — drop them
                # from the write-request log so the AFS's "zero network call"
                # claim (Coverage Map row 9 / § Network Behavior) is checked
                # only across Steps 1-9 (add-node through Discard-confirm),
                # not against Setup's own precondition-replication traffic.
                write_requests.clear()

            with allure.step(
                'Step 1 — Verify the "test-pipeline" canvas is open with '
                '"Configuration" and "Flow Editor" tabs'
            ):
                expect(pipeline_canvas.title).to_have_text(PIPELINE_NAME, timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_canvas.subtitle).to_have_text("base", timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_canvas.configuration_tab).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_canvas.configuration_tab).to_have_attribute(
                    "aria-selected", "true", timeout=UI_ELEMENT_TIMEOUT
                )
                expect(pipeline_canvas.flow_editor_tab).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step('Step 2 — Click on the "Flow Editor" tab'):
                pipeline_canvas.click_flow_editor_tab(timeout=UI_ELEMENT_TIMEOUT)
                pipeline_detail.wait_for_canvas(timeout=CANVAS_TIMEOUT)
                expect(pipeline_detail.canvas_wrapper).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 3 — Verify "Flow" and "Yaml" sub-tabs appear; "Flow" '
                'tab is active; only the "End" node is visible'
            ):
                expect(pipeline_detail.flow_view_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_detail.yaml_view_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert pipeline_detail.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
                    "Flow (visual) sub-view should be active by default"
                )
                assert pipeline_detail.get_node_count() == 1, (
                    "Freshly-opened Flow Editor should show exactly 1 node (End)"
                )
                assert pipeline_detail.get_node_ids() == ["END"], (
                    f"The single node should be the End node, got: "
                    f"{pipeline_detail.get_node_ids()!r}"
                )

            with allure.step('Step 4 — Click the "+ Add node" button in the top right'):
                menu_items = pipeline_detail.get_add_node_menu_items(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 5 — Verify the menu shows node types including: "
                "Agent, MCP, Code, Printer, Custom, Router, Decision, "
                "State modifier, Human-in-the-loop, Toolkit, LLM"
            ):
                assert set(menu_items) == EXPECTED_NODE_TYPE_LABELS, (
                    f"Add Node menu items mismatch.\nExpected: "
                    f"{sorted(EXPECTED_NODE_TYPE_LABELS)}\nGot: {sorted(menu_items)}"
                )

            with allure.step('Step 6 — Click on "LLM" from the menu'):
                pipeline_detail.select_add_node_menu_item("llm", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 7 — Verify the LLM node appears with icon, label, "
                "and connection ports (visible and selectable)"
            ):
                llm_node_id = pipeline_detail.wait_for_node_on_canvas("LLM", timeout=UI_ELEMENT_TIMEOUT)
                assert llm_node_id.startswith("LLM"), (
                    f"Added node's id should start with 'LLM', got: {llm_node_id!r}"
                )
                assert pipeline_detail.get_node_count() == 2, (
                    "Node count should become 2 after adding the LLM node"
                )
                llm_node = pipeline_detail.canvas_wrapper.locator(
                    pipeline_detail.RF_NODE_TESTID_PREFIX.format("LLM")
                )
                expect(llm_node).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step('Step 8 — Click the "Discard" button without saving'):
                assert pipeline_canvas.is_discard_enabled(timeout=UI_ELEMENT_TIMEOUT), (
                    "Discard should become enabled once the LLM node dirties "
                    "the Flow graph (PipelineEditor.jsx's isYamlDirty)"
                )
                pipeline_canvas.click_discard(timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_canvas.discard_confirm_modal).to_contain_text(
                    "Are you sure you want to discard changes?", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step('Step 9 — Click "Discard" to confirm'):
                pipeline_canvas.confirm_discard(timeout=UI_ELEMENT_TIMEOUT)
                assert not write_requests, (
                    "Discard should revert the Flow graph via a purely "
                    "client-side Redux reset — expected zero POST/PUT "
                    "network calls between adding the LLM node (step 6) and "
                    f"the post-discard state, but observed: {write_requests!r}"
                )

            with allure.step('Step 10 — Verify only the "End" node remains on the canvas'):
                assert pipeline_detail.get_node_count() == 1, (
                    "Canvas should revert to exactly 1 node (End) after discarding"
                )
                assert pipeline_detail.get_node_ids() == ["END"], (
                    f"The remaining node should be the End node, got: "
                    f"{pipeline_detail.get_node_ids()!r}"
                )
                assert not pipeline_canvas.is_discard_enabled(timeout=UI_ELEMENT_TIMEOUT), (
                    "Discard should re-disable once the Flow graph is no "
                    "longer dirty, corroborating the revert to last-saved state"
                )

            with allure.step("Side-channel check — no unexpected console errors across the full flow"):
                assert not console_messages, (
                    f"Unexpected console errors during the add-node/discard flow: "
                    f"{[m.text for m in console_messages]}"
                )
        finally:
            with allure.step("Cleanup — delete the created pipeline"):
                # conversation_id fixture handles conversation cleanup — the
                # pipeline is an independent entity that does NOT cascade-
                # delete from conversation deletion (AFS § Cleanup).
                if pipeline_id:
                    try:
                        pipeline_api.delete_pipeline(pipeline_id)
                        logger.info("Deleted pipeline %s", pipeline_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup failed for pipeline %s: %s", pipeline_id, exc
                        )
