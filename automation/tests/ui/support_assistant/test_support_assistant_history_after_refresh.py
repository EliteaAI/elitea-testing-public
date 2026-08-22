"""Support Assistant — history loads correctly after page refresh.

TMS case ELITEA-2423 · AFS
``test-specs/support-assistant/l2_history-loads-correctly-after-page-refresh_ELITEA-2423.md``

Sends a message in the Support Assistant widget, refreshes the browser page,
reopens the widget, opens the conversation-history panel, opens a previous
session from it, then repeats the send-and-refresh cycle — asserting that every
``GET /api/v2/support_assistant/conversations/`` the reloads trigger comes back
200 (never 500) and that the history panel keeps loading.

Two source facts shape this spec (both confirmed live, AFS § How this surface
actually works):

1. ``GET .../conversations/`` fires on PAGE LOAD, not on the History click —
   ``initAssistant.hook.ts`` calls ``getConversations()`` in the mount effect and
   the History button only flips local state over the already-fetched array
   (live: zero requests during the click). So the response collector is armed
   around the RELOAD; registering it on the click would capture nothing and the
   case's own assertion would pass vacuously. The endpoint is also hit twice per
   load (React StrictMode double-invokes the effect in dev), which is why every
   captured status is asserted rather than the first — tolerating a 500 on the
   second call would miss exactly the regression this case exists to catch.
2. A history entry is ``disabled`` exactly when it is the currently-open
   conversation (``ChatHeader.tsx``). After a refresh the widget auto-restores
   the list's first conversation, so index 0 is always disabled at that moment;
   the case's "can be opened" is satisfied by the first ``:not([disabled])``
   entry, and clicking index 0 would be a silent no-op.

Fidelity: no substitutions. Every asserted observable — HTTP statuses, widget
visibility, message items, message text, copy buttons, history entries, console
— is produced by the live product. Both replies are real live responses; typing
uses real input events (``fill``), never ``page.evaluate`` value assignment.

Baselines, not absolutes: the widget restores whatever conversation the test
user already has, history is shared account data, and this spec deliberately
leaves its messages behind (no teardown — the suite convention), so counts are
asserted as deltas against a baseline or as stability across the refresh. The
two probe messages carry a run-unique ``uuid4`` suffix, which is what makes the
message-text assertions exact instead of accumulating across runs.

Markers:
    - p2 / support_assistant / ui / regression / slow (two live LLM round trips
      plus two full page reloads put the runtime around 110-150 s)

Usage::

    cd automation
    ../.venv/bin/pytest tests/ui/support_assistant/test_support_assistant_history_after_refresh.py -v
"""

import re
from uuid import uuid4

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
    pytest.mark.slow,
]

WIDGET_TIMEOUT = 15_000
EXPECT_TIMEOUT = 10_000
RELOAD_TIMEOUT = 60_000

# Observed reply latency on this surface: 31-135 s (surface digest quirks 5/15;
# 32.3 s and 31.8 s in the ELITEA-2423 analysis run). 120 s is tight.
REPLY_TIMEOUT = 180_000

WIDGET_TITLE = "ELITEA Support"

# The conversation LIST endpoint the case names, and the per-conversation DETAIL
# endpoint that selecting a history entry fires. Distinct paths (``conversations``
# vs ``conversation``), so the two patterns cannot cross-match.
LIST_URL_RE = re.compile(r"/api/v2/support_assistant/conversations/?(?:\?|$)")
DETAIL_URL_RE = re.compile(r"/api/v2/support_assistant/conversation/[^/?]+")

# Vite HMR and the dev server's own polling socket log ERR_CONNECTION_REFUSED
# entries unrelated to the app (surface digest quirk 23). Only these two are
# excluded — every other console error still fails the test.
_DEV_SERVER_NOISE = ("@vite/client", "/socket.io/")


