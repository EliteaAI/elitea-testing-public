"""UI Test for ELITEA-2077 — Chat: Create Pipeline from Conversation – Save
Basic Configuration and Verify Pipeline is Created.

Verifies that filling in the pipeline Name and Description in the in-chat
"Create New Pipeline" canvas and clicking Save creates the pipeline,
transitions the canvas to edit mode with Configuration/Flow Editor tabs,
and adds the pipeline chip to the message input area — all while the
canvas remains OPEN (unlike the sibling ELITEA-2079 spec, which asserts
the composer chip AFTER closing the canvas).

Spec: test-specs/chat-interface/l2_pipeline-create-save-basic-configuration_ELITEA-2077.md

New page-object surface (AFS § Automation Hints): reuses ``ChatPage``
(canvas entry point, composer chip elements) + ``PipelineCanvasPage``
(canvas chrome) + ``PipelineDetailPage`` (Name/Description/Save/Step-limit
fields, inherited via ``PipelineFormPage``) on the SAME ``page`` — the
identical composition pattern ``test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py``
(ELITEA-2079) and ``test_pipeline_discard_changes_clears_canvas.py``
(ELITEA-2076) already use.

Testid gap filled this implementation (``add-data-testid``, pushed to
``automation/testids``, ``EliteaAI/EliteaUI@7b1e2c5a``):
- ``pipeline-canvas-subtitle`` — the LAST remaining gap in the four-way
  canvas-chrome testid family (title/close/discard were filled by
  ELITEA-2076/2079). ``BaseEditor``/``EditorHeader`` already supported an
  optional ``subtitleTestId`` prop end-to-end (same shape as
  ``titleTestId``, already supplied by ``AgentEditor.jsx`` as
  ``agent-canvas-subtitle``) — ``PipelineEditor.jsx``'s own
  ``<BaseEditor>`` call simply never passed a value. Added
  ``subtitleTestId="pipeline-canvas-subtitle"`` at that one call site.
  New ``PipelineCanvasPage.subtitle`` field.

No product defect found — this flow behaves exactly as the case describes.
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from pages.pipeline_canvas_page import PipelineCanvasPage
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat.pipeline_create_save_basic_configuration")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.pipelines, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

PIPELINE_NAME = "test-pipeline"
PIPELINE_DESCRIPTION = "A test pipeline for conversation"
EXPECTED_STEP_LIMIT = "25"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as the sibling pipeline-canvas specs (ELITEA-2076/2079) — an
    unrelated toolkit/secrets panel probe that fires on every page load in
    this local environment, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestPipelineCreateSaveBasicConfiguration:
    """ELITEA-2077: Chat – Create Pipeline from Conversation – Save Basic
    Configuration and Verify Pipeline is Created (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2077_chat-create-pipeline-from-conversation-save-basic-configuration-and-verify-pipeline-is-created.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_create_pipeline_save_basic_configuration(
        self, page, conversation_id, pipeline_api,
    ):
        """Fill Name/Description in the in-chat 'Create New Pipeline'
        canvas, click Save, and verify the pipeline is created: canvas
        header shows name + 'base' version, Configuration/Flow Editor tabs
        appear, and the composer chip shows name/version/'Editing...'.

        Steps (AFS
        test-specs/chat-interface/l2_pipeline-create-save-basic-configuration_ELITEA-2077.md):
        1. Navigate to Chats and open a conversation.
        2. Click + icon, select Pipelines, click + Create New Pipeline.
        3. Type "test-pipeline" in the Name field.
        4. Type the description in the Description field.
        5. Verify the ADVANCED section (Step limit "25" + model chip).
        6. Click Save; verify the create request resolves 201.
        7. Verify the canvas header shows "test-pipeline" + "base".
        8. Verify Configuration (active) + Flow Editor tabs.
        9. Verify the composer chip's 3-way split (name/version/"Editing...").
        """
        chat = ChatPage(page)
        pipeline_canvas = PipelineCanvasPage(page)
        pipeline_detail = PipelineDetailPage(page)

        pipeline_id = None
        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Step 1 — Navigate to Chats and open a conversation"):
                chat.navigate_to_chat(conversation_id=conversation_id)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 2 — Click the "+" icon, select "Pipelines", click '
                '"+ Create New Pipeline"; canvas opens'
            ):
                chat.open_create_new_pipeline_canvas(timeout=NAVIGATION_TIMEOUT)
                expect(pipeline_canvas.title).to_have_text("Create New Pipeline", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step('Step 3 — Type "test-pipeline" in the "Name *" field'):
                pipeline_detail.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                pipeline_detail.name_input.click()
                pipeline_detail.name_input.type(PIPELINE_NAME)
                expect(pipeline_detail.name_input).to_have_value(PIPELINE_NAME, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 4 — Type the description in the "Description *" field'
            ):
                pipeline_detail.description_input.click()
                pipeline_detail.description_input.type(PIPELINE_DESCRIPTION)
                expect(pipeline_detail.description_input).to_have_value(
                    PIPELINE_DESCRIPTION, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                'Step 5 — Verify the ADVANCED section shows "Step limit" '
                'with value "25" and a model chip'
            ):
                expect(pipeline_detail.step_limit_input).to_have_value(
                    EXPECTED_STEP_LIMIT, timeout=UI_ELEMENT_TIMEOUT
                )
                # Two "model-selector-name" elements render while the canvas
                # is open: the composer's own (always present) and the
                # canvas form's own copy inside the ADVANCED-section area
                # (confirmed live, AFS § Concrete Handles). `.last` is the
                # canvas's own copy in DOM order — asserted non-empty rather
                # than a hardcoded model name, which is environment-dependent
                # (`.agents/testing.md` § Known issues).
                canvas_model_chip = chat.model_selector_name.last
                expect(canvas_model_chip).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                model_chip_text = (canvas_model_chip.text_content() or "").strip()
                assert model_chip_text, "Advanced section's model chip should show a non-empty model name"

            with allure.step('Step 6 — Click "Save"; verify the create request resolves 201'):
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

            with allure.step(
                'Step 7 — Verify the canvas header now shows "test-pipeline" '
                'with "base" version tag'
            ):
                expect(pipeline_canvas.title).to_have_text(PIPELINE_NAME, timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_canvas.subtitle).to_have_text("base", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 8 — Verify "Configuration" (active) and "Flow Editor" '
                "tabs both appear"
            ):
                expect(pipeline_canvas.configuration_tab).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(pipeline_canvas.configuration_tab).to_have_attribute(
                    "aria-selected", "true", timeout=UI_ELEMENT_TIMEOUT
                )
                expect(pipeline_canvas.flow_editor_tab).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 9 — Verify the composer chip shows "test-pipeline", '
                '"base" version, and "Editing..." status'
            ):
                # Three SEPARATE composer elements (confirmed live, AFS §
                # Concrete Handles) — "Editing..." lives on a third sibling
                # button, not appended to either the name or version chip.
                switch_participant_text = (chat.switch_participant_button.text_content() or "").strip()
                assert switch_participant_text == PIPELINE_NAME, (
                    f"Composer name chip should read {PIPELINE_NAME!r}, "
                    f"got: {switch_participant_text!r}"
                )

                version_text = (chat.chat_version_selector_trigger.text_content() or "").strip()
                assert version_text == "base", (
                    f"Composer version chip should read 'base', got: {version_text!r}"
                )

                settings_text = (chat.chat_participant_settings_button.text_content() or "").strip()
                assert settings_text == "Editing...", (
                    f"Composer settings button should show the 'Editing...' "
                    f"status while the canvas is still open, got: {settings_text!r}"
                )

            with allure.step("Side-channel check — no unexpected console errors across the full flow"):
                assert not console_messages, (
                    f"Unexpected console errors during the create-pipeline flow: "
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
