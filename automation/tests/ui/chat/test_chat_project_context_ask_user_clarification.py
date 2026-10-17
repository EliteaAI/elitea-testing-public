"""UI test — Project Context creation with missing information triggers Ask
User clarification (ELITEA-3369).

Verifies that an ambiguous Project Context creation request (with both the
``project_context_builder`` AND ``ask_user`` chat modules enabled) pauses on
the ``ClarifyingQuestionControl`` HITL card instead of guessing, that the
card is answered to completion regardless of how many questions it asks
(see the non-determinism note below), that it never reappears after the
final answer, and that the resulting Project Context's content reflects the
submitted background answer — confirmed both via a direct API GET and by
reopening the in-chat Canvas.

AFS: test-specs/chat-interface/l1_project-context-ambiguous-request-ask-user-clarification_ELITEA-3369.md

Case-text clarifications (not product defects — see the AFS's Known Defects
section and ``.agents/role-overrides.md``'s reverse-masking guard):
    - The case's "Ask User is enabled in Chat Modules" precondition is a
      PER-CONVERSATION toggle, not an ambient project setting (same
      mechanism ELITEA-3368 already documented for
      ``project_context_builder``) — this test enables BOTH toggles
      explicitly before sending the ambiguous message (Step 1). Omitting
      ``ask_user`` causes the assistant to silently degrade to a plain text
      follow-up question instead of the structured clarifying card.
    - The live clarifying card's question set does not match the case's
      named scope-option list ("current project only / all conversations /
      specific Agent or Pipeline") — this test asserts the LIVE contract
      (a card that asks for missing information and uses the answer) rather
      than the stale case-text wording — the feature's own intent is fully
      met.
    - **Non-determinism found during implementation is WIDER than the
      AFS's own findings** (8+ live runs of the identical ambiguous message
      + identical Q1 answer, this session): not only does the question
      COUNT vary (roughly half the runs resolve after Q1 alone, matching
      AFS Known Defects #3), but on a 2-question run the SECOND question's
      content/options ALSO vary — observed as a "when to load"
      Always/When-relevant select in some runs, and as an entirely
      different "Activation"/"Setup Mode" question with 2-3 differently
      worded options (including a "Custom instruction" free-text branch)
      in others. The AFS's claim that the Q2 option labels are "stable
      verbatim across all 3 runs" did not hold up over a larger sample.
      Rather than special-case option text, this test answers EVERY
      question (1..N, whatever N turns out to be) via the card's own
      always-present free-text input — never a hardcoded option label —
      which the component's own source
      (``ClarifyingQuestionControl.jsx``) accepts as a valid answer to any
      question, select or free-text alike. The AFS and the chat-interface
      surface digest have been amended with this finding in the same
      commit as this test.

Markers:
    - ui: requires browser
    - chat: Chat-surface feature
    - p0: critical priority (AFS: l1, case priority: critical)
    - regression

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_project_context_ask_user_clarification.py -v
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
CLARIFYING_CARD_TIMEOUT = 45_000  # first ask_user pause observed live at 15-25s,
# occasionally longer (implementer exploration this session saw one 30s+
# miss) — widened past the AFS's own 15-25s estimate; the project's
# `--only-rerun="TimeoutError"` global rerun policy (pytest.ini) is the
# second line of defense for genuine transient misses past this margin.
AI_RESPONSE_TIMEOUT = 60_000  # final generate-and-save round trip observed 15-20s live

AMBIGUOUS_MESSAGE = "Set up project context for this."
Q1_BACKGROUND_ANSWER = "This project is a Python REST API for order management."
# Free-text answer for any FOLLOW-UP question beyond Q1 — the card's own
# custom-text input accepts a free-text answer for a select-type question
# too (ClarifyingQuestionControl.jsx's handleCustomChange clears any radio
# selection and the typed text becomes the submitted value instead), which
# sidesteps the Q2 content/option-set non-determinism documented in this
# module's docstring without weakening what the test proves (the card is
# still answered to completion and the submitted text still has to show up
# in the created content for the test to pass).
FOLLOWUP_ANSWER = "When relevant, for this project."
MAX_QUESTIONS = 5  # generous ceiling — observed live max this session was 2

PROJECT_CONTEXT_ENTITY_LABEL = "Project Context"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/chat/build-skills-project-context/"
    "ELITEA-3369_project-context-with-ask-user-clarification.md",
    "onetest-ai Test Case link (ELITEA-3369)",
)
@pytest.mark.tms("ELITEA-3369")
class TestChatProjectContextAskUserClarification:
    """ELITEA-3369 — an ambiguous Project Context request triggers the
    Ask User clarifying-question card; submitted answers determine the
    resulting Project Context's content; the card never reappears."""

    @allure.title(
        "Project Context: ambiguous request triggers Ask User clarification, "
        "answers determine content"
    )
    def test_ambiguous_project_context_request_triggers_ask_user_clarification(
        self, page, conversation_id, clean_project_context, project_context_api,
    ):
        chat = ChatPage(page)
        console_errors = chat.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Open a fresh conversation, enable BOTH the Project "
                "Context Builder AND Ask User modules via the Modules submenu"
            ):
                chat.navigate_to_chat(conversation_id=conversation_id)
                chat.open_internal_tools_menu(timeout=NAVIGATION_TIMEOUT)
                chat.ensure_module_toggle_checked(
                    "project_context_builder", timeout=UI_ELEMENT_TIMEOUT
                )
                chat.ensure_module_toggle_checked(
                    "ask_user", timeout=UI_ELEMENT_TIMEOUT
                )
                assert chat.is_module_toggle_checked("project_context_builder"), (
                    "Expected the Project Context Builder module toggle to be "
                    "checked before sending the ambiguous message"
                )
                assert chat.is_module_toggle_checked("ask_user"), (
                    "Expected the Ask User module toggle to be checked before "
                    "sending the ambiguous message"
                )
                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Send the ambiguous request; the assistant pauses on "
                "a clarifying-question card instead of creating directly"
            ):
                initial_count = chat.get_message_count()
                chat.send_message(AMBIGUOUS_MESSAGE, use_enter=True)
                chat.wait_for_clarifying_question_card(timeout=CLARIFYING_CARD_TIMEOUT)

                tool_chips = chat.answer_tool_chip
                chip_texts = [
                    tool_chips.nth(i).text_content() or "" for i in range(tool_chips.count())
                ]
                assert any("Ask User" in t for t in chip_texts), (
                    f"Expected a tool-invocation chip naming the Ask User tool, "
                    f"got chip texts: {chip_texts!r}"
                )

                # No generated-entity-chip yet — the assistant must not have
                # proceeded directly to creation (AFS Expected Results).
                assert chat.generated_entity_chip.count() == 0, (
                    "Expected NO generated-entity-chip before the clarifying "
                    "question is answered — the assistant must not create "
                    "the Project Context without first asking"
                )

            with allure.step(
                "Step 3 — Verify the clarifying card presents a background "
                "question; if a stepper renders, read the TOTAL question "
                "count it reports (this run's own fixed total, never "
                "assumed to be 2)"
            ):
                # A stepper only renders when the question set has MORE
                # THAN ONE entry (AFS Known Defects #3 / Concrete Handles).
                # The full question SET — and so the stepper's "N/total" —
                # is fixed at the card's own render time (source:
                # ClarifyingQuestionControl.jsx's `specs` is derived once
                # from the `questions` prop), so reading it HERE, before
                # answering anything, tells us exactly how many questions
                # this run will ask without assuming a fixed count.
                stepper_text = chat.get_clarifying_question_stepper_text(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                if stepper_text:
                    current, total_questions = (int(x) for x in stepper_text.split("/"))
                    assert current == 1, (
                        f"Expected the clarifying card's stepper to start "
                        f"at question 1, got {stepper_text!r}"
                    )
                    assert 2 <= total_questions <= MAX_QUESTIONS, (
                        f"Expected a sane multi-question total (2-"
                        f"{MAX_QUESTIONS}), got {stepper_text!r}"
                    )
                else:
                    total_questions = 1
                    logger.info(
                        "No stepper rendered — this run's model will "
                        "resolve the request with a single question (AFS "
                        "Known Defects #3 non-determinism)"
                    )

            with allure.step(
                "Step 4 — Answer every question in sequence via free text "
                "(never a hardcoded option label — Q2's own content/"
                "options vary run to run, see module docstring); the "
                "stepper advances correctly between questions and the "
                "card closes immediately after the last answer"
            ):
                for step_num in range(1, total_questions + 1):
                    answer_text = (
                        Q1_BACKGROUND_ANSWER if step_num == 1 else FOLLOWUP_ANSWER
                    )
                    chat.answer_clarifying_question(
                        custom_text=answer_text, timeout=UI_ELEMENT_TIMEOUT
                    )
                    if step_num < total_questions:
                        next_stepper_text = chat.get_clarifying_question_stepper_text(
                            timeout=UI_ELEMENT_TIMEOUT
                        )
                        expected = f"{step_num + 1}/{total_questions}"
                        assert next_stepper_text == expected, (
                            f"Expected the clarifying card's stepper to "
                            f"advance to {expected!r} after answering "
                            f"question {step_num}, got {next_stepper_text!r}"
                        )
                chat.wait_for_clarifying_question_card_closed(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 5 — Wait for the AI response: the clarifying card does "
                "not reappear, a generated-entity-chip for 'Project Context' "
                "renders, and the created content reflects the Q1 answer "
                "(verified via API GET and by reopening the Canvas)"
            ):
                chat.wait_for_ai_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT
                )

                assert chat.clarifying_question_custom_input.count() == 0, (
                    "Expected the clarifying card to NOT reappear after the "
                    "final answer was submitted"
                )

                chat.generated_entity_chip.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )
                chip_label = (chat.generated_entity_chip.text_content() or "").strip()
                assert PROJECT_CONTEXT_ENTITY_LABEL in chip_label, (
                    f"Expected the generated-entity-chip to be labeled "
                    f"'{PROJECT_CONTEXT_ENTITY_LABEL}', got {chip_label!r}"
                )

                get_resp = project_context_api.get_project_context()
                assert get_resp.status_code == 200, (
                    f"Expected GET project-context to return 200 after "
                    f"creation, got {get_resp.status_code}"
                )
                created_body = get_resp.json()
                assert created_body.get("id") is not None, (
                    f"Expected a non-null id after creation, got body: "
                    f"{created_body}"
                )
                created_content = (created_body.get("content") or "").lower()
                assert any(kw in created_content for kw in ("python", "rest", "order")), (
                    f"Expected the created content to be topically consistent "
                    f"with the submitted background answer (mentioning "
                    f"python/rest/order), got: {created_content[:200]!r}"
                )

                chat.open_generated_entity_chip(
                    entity_label=PROJECT_CONTEXT_ENTITY_LABEL, timeout=UI_ELEMENT_TIMEOUT
                )
                canvas = ProjectContextChatCanvasPage(page)
                canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                context_page = ProjectContextPage(page)
                context_page.editor_content.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )
                reopened_text = (context_page.editor_content.text_content() or "").lower()
                assert any(kw in reopened_text for kw in ("python", "rest", "order")), (
                    f"Expected the reopened Canvas content to be topically "
                    f"consistent with the submitted background answer, got: "
                    f"{reopened_text[:200]!r}"
                )

            with allure.step("Side-channel check — no console errors at any step"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
