"""UI Test for ELITEA-2078 — Chat: Pipeline Flow Editor – Add LLM Node,
Discard Changes, and Verify Node is Removed.

Verifies that adding an LLM node to the in-chat pipeline canvas's Flow
editor and then clicking Discard removes the unsaved node and reverts the
canvas to its last-saved state (only the End node), with the canvas-header
Discard AND Save buttons both returning to disabled.

Spec: test-specs/chat-interface/
l3_pipeline-flow-editor-add-llm-node-discard-verify-node-removed_ELITEA-2078.md

Case-chain caveat (AFS § Preconditions): the original case's Preconditions
read "The 'test-pipeline' canvas is open ... (following ELITEA-2077)" —
narrating a manual regression-suite chain. Per the project's Test
Isolation principle (.claude/rules/ui-tests.md), this test reconstructs
the equivalent precondition from scratch in its own Setup: create a fresh
pipeline via the in-chat canvas, save it once, reach the Flow editor's
Flow tab with only the End node visible. The pipeline's name is not
asserted anywhere in the case's own steps, so a random suffix is used
instead of hardcoding the manual case's literal "test-pipeline" name.

New page-object surface (AFS § Automation Hints):
- ``ChatPage`` gained ``pipelines_menuitem``/``pipelines_create_new_button``
  + ``open_create_new_pipeline_canvas()`` — same "+ menu -> hover submenu
  -> click create-new" pattern as ``open_create_new_agent_canvas()``
  (ELITEA-2166).
- ``PipelineCanvasPage`` (new) owns the canvas-specific chrome this case's
  steps touch: the create-mode Save button (``pipeline-save-button`` —
  DIFFERENT testid than the Agent canvas's ``agent-save-button``, since
  ``CreateApplicationSaveButton.jsx`` is shared but supplied a
  pipeline-specific testid at this call site), the Flow editor tab, and
  the Discard button + its confirmation dialog + confirm button. The
  Name/Description fields are NOT redeclared — ``AgentFormPage`` is
  reused directly on the same ``page`` (same ``CreateAgentForm`` component,
  ``entityType="pipeline"``, ``showInstructions=False`` so
  ``fill_form(name, description)`` — omitting ``instructions`` — never
  touches the non-rendered Instructions field).
- ``PipelineDetailPage`` gained additive testid-only siblings to its
  pre-existing raw-selector ``add_node()`` (3 merged callers, left
  untouched per the shared-caller rule): ``add_node_button``,
  ``open_add_node_menu()``, ``get_add_node_menu_item_count()``,
  ``get_add_node_menu_item_texts()``, ``click_add_node_menu_item()``,
  ``add_node_via_testid()`` (``pipeline-add-node-button`` / dynamic
  ``pipeline-add-node-menu-item-{type}``), plus ``get_rf_node_locator()``,
  ``node_has_icon()``, ``get_node_handle_count()`` for the per-node
  icon/label/handle-count checks in step 7 and the targeted "node now
  gone" wait in step 9. Reused as-is: ``flow_view_button``/
  ``yaml_view_button``, ``wait_for_canvas()``, ``get_node_count()``,
  ``get_node_ids()``, ``get_node_name()``, ``wait_for_node_on_canvas()``.
  Composed on the SAME ``page`` as the in-chat canvas — confirmed live
  identical to the standalone Pipeline Detail page (AFS).

Testid gap filled this implementation (``add-data-testid``, committed +
pushed to ``automation/testids``): ``PipelineEditor.jsx``'s ``<BaseEditor>``
call gained ``discardButtonTestId="pipeline-canvas-discard-button"`` /
``discardModalTestId="pipeline-canvas-discard-confirm-dialog"`` /
``discardConfirmButtonTestId="pipeline-canvas-discard-confirm-button"`` —
pure prop-threading onto ``EditorHeader.jsx``/``BaseEditor.jsx``'s ALREADY
EXISTING optional props (added generically for the Toolkit canvas's own
Discard flow, ELITEA-2082/2083/2080 — this case's call site is the first
one to actually supply real testid strings, mirroring
``closeButtonTestId="pipeline-canvas-close-button"`` already on the same
call). Confirmed live: MUI forwards ``discardModalTestId`` to the Dialog's
own ancestor wrapper, not the ``role="dialog"`` Paper (same quirk noted
for the node-delete dialog in ``test-specs/pipelines/_surface.md``) — the
dialog's full text is still readable via ``text_content()`` regardless,
and the confirm button carries a real, directly-clickable testid
unaffected by this.

Known defects: none. Confirmed live, twice (implementer's own Phase 2
exploration + the AFS's own two independent repro passes): adding an LLM
node and discarding correctly and completely reverts the canvas, with
both dirty-state indicators clearing and zero console errors.
"""

