"""Support Assistant — expanding mid-generation does not restart or drop the reply.

TMS case ELITEA-2426 · AFS
``test-specs/support-assistant/l2_expand-during-streaming-does-not-restart_ELITEA-2426.md``

Sends a long-answer prompt, clicks the header Expand toggle **while the reply is
still in flight**, and asserts the generation neither restarts nor loses what it
had rendered: exactly one ``support_predict`` frame for the whole flow, the Stop
button still showing right after the expand, the same single assistant message
item completing, and the widget still expanded when the answer lands.

**Case-text drift, filed as clarification #1662.** Steps 4-5 of the case are
written against token-by-token streaming ("the stream continues from where it
was", "no previously streamed tokens are lost"). This surface never renders
partial text: the backend emits ``agent_llm_chunk`` (status only, never content)
and one terminal ``agent_response`` that assigns the whole body at once
(``chat.hook.ts:258-281``), and the client typewriter is dead code here
(``isAnimating`` is only ever assigned ``false``). Measured twice at 150 ms
sampling: 0 chars for the entire ~80 s window, then the complete answer in a
single sample. Per the reverse-masking guard the LIVE contract is asserted and
the stale wording is filed as a clarification, not a defect — the case's actual
subject (no restart, no loss) is fully observable without partial text:

- "does NOT restart"      -> one ``support_predict`` frame total; Stop still
                             visible immediately after the expand; assistant
                             item count unchanged across the expand.
- "no tokens lost"        -> the rendered text never decreases
                             (``startswith(pre_expand_text)`` at the expand and
                             again at completion) and the SAME single in-flight
                             item is the one that completes.

Fidelity: no substitutions. ``page.on("websocket")`` is passive observation of
frames the PRODUCT sends — nothing is routed, fulfilled, delayed or rewritten
(.agents/testing.md § Fidelity policy). The reply comes from the live LLM over
the real backend; because that producer is nondeterministic, nothing about the
answer's *content* is asserted — only invariants (one request, one message, text
never shrinking, non-empty at the end).

Markers:
    - p2 / support_assistant / ui / regression / slow (one live LLM round trip;
      measured 72.5 s and 86.6 s of generation, ~95-110 s total)

Usage::

    cd automation
    ../.venv/bin/pytest tests/ui/support_assistant/test_support_assistant_expand_during_streaming.py -v
"""

import allure
import pytest
from pages.support_assistant_page import SupportAssistantPage
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.p2,
    pytest.mark.ui,
    pytest.mark.support_assistant,
    pytest.mark.regression,
    pytest.mark.slow,
]

WIDGET_TIMEOUT = 15_000
EXPECT_TIMEOUT = 10_000

# The Stop button is the product's own "generation in flight" signal; observed
# at t~3.9 s after send. Wide enough to absorb a slow backend start.
IN_FLIGHT_TIMEOUT = 60_000

# Measured generation window: 72.5 s and 86.6 s (AFS § Execution Evidence).
# Same budget as ELITEA-2424/2425 on this surface.
REPLY_TIMEOUT = 240_000

# A long-answer prompt: the wording is irrelevant, only that generation lasts
# long enough to click Expand inside it.
PROMPT = "List all ELITEA toolkits and describe each one in detail"