def _is_dev_server_noise(text: str) -> bool:
    """Whether *text* is a Vite/dev-server connection error, not an app error."""
    return "ERR_CONNECTION_REFUSED" in text and any(p in text for p in _DEV_SERVER_NOISE)


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-2423_history-loads-correctly-after-page-refresh.md",
    "onetest-ai Test Case link",
)
class TestSupportAssistantHistoryAfterRefresh:
    """ELITEA-2423 — history loads correctly after page refresh."""

    def test_history_loads_correctly_after_page_refresh(self, page):
        """History still loads, and lists an openable session, across two refreshes."""
        run_id = uuid4().hex[:8]
        first_message = f"ELITEA-2423 refresh probe A {run_id}"
        second_message = f"ELITEA-2423 refresh probe B {run_id}"

        console_errors: list[str] = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text)
            if msg.type == "error" and not _is_dev_server_noise(msg.text)
            else None,
        )

        # Collect every conversation-LIST response, rather than waiting for one:
        # the request is issued by the page-load mount effect (twice under
        # StrictMode), so there is no single response to await around a click.
        list_statuses: list[int] = []

        def _record_list_response(response):
            if LIST_URL_RE.search(response.url) and response.request.method == "GET":
                list_statuses.append(response.status)

        page.on("response", _record_list_response)

        support_page = SupportAssistantPage(page)

        with allure.step(
            "Step 1 — Open the Support Assistant widget, send a message, wait for the response"
        ):
            ChatPage(page).navigate_to_chat()
            support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)
            expect(support_page.widget_header_title).to_have_text(
                WIDGET_TITLE, timeout=EXPECT_TIMEOUT
            )

            # The widget restores the previous session on open — never assume an
            # empty conversation (surface digest quirks 2/10).
            baseline_items = support_page.get_message_item_count()
            baseline_copies = support_page.get_copy_button_count()

            support_page.set_message_text(first_message)
            # Real typing enables Send immediately; #1581 ("Send never enables")
            # is a non-reproducing false bug produced by synthetic value writes
            # against the React controlled textarea (AFS § Known Defects).
            expect(support_page.send_message_button).to_be_enabled(timeout=EXPECT_TIMEOUT)
            support_page.send_message_button.click(timeout=EXPECT_TIMEOUT)

            expect(support_page.bubble_in(support_page.last_user_item())).to_have_text(
                first_message, timeout=EXPECT_TIMEOUT
            )
            # The copy button renders only on a COMPLETED assistant message
            # (``MessageItem.tsx``: ``!isStreaming && !isAnimating``), which makes
            # its count the accurate completion signal — an item-count delta fires
            # while the reply is still arriving.
            expect(support_page.message_copy_buttons).to_have_count(
                baseline_copies + 1, timeout=REPLY_TIMEOUT
            )
            expect(support_page.message_items).to_have_count(
                baseline_items + 2, timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 2 — Refresh the browser page"):
            list_statuses.clear()
            page.reload(wait_until="domcontentloaded", timeout=RELOAD_TIMEOUT)
            # The list request is fired by the mount effect, so wait on the
            # product's own "history has loaded" signal rather than the network:
            # the History button is disabled until ``history.length > 0``.
            expect(support_page.history_toggle_button).to_be_enabled(
                timeout=WIDGET_TIMEOUT
            )
            assert list_statuses, (
                "no GET /api/v2/support_assistant/conversations/ observed across the reload"
            )
            assert all(status == 200 for status in list_statuses), (
                f"conversation-list request failed after refresh: {list_statuses}"
            )
            first_refresh_statuses = list(list_statuses)

        with allure.step("Step 3 — After the reload, open the Support Assistant widget"):
            # The widget does NOT auto-open after a reload (surface digest quirk
            # 29 — in contrast to an in-app route change, which never closes it),
            # so an explicit launcher click is required and is not a workaround.
            expect(support_page.widget).to_have_count(0)
            support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)

            # The pre-refresh conversation survived: without this, "open the
            # widget" would pass just as well on an empty one.
            expect(
                support_page.user_message_item_with_text(first_message)
            ).to_have_count(1, timeout=EXPECT_TIMEOUT)
            expect(support_page.message_items).to_have_count(
                baseline_items + 2, timeout=EXPECT_TIMEOUT
            )
            expect(support_page.message_copy_buttons).to_have_count(
                baseline_copies + 1, timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 4 — Open the History panel; the conversation-list request returned 200"
        ):
            # The case's own assertion. The statuses were captured around the
            # reload in Step 2 because that is where the product issues the
            # request — arming a collector on this click would capture nothing.
            assert all(status == 200 for status in first_refresh_statuses), (
                "GET /api/v2/support_assistant/conversations/ did not return 200 after the "
                f"refresh: {first_refresh_statuses}"
            )
            support_page.open_history_via_testid(timeout=EXPECT_TIMEOUT)
            expect(support_page.history_dropdown).to_be_visible(timeout=EXPECT_TIMEOUT)
            history_count_before = support_page.get_history_item_count_via_testid()
            assert history_count_before >= 1, (
                "history panel opened but listed no conversations"
            )

        with allure.step(
            "Step 5 — The previous session is listed in history and can be opened"
        ):
            # "Openable" means an enabled entry: index 0 is the conversation the
            # widget just auto-restored and is disabled by design, so clicking it
            # would be a no-op that asserts nothing.
            openable = support_page.first_openable_history_item()
            expect(openable).to_be_visible(timeout=EXPECT_TIMEOUT)

            with page.expect_response(
                lambda response: bool(DETAIL_URL_RE.search(response.url))
                and response.request.method == "GET",
                timeout=EXPECT_TIMEOUT,
            ) as detail_response:
                openable.click(timeout=EXPECT_TIMEOUT)
            assert detail_response.value.status == 200, (
                "opening a previous session returned "
                f"{detail_response.value.status} for {detail_response.value.url}"
            )

            # The conversation really swapped: the run-unique probe message
            # belongs to the session we just left, so it must be gone. This is
            # deterministic where a message-count change is not — another
            # conversation may happen to hold the same number of messages.
            expect(
                support_page.user_message_item_with_text(first_message)
            ).to_have_count(0, timeout=EXPECT_TIMEOUT)
            expect(support_page.history_dropdown).not_to_be_visible(
                timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 6 — Send another message, refresh again, verify history still loads"
        ):
            # Fresh baselines: this is a different conversation from Step 1's.
            items_in_opened_session = support_page.get_message_item_count()
            copies_in_opened_session = support_page.get_copy_button_count()

            support_page.send_message_via_testid(second_message, timeout=EXPECT_TIMEOUT)
            expect(support_page.bubble_in(support_page.last_user_item())).to_have_text(
                second_message, timeout=EXPECT_TIMEOUT
            )
            expect(support_page.message_copy_buttons).to_have_count(
                copies_in_opened_session + 1, timeout=REPLY_TIMEOUT
            )
            expect(support_page.message_items).to_have_count(
                items_in_opened_session + 2, timeout=EXPECT_TIMEOUT
            )

            list_statuses.clear()
            page.reload(wait_until="domcontentloaded", timeout=RELOAD_TIMEOUT)
            expect(support_page.history_toggle_button).to_be_enabled(
                timeout=WIDGET_TIMEOUT
            )
            assert list_statuses, (
                "no GET /api/v2/support_assistant/conversations/ observed across the "
                "second reload"
            )
            assert all(status == 200 for status in list_statuses), (
                f"conversation-list request failed after the second refresh: {list_statuses}"
            )

            support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)
            support_page.open_history_via_testid(timeout=EXPECT_TIMEOUT)
            expect(support_page.history_dropdown).to_be_visible(timeout=EXPECT_TIMEOUT)
            # "Still loads" must not be satisfiable by a panel that lost its
            # entries — the count is asserted stable, not merely non-zero.
            expect(support_page.history_items).to_have_count(
                history_count_before, timeout=EXPECT_TIMEOUT
            )

            # Deliberately no assertion on ``second_message`` here: restore after
            # a refresh always loads the list's FIRST conversation, which is
            # ordered by creation rather than by last activity, so the session
            # opened in Step 5 is not the one restored (AFS § Known Deviations 3).

            assert console_errors == [], f"Unexpected console errors: {console_errors}"
