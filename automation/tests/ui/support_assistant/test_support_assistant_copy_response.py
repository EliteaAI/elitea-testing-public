"""Support Assistant — copy an assistant response to the clipboard.

TMS case ELITEA-2419 · AFS
``test-specs/support-assistant/l2_copy-assistant-response-to-clipboard_ELITEA-2419.md``

Sends a prompt to the Support Assistant widget, waits for the reply, clicks the
"Copy to clipboard" button on the assistant's response bubble, verifies the
transient visual confirmation, and pastes the clipboard back into the widget
input to prove the copied payload is the response.

Fidelity: no substitutions. The assistant's answer is nondeterministic, so the
value the PRODUCT wrote to the clipboard is the oracle — the test never
hand-writes an expected response. Two ``page.evaluate`` calls touch the
clipboard and neither produces an asserted value: ``clear_clipboard()`` is
precondition hygiene (it removes a stale value so a fresh copy is provable) and
``get_clipboard_text()`` is the only available observation channel for an OS
clipboard write.

Two live-product facts the case text does not anticipate (both recorded in the
AFS § Known Deviations, neither a defect):

1. The clipboard receives the RAW MARKDOWN source (``message.content``), while
   the bubble renders it — so ``clipboard == bubble.inner_text()`` is false by
   design. Correspondence is asserted on a markdown-normalised basis; the paste
   round-trip is the exact-equality assertion.
2. The confirmation is an SVG icon swap that self-reverts after 2000 ms; the
   tooltip never reads "Copied". The case offers the icon change as its first
   alternative, so its expected result is satisfied — do not add a tooltip-text
   assertion.

Markers:
    - p2 / support_assistant / ui / regression (not smoke — a ~70 s live LLM
      round trip is not a critical-path fast test)

Usage::

    cd automation
    ../.venv/bin/pytest tests/ui/support_assistant/test_support_assistant_copy_response.py -v
"""

import re

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

# Observed reply latency on this surface: 33-135 s, sampled at 69.6 s for this
# very prompt (surface digest quirks 5 and 15). 120 s is tight, not generous.
REPLY_TIMEOUT = 180_000

PROMPT = "Explain in one sentence what an AI agent is"
COPY_BUTTON_LABEL = "Copy to clipboard"


