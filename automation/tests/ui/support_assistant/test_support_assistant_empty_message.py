"""Support Assistant — empty / whitespace-only message cannot be sent.

TMS case ELITEA-2418 · AFS
``test-specs/support-assistant/l2_empty_message_cannot_be_sent_ELITEA-2418.md``

Verifies the Send-button state machine of the Support Assistant message input:
an empty or whitespace-only input keeps Send disabled, Enter on such an input
sends nothing (no new message item, no ``predict`` socket frame, no POST), and
typing real text enables Send again.

Fidelity: no substitutions. Every observable — input value, ``disabled``
attribute, message-item count, outbound WebSocket frames, POST requests,
console — is produced by the live product and read directly. Typing uses real
input/key events (``fill`` / ``press``), never ``page.evaluate`` value
assignment: a React controlled ``<textarea>`` ignores synthetic value writes,
which is what produced the non-reproducing bug #1581 (stale; NOT a known defect
for this test — this spec is hard-green).

Markers:
    - p2 / support_assistant / ui / regression

Usage::

    cd automation
    ../.venv/bin/pytest tests/ui/support_assistant/test_support_assistant_empty_message.py -v
"""

import allure
import pytest
from pages.chat_page import ChatPage
from pages.support_assistant_page import SupportAssistantPage
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.p2,
    pytest.mark.ui,
    pytest.mark.support_assistant,
    pytest.mark.regression,
]

WIDGET_TIMEOUT = 15_000
EXPECT_TIMEOUT = 10_000

# Asserting an ABSENCE (no message sent) has no positive condition to wait on —
# Playwright's auto-retrying assertions pass the instant they are satisfied, so
# they cannot prove "nothing happened over a window". This short settle window
# is the documented exception to the no-sleep rule (Hard Rule 5): the product
# emits its ``predict`` socket frame synchronously in the Enter handler, so 1.5 s
# is an order of magnitude more than a real send needs to become observable.
NO_SEND_SETTLE_MS = 1_500

WIDGET_TITLE = "ELITEA Support"
PREDICT_EVENT = "predict"


class _SideChannels:
    """Collects console errors, POST requests and outbound WS frames."""

    def __init__(self, page):
        self.console_errors: list[str] = []
        self.posts: list[str] = []
        self.ws_sent: list[str] = []

        page.on(
            "console",
            lambda msg: self.console_errors.append(msg.text)
            if msg.type == "error"
            else None,
        )
        page.on(
            "request",
            lambda request: self.posts.append(request.url)
            if request.method == "POST"
            else None,
        )
        page.on("websocket", self._attach_ws)

    def _attach_ws(self, ws):
        ws.on(
            "framesent",
            lambda payload: self.ws_sent.append(
                payload if isinstance(payload, str) else payload.decode("utf-8", "replace")
            ),
        )

    def mark(self) -> tuple[int, int]:
        """Snapshot the current lengths so a window can be sliced later."""
        return len(self.posts), len(self.ws_sent)

    def since(self, mark: tuple[int, int]) -> tuple[list[str], list[str]]:
        """Return (POST urls, sent WS frames) captured after ``mark``."""
        return self.posts[mark[0]:], self.ws_sent[mark[1]:]

    def predict_frames_since(self, mark: tuple[int, int]) -> list[str]:
        _, frames = self.since(mark)
        return [f for f in frames if PREDICT_EVENT in f]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-2418_empty-message-cannot-be-sent.md",
    "onetest-ai Test Case link",
)
class TestSupportAssistantEmptyMessage:
    """ELITEA-2418 — empty message cannot be sent."""

    def test_empty_message_cannot_be_sent(self, page):
        """Empty / whitespace-only input keeps Send disabled and sends nothing."""
        side = _SideChannels(page)
        support_page = SupportAssistantPage(page)

        with allure.step("Step 1 — Open the Support Assistant widget"):
            ChatPage(page).navigate_to_chat()
            support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)
            expect(support_page.widget_header_title).to_have_text(
                WIDGET_TITLE, timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 2 — Ensure the message input field is empty"):
            # The widget restores the previous session, so the input — not the
            # conversation — is what must be empty here.
            support_page.set_message_text("")
            expect(support_page.message_input_field).to_have_value(
                "", timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 3 — Verify the Send button is disabled"):
            expect(support_page.send_message_button).to_be_disabled(
                timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 4 — Press Enter; no message is sent and the conversation is unchanged"
        ):
            baseline_count = support_page.get_message_item_count()
            mark = side.mark()

            support_page.message_input_field.click()
            support_page.message_input_field.press("Enter")
            page.wait_for_timeout(NO_SEND_SETTLE_MS)  # see NO_SEND_SETTLE_MS

            expect(support_page.message_items).to_have_count(
                baseline_count, timeout=EXPECT_TIMEOUT
            )
            posts, _ = side.since(mark)
            assert side.predict_frames_since(mark) == [], (
                "Enter on an empty input must not emit a 'predict' socket frame, "
                f"but got: {side.predict_frames_since(mark)}"
            )
            assert posts == [], (
                f"Enter on an empty input must not issue any POST request, got: {posts}"
            )
            expect(support_page.message_input_field).to_have_value("")
            expect(support_page.send_message_button).to_be_disabled()

        with allure.step(
            "Step 5 — Type a single space; the Send button remains disabled"
        ):
            support_page.set_message_text(" ")
            expect(support_page.message_input_field).to_have_value(
                " ", timeout=EXPECT_TIMEOUT
            )
            expect(support_page.send_message_button).to_be_disabled(
                timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 5b — Enter on a whitespace-only input also sends nothing "
            "and does not clear the input"
        ):
            mark = side.mark()
            support_page.message_input_field.press("Enter")
            page.wait_for_timeout(NO_SEND_SETTLE_MS)  # see NO_SEND_SETTLE_MS

            expect(support_page.message_items).to_have_count(
                baseline_count, timeout=EXPECT_TIMEOUT
            )
            posts, _ = side.since(mark)
            assert side.predict_frames_since(mark) == [], (
                "Enter on a whitespace-only input must not emit a 'predict' socket "
                f"frame, but got: {side.predict_frames_since(mark)}"
            )
            assert posts == [], (
                "Enter on a whitespace-only input must not issue any POST request, "
                f"got: {posts}"
            )
            # The product does NOT clear a rejected input.
            expect(support_page.message_input_field).to_have_value(" ")

        with allure.step("Step 6 — Type actual text; the Send button becomes enabled"):
            support_page.set_message_text("Hello")
            expect(support_page.message_input_field).to_have_value(
                "Hello", timeout=EXPECT_TIMEOUT
            )
            expect(support_page.send_message_button).to_be_enabled(
                timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 7 — Boundary probes: trim-based guard, reversible transition"
        ):
            support_page.set_message_text("   ")
            expect(support_page.send_message_button).to_be_disabled(
                timeout=EXPECT_TIMEOUT
            )

            support_page.set_message_text("  hi  ")
            expect(support_page.send_message_button).to_be_enabled(
                timeout=EXPECT_TIMEOUT
            )

            support_page.set_message_text("")
            expect(support_page.send_message_button).to_be_disabled(
                timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 8 — No console errors during the flow"):
            # The Vite dev server emits a `stream` externalization WARNING on
            # this page; only `error`-type entries are collected above.
            assert side.console_errors == [], (
                f"Unexpected console errors: {side.console_errors}"
            )