CHAT_PATH = "/chat"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-2426_expand-widget-during-active-streaming-does-not-restart-stream.md",
    "onetest-ai Test Case link",
)
class TestSupportAssistantExpandDuringStreaming:
    """ELITEA-2426 — expand during active generation does not restart it."""

    def test_expand_during_generation_does_not_restart_response(self, page):
        """Expanding mid-generation keeps one request, one message, no loss."""
        console_errors: list[str] = []
        page_errors: list[str] = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
        )
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        support_page = SupportAssistantPage(page)

        # Armed before the first navigation: page.on("websocket") only fires
        # for sockets opened after the listener is attached.
        frames = support_page.capture_sent_socket_frames()

        with allure.step("Step 1 — Open the Support Assistant in compact mode"):
            support_page.navigate(CHAT_PATH)
            support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)
            # The widget restores the previous conversation on mount, so a
            # fresh session is required before any baseline is taken.
            support_page.start_new_chat_via_testid(timeout=WIDGET_TIMEOUT)
            expect(support_page.message_copy_buttons).to_have_count(
                1, timeout=WIDGET_TIMEOUT
            )
            expect(support_page.compact_widget()).to_be_visible(timeout=EXPECT_TIMEOUT)

            copy_baseline = support_page.get_copy_button_count()
            assistant_baseline = support_page.get_assistant_message_item_count()

        with allure.step("Step 2 — Send a prompt that produces a long response"):
            support_page.send_message_via_testid(PROMPT, timeout=EXPECT_TIMEOUT)
            expect(support_page.bubble_in(support_page.last_user_item())).to_have_text(
                PROMPT, timeout=EXPECT_TIMEOUT
            )
            # Generation is in flight: Stop replaces Send, and a cycling status
            # line shows above the bubble. The status TEXT cycles and revisits
            # earlier values, so only its presence is asserted, never a string.
            expect(support_page.stop_generation_button).to_be_visible(
                timeout=IN_FLIGHT_TIMEOUT
            )
            expect(support_page.status_message.first).to_be_visible(
                timeout=EXPECT_TIMEOUT
            )
            expect(support_page.assistant_message_items()).to_have_count(
                assistant_baseline + 1, timeout=EXPECT_TIMEOUT
            )
            # Captured, not assumed: today this surface renders no partial
            # text, but the prefix guard below becomes a real check the moment
            # token streaming ever ships.
            pre_expand_text = support_page.get_last_assistant_text_or_empty()

        with allure.step("Step 3 — Click Expand while the response is in flight"):
            # Asserted immediately before the click so the click is PROVEN to
            # land inside the generation window.
            expect(support_page.stop_generation_button).to_be_visible(
                timeout=EXPECT_TIMEOUT
            )
            support_page.toggle_fullview_via_testid(timeout=EXPECT_TIMEOUT)
            # The state attribute, never geometry: the expand is animated
            # (684x644 -> 716x674 -> 720x678) and a size read taken here would
            # catch a mid-transition value.
            expect(support_page.expanded_widget()).to_be_visible(timeout=EXPECT_TIMEOUT)

        with allure.step(
            "Step 4 — The response did NOT restart (case Step 4, re-expressed per #1662)"
        ):
            # Still in flight right after the expand — a restart would have
            # dropped the Stop button while the new request spun up.
            expect(support_page.stop_generation_button).to_be_visible(
                timeout=EXPECT_TIMEOUT
            )
            # The other restart shape: a NEW assistant message replacing or
            # duplicating the in-flight one. Invisible to a text check while
            # the text is empty.
            expect(support_page.assistant_message_items()).to_have_count(
                assistant_baseline + 1, timeout=EXPECT_TIMEOUT
            )
            # Protocol-level proof: a silent re-send would still look correct
            # in the DOM. One send must be exactly one support_predict frame.
            predicts_after_expand = support_page.count_frames(
                frames, SupportAssistantPage.SUPPORT_PREDICT_EVENT
            )
            assert predicts_after_expand == 1, (
                "Expanding mid-generation re-issued the request: "
                f"{predicts_after_expand} support_predict frames sent, expected 1"
            )

        with allure.step(
            "Step 5 — Nothing rendered was lost (case Step 5, re-expressed per #1662)"
        ):
            post_expand_text = support_page.get_last_assistant_text_or_empty()
            assert post_expand_text.startswith(pre_expand_text), (
                "Rendered assistant text shrank across the expand: "
                f"{pre_expand_text!r} -> {post_expand_text!r}"
            )
            expect(support_page.assistant_message_items()).to_have_count(
                assistant_baseline + 1, timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 6 — The response completes normally in full view"):
            # The copy button renders only on a COMPLETED assistant message,
            # which makes its count the accurate "reply finished" signal — the
            # message item itself mounted back in Step 2.
            expect(support_page.message_copy_buttons).to_have_count(
                copy_baseline + 1, timeout=REPLY_TIMEOUT
            )
            expect(support_page.stop_generation_button).not_to_be_visible(
                timeout=EXPECT_TIMEOUT
            )
            # Guards the inverse regression: an arriving response silently
            # collapsing the widget back to compact.
            expect(support_page.expanded_widget()).to_be_visible(timeout=EXPECT_TIMEOUT)
            expect(support_page.assistant_message_items()).to_have_count(
                assistant_baseline + 1, timeout=EXPECT_TIMEOUT
            )

            final_text = support_page.get_last_assistant_text()
            assert len(final_text) > 100, (
                f"Completed reply is implausibly short ({len(final_text)} chars): "
                f"{final_text!r}"
            )
            assert final_text.startswith(pre_expand_text), (
                "Completed reply does not extend what was rendered before the "
                f"expand: {pre_expand_text!r} is not a prefix of {final_text[:120]!r}"
            )

            total_predicts = support_page.count_frames(
                frames, SupportAssistantPage.SUPPORT_PREDICT_EVENT
            )
            assert total_predicts == 1, (
                f"{total_predicts} support_predict frames sent for one message; "
                "the response was re-requested"
            )

            assert not console_errors, f"Console errors: {console_errors}"
            assert not page_errors, f"Uncaught page errors: {page_errors}"
