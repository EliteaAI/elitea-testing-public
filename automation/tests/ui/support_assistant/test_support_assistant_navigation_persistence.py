"""Support Assistant — widget state preserved after in-app navigation.

TMS case ELITEA-2422 · AFS
``test-specs/support-assistant/l2_widget-state-preserved-after-in-app-navigation_ELITEA-2422.md``

Opens the Support Assistant widget on the Chat page, sends a message and waits
for the reply, navigates to Agents and back through the sidebar WITHOUT closing
the widget, verifies the widget is still open with the conversation intact, and
sends a follow-up that lands in the same session.

Why the strong form: the widget is mounted at app-shell level, outside the
routed subtree (``EliteaUI/src/[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx``
renders ``<EliteaAssistant>`` as a sibling of the routed ``children``), so a
route change cannot unmount it. The case text hedges with "(or can be reopened
via the launcher)"; the live contract is stronger, and a conditional reopen
would be a never-executed branch that masks a regression to a routed mount.
Assert it never closes (AFS § Known Deviations).

Fidelity: no substitutions. Every asserted observable — widget visibility,
message items, message text, copy buttons, input value, URL, console — is
produced by the live product and read from the DOM. Both replies are real live
responses over the assistant's own socket; nothing is fabricated. Typing uses
real input events (``fill``), never ``page.evaluate`` value assignment.

Baselines, not absolutes: the widget restores whatever conversation the test
user already has (varies by history), and this spec deliberately leaves its
messages behind, so every count assertion is a DELTA against a baseline taken
right after the widget opens — including the count of the pre-navigation
message text, which a previous run may already have contributed.

Markers:
    - p2 / support_assistant / ui / regression (not smoke — two live LLM round
      trips put the runtime around 70-90 s)

Usage::

    cd automation
    ../.venv/bin/pytest tests/ui/support_assistant/test_support_assistant_navigation_persistence.py -v
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
NAV_TIMEOUT = 30_000

# Observed reply latency on this surface: 31-135 s (surface digest quirks 5/15,
# 31.0 s twice in the ELITEA-2422 analysis run). 120 s is tight, not generous.
REPLY_TIMEOUT = 180_000

WIDGET_TITLE = "ELITEA Support"
FIRST_MESSAGE = "Navigation persistence test"
FOLLOW_UP_MESSAGE = "Follow-up after navigation"

# Vite HMR and the dev server's own polling socket log ERR_CONNECTION_REFUSED
# entries unrelated to the app (surface digest quirk 21). Only these two are
# excluded — every other console error still fails the test.
_DEV_SERVER_NOISE = ("@vite/client", "/socket.io/")


def _is_dev_server_noise(text: str) -> bool:
    """Whether *text* is a Vite/dev-server connection error, not an app error."""
    return "ERR_CONNECTION_REFUSED" in text and any(p in text for p in _DEV_SERVER_NOISE)


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-2422_widget-state-preserved-after-in-app-navigation.md",
    "onetest-ai Test Case link",
)
class TestSupportAssistantNavigationPersistence:
    """ELITEA-2422 — widget state preserved after in-app navigation."""

    def test_widget_state_preserved_after_in_app_navigation(self, page):
        """The open widget and its conversation survive /chat -> /agents/all -> /chat."""
        console_errors: list[str] = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text)
            if msg.type == "error" and not _is_dev_server_noise(msg.text)
            else None,
        )
        support_page = SupportAssistantPage(page)

        with allure.step("Step 1 — Open the Support Assistant widget on the Chat page"):
            ChatPage(page).navigate_to_chat()
            support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)
            expect(support_page.widget_header_title).to_have_text(
                WIDGET_TITLE, timeout=EXPECT_TIMEOUT
            )

            # The widget restores the previous session on open — never assume
            # an empty conversation (surface digest quirk 2/10).
            baseline_items = support_page.get_message_item_count()
            baseline_copies = support_page.get_copy_button_count()
            # A previous run of this very spec may already have left
            # FIRST_MESSAGE in the restored conversation.
            baseline_first_message = support_page.user_message_item_with_text(
                FIRST_MESSAGE
            ).count()

        with allure.step(f"Step 2 — Send {FIRST_MESSAGE!r} and wait for a response"):
            support_page.set_message_text(FIRST_MESSAGE)
            # Real typing enables Send immediately; #1581 ("Send never enables")
            # is a non-reproducing false bug produced by synthetic value writes
            # against the React controlled textarea (AFS § Known Defects).
            expect(support_page.send_message_button).to_be_enabled(timeout=EXPECT_TIMEOUT)
            support_page.send_message_button.click(timeout=EXPECT_TIMEOUT)

            expect(support_page.bubble_in(support_page.last_user_item())).to_have_text(
                FIRST_MESSAGE, timeout=EXPECT_TIMEOUT
            )
            # The copy button renders only on a COMPLETED assistant message
            # (MessageItem.tsx: content && !isStreaming && !isAnimating), which
            # makes its count the accurate completion signal — an item-count
            # delta fires while the reply is still arriving.
            expect(support_page.message_copy_buttons).to_have_count(
                baseline_copies + 1, timeout=REPLY_TIMEOUT
            )
            expect(support_page.message_items).to_have_count(
                baseline_items + 2, timeout=EXPECT_TIMEOUT
            )
            # The product clears the input on a successful send (a REJECTED
            # input is not cleared — digest quirk 3), so this is a real signal.
            expect(support_page.message_input_field).to_have_value(
                "", timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 3 — Navigate to the Agents page via the sidebar (widget left open)"
        ):
            support_page.sidebar_menu_item("agents").click()
            page.wait_for_url("**/agents/all", timeout=NAV_TIMEOUT)

        with allure.step(
            "Step 4 — Verify the widget is still open with the conversation intact"
        ):
            # No launcher click in between — the widget must survive the route
            # change already open. This is the assertion the case exists for.
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)
            expect(support_page.message_input_field).to_be_visible(timeout=EXPECT_TIMEOUT)
            expect(support_page.message_items).to_have_count(
                baseline_items + 2, timeout=EXPECT_TIMEOUT
            )
            expect(support_page.message_copy_buttons).to_have_count(
                baseline_copies + 1, timeout=EXPECT_TIMEOUT
            )
            expect(support_page.user_message_item_with_text(FIRST_MESSAGE)).to_have_count(
                baseline_first_message + 1, timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 5 — Navigate back to the Chat page"):
            support_page.sidebar_menu_item("chat").click()
            page.wait_for_url("**/chat", timeout=NAV_TIMEOUT)

        with allure.step(
            "Step 6 — Verify the previous session messages are still visible"
        ):
            # Deliberately no conditional reopen: the widget does not close, and
            # a branch that never executes would mask a regression to a routed
            # mount point (AFS § Known Deviations).
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)
            expect(support_page.message_items).to_have_count(
                baseline_items + 2, timeout=EXPECT_TIMEOUT
            )
            expect(support_page.message_copy_buttons).to_have_count(
                baseline_copies + 1, timeout=EXPECT_TIMEOUT
            )
            expect(support_page.user_message_item_with_text(FIRST_MESSAGE)).to_have_count(
                baseline_first_message + 1, timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 7 — Send a follow-up and verify the reply lands in the same session"
        ):
            support_page.send_message_via_testid(
                FOLLOW_UP_MESSAGE, timeout=EXPECT_TIMEOUT
            )
            expect(support_page.bubble_in(support_page.last_user_item())).to_have_text(
                FOLLOW_UP_MESSAGE, timeout=EXPECT_TIMEOUT
            )
            expect(support_page.message_copy_buttons).to_have_count(
                baseline_copies + 2, timeout=REPLY_TIMEOUT
            )
            expect(support_page.message_items).to_have_count(
                baseline_items + 4, timeout=EXPECT_TIMEOUT
            )
            expect(support_page.message_input_field).to_have_value(
                "", timeout=EXPECT_TIMEOUT
            )
            # Same session, not a fresh one: counting alone can be satisfied by
            # a reset conversation of the same size — the pre-navigation message
            # text is what proves the thread survived.
            expect(support_page.user_message_item_with_text(FIRST_MESSAGE)).to_have_count(
                baseline_first_message + 1, timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 8 — No console errors across both navigations"):
            assert console_errors == [], f"Unexpected console errors: {console_errors}"