def _plain(text: str) -> str:
    """Normalise markdown source and rendered text onto a comparable basis.

    Strips emphasis / code / heading markers, drops horizontal rules and
    collapses whitespace, so the raw markdown the product copies can be
    compared against the HTML the product renders without asserting anything
    about the markdown renderer itself.
    """
    text = re.sub(r"[*_`#]", "", text)
    text = re.sub(r"^\s*-{3,}\s*$", "", text, flags=re.M)
    return re.sub(r"\s+", " ", text).strip()


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-2419_copy-assistant-response-to-clipboard.md",
    "onetest-ai Test Case link",
)
class TestSupportAssistantCopyResponse:
    """ELITEA-2419 — copy assistant response to clipboard."""

    def test_copy_assistant_response_to_clipboard(self, page):
        """The response's copy button writes the reply to the OS clipboard."""
        console_errors: list[str] = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
        )
        support_page = SupportAssistantPage(page)

        with allure.step("Step 1 — Open the Support Assistant widget"):
            ChatPage(page).navigate_to_chat()
            support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)

            # A fresh session keeps the test independent of restored history.
            # It is NOT empty — the assistant posts a greeting, so the copy
            # button count starts at 1 (surface digest quirk 10).
            support_page.start_new_chat(timeout=WIDGET_TIMEOUT)
            copy_baseline = support_page.get_copy_button_count()

        with allure.step(f"Step 2 — Send the message {PROMPT!r}"):
            support_page.send_message_via_testid(PROMPT, timeout=EXPECT_TIMEOUT)
            expect(support_page.bubble_in(support_page.last_user_item())).to_have_text(
                PROMPT, timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 3 — Wait for the assistant response to appear"):
            # The copy button renders only once the message is complete
            # (MessageItem.tsx: content && !isStreaming && !isAnimating), which
            # makes its count the accurate completion signal — a message-count
            # delta fires while the reply is still arriving.
            expect(support_page.message_copy_buttons).to_have_count(
                copy_baseline + 1, timeout=REPLY_TIMEOUT
            )
            assistant_item = support_page.last_assistant_item()
            response_bubble = support_page.bubble_in(assistant_item)
            expect(response_bubble).not_to_have_text("", timeout=EXPECT_TIMEOUT)

        with allure.step(
            "Step 4 — Locate the Copy to clipboard button on the response bubble"
        ):
            copy_button = support_page.copy_button_in(assistant_item)
            expect(copy_button).to_have_count(1, timeout=EXPECT_TIMEOUT)
            expect(copy_button).to_be_visible(timeout=EXPECT_TIMEOUT)
            expect(copy_button).to_have_attribute(
                "aria-label", COPY_BUTTON_LABEL, timeout=EXPECT_TIMEOUT
            )
            # The affordance is assistant-only — that is what makes this case's
            # subject well defined. Absence assertions are first-class
            # references (canon #511 extension).
            expect(
                support_page.copy_button_in(support_page.last_user_item())
            ).to_have_count(0, timeout=EXPECT_TIMEOUT)
            # Idle state before the click, so the flip below is a transition.
            expect(copy_button).to_have_attribute(
                "data-copied", "false", timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 5 — Click the button and verify the visual confirmation appears"
        ):
            support_page.clear_clipboard()
            copy_button.click()

            # Assert the confirmation FIRST: it self-reverts after 2000 ms and a
            # clipboard read plus paste round trip can burn that window.
            expect(page.locator(support_page.MESSAGE_COPY_BUTTON_COPIED)).to_have_count(
                1, timeout=EXPECT_TIMEOUT
            )

            clipboard_text = support_page.get_clipboard_text()

            # The confirmation is transient by design; asserting only the "true"
            # edge would also pass if the button latched permanently.
            expect(page.locator(support_page.MESSAGE_COPY_BUTTON_COPIED)).to_have_count(
                0, timeout=EXPECT_TIMEOUT
            )
            expect(copy_button).to_have_attribute(
                "data-copied", "false", timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 6 — Paste the clipboard content and verify it matches the response"
        ):
            assert clipboard_text.strip(), (
                "clipboard is empty after clicking 'Copy to clipboard' — nothing was copied"
            )
            assert clipboard_text.strip() != PROMPT, (
                "clipboard holds the user prompt, not the assistant response"
            )

            # Correspondence, markdown-tolerant: the clipboard carries the raw
            # markdown source while the bubble carries the rendered text. The
            # first paragraph is the substantive answer and is plain prose; the
            # trailing boilerplate is markdown-heavy and is not this case's
            # subject.
            bubble_text = response_bubble.inner_text()
            first_paragraph = bubble_text.split("\n")[0].strip()
            assert _plain(first_paragraph) in _plain(clipboard_text), (
                "the copied text does not contain the assistant response's first "
                f"paragraph.\nbubble: {first_paragraph!r}\nclipboard: {clipboard_text!r}"
            )

            # The literal observable of the case step: the paste round trip is
            # byte-exact, because both sides were produced by the product.
            support_page.message_input_field.click()
            page.keyboard.press("ControlOrMeta+V")
            expect(support_page.message_input_field).to_have_value(
                clipboard_text, timeout=EXPECT_TIMEOUT
            )

            # Leave nothing staged in the input.
            support_page.set_message_text("")
            expect(support_page.message_input_field).to_have_value("")

        with allure.step("Step 7 — No console errors during the flow"):
            # The Vite dev server emits a `stream` externalization WARNING on
            # this page; only `error`-type entries are collected above.
            assert console_errors == [], f"Unexpected console errors: {console_errors}"
