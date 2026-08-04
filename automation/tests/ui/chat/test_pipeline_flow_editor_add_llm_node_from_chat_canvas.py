"""UI Test for ELITEA-2079 — Chat: Pipeline Flow Editor – Add LLM Node,
Verify YAML, Save Pipeline, and Add to Conversation.

Verifies the full "add an LLM node to the in-chat pipeline canvas's Flow
Editor" flow: creating the pipeline via the in-chat "+ Create New Pipeline"
canvas (this case's own precondition, replicated live per AFS §
Preconditions — ELITEA-2077/2078 are not yet automated in this batch),
adding an LLM node, verifying its generated YAML, switching back to the
Flow view, saving, closing the canvas, and confirming the pipeline is added
as a PIPELINES participant that responds to a message.

Spec: test-specs/chat-interface/l2_pipeline-flow-editor-add-llm-node-save-and-participant_ELITEA-2079.md

New page-object surface (AFS § Automation Hints): the Flow Editor / YAML /
add-node surface inside the chat canvas is the exact same ``EditorPanel``
component ``PipelineDetailPage`` already drives standalone (confirmed via
source: ``PipelineEditor.jsx`` imports
``@/pages/Pipelines/Components/EditorPanel``) — so ``PipelineDetailPage``
is composed directly on the same ``page`` alongside ``ChatPage`` (canvas
entry point, chip, participants) and the new ``PipelineCanvasPage`` (close
button, post-save Configuration/Flow-editor tab bar), mirroring
``test_create_agent_via_chat_canvas.py``'s ``ChatPage`` + ``AgentFormPage``
composition.

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``):
- ``agent-save-button`` on ``PipelineEditor.jsx``'s create-mode
  ``<CreateApplicationSaveButton>`` call site — the SAME testid
  ELITEA-2166 added only at ``AgentEditor.jsx``'s call site; this case's
  own precondition setup exercises the Pipeline-create Save button for the
  first time, so the same literal value is wired at this second call site
  too (component-sharing guard is per-caller opt-in, not a ban — canon
  ruling #511's touched-scope discipline: THIS case now touches this call
  site). Matches the pre-existing edit-mode naming quirk already tracked
  as issue #1040 (``agent-save-button`` on ``SaveApplicationButton.jsx``,
  shared unconditionally across Agent/Pipeline/Toolkit edit-mode canvases)
  rather than introducing a third, differently-named button for the same
  create-mode component.
- ``pipeline-canvas-close-button`` — threaded as
  ``PipelineEditor.jsx``'s ``<BaseEditor closeButtonTestId=...>`` call
  (the prop already exists end-to-end, same as ``agent-canvas-close-button``
  added for ELITEA-2166).
- ``pipeline-canvas-tab-configuration`` / ``pipeline-canvas-tab-flow`` — the
  post-save canvas's own Configuration/Flow-editor Tab elements (AFS
  Concrete Handles flagged this as a low-priority, non-blocking gap; added
  since it was cheap and keeps the setup's tab switch testid-only rather
  than falling back to a role-based lookup).

Known defect handling (step 11, issue #1039): a bare LLM node — added via
"+ Add Node" with zero further configuration, exactly matching this case's
own literal steps (System/Task/Chat History left at their defaults) — does
NOT generate a response when used as a chat participant; the backend
errors instead (confirmed live during this implementation: the composer
stays stuck on "Fetching keys & creds…" past a 60s wait, matching the
already-filed #1039 repro — filed by a prior session working this exact
case, describing the same defect surfacing as a rendered 400 error in the
transcript). Automated via the pytest-native ``soft_failures``/
``pytest.fail()`` idiom (mirrors ``test_create_agent_via_chat_canvas.py``'s
#708 handling) rather than ``expect.soft()`` directly, since the observable
(``wait_for_ai_response()`` raising ``TimeoutError``) isn't a bare Locator/
Page/APIResponse assertion. The user-message-appears and
no-new-console-errors-on-send assertions stay HARD — only the response-
generation itself is soft-asserted. Steps 1-10 (LLM node add, YAML verify,
Save, canvas close, composer chip, PARTICIPANTS listing) are fully clean and
unaffected.

Step 11's send-message uses the ``conversation_id`` API fixture +
``navigate_to_chat(conversation_id=...)`` pattern (AFS Automation Hint)
rather than a raw ``+Chat`` sidebar click, to sidestep the known,
already-tracked issue #1085 composer-covered-by-loading-overlay class of
flake when driving a brand-new, ID-less conversation.

Shared page-object fix (ELITEA-2079, ``pipeline_detail_page.py``): the
``PipelineDetailPage.get_yaml_content()`` shared method used to silently
fall back to a broken, gutter-number-interleaved raw ``text_content()``
read whenever ``yaml_lines``'s ``pipeline-yaml-lines`` testid resolved zero
elements — which it always does; that testid was never actually added to
EliteaUI. Both existing merged callers (``test_pipeline_advanced.py``,
``test_pipeline_yaml_flow_sync.py``) only ever did substring/count checks
on the return value, so the defect went uncaught. Fixed to read through a
scoped ``.cm-line`` selector (sanctioned #579 third-party-editor-internal-
render-node exception, same shape already used by ``edit_yaml_line()``)
instead — re-ran both existing callers locally after the fix, both still
GREEN.
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from config import settings
from pages.chat_page import ChatPage
from pages.pipeline_canvas_page import PipelineCanvasPage
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger("elitea.tests.chat.pipeline_flow_editor_canvas")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.pipelines, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
CANVAS_TIMEOUT = 30_000  # ReactFlow's FlowWrapper is lazy-loaded (React.lazy/Suspense)
AI_RESPONSE_TIMEOUT = 60_000  # real (non-mocked) LLM call through a pipeline node

PIPELINE_NAME = "test-pipeline"
PIPELINE_DESCRIPTION = "A test pipeline for conversation"
TEST_MESSAGE = "hello"

# Case's own confirmed-live YAML content (AFS step 4/5) — exact text as
# extracted by PipelineDetailPage.get_yaml_content() (.cm-line based, not a
# naive inner_text() which would interleave CodeMirror's gutter line-numbers
# — AFS Axis 2).
EXPECTED_YAML_CONTENT = """entry_point: LLM 1
nodes:
  - id: LLM 1
    type: llm
    input: []
    input_mapping:
      chat_history:
        type: fixed
        value: []
      system:
        type: fixed
        value: ''
      task:
        type: fixed
        value: ''
    output: []
    structured_output: false
    transition: END"""


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_create_agent_via_chat_canvas.py`` — an unrelated
    toolkit/secrets panel probe that fires on every page load in this
    local environment, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestPipelineFlowEditorAddLlmNodeFromChatCanvas:
    """ELITEA-2079: Chat – Pipeline Flow Editor – Add LLM Node, Verify YAML,
    Save Pipeline, and Add to Conversation (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2079_chat-pipeline-flow-editor-add-llm-node-verify-yaml-save-pipeline-and-add-to-conversation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_add_llm_node_save_pipeline_and_verify_participant(
        self, page, conversation_id, pipeline_api,
    ):
        """Create a pipeline via the in-chat canvas, add an LLM node,
        verify its YAML, save, close the canvas, and verify the pipeline
        is added as a PIPELINES participant that responds to a message.

        Steps (AFS
        test-specs/chat-interface/l2_pipeline-flow-editor-add-llm-node-save-and-participant_ELITEA-2079.md):
        Setup (not a numbered case step — AFS § Preconditions live
        replication): open the fixture-created conversation, + menu ->
        Pipelines -> + Create New Pipeline, fill Name/Description, Save
        (create-mode), switch to the Flow editor tab.
        1. Verify the Flow Editor is open with only the End node visible
           and the Flow sub-tab active.
        2. Add an LLM node.
        3. Click the Yaml tab.
        4-5. Verify the YAML content.
        6. Click back on the Flow tab.
        7. Click Save; verify the update PUT resolves 201 and a success toast.
        8. Close the canvas; verify it's gone.
        9. Verify the composer chip shows "test-pipeline base" (no "Editing…").
        10. Verify the PIPELINES participant row.
        11. Send "hello"; verify the pipeline responds.
        """
        chat = ChatPage(page)
        pipeline_canvas = PipelineCanvasPage(page)
        pipeline_detail = PipelineDetailPage(page)

        pipeline_id = None
        soft_failures: list[str] = []

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — open the fixture-created conversation; + menu -> "
                "Pipelines -> + Create New Pipeline; fill Name/Description; "
                "Save (create-mode); switch to the Flow editor tab"
            ):
                chat.navigate_to_chat(conversation_id=conversation_id)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                chat.open_create_new_pipeline_canvas(timeout=NAVIGATION_TIMEOUT)
                pipeline_detail.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                pipeline_detail.fill_form(name=PIPELINE_NAME, description=PIPELINE_DESCRIPTION)

                with page.expect_response(
                    lambda r: r.request.method in ("POST", "PUT")
                    and "/applications/prompt_lib/" in r.url
                ) as create_resp_info:
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

                pipeline_canvas.click_flow_editor_tab(timeout=UI_ELEMENT_TIMEOUT)
                pipeline_detail.wait_for_canvas(timeout=CANVAS_TIMEOUT)

            with allure.step(
                "Step 1 — Verify the Flow Editor is open with only the "
                "'End' node visible and the Flow sub-tab active"
            ):
                assert pipeline_detail.get_node_count() == 1, (
                    "Freshly-opened Flow Editor should show exactly 1 node (End)"
                )
                assert pipeline_detail.get_node_ids() == ["END"], (
                    f"The single node should be the End node, got: "
                    f"{pipeline_detail.get_node_ids()!r}"
                )
                assert pipeline_detail.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
                    "Flow (visual) sub-view should be active by default"
                )

            with allure.step('Step 2 — Click "+ Add node" and select "LLM"'):
                pipeline_detail.add_node("LLM")
                pipeline_detail.wait_for_node_on_canvas("LLM", timeout=UI_ELEMENT_TIMEOUT)
                assert pipeline_detail.get_node_count() == 2, (
                    "Node count should become 2 after adding the LLM node"
                )

            with allure.step('Step 3 — Click the "Yaml" tab; verify the YAML editor opens'):
                pipeline_detail.switch_to_yaml_view()
                expect(pipeline_detail.yaml_editor).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Steps 4-5 — Verify the YAML content: lines 1-4, and "
                "input_mapping/task/structured_output/transition"
            ):
                yaml_content = pipeline_detail.get_yaml_content().strip()
                assert yaml_content == EXPECTED_YAML_CONTENT, (
                    f"YAML content mismatch.\nExpected:\n{EXPECTED_YAML_CONTENT}\n\n"
                    f"Got:\n{yaml_content}"
                )
                for expected_fragment in (
                    "input_mapping", "task", "structured_output: false", "transition: END",
                ):
                    assert expected_fragment in yaml_content, (
                        f"YAML should include {expected_fragment!r}"
                    )

            with allure.step(
                "Step 6 — Click back on the Flow tab; verify the visual "
                "editor is shown and the LLM node is still present"
            ):
                pipeline_detail.switch_to_flow_view()
                assert pipeline_detail.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
                    "Flow view should be active again after switching back"
                )
                assert pipeline_detail.get_node_count() == 2, (
                    "LLM node should still be present after switching views"
                )

            with allure.step(
                'Step 7 — Click "Save"; verify the update request resolves '
                "201 and a success toast appears"
            ):
                with page.expect_response(
                    lambda r: r.request.method == "PUT"
                    and "/application/prompt_lib/" in r.url
                    and str(pipeline_id) in r.url
                ) as save_resp_info:
                    pipeline_detail.save_button.click()
                save_response = save_resp_info.value
                assert save_response.status == 201, (
                    f"Pipeline-update PUT should resolve 201, got "
                    f"{save_response.status} for {save_response.url}"
                )
                expect(chat.toast_message).to_contain_text(
                    "The pipeline has been updated", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 8 — Click the X button to close the canvas panel"):
                pipeline_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_canvas.close_button).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_detail.yaml_view_button).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 9 — Verify the composer chip shows "test-pipeline '
                'base" without an "Editing..." status'
            ):
                # The name and version render as two adjacent chip elements
                # (confirmed live), not one concatenated string — mirrors
                # ELITEA-2166's switch_participant_button/
                # chat_version_selector_trigger split.
                switch_participant_text = chat.switch_participant_button.text_content() or ""
                assert PIPELINE_NAME in switch_participant_text, (
                    f"Composer chip should contain {PIPELINE_NAME!r}, got: "
                    f"{switch_participant_text!r}"
                )

                version_text = chat.chat_version_selector_trigger.text_content() or ""
                assert version_text.strip() == "base", (
                    f"Composer version chip should read 'base' once the "
                    f"canvas is closed, got: {version_text!r}"
                )
                assert "Editing" not in version_text, (
                    f"Composer version chip should NOT show an "
                    f"'Editing...' status once the canvas is closed, got: "
                    f"{version_text!r}"
                )

            with allure.step(
                'Step 10 — Verify a "PIPELINES" section appears in the '
                'PARTICIPANTS panel with "test-pipeline base" listed'
            ):
                popper = chat.open_participants_popover(
                    timeout=UI_ELEMENT_TIMEOUT, section="pipelines"
                )
                # Live DOM text is "Pipelines" (CSS text-transform renders it
                # visually all-caps, matching the case's "PIPELINES" wording
                # cosmetically, not literally) — asserting the live text per
                # the reverse-masking guard rather than the case's literal casing.
                expect(popper).to_contain_text("Pipelines", timeout=UI_ELEMENT_TIMEOUT)
                expect(popper).to_contain_text(PIPELINE_NAME, timeout=UI_ELEMENT_TIMEOUT)
                expect(popper).to_contain_text("base", timeout=UI_ELEMENT_TIMEOUT)

                unique_id = f"pipeline_{pipeline_id}_{settings.elitea_project_id}"
                row = popper.locator(chat.PARTICIPANT_ROW.format(unique_id))
                expect(row).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                chat.dismiss_participants_popover()

            with allure.step(
                'Step 11 — Send "hello"; verify it appears and the '
                "pipeline (through its LLM node) generates a response"
            ):
                baseline_error_count = len(console_messages)
                initial_count = chat.get_message_count()
                chat.send_message(TEST_MESSAGE)

                expect(chat.messages_container.nth(initial_count)).to_contain_text(
                    TEST_MESSAGE, timeout=UI_ELEMENT_TIMEOUT
                )

                send_time_new_errors = [
                    m.text for m in console_messages[baseline_error_count:]
                ]
                assert not send_time_new_errors, (
                    f"Unexpected console errors on the send action itself: "
                    f"{send_time_new_errors!r}"
                )

                try:
                    chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                    new_count = chat.get_message_count()
                    assert new_count > initial_count, (
                        f"Expected the pipeline's response to add a new "
                        f"message: {initial_count} -> {new_count}"
                    )
                except TimeoutError as exc:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1039: "
                        "a bare LLM node (added via + Add Node with zero further config, matching "
                        "this case's own literal steps) errors instead of responding when used as a "
                        f"chat participant: {exc}"
                    )

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known isolated product "
                    "defect, not test/infrastructure — steps 1-10 above "
                    "passed cleanly):\n" + "\n".join(soft_failures)
                )
        finally:
            with allure.step("Cleanup — delete the created pipeline"):
                # conversation_id fixture handles conversation cleanup —
                # the pipeline is an independent entity that does NOT
                # cascade-delete from conversation deletion (AFS § Cleanup).
                if pipeline_id:
                    try:
                        pipeline_api.delete_pipeline(pipeline_id)
                        logger.info("Deleted pipeline %s", pipeline_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup failed for pipeline %s: %s", pipeline_id, exc
                        )
