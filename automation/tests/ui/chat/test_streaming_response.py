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

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

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
# ELITEA-2179/2466 — a short, unambiguous message; this test only needs a
# real response to eventually complete (Step 7), not a long one.
SEND_TOGGLE_MESSAGE_TEXT = "Hello"


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
            "and each sample is a strict superset of the prior one"
        ):
            # AFS Axis 2 names this a regression guard: "the growing text is
            # a strict superset across polls (never shrinks) — guards
            # against a regression where the streamed preview gets
            # replaced/reset mid-generation instead of appended, which
            # would still show 'changing text' but not genuine progressive
            # streaming." A length-only check does NOT catch that class of
            # regression (content reset to different-but-longer text still
            # grows in length) — so containment is the correct primary
            # signal, asserted unconditionally below, exactly as the AFS
            # specifies (no exception documented there).
            #
            # PR #1106 review round 2 verified in source (not just re-read
            # of round 1's own claim) that no dual-path unmount risk exists
            # inside this step's sampling window, so the round-1 structural
            # presence gate was removed as a no-op:
            #   - ApplicationThinkView.jsx:993-1002 — the
            #     `chat-answer-thought-accordion` testid sits on the OUTER
            #     `<StyledAccordion>` root. `slotProps.transition.
            #     unmountOnExit` only governs whether `AccordionDetails`'
            #     CHILDREN unmount on collapse (standard MUI `Collapse`);
            #     it cannot remove the root element the testid is on. And
            #     `expanded={isStreaming || expanded}` keeps the accordion
            #     expanded for the accordion's entire `isStreaming` window,
            #     so `Collapse` never reaches a collapsed state — the
            #     children stay mounted too.
            #   - ApplicationAnswer.jsx:591 — the wrapper renders only
            #     while `nonSwarmChildActions?.length > 0`.
            #   - ApplicationAnswer.jsx:270-282 — while `isProcessing`
            #     (`isLoading || isRegenerating || isStreaming`) is true,
            #     `nonSwarmChildActions` IS `filteredToolActions` directly
            #     (no type-filtering happens during streaming; the
            #     swarm/non-swarm split only runs once processing ends).
            #   - ApplicationAnswer.jsx:222-268 — `filteredToolActions` is
            #     built with `.map()`, never `.filter()`; while
            #     `isStreaming` is true the map is a no-op copy, so
            #     `filteredToolActions.length === toolActions.length` for
            #     the whole streaming window — it can only grow, not shrink,
            #     between two in-stream samples.
            # Net: since Step 2 already asserts the accordion visible
            # before this step begins (i.e. `toolActions.length` is already
            # > 0), and that array is never filtered down while streaming,
            # the wrapper cannot unmount between any two samples taken here
            # — all of which land strictly inside the streaming window
            # (`wait_for_message_body_growth` only returns on length
            # growth, before Step 7's completion wait). The only place
            # `nonSwarmChildActions` can shrink to 0 is the
            # processing->complete transition, which happens after this
            # step's window and which Step 7 does not assert against the
            # accordion's own count.
            sample_1_text = chat._extract_message_body(ai_message)
            sample_1_len = len(sample_1_text)
            assert sample_1_len > 0, (
                "Body text should already have some content once the "
                "Thought accordion is visible"
            )

            sample_2_text = chat.wait_for_message_body_growth(
                ai_message, sample_1_len, timeout=STREAM_GROWTH_TIMEOUT
            )
            sample_2_len = len(sample_2_text)
            assert sample_2_len > sample_1_len, (
                f"Body text should have grown: {sample_1_len} -> {sample_2_len} chars"
            )
            assert sample_1_text in sample_2_text, (
                "Sample 2 should be a superset of sample 1 (progressive "
                f"append, not replace/reset): {sample_1_text!r} not found "
                f"in {sample_2_text!r}"
            )

            sample_3_text = chat.wait_for_message_body_growth(
                ai_message, sample_2_len, timeout=STREAM_GROWTH_TIMEOUT
            )
            sample_3_len = len(sample_3_text)
            assert sample_3_len > sample_2_len, (
                f"Body text should keep growing (not reset): {sample_2_len} -> {sample_3_len} chars"
            )
            assert sample_2_text in sample_3_text, (
                "Sample 3 should be a superset of sample 2 (progressive "
                f"append, not replace/reset): {sample_2_text!r} not found "
                f"in {sample_3_text!r}"
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

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2179_chat-message-input-field-empty-send-button-not-visible-and-typing-makes-send-button-appear.md",
        "onetest-ai Test Case link (ELITEA-2179)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2466_chat-message-input-empty-shows-no-send-button-typing-shows-send-button-send-clears-field.md",
        "onetest-ai Test Case link (ELITEA-2466)",
    )
    @pytest.mark.p0
    def test_composer_send_button_toggles_with_empty_input_and_waveform_reappears(
        self, page, conversation_id
    ):
        """ELITEA-2179 / ELITEA-2466 (family — 2466 is a more granular
        superset of the same flow 2179 describes; one live execution
        satisfies both).

        The composer's send-button slot swaps between the waveform
        ("enter speaking mode") button and the real Send button based on
        whether the input has text — SendButton.jsx renders exactly one of
        two mutually exclusive DOM nodes, never a visibility toggle on a
        single node (source- and live-confirmed). Also covers the
        surrounding bottom-bar icon inventory, the composer's focus-border
        glow, and a sent message's sender-name/avatar (ELITEA-2466's extra
        granularity beyond ELITEA-2179).

        Steps (AFS
        test-specs/chat-interface/l1_composer-send-button-visibility-toggle_ELITEA-2179.md,
        family AFS — also covers ELITEA-2466):
        1. Baseline: input empty, Send button absent, waveform button
           present; bottom-bar icon inventory (+ / model name / gear /
           mic / waveform) all present.
        2. Click into the input; verify the focus-border glow activates.
        3. Type a single character; verify the waveform is replaced by
           the Send button.
        4. Delete the character; verify the Send button disappears and
           the waveform reappears.
        5. Type the full message and click Send; verify it appears with
           the sender's name + avatar, the input clears, and the Send
           button disappears.
        6. Verify neither the Send button nor the waveform render while
           the response streams (a Stop control takes that slot instead).
        7. Wait for the response to finish generating; verify the
           waveform reappears once generation completes.

        CLARIFICATION (both cases' own wording): "waveform reappears" is
        live-confirmed to resolve once generation COMPLETES, not while the
        LLM is still streaming — matches this page object's own
        pre-existing `wait_for_generation_complete()` docstring ("The
        Speaking mode button appears when generation is complete... During
        generation, a stop button is shown instead"). Step 6 asserts the
        live, self-consistent mid-stream state (neither button present);
        Step 7 asserts the reappearance the case describes, at the point
        it actually happens.
        """
        chat = ChatPage(page)

        with allure.step("Setup — navigate to the fresh conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step(
            "Step 1 — Baseline: input empty, Send button absent, waveform "
            "button present; full bottom-bar icon inventory present"
        ):
            assert chat.is_input_empty(), "Message input should start empty"
            assert chat.send_button.count() == 0, (
                "Send button should be absent while the input is empty"
            )
            expect(chat.voice_mode_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.plus_menu_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.model_selector_name).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.model_settings_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.voice_input_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 2 — Click into the input; verify the composer's "
            "focus-border glow activates (teal/cyan box-shadow)"
        ):
            chat.message_input.click()
            expect(chat.composer_focus_border).to_have_attribute(
                "data-focused", "true", timeout=UI_ELEMENT_TIMEOUT
            )
            box_shadow = chat.composer_focus_border.evaluate(
                "el => getComputedStyle(el).boxShadow"
            )
            assert box_shadow != "none", (
                "Composer should show a focus glow (box-shadow) once the "
                f"input is focused, got: {box_shadow!r}"
            )

        with allure.step(
            "Step 3 — Type a single character; verify the waveform button "
            "is replaced by the Send button (mutually exclusive DOM nodes)"
        ):
            chat.message_input.press_sequentially("h", delay=30)
            expect(chat.send_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.voice_mode_button).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 4 — Delete the character; verify the Send button "
            "disappears and the waveform button reappears"
        ):
            chat.message_input.press("Backspace")
            expect(chat.send_button).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.voice_mode_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 5 — Type the full message and send; verify it appears "
            "with the sender's name + avatar, the input clears, and the "
            "Send button disappears"
        ):
            initial_count = chat.get_message_count()
            chat.send_message(SEND_TOGGLE_MESSAGE_TEXT)

            sent_message = chat.messages_container.nth(initial_count)
            expect(sent_message).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            sender_name = sent_message.locator(chat.MESSAGE_SENDER_NAME)
            sender_avatar = sent_message.locator(chat.MESSAGE_SENDER_AVATAR)
            expect(sender_name).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(sender_avatar).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert sender_name.text_content().strip() != "", (
                "Sent message should render a non-empty sender name"
            )

            assert chat.message_input.input_value() == "", (
                "Input should be cleared immediately after send"
            )
            assert chat.send_button.count() == 0, (
                "Send button should be absent again once the message is sent"
            )

        with allure.step(
            "Step 6 — Verify neither the Send button nor the waveform "
            "button render while the response is streaming (a Stop "
            "control occupies that slot instead)"
        ):
            assert chat.send_button.count() == 0, (
                "Send button should stay absent during streaming"
            )
            assert chat.voice_mode_button.count() == 0, (
                "Waveform button should stay absent during streaming — a "
                "Stop control occupies the send-button slot instead"
            )

        with allure.step(
            "Step 7 — Wait for the response to finish generating; verify "
            "the waveform button reappears once generation completes"
        ):
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            expect(chat.voice_mode_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

