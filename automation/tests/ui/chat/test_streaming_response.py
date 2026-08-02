"""UI Test for ELITEA-2181 — Chat: Streaming Response Displayed While LLM
Generates Output.

Verifies the full in-progress-response widget sequence on a single chat
exchange: rotating text placeholder -> "Thought for <n> secs" accordion
(model-name chip inside it), progressive/monotonic text growth during
generation, the Pause/Resume-scroll toggle, Send-button absence while
streaming, dual completion signals, and the post-completion action-icon
row + editable input.

Spec: test-specs/chat-interface/l2_streaming-response-progressive-display_ELITEA-2181.md

CLARIFICATION (issue EliteaAI/elitea-testing-public#1100, reverse-masking
guard): the case's literal "spinning loading circle" and bubble/page-level
"Pause scroll" wording do not match the live widget. The live product
shows a text-cycling placeholder (``RotatingMessages``) followed by a
model-chip-bearing "Thought…" accordion, with "Pause scroll" scoped to
that accordion — this test asserts the live contract, not the stale case
text. No functional product defect was found.

Six new testids were added to EliteaUI for this case (all touched by the
steps below, none blanket-added to sibling elements the case doesn't
assert on): ``chat-answer-loading-placeholder``, ``chat-answer-thought-
accordion``, ``chat-answer-model-chip`` (named only when the chip's
``toolkitType === 'model'`` — canon ruling #277, the shared ``ActionView``
component's other chip kinds stay unnamed), ``chat-answer-pause-scroll-
toggle``, ``chat-copy-button``, ``chat-regenerate-button``.

Environment note (AFS § Automation Hints): this environment's default chat
participant answers "write a poem" prompts via a file-writing TOOL rather
than a plain text completion, so full generation took 34-54s across the
analyst's 4 live runs — timeouts below are sized accordingly (do not
shrink them to "make the test faster").
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 15_000
# Generous ceiling for the FIRST content-growth check during streaming —
# well inside the 34-54s full-generation range observed live.
STREAM_GROWTH_TIMEOUT = 60_000
# Full-generation completion — sized above the 34-54s observed range with
# CI headroom (AFS § Automation Hints: "do NOT assume a short prompt
# completes quickly on this environment's default participant").
AI_RESPONSE_TIMEOUT = 120_000

MESSAGE_TEXT = "Write a long poem about the city"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_conversation_deletion_flow.py`` /
    ``test_open_conversation_today_section.py`` — a ``403`` on
    ``GET .../secrets/secrets/default/{project_id}`` fires on every page
    load in this local environment regardless of the action taken, and is
    unrelated to the streaming flow under test.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestStreamingResponse:
    """ELITEA-2181: Chat – Streaming Response Displayed While LLM Generates Output (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2181_chat-streaming-response-displayed-while-llm-generates-output.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1100",
        "CLARIFICATION — case text vs live widget shape",
    )
    @pytest.mark.p1
    def test_streaming_response_progressive_display(self, page, conversation_id):
        """Full streaming-response widget lifecycle for one exchange.

        Steps (AFS
        test-specs/chat-interface/l2_streaming-response-progressive-display_ELITEA-2181.md):
        1. Baseline: Send button absent with empty input, appears the
           instant text is typed; send the message; verify it appears and
           input clears.
        2. Verify the RotatingMessages placeholder appears, then the
           "Thought…" accordion + model-name chip.
        3. Verify the response text streams progressively (monotonic
           growth, never shrinks).
        4. Verify "Pause scroll" appears, scoped to the Thought accordion.
        5. Click it; verify the label flips to "Resume scroll".
        6. Verify the Send button stays absent during streaming.
        7. Wait for completion; verify both the loading placeholder and
           the Pause-scroll toggle are gone.
        8. Hover the completed message; verify all 4 action icons
           (speaker, copy, regenerate, delete) become visible.
        9. Verify the input field is editable again.
        """
        chat = ChatPage(page)

        # Registered before Step 1 so console errors from the whole flow
        # are captured (side-channel discipline — AFS Axis 2: "console/
        # network checked after every step across all 4 runs").
        console_issues = []
        page_errors = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_issues.append(msg)

        page.on("console", _on_console)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        with allure.step("Setup — navigate to the fresh conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step(
            "Step 1 — Baseline: Send button absent with empty input, "
            "appears the instant text is typed; send the message; verify "
            "it appears in the list and the input clears"
        ):
            assert chat.send_button.count() == 0, (
                "Send button should be absent while the input is empty (baseline)"
            )
            chat.message_input.click()
            # Single char typed -> a single Backspace fully clears it, which
            # sidesteps the platform-dependent select-all quirk documented
            # elsewhere in this page-object family (Control+a alone is NOT
            # reliable select-all on macOS Chromium — agent_form_page.py:442
            # / credential_form_fields.py:46 — ControlOrMeta+a is the fix,
            # but a single-char clear needs no selection at all).
            chat.message_input.press_sequentially("x", delay=30)
            expect(chat.send_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            chat.message_input.press("Backspace")
            expect(chat.send_button).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

            initial_count = chat.get_message_count()
            chat.send_message(MESSAGE_TEXT)

            expect(chat.messages_container.nth(initial_count)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert chat.message_input.input_value() == "", (
                "Input should be cleared immediately after send"
            )

        ai_index = initial_count + 1
        ai_message = chat.messages_container.nth(ai_index)

        with allure.step(
            "Step 2 — Verify the RotatingMessages placeholder appears, "
            "then the 'Thought…' accordion + model-name chip "
            "(CLARIFICATION #1100: no literal spinning circle)"
        ):
            expect(ai_message).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.answer_loading_placeholder).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.answer_thought_accordion).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.answer_model_chip).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 3 — Verify the response text streams progressively: "
            "length grows across 3 independent, condition-waited samples, "
            "never regressing"
        ):
            # AFS-drift discovered live (amended in-PR, see the AFS's
            # Automation Hints): this environment's default participant
            # sometimes answers via a file-writing TOOL (growth happens
            # inside the Thought accordion's tool-preview pane, as the
            # AFS's own analyst run observed) and sometimes answers via a
            # plain-text completion (growth happens directly in the Answer/
            # Markdown block instead, and the near-instant "Thought for
            # less than a second" reasoning accordion unmounts once
            # streaming ends — a benign structural change, not a content
            # reset). A strict "first sample is a substring of the second"
            # check breaks on the plain-text path when that transient
            # accordion text later disappears from the DOM. A 3-point
            # strictly-increasing LENGTH series over real, condition-waited
            # intervals proves the same thing the AFS cares about
            # (differs, grows, never resets to empty-then-regrows) while
            # staying robust to either generation path.
            sample_1_len = len(chat._extract_message_body(ai_message))
            assert sample_1_len > 0, (
                "Body text should already have some content once the "
                "Thought accordion is visible"
            )
            chat.wait_for_message_body_growth(
                ai_message, sample_1_len, timeout=STREAM_GROWTH_TIMEOUT
            )
            sample_2_len = len(chat._extract_message_body(ai_message))
            assert sample_2_len > sample_1_len, (
                f"Body text should have grown: {sample_1_len} -> {sample_2_len} chars"
            )
            chat.wait_for_message_body_growth(
                ai_message, sample_2_len, timeout=STREAM_GROWTH_TIMEOUT
            )
            sample_3_len = len(chat._extract_message_body(ai_message))
            assert sample_3_len > sample_2_len, (
                f"Body text should keep growing (not reset): {sample_2_len} -> {sample_3_len} chars"
            )

        with allure.step(
            "Step 4 — Verify 'Pause scroll' appears, scoped to the Thought "
            "accordion (CLARIFICATION #1100: not a bubble/page-level control)"
        ):
            expect(chat.answer_pause_scroll_toggle).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert chat.answer_pause_scroll_toggle.text_content().strip() == "Pause scroll"

        with allure.step(
            "Step 5 — Click 'Pause scroll'; verify auto-scroll stops "
            "(the control's own label flips to 'Resume scroll')"
        ):
            chat.answer_pause_scroll_toggle.click()
            expect(chat.answer_pause_scroll_toggle).to_have_text(
                "Resume scroll", timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 6 — Verify the Send button stays absent while streaming "
            "(general empty-input rule, not streaming-aware hide/show logic)"
        ):
            assert chat.send_button.count() == 0, (
                "Send button should remain absent during streaming (input stays empty)"
            )

        with allure.step(
            "Step 7 — Wait for streaming to complete; verify the loading "
            "placeholder and the Pause-scroll toggle are both gone "
            "(dual completion signal alongside the Copy-button visibility "
            "wait_for_ai_response already performs)"
        ):
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            expect(chat.answer_pause_scroll_toggle).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.answer_loading_placeholder).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 8 — Hover the completed message; verify all 4 action "
            "icons (speaker, copy, regenerate, delete) become visible"
        ):
            ai_message.scroll_into_view_if_needed()
            ai_message.hover()
            expect(chat.read_out_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.copy_action_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.regenerate_action_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.delete_action_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 9 — Verify the input field is editable again"):
            assert chat.message_input.is_editable(), (
                "Message input should be editable again after streaming completes"
            )

        with allure.step("Side-channel check — no console/JS errors across the whole flow"):
            assert not console_issues and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_issues]!r}; "
                f"page errors: {page_errors!r}"
            )