import logging
import uuid

import allure
import pytest
from pages.agent_form_page import AgentFormPage
from pages.chat_page import ChatPage
from pages.pipeline_canvas_page import PipelineCanvasPage
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.pipelines, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Live-verified (AFS + implementer Phase 2 exploration, twice each): exactly
# these 11 node types, in this exact order (AddNodeMenu.jsx sorts by label,
# case-insensitive, then splits into two menu columns).
EXPECTED_ADD_NODE_MENU_ITEMS = [
    "Agent", "Code", "Custom", "Decision", "Human-in-the-loop", "LLM",
    "MCP", "Printer", "Router", "State modifier", "Toolkit",
]


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_create_agent_via_chat_canvas.py`` /
    ``test_conversation_deletion_flow.py`` / ``test_folder_creation.py`` —
    an unrelated toolkit/secrets panel probe that fires on every page load
    in this local environment, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestPipelineFlowEditorAddLlmNodeDiscard:
    """ELITEA-2078: Pipeline Flow Editor – Add LLM Node, Discard, Verify Removed (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat-interface/"
        "ELITEA-2078_chat-pipeline-flow-editor-add-llm-node-discard-changes-and-verify-node-is-removed.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_add_llm_node_discard_reverts_canvas(self, page, pipeline_api):
        """Add an LLM node in the in-chat pipeline Flow editor, discard
        without saving, and verify the canvas reverts to only the End
        node with both Discard and Save disabled again.

        Steps (AFS test-specs/chat-interface/
        l3_pipeline-flow-editor-add-llm-node-discard-verify-node-removed_ELITEA-2078.md):
        Setup — create a fresh pipeline via the in-chat canvas (reconstructs
                the case's own precondition — see module docstring).
        1-2. Open the Flow editor tab; verify the ReactFlow canvas renders.
        3. Verify Flow/Yaml sub-tabs and only the End node.
        4-5. Open "+ Add node" menu; verify all 11 node types listed.
        6-7. Add an LLM node; verify it renders with icon/label/ports.
        8. Click Discard (now enabled); verify the confirmation dialog.
        9. Confirm Discard; verify the LLM node is removed.
        10. Verify only the End node remains and Discard/Save both disabled.
        """
        chat = ChatPage(page)
        # Name/Description fields — shared CreateAgentForm component, same
        # composition pattern as agent_canvas_page.py / ELITEA-2166.
        agent_form = AgentFormPage(page)
        pipeline_canvas = PipelineCanvasPage(page)
        # Flow/Add-node/canvas-node helpers — composed on the SAME page,
        # confirmed live identical to the standalone Pipeline Detail page.
        pipeline_detail = PipelineDetailPage(page)

        pipeline_name = f"autotest_ELITEA_2078_{uuid.uuid4().hex[:8]}"
        pipeline_description = "ELITEA-2078 — pipeline flow editor add LLM node discard"
        pipeline_id = None

        # Registered before Setup so console errors from every step are
        # captured (side-channel discipline). The pre-existing secrets 403
        # noise is filtered so it can't mask a genuinely new error.
        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create a fresh pipeline via the in-chat canvas "
                "(reconstructs the case's own precondition: canvas open "
                "with Configuration/Flow editor tabs)"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)

                chat.open_create_new_pipeline_canvas(timeout=NAVIGATION_TIMEOUT)
                agent_form.fill_form(name=pipeline_name, description=pipeline_description)
                assert agent_form.get_name() == pipeline_name
                assert agent_form.get_description() == pipeline_description

                with page.expect_response(
                    lambda r: r.request.method == "POST"
                    and "/applications/prompt_lib/" in r.url
                ) as resp_info:
                    pipeline_canvas.save_button.click()
                create_response = resp_info.value
                assert create_response.status == 201, (
                    f"Pipeline-creation POST should resolve 201, got "
                    f"{create_response.status} for {create_response.url}"
                )
                created_pipeline = create_response.json()
                pipeline_id = created_pipeline.get("id")
                assert pipeline_id, (
                    f"Expected a numeric pipeline id in the creation "
                    f"response, got: {created_pipeline!r}"
                )

                expect(pipeline_canvas.flow_editor_tab).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 1-2 — Click the Flow editor tab; verify the "
                "ReactFlow grid canvas renders"
            ):
                pipeline_canvas.open_flow_editor_tab(timeout=UI_ELEMENT_TIMEOUT)
                pipeline_detail.wait_for_canvas(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Verify Flow/Yaml sub-tabs are present, Flow is "
                "active (default), and only the End node is visible"
            ):
                expect(pipeline_detail.flow_view_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_detail.yaml_view_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert pipeline_detail.get_node_count() == 1, (
                    "Only the End node should be visible before any node is added"
                )
                assert pipeline_detail.get_node_ids() == ["END"], (
                    "The sole node on a freshly-saved, empty pipeline should be END"
                )

            with allure.step("Step 4 — Click the '+ Add node' button; verify the menu opens"):
                pipeline_detail.open_add_node_menu(timeout=UI_ELEMENT_TIMEOUT)
                assert pipeline_detail.get_add_node_menu_item_count() > 0, (
                    "Add-node menu should list at least one node type once open"
                )

            with allure.step(
                "Step 5 — Verify the menu lists all 11 node types (LLM among them)"
            ):
                item_texts = pipeline_detail.get_add_node_menu_item_texts()
                assert item_texts == EXPECTED_ADD_NODE_MENU_ITEMS, (
                    f"Expected the 11 node types {EXPECTED_ADD_NODE_MENU_ITEMS}, "
                    f"got {item_texts}"
                )

            with allure.step("Step 6 — Click 'LLM' from the menu; verify the LLM node is added"):
                pipeline_detail.click_add_node_menu_item("llm", timeout=UI_ELEMENT_TIMEOUT)
                llm_node_id = pipeline_detail.wait_for_node_on_canvas(
                    "llm", timeout=UI_ELEMENT_TIMEOUT
                )
                assert pipeline_detail.get_node_count() == 2, (
                    "Canvas should now show the LLM node alongside the End node"
                )

            with allure.step(
                "Step 7 — Verify the LLM node has an icon, label, and connection ports"
            ):
                assert pipeline_detail.node_has_icon(llm_node_id), (
                    "LLM node should render an icon"
                )
                assert pipeline_detail.get_node_name(llm_node_id) == "LLM 1", (
                    "LLM node should display its label 'LLM 1'"
                )
                assert pipeline_detail.get_node_handle_count(llm_node_id) >= 2, (
                    "LLM node should render its connection-port handles"
                )

            with allure.step(
                "Step 8 — Click 'Discard' without saving; verify the "
                "Discard button transitioned to ENABLED, and the "
                "confirmation dialog appears with the expected title/body/buttons"
            ):
                assert pipeline_canvas.is_discard_enabled(), (
                    "Discard should be enabled once the unsaved LLM node exists"
                )
                pipeline_canvas.click_discard(timeout=UI_ELEMENT_TIMEOUT)
                dialog_text = pipeline_canvas.get_discard_dialog_text(timeout=UI_ELEMENT_TIMEOUT)
                assert "Warning" in dialog_text, f"Dialog should show 'Warning' title: {dialog_text!r}"
                assert "Are you sure you want to discard changes?" in dialog_text, (
                    f"Dialog should show the discard-confirmation body: {dialog_text!r}"
                )
                assert "Cancel" in dialog_text, f"Dialog should offer 'Cancel': {dialog_text!r}"
                assert "Discard" in dialog_text, f"Dialog should offer 'Discard': {dialog_text!r}"

            with allure.step(
                "Step 9 — Click 'Discard' (confirm); verify the dialog "
                "closes and the LLM node is removed"
            ):
                pipeline_canvas.confirm_discard(timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_detail.get_rf_node_locator(llm_node_id)).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 10 — Verify only the End node remains on the canvas, "
                "and both Discard and Save return to disabled (proving the "
                "revert is a genuine clean state, not merely a visual one)"
            ):
                assert pipeline_detail.get_node_count() == 1, (
                    "Only the End node should remain after discarding"
                )
                assert pipeline_detail.get_node_ids() == ["END"], (
                    "The canvas should revert to exactly the last-saved state (END only)"
                )
                assert not pipeline_canvas.is_discard_enabled(), (
                    "Discard should return to disabled after a clean revert"
                )
                assert not agent_form.is_save_enabled(), (
                    "Save should return to disabled after a clean revert "
                    "(edit-mode Save reuses the shared agent-save-button testid)"
                )

            with allure.step(
                "Side-channel check — zero NEW error-level console messages "
                "across the whole flow"
            ):
                assert not console_messages, (
                    f"Unexpected console errors: {[m.text for m in console_messages]!r}"
                )
        finally:
            with allure.step("Cleanup — delete the created pipeline via API"):
                if pipeline_id:
                    try:
                        pipeline_api.delete_pipeline(int(pipeline_id))
                        logger.info("Deleted pipeline %s", pipeline_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup failed for pipeline %s: %s", pipeline_id, exc
                        )
