"""UI test — Project Context creation and update from chat with chip opening
in Canvas (ELITEA-3368).

Verifies that:
    1. Creating a Project Context via a chat message (through the
       ``project_context_builder`` chat module) surfaces a
       ``generated-entity-chip`` whose "Open entity" button opens an in-chat
       Canvas showing the AI-generated content.
    2. The newly created Project Context is NOT auto-added as a chat
       participant.
    3. A follow-up update message modifies the SAME Project Context in
       place (identical API ``id`` before/after, content now mentioning
       the new detail) rather than creating a duplicate, and the updated
       content is visible both via the API and by reopening the Canvas.

AFS: test-specs/chat-interface/l1_chat-project-context-create-update-chip-canvas_ELITEA-3368.md

Case-text clarifications (not product defects — see the AFS's Known Defects
section and ``.agents/role-overrides.md``'s reverse-masking guard):
    - The case's "Project Context Builder is enabled in Chat Modules"
      precondition is a PER-CONVERSATION toggle, not an ambient project
      setting — every new conversation starts with it OFF; this test
      enables it explicitly via the Modules submenu before sending the
      creation message (Step 1).
    - The case's step 9 "Navigate to Project Context list" does not map to
      a literal UI element — Project Context is a per-project SINGLETON
      (one GET endpoint, never a collection). The "no duplicate" check is
      implemented via a direct API GET comparing ``id`` before/after,
      matching the AFS's own implementation of that step.

Markers:
    - ui: requires browser
    - chat: Chat-surface feature
    - p0: critical priority (AFS: l1, case priority: critical)
    - regression

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_project_context_builder.py -v
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from pages.project_context_chat_canvas_page import ProjectContextChatCanvasPage
from pages.project_context_page import ProjectContextPage

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.p0,
    pytest.mark.regression,
    pytest.mark.new,
]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000   # tool invocation + generation observed 9-20s live

CREATE_MESSAGE = (
    "Create project context: This project is a Python REST API for order "
    "management."
)
UPDATE_MESSAGE = (
    "Update the project context to mention we now support GraphQL in "
    "addition to REST."
)

PROJECT_CONTEXT_ENTITY_LABEL = "Project Context"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/chat/build-skills-project-context/"
    "ELITEA-3368_chat-project-context-create-update-chip-canvas.md",
    "onetest-ai Test Case link (ELITEA-3368)",
)
@pytest.mark.tms("ELITEA-3368")
class TestChatProjectContextBuilder:
    """ELITEA-3368 — Project Context created/updated via chat, with the
    chip's 'Open entity' button opening an in-chat Canvas, and the update
    modifying the existing entity in place (no duplicate)."""

    @allure.title(
        "Chat Project Context builder: create via chip+Canvas, not a participant, "
        "update modifies in place"
    )
    def test_create_and_update_project_context_via_chat_chip_canvas(
        self, page, conversation_id, clean_project_context, project_context_api,
    ):
        chat = ChatPage(page)
        console_errors = chat.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Open a fresh conversation, enable the Project Context "
                "Builder module for it via the Modules submenu"
            ):
                chat.navigate_to_chat(conversation_id=conversation_id)
                chat.open_internal_tools_menu(timeout=NAVIGATION_TIMEOUT)
                chat.ensure_module_toggle_checked(
                    "project_context_builder", timeout=UI_ELEMENT_TIMEOUT
                )
                assert chat.is_module_toggle_checked("project_context_builder"), (
                    "Expected the Project Context Builder module toggle to be "
                    "checked before sending the creation message"
                )
                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Send the creation message; assistant proceeds without "
                "a clarifying question"
            ):
                initial_count = chat.get_message_count()
                chat.send_message(CREATE_MESSAGE, use_enter=True)
                chat.wait_for_ai_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT
                )
                response_text = chat.get_message_text_at(initial_count + 1)
                assert "?" not in response_text, (
                    f"Expected a direct creation response with no clarifying "
                    f"question, got: {response_text!r}"
                )

            with allure.step(
                "Step 3 — Verify a tool-invocation chip for the Project Context "
                "generate tool, and a generated-entity-chip labeled "
                "'Project Context' in the response"
            ):
                tool_chips = chat.answer_tool_chip
                chip_texts = [
                    tool_chips.nth(i).text_content() or "" for i in range(tool_chips.count())
                ]
                assert any(
                    "Elitea Project Context" in t
                    and "generate_project_context_draft" in t
                    for t in chip_texts
                ), (
                    f"Expected a tool-invocation chip naming the Project Context "
                    f"generate tool, got chip texts: {chip_texts!r}"
                )

                chat.generated_entity_chip.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )
                chip_label = (chat.generated_entity_chip.text_content() or "").strip()
                assert PROJECT_CONTEXT_ENTITY_LABEL in chip_label, (
                    f"Expected the generated-entity-chip to be labeled "
                    f"'{PROJECT_CONTEXT_ENTITY_LABEL}', got {chip_label!r}"
                )

            with allure.step(
                "Step 4 — Hover the chip, click 'Open entity' — Canvas opens on "
                "the right showing 'Project Context'"
            ):
                chat.open_generated_entity_chip(
                    entity_label=PROJECT_CONTEXT_ENTITY_LABEL, timeout=UI_ELEMENT_TIMEOUT
                )
                canvas = ProjectContextChatCanvasPage(page)
                canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                context_page = ProjectContextPage(page)
                context_page.editor_content.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 5 — Verify the Canvas content is non-empty and topically "
                "consistent with the prompt (AI phrasing is non-deterministic — "
                "assert substance, not an exact string match)"
            ):
                editor_text = context_page.editor_content.text_content() or ""
                assert editor_text.strip(), (
                    "Expected the Canvas editor to show non-empty generated content"
                )
                lowered = editor_text.lower()
                assert any(kw in lowered for kw in ("python", "rest", "order")), (
                    f"Expected the generated content to be topically consistent "
                    f"with the prompt (mentioning python/rest/order), got: "
                    f"{editor_text[:200]!r}"
                )

                get_resp_after_create = project_context_api.get_project_context()
                assert get_resp_after_create.status_code == 200, (
                    f"Expected GET project-context to return 200 after creation, "
                    f"got {get_resp_after_create.status_code}"
                )
                created_body = get_resp_after_create.json()
                created_id = created_body.get("id")
                assert created_id is not None, (
                    f"Expected a non-null id after creation, got body: {created_body}"
                )

            with allure.step(
                "Step 6 — Open the Participants panel — the created Project "
                "Context is NOT auto-added as a participant"
            ):
                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
                participant_row_count = chat.get_participant_row_count()
                assert participant_row_count == 0, (
                    f"Expected zero participant rows after Project Context "
                    f"creation, found {participant_row_count}"
                )

            with allure.step(
                "Step 7 — Close the Canvas, send the update message; assistant "
                "updates the existing Project Context (no clarifying question)"
            ):
                canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                update_initial_count = chat.get_message_count()
                chat.send_message(UPDATE_MESSAGE, use_enter=True)
                chat.wait_for_ai_response(
                    initial_count=update_initial_count, timeout=AI_RESPONSE_TIMEOUT
                )
                update_response_text = chat.get_message_text_at(update_initial_count + 1)
                assert "?" not in update_response_text, (
                    f"Expected a direct update response with no clarifying "
                    f"question, got: {update_response_text!r}"
                )

            with allure.step(
                "Step 8 — Verify the read-then-write tool-chip pair for the "
                "update path, and a generated-entity-chip in the new answer"
            ):
                update_tool_chips = chat.answer_tool_chip
                update_chip_texts = [
                    update_tool_chips.nth(i).text_content() or ""
                    for i in range(update_tool_chips.count())
                ]
                assert any(
                    "Elitea Project Context" in t and "get_project_context" in t
                    for t in update_chip_texts
                ), (
                    f"Expected a tool-invocation chip for the Project Context "
                    f"GET call on the update path, got chip texts: "
                    f"{update_chip_texts!r}"
                )
                assert any(
                    "Elitea Project Context" in t and "put_project_context" in t
                    for t in update_chip_texts
                ), (
                    f"Expected a tool-invocation chip for the Project Context "
                    f"PUT call on the update path, got chip texts: "
                    f"{update_chip_texts!r}"
                )

                updated_chip = chat.generated_entity_chip.last
                updated_chip.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                updated_chip_label = (updated_chip.text_content() or "").strip()
                assert PROJECT_CONTEXT_ENTITY_LABEL in updated_chip_label, (
                    f"Expected the update response's generated-entity-chip to be "
                    f"labeled '{PROJECT_CONTEXT_ENTITY_LABEL}', got "
                    f"{updated_chip_label!r}"
                )

            with allure.step(
                "Step 9 — Verify via API: same id as after creation (no duplicate), "
                "content now mentions GraphQL — then reopen the Canvas and confirm "
                "the UI reflects the same update"
            ):
                get_resp_after_update = project_context_api.get_project_context()
                assert get_resp_after_update.status_code == 200, (
                    f"Expected GET project-context to return 200 after update, "
                    f"got {get_resp_after_update.status_code}"
                )
                updated_body = get_resp_after_update.json()
                assert updated_body.get("id") == created_id, (
                    f"Expected the Project Context id to stay identical across "
                    f"the update (no duplicate created): before={created_id}, "
                    f"after={updated_body.get('id')}"
                )
                updated_content = updated_body.get("content") or ""
                assert "graphql" in updated_content.lower(), (
                    f"Expected the updated content to mention GraphQL, got: "
                    f"{updated_content[:200]!r}"
                )

                chat.open_generated_entity_chip(
                    entity_label=PROJECT_CONTEXT_ENTITY_LABEL, timeout=UI_ELEMENT_TIMEOUT
                )
                canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                context_page.editor_content.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )
                reopened_text = (context_page.editor_content.text_content() or "").lower()
                assert "graphql" in reopened_text, (
                    f"Expected the reopened Canvas content to mention GraphQL, "
                    f"got: {reopened_text[:200]!r}"
                )

            with allure.step("Side-channel check — no console errors at any step"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
