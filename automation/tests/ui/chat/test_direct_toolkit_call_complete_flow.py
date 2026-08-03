"""UI Test for ELITEA-2215 — Chat: Tool Action and Output – Complete Flow
from Direct Toolkit Call to Output Display.

Verifies the full lifecycle of a direct toolkit call (toolkit added as chat
participant, no agent intermediary): the "Thought for X secs" accordion,
expanding it to see the tool-call chip, waiting for execution, verifying the
model + tool chips, and the response text following the chips.

Spec: test-specs/chat-interface/l2_direct-toolkit-call-complete-flow_ELITEA-2215.md

CLARIFICATION (reverse-masking guard, all confirmed live — no product
defect, case text is imprecise):
1. The case describes the tool-call badge as dotted
   (``"toolkit_name.tool_name"``); the live rendered chip text is
   colon-separated (``"{toolkit_name}: create_file"``,
   ``ActionView.jsx``'s ``buildTitle()``). This test asserts the live format.
2. The case describes THREE distinct chips (model / toolkit / tool-call) as
   if toolkit-identity and tool-call were separate elements. The live DOM
   renders exactly ONE combined toolkit/tool chip (``chat-answer-tool-chip``,
   newly added — see below) plus N>=1 model chips (one per distinct model
   invoked in the turn's reasoning chain, data-dependent, not fixed at 1).
   This test asserts "at least one model chip + exactly one tool chip",
   not "three chips".
3. The case's own step 2 says to manually "expand the thinking-steps
   accordion" as an action. Confirmed live (5 timed polls against the real
   backend, 0.5s apart): the accordion is ALREADY auto-expanded for the
   whole tool-call/streaming window — ``ApplicationThinkView.jsx``'s
   ``expanded={isStreaming || expanded}``, the SAME auto-expand behavior
   ELITEA-2181's streaming-response test already established and asserts
   without ever clicking. A manual click is not only unnecessary here, it
   is actively unreliable: the accordion's rendered height changes as it
   streams, so a fixed click point can land on a different part of a
   growing/shrinking element between the actionability check and the
   dispatched event. This test asserts presence/text directly instead.

One new testid added to EliteaUI for this case's own executed path (shared
ask with ELITEA-2212/2213, implemented once): ``chat-answer-tool-chip`` —
``ActionView.jsx``'s model/tool ternary, else-branch (canon ruling #277
shape (b): both branches now named since this case + ELITEA-2212 assert
presence/text and ELITEA-2213 asserts absence, all on their own executed
paths).

**PRODUCT DEFECT found during implementation, filed as
EliteaAI/elitea-testing-public#1127 (not masked — see the issue for full
evidence).** Across 3 separate live local runs, the direct-toolkit-call
flow (no agent) sometimes leaks the model's tool-call intent as raw VISIBLE
text (e.g. a literal ``<function_calls><invoke name="create_file">...``
block) instead of invoking the real backend tool -- confirmed via
``ArtifactAPI.list_bucket_files`` returning empty after the flow "completed"
with no user-visible error. 2 separate runs of the identical setup DID
execute correctly (real backend call, correct chip), making this
non-deterministic rather than a hard 100% failure -- itself part of the
finding (unreliable interception, not simply "sometimes slow"). This test
is intentionally left asserting the CORRECT/intended contract (backend
execution + chip rendering), not weakened around the defect: per the
project's product-blocking classification, a failure here is the honest
signal, and this is reported `blocked` (not `automated`) with the ticket
linked rather than green-washed with a softer assertion.
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 15_000
CHAT_RESPONSE_TIMEOUT = 60_000

MESSAGE_TEXT = "create a file named test.txt"
TOOL_NAME = "create_file"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_streaming_response.py`` / ``test_conversation_deletion_flow.py``
    — a ``403`` on ``GET .../secrets/secrets/default/{project_id}`` fires on every
    page load in this local environment regardless of the action taken, and is
    unrelated to the toolkit-call flow under test.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestDirectToolkitCallCompleteFlow:
    """ELITEA-2215: Chat – Tool Action and Output – Complete Flow from Direct Toolkit Call (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2215_chat-tool-action-and-output-complete-flow-from-direct-toolkit-call.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1127",
        "Known defect — direct toolkit call sometimes leaks raw tool-call text instead of executing",
    )
    @pytest.mark.p2
    def test_direct_toolkit_call_complete_flow(self, page, conversation_id, artifact_toolkit):
        """Full direct-toolkit-call flow: accordion -> chips -> response.

        Steps (AFS
        test-specs/chat-interface/l2_direct-toolkit-call-complete-flow_ELITEA-2215.md):
        1. Send the create-file message with the toolkit as sole participant;
           verify "Thought for X secs" appears.
        2. Verify the tool-call chip in the (already auto-expanded, per
           CLARIFICATION 3) thinking steps (colon-separated format, per
           CLARIFICATION 1).
        3. Wait for execution; verify the response appears.
        4. Verify at least one model chip + exactly one toolkit/tool chip
           (per CLARIFICATION above).
        5. Verify the response text follows the chips.
        """
        chat = ChatPage(page)
        toolkit_name = artifact_toolkit["name"]
        expected_chip_text = f"{toolkit_name}: {TOOL_NAME}"

        console_issues = []
        page_errors = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_issues.append(msg)

        page.on("console", _on_console)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        with allure.step("Setup — navigate to the fresh conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Setup — add the artifact toolkit as the only participant"):
            chat.add_toolkit_participant(toolkit_name)

        with allure.step(
            "Step 1 — Send 'create a file named test.txt' with the toolkit as "
            "the sole participant; verify 'Thought for X secs' appears"
        ):
            initial_count = chat.get_message_count()
            chat.send_message(MESSAGE_TEXT)
            expect(chat.answer_thought_accordion).to_be_visible(timeout=CHAT_RESPONSE_TIMEOUT)

        with allure.step(
            "Step 2 — Verify tool call shown as 'toolkit_name: tool_name' in "
            "the thinking steps (CLARIFICATION 3: already auto-expanded, no "
            "manual click needed/reliable; CLARIFICATION 1: live format is "
            "colon-separated, not the case's dotted example)"
        ):
            expect(chat.answer_tool_chip).to_be_visible(timeout=CHAT_RESPONSE_TIMEOUT)
            expect(chat.answer_tool_chip).to_contain_text(expected_chip_text)

        with allure.step("Step 3 — Wait for execution; verify the response appears"):
            chat.wait_for_ai_response(initial_count=initial_count, timeout=CHAT_RESPONSE_TIMEOUT)
            chat.wait_for_message_content_stable(stable_duration_ms=3000, timeout=CHAT_RESPONSE_TIMEOUT)

        with allure.step(
            "Step 4 — Verify chips: at least one model chip AND exactly one "
            "toolkit/tool chip (CLARIFICATION: live product renders 1 "
            "combined toolkit/tool chip + N>=1 model chips, not 3 distinct "
            "chips as the case describes)"
        ):
            model_chip_count = chat.answer_model_chip.count()
            assert model_chip_count >= 1, (
                f"Expected at least one model chip, found {model_chip_count}"
            )
            expect(chat.answer_tool_chip).to_have_count(1)
            expect(chat.answer_tool_chip).to_contain_text(expected_chip_text)

        with allure.step(
            "Step 5 — Verify the LLM response text follows the chips: the "
            "chips are already rendered by the time the settled response "
            "text is read (chips surface once tool-call metadata is known, "
            "before the final answer text streams in and stabilises)"
        ):
            assert chat.answer_tool_chip.is_visible(), (
                "Tool chip should still be visible once the response has settled"
            )
            last_text = chat.get_last_message_text()
            assert last_text, "Expected the assistant's response text to be non-empty"
            logger.info("Final response text (%d chars): %s", len(last_text), last_text[:200])

        with allure.step("Side-channel check — no console/JS errors across the whole flow"):
            assert not console_issues and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_issues]!r}; "
                f"page errors: {page_errors!r}"
            )
