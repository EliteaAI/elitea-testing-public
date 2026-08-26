"""UI Test for ELITEA-2076 — Chat: Create Pipeline from Conversation –
Discard Changes and Verify Data is Cleared.

Verifies that entering data in the in-chat "Create New Pipeline" canvas and
confirming Discard clears all entered data, re-disables the Discard button,
never fires a create request, and never adds a PIPELINES participant.

Spec: test-specs/chat-interface/l2_pipeline-discard-changes-clears-canvas_ELITEA-2076.md

New page-object surface (AFS § Automation Hints): the canvas entry point
(``ChatPage.open_create_new_pipeline_canvas()``) and Name/Description
fields (``PipelineDetailPage`` — inherited from ``PipelineFormPage``) are
the SAME testids already automated by ELITEA-2079. This case's own new
surface is the canvas's Discard button + its confirmation modal
(``PipelineCanvasPage.discard_button`` / ``discard_confirm_modal`` /
``discard_confirm_button``) — neither ELITEA-2079 (which only ever clicked
Save) nor ELITEA-2089 (whose AFS/test only asserted the sibling Agent
canvas's Discard button becomes *enabled*, never clicked it) exercised
this path.

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``, ``EliteaAI/EliteaUI@d4edc6e5``):
- ``pipeline-canvas-discard-button`` — threaded as ``PipelineEditor.jsx``'s
  ``<BaseEditor discardButtonTestId=...>`` call. The prop already existed
  end-to-end (added for ELITEA-2089's Agent-canvas Discard), just never
  supplied at the Pipeline call site.
- ``pipeline-canvas-discard-confirm-modal`` / ``pipeline-canvas-discard-confirm-button``
  — two NEW optional props (``discardModalTestId`` / ``discardConfirmButtonTestId``)
  threaded ``BaseEditor.jsx`` -> ``EditorHeader.jsx`` -> the pre-existing
  ``Button.DiscardButton`` props ``modalDataTestId`` / ``confirmButtonDataTestId``
  (already proven live by ``CredentialsTabBar.jsx``'s direct usage — only
  ``EditorHeader.jsx``'s own call never forwarded them). Supplied ONLY at
  ``PipelineEditor.jsx``'s call site — the sibling Agent/MCP chat canvases
  are unaffected since the new props are optional and caller-supplied.

Fix round 1 (review): Coverage Map step-4 claimed the canvas heading text
was asserted, but no such assertion shipped and no testid existed for the
title ``Typography``. Filled the gap the same way as the Discard testids
above — ``pipeline-canvas-title`` supplies ``EditorHeader.jsx``'s
pre-existing optional ``titleTestId`` prop (already forwarded by
``BaseEditor.jsx``; sibling canvases already supply it —
``agent-canvas-title``, ``toolkit-canvas-title``/``mcp-canvas-title``) at
``PipelineEditor.jsx``'s call site (``EliteaAI/EliteaUI@93dc5667``). Also
wrapped the trailing console-error side-channel check in its own
``allure.step`` (idiom: "Side-channel check — ...", matching
``test_invite_users_add_cancel_close.py`` et al.) — it was previously
unwrapped, violating the mandatory step-reporting rule.

No product defect found — this flow behaves exactly as the case describes.
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from pages.pipeline_canvas_page import PipelineCanvasPage
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat.pipeline_discard_changes_clears_canvas")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.pipelines, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

PIPELINE_NAME = "test-pipeline"
PIPELINE_DESCRIPTION = "This is a test pipeline for validation"

DISCARD_CONFIRM_TEXT = "Are you sure you want to discard changes?"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py``
    — an unrelated toolkit/secrets panel probe that fires on every page load
    in this local environment, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestPipelineDiscardChangesClearsCanvas:
    """ELITEA-2076: Chat – Create Pipeline from Conversation – Discard
    Changes and Verify Data is Cleared (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2076_chat-create-pipeline-from-conversation-discard-changes-and-verify-data-is-cleared.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_discard_clears_canvas_and_creates_no_pipeline(self, page, conversation_id):
        """Type Name/Description in the in-chat 'Create New Pipeline' canvas,
        click Discard, confirm the Warning dialog, and verify both fields
        clear, Discard re-disables, no create request fires, the canvas
        closes, and no PIPELINES participant is added.

        Steps (AFS
        test-specs/chat-interface/l2_pipeline-discard-changes-clears-canvas_ELITEA-2076.md):
        1. Navigate to the fixture-created conversation.
        2. Click the + icon; popup menu opens.
        3. Click Pipelines -> + Create New Pipeline; canvas opens.
        4. Verify canvas header: title + X/Discard/Save, Discard/Save disabled.
        5. Type "test-pipeline" in Name.
        6. Type the description; Discard becomes enabled.
        7. Click Discard; confirmation dialog appears.
        8. Click Discard to confirm; fields clear, Discard re-disables, zero
           create requests fired across the whole flow.
        9. Close the canvas via X.
        10. Verify no PIPELINES participant was added.
        """
        chat = ChatPage(page)
        pipeline_canvas = PipelineCanvasPage(page)
        pipeline_detail = PipelineDetailPage(page)

        console_messages = []
        create_requests = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        def _on_response(resp):
            if resp.request.method in ("POST", "PUT") and "/applications/prompt_lib/" in resp.url:
                create_requests.append(f"{resp.request.method} {resp.url}")

        page.on("console", _on_console)
        page.on("response", _on_response)

        with allure.step("Step 1 — Navigate to the fixture-created conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step('Step 2 — Click the "+" icon; popup menu opens'):
            chat.plus_menu_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            chat.plus_menu_button.click()
            expect(chat.pipelines_menuitem).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step('Step 3 — Click Pipelines -> "+ Create New Pipeline"; canvas opens'):
            chat.pipelines_menuitem.hover()
            expect(chat.pipelines_create_new_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            chat.pipelines_create_new_button.click()
            pipeline_canvas.wait_for_open(timeout=NAVIGATION_TIMEOUT)

        with allure.step(
            'Step 4 — Verify canvas header shows "Create New Pipeline" with '
            "X, Discard, and Save buttons — Discard/Save start disabled"
        ):
            expect(pipeline_canvas.title).to_have_text("Create New Pipeline", timeout=UI_ELEMENT_TIMEOUT)
            expect(pipeline_canvas.close_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(pipeline_canvas.discard_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(pipeline_canvas.discard_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)
            expect(pipeline_detail.save_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(pipeline_detail.save_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step('Step 5 — Type "test-pipeline" in the "Name *" field'):
            pipeline_detail.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            pipeline_detail.name_input.click()
            pipeline_detail.name_input.type(PIPELINE_NAME)
            expect(pipeline_detail.name_input).to_have_value(PIPELINE_NAME, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            'Step 6 — Type the description in the "Description *" field; '
            "Discard becomes enabled"
        ):
            pipeline_detail.description_input.click()
            pipeline_detail.description_input.type(PIPELINE_DESCRIPTION)
            expect(pipeline_detail.description_input).to_have_value(
                PIPELINE_DESCRIPTION, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(pipeline_canvas.discard_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step('Step 7 — Click "Discard"; confirmation dialog appears'):
            pipeline_canvas.click_discard(timeout=UI_ELEMENT_TIMEOUT)
            assert DISCARD_CONFIRM_TEXT in (pipeline_canvas.discard_confirm_modal.text_content() or ""), (
                f"Discard confirmation modal should ask "
                f"{DISCARD_CONFIRM_TEXT!r}, got: "
                f"{pipeline_canvas.discard_confirm_modal.text_content()!r}"
            )

        with allure.step(
            'Step 8 — Click "Discard" to confirm; canvas content is cleared, '
            "Discard re-disables, and zero create requests fire"
        ):
            pipeline_canvas.confirm_discard(timeout=UI_ELEMENT_TIMEOUT)
            expect(pipeline_detail.name_input).to_have_value("", timeout=UI_ELEMENT_TIMEOUT)
            expect(pipeline_detail.description_input).to_have_value("", timeout=UI_ELEMENT_TIMEOUT)
            expect(pipeline_canvas.discard_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)
            assert not create_requests, (
                f"Discard must never call the pipeline-creation endpoint, "
                f"but observed: {create_requests!r}"
            )

        with allure.step('Step 9 — Close the canvas by clicking "X"'):
            pipeline_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
            pipeline_canvas.close_button.wait_for(state="detached", timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 10 — Verify no pipeline was created in the PARTICIPANTS panel"):
            assert not chat.is_participants_badge_visible(section="pipelines", timeout=UI_ELEMENT_TIMEOUT), (
                "No PIPELINES participants badge should be present — Discard must "
                "not have created a pipeline"
            )

        with allure.step("Side-channel check — no unexpected console errors across the full flow"):
            assert not console_messages, (
                f"Unexpected console errors during the discard flow: "
                f"{[m.text for m in console_messages]}"
            )
