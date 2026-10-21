"""UI Test for ELITEA-2877 — Attachment blocking during an active run (mid-turn interjections).

While an agent turn is streaming, the real attachment entry point
(`chat-attach-menuitem-button`, inside the plus-menu popper) must be
disabled and inert — a click fires zero `filechooser` events — while a
plain-text interjection is still accepted and queues with no attachment
indicator. The entry point re-enables once the run completes.

Feature-gated: same `midturn_injection_enabled` fixture as ELITEA-2875/2876.

Markers:
    - ui: requires browser
    - chat: chat-related test
    - p0: critical priority (AFS Priority l1 == TMS `priority: critical`)

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_interjection_attachment_blocking.py -v
"""

import logging

import allure
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p0, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
INTERJECTABLE_WINDOW_TIMEOUT = 30_000
DRAIN_TIMEOUT = 30_000
BLOCKED_CLICK_ATTEMPT_TIMEOUT = 3_000   # expected to time out — the button is inert

_LONG_RUNNING_PROMPT = (
    "Please write a detailed 500-word story about a dragon who learns to code. "
    "Take your time and be thorough."
)
_PLAIN_TEXT_INTERJECTION = "plain text interjection, no attachment"


@allure.epic("Chat")
@allure.feature("Mid-turn Interjection")
class TestInterjectionAttachmentBlockingDuringActiveRun:
    """ELITEA-2877 — The attach entry point is disabled+inert during an active
    run; a plain-text interjection still queues with no attachment indicator;
    the entry point re-enables once the run completes."""

    @pytest.mark.tms("ELITEA-2877")
    @allure.title("Attach entry point is blocked during an active run; plain-text interjection still queues")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2877_attachment-blocking-automated.md",
        "onetest-ai Test Case link",
    )
    def test_attachment_blocked_during_run_plain_text_interjection_still_queues(
        self, page, conversation_id, midturn_injection_enabled
    ):
        chat = ChatPage(page)

        filechooser_events = []
        page.on("filechooser", lambda fc: filechooser_events.append(fc))

        with allure.step(
            "Step 1 — Navigate to a fresh conversation, send the long-running prompt, "
            "and reach the interjectable window"
        ):
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.send_message(_LONG_RUNNING_PROMPT)
            chat.wait_for_interjectable(timeout=INTERJECTABLE_WINDOW_TIMEOUT)

        with allure.step(
            "Step 2 — Check the attachment entry point's state: it must carry the DOM "
            "disabled attribute and pointer-events: none while the run is active"
        ):
            chat.open_attach_menuitem()
            disabled_state = chat.attach_files_button.evaluate(
                "el => ({disabled: el.disabled, hasAttr: el.hasAttribute('disabled'), "
                "pointerEvents: getComputedStyle(el).pointerEvents})"
            )
            assert disabled_state["disabled"] is True, "chat-attach-menuitem-button should be el.disabled === true"
            assert disabled_state["hasAttr"] is True, "chat-attach-menuitem-button should carry the disabled attribute"
            assert disabled_state["pointerEvents"] == "none", (
                "chat-attach-menuitem-button should have computed pointer-events: none while streaming"
            )

        with allure.step(
            "Step 3 — Attempt to trigger a file attach while the run is active: the click "
            "must fire ZERO filechooser events and no attachment chip must render"
        ):
            with pytest.raises(PlaywrightTimeoutError):
                chat.attach_files_button.click(timeout=BLOCKED_CLICK_ATTEMPT_TIMEOUT)
            assert len(filechooser_events) == 0, (
                f"Clicking the disabled attach entry point should fire 0 filechooser events, "
                f"got {len(filechooser_events)}"
            )
            assert chat.get_attachment_chip_count() == 0, (
                "No attachment chip should render after a blocked attach attempt"
            )
            page.keyboard.press("Escape")  # close the popper before continuing

        with allure.step("Step 4 — Send a plain-text interjection message while the run is still active"):
            chat.queue_interjection(_PLAIN_TEXT_INTERJECTION)
            assert not chat.is_inject_button_errored(), "chat-inject-button should show no error state after the click"
            assert chat.get_interjection_queue_count() == 1, "Exactly one interjection should be queued"
            assert chat.get_interjection_queue_item_texts() == [_PLAIN_TEXT_INTERJECTION], (
                "Queued item text should match the sent plain-text interjection"
            )

        with allure.step("Step 5 — Verify the queued message carries no attachment indicator"):
            assert chat.get_queue_item_attachment_descendant_count(index=0) == 0, (
                "The queued interjection item should have zero [data-testid*='attachment'] descendants"
            )

        with allure.step(
            "Step 6 — Wait for the agent run to complete (full drain — interjection-composer "
            "and interjection-queue-area both gone)"
        ):
            chat.wait_for_interjection_drain(timeout=DRAIN_TIMEOUT)

        with allure.step("Step 7 — Verify the attachment entry point re-enables after completion"):
            chat.open_attach_menuitem()
            # Confirmed live (ELITEA-2877 implementation, 2026-10-17): the
            # re-enable does not land synchronously with the drain signal —
            # poll rather than a one-shot check, never a fixed sleep.
            chat.wait_for_attach_menuitem_enabled(timeout=10_000)
            page.keyboard.press("Escape")
