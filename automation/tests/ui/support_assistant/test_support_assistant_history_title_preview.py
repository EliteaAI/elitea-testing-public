"""Support Assistant — history session shows the correct title, timestamp and preview.

TMS case ELITEA-2427 · AFS
``test-specs/support-assistant/l2_history-session-preview-and-title_ELITEA-2427.md``

Creates a fresh Support Assistant conversation from a distinctive message, waits
for the live assistant reply, pushes the session into history with New chat, then
reads the newest history entry and asserts the three observables the case names:
a recognizable label (Step 6), a timestamp/date indicator (Step 7) and a short
preview of the conversation content (Step 8 / Expected Final State).

**RED BY DESIGN on Steps 7 and 8.** A history entry's entire DOM body is the
conversation's generated title — no timestamp node, no preview node, no ``title``
attribute, no ``aria-label`` (``elitea_assistant`` ``ChatHeader.tsx``:
``{conversation.name}``). Both gaps are filed, open and deterministic, so they are
written as the CORRECT expected behaviour with ``expect.soft()`` per
``.agents/testing.md`` § Merge gate ▸ sanctioned-RED (analysis-time entry):

- ``EliteaAI/elitea-testing-public#1658`` — Step 7, no timestamp/date indicator
  (the list API returns ``created_at``/``updated_at``; the UI drops them).
- ``EliteaAI/elitea-testing-public#1659`` — Step 8, no conversation preview
  (upstream issue 5723, unshipped — the case text says so itself).

They are a closed, enumerable set of two on one render site, so a gate run showing
either or both is one sanctioned signature; anything else red blocks. Neither is
inverted into "assert no timestamp is shown" — that would be reverse-masking, it
would go green today AND stay green after the fix, permanently hiding the feature.

Two documented divergences from the case text (filed as ``#1660``, a case-text
clarification rather than a defect — the product is correct):

1. **New chat is clicked BEFORE the distinctive message.** The widget restores
   ``items[0]`` of the conversation list on mount (``initAssistant.hook.ts``), so
   sending straight after opening joins a PRE-EXISTING conversation and creates no
   history entry at all — the case's own Step 6 observable would never exist. With
   New chat first, ``handleSend`` calls ``createConversation()`` and prepends the
   new session locally. This is a navigation choice through the product's own
   control, not a substitution.
2. **The label is asserted by distinctive-token containment, never equality with
   the sent message.** The title is an LLM paraphrase delivered over the socket
   (``conversation_name_updated``); live, ``HISTORY-TITLE-TEST: Tell me about
   ELITEA`` became ``HISTORY-TITLE-TEST: Tell about ELITEA`` — "me" dropped.
   Asserting the case's literal wording would be reverse-masking a stale
   hypothesis against a correct product.

That paraphrase is also what makes the Step 8 assertion a real discriminator: the
TITLE provably does not carry the verbatim message, so ``to_contain_text(MESSAGE)``
can only pass once genuine conversation content is rendered.

Fidelity: no substitutions. No ``page.route``, no ``route.fulfill``, no
``page.evaluate`` state injection, no API-seeded preconditions. Every asserted
value — the entry text, the entry count, the reply completion, the console and
pageerror channels — is produced by the live product reached through the real UI:
real launcher click, real ``fill`` into the React textarea, real send click, real
LLM round trip, real socket-delivered title.

Baselines, not absolutes: history is shared account data, the server list appears
capped at ~20 while the client prepends locally (live: 20 -> 21), so the count is
asserted as a ``+1`` delta against a baseline read before the send. No teardown —
the suite convention on this surface leaves conversations behind, and the widget's
own restore behaviour depends on them existing.

Markers:
    - p2 / support_assistant / ui / regression / slow (one live LLM round trip;
      observed 74 s reply, 83 s end-to-end headless)

Usage::

    cd automation
    ../.venv/bin/pytest tests/ui/support_assistant/test_support_assistant_history_title_preview.py -v
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
    pytest.mark.slow,
]

WIDGET_TIMEOUT = 15_000
EXPECT_TIMEOUT = 10_000

# Observed reply latency on this surface: 31-135 s (surface digest quirks 5/15;
# 74 s in the ELITEA-2427 analysis run). 120 s is tight.
REPLY_TIMEOUT = 180_000

# The title arrives over the socket (``conversation_name_updated``), independently
# of the reply itself. Live it was already present at the first poll after the
# reply landed; 60 s is headroom, not an expectation.
TITLE_TIMEOUT = 60_000

# The two known-defect assertions run against a history entry whose text is ALREADY
# rendered (the hard label assertion above them just resolved it), so a correctly
# built entry would match instantly. A long timeout here would add two minutes of
# dead wait to every RED-by-design run without making either assertion stronger.
KNOWN_DEFECT_TIMEOUT = 1_000

WIDGET_TITLE = "ELITEA Support"

# Case-mandated verbatim (TMS Step 2). Deliberately NOT run-unique: the assertions
# read index 0, which is the conversation this run just created and prepended, and
# the token only has to survive the backend's paraphrase.
MESSAGE = "HISTORY-TITLE-TEST: Tell me about ELITEA"
TOKEN = "HISTORY-TITLE-TEST"

# A "New chat" is not empty — it opens with exactly one assistant greeting, and a
# copy button renders only on a COMPLETED assistant message (surface digest quirks
# 9/10). So this is both the fresh-session settle and the reply-count baseline.
GREETING_COPY_BUTTONS = 1

# Any wall-clock-ish indicator: 14:32, 22/08/2026, 2026-08-22, 8.22.26.
TIMESTAMP_RE = re.compile(r"\d{1,2}[:/.\-]\d{2}|\d{4}-\d{2}-\d{2}")

# Vite HMR and the dev server's own polling socket log ERR_CONNECTION_REFUSED
# entries unrelated to the app (surface digest quirk 23). Only these two are
# excluded — every other console error still fails the test.
_DEV_SERVER_NOISE = ("@vite/client", "/socket.io/")


def _is_dev_server_noise(text: str) -> bool:
    """Whether *text* is a Vite/dev-server connection error, not an app error."""
    return "ERR_CONNECTION_REFUSED" in text and any(p in text for p in _DEV_SERVER_NOISE)


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-2427_history-session-shows-correct-preview-and-title.md",
    "onetest-ai Test Case link",
)
@allure.issue(
    "https://github.com/EliteaAI/elitea-testing-public/issues/1658",
    "Known defect — history entry renders no timestamp/date indicator",
)
@allure.issue(
    "https://github.com/EliteaAI/elitea-testing-public/issues/1659",
    "Known defect — history entry renders no conversation preview",
)
class TestSupportAssistantHistoryTitleAndPreview:
    """ELITEA-2427 — history session shows correct preview and title."""

    def test_history_entry_shows_title_timestamp_and_preview(self, page):
        """Newest history entry carries the session's label, timestamp and preview."""
        console_errors: list[str] = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text)
            if msg.type == "error" and not _is_dev_server_noise(msg.text)
            else None,
        )
        # An uncaught exception never reaches the console listener, so the console
        # channel alone would not see the failure mode the case's "all steps
        # complete without errors" criterion names. Both are registered before
        # Step 1 — a listener armed mid-flow cannot observe what precedes it.
        page_errors: list[str] = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        support_page = SupportAssistantPage(page)

        with allure.step("Step 1 — Open the Support Assistant widget"):
            ChatPage(page).navigate_to_chat()
            support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)
            expect(support_page.widget_header_title).to_have_text(
                WIDGET_TITLE, timeout=EXPECT_TIMEOUT
            )

            # The History button is ``disabled`` until ``history.length > 0``
            # (``ChatHeader.tsx``), which makes this the product's own "the
            # conversation list has loaded" signal — no networkidle, no sleep.
            expect(support_page.history_toggle_button).to_be_enabled(
                timeout=WIDGET_TIMEOUT
            )
            support_page.open_history_via_testid(timeout=EXPECT_TIMEOUT)
            expect(support_page.history_dropdown).to_be_visible(timeout=EXPECT_TIMEOUT)

            # Baseline, never an absolute: shared account data, the server list
            # appears capped at ~20, and the client prepends locally on top of it.
            history_count_before = support_page.get_history_item_count_via_testid()
            assert history_count_before >= 1, (
                "history panel opened but listed no conversations"
            )

            # Close the dropdown before touching the composer — it renders over
            # the message area, and leaving it open would have the New chat click
            # doing double duty as a dismiss.
            support_page.history_toggle_button.click(timeout=EXPECT_TIMEOUT)
            expect(support_page.history_dropdown).not_to_be_visible(
                timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 2 — Start a new session (case-text deviation #1660), then send "
            "the distinctive message"
        ):
            # Without this, the message joins the conversation the widget restored
            # on mount and no new history entry is ever created (AFS § Known
            # Deviations 1). The product is correct; the case assumes an empty
            # account.
            support_page.start_new_chat_via_testid(timeout=WIDGET_TIMEOUT)
            expect(support_page.message_copy_buttons).to_have_count(
                GREETING_COPY_BUTTONS, timeout=WIDGET_TIMEOUT
            )

            support_page.set_message_text(MESSAGE)
            # Real typing enables Send immediately; #1581 ("Send never enables")
            # is a non-reproducing false bug produced by synthetic value writes
            # against the React controlled textarea (AFS § Known Defects).
            expect(support_page.send_message_button).to_be_enabled(
                timeout=EXPECT_TIMEOUT
            )
            support_page.send_message_button.click(timeout=EXPECT_TIMEOUT)

            expect(support_page.bubble_in(support_page.last_user_item())).to_have_text(
                MESSAGE, timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 3 — Wait for the assistant response"):
            # The copy button renders only on a COMPLETED assistant message
            # (``MessageItem.tsx``: ``!isStreaming && !isAnimating``), which makes
            # its count the accurate completion signal — an item-count delta fires
            # while the reply is still arriving.
            expect(support_page.message_copy_buttons).to_have_count(
                GREETING_COPY_BUTTONS + 1, timeout=REPLY_TIMEOUT
            )

        with allure.step("Step 4 — Click New Chat to push the session into history"):
            support_page.start_new_chat_via_testid(timeout=WIDGET_TIMEOUT)
            expect(support_page.message_copy_buttons).to_have_count(
                GREETING_COPY_BUTTONS, timeout=WIDGET_TIMEOUT
            )
            # The session really was left behind rather than merely re-rendered:
            # its distinctive user message is gone from the composer's list.
            expect(
                support_page.user_message_item_with_text(MESSAGE)
            ).to_have_count(0, timeout=EXPECT_TIMEOUT)

        with allure.step("Step 5 — Open the History panel"):
            expect(support_page.history_toggle_button).to_be_enabled(
                timeout=WIDGET_TIMEOUT
            )
            support_page.open_history_via_testid(timeout=EXPECT_TIMEOUT)
            expect(support_page.history_dropdown).to_be_visible(timeout=EXPECT_TIMEOUT)

            # The case says Step 4 "pushes the session into history" but asserts
            # nothing about it; without this delta, that step is unverified.
            expect(support_page.history_items).to_have_count(
                history_count_before + 1, timeout=EXPECT_TIMEOUT
            )

        newest_entry = support_page.newest_history_item()

        with allure.step(
            "Step 6 — The most recent history entry shows a recognizable label"
        ):
            # Containment of the distinctive token, NOT equality with the sent
            # message: the label is a backend-generated paraphrase delivered over
            # the socket, and live it dropped a word ("Tell about" for "Tell me
            # about"). Asserting the case's literal wording would fail against a
            # correctly behaving product (AFS § Known Deviations 2, #1660).
            expect(newest_entry).to_contain_text(TOKEN, timeout=TITLE_TIMEOUT)

            # Index 0 is enabled exactly because Step 4's New chat cleared
            # ``currentConversationId`` (an entry is ``disabled`` only while it is
            # the open conversation). A regression here would silently break every
            # "open a previous session" spec on this surface.
            expect(newest_entry).to_be_enabled(timeout=EXPECT_TIMEOUT)

        with allure.step(
            "Step 7 — The history entry shows a timestamp or date indicator "
            "(KNOWN DEFECT #1658 — RED by design, soft-asserted)"
        ):
            # Known defect: #1658 — the entry renders no timestamp, no date, no
            # ``title`` attribute and no ``aria-label``; its whole body is
            # ``{conversation.name}``. The list API returns ``created_at`` and
            # ``updated_at`` for every entry and the UI drops them. This encodes
            # the case's EXPECTED behaviour and flips green when the product ships.
            expect.soft(newest_entry).to_contain_text(
                TIMESTAMP_RE, timeout=KNOWN_DEFECT_TIMEOUT
            )

        with allure.step(
            "Step 8 / Expected Final State — The history entry shows a short "
            "preview of the conversation content (KNOWN DEFECT #1659 — RED by "
            "design, soft-asserted)"
        ):
            # Known defect: #1659 — no preview node and no second line (upstream
            # issue 5723, unshipped; the case text says so itself). The VERBATIM
            # message is the discriminator: the generated title provably does not
            # contain it (the generator drops words), so this can only pass once
            # real conversation content is rendered.
            expect.soft(newest_entry).to_contain_text(
                MESSAGE, timeout=KNOWN_DEFECT_TIMEOUT
            )

        with allure.step(
            "Pass criterion — all steps completed without errors (console and "
            "pageerror channels clean)"
        ):
            # The case's closing criterion has no step of its own, and it is two
            # independent channels: a client-side exception during history
            # hydration leaves the console empty, and an uncaught exception never
            # reaches the console listener at all. The analysis run recorded zero
            # of each over the identical flow, so anything captured here is real.
            assert console_errors == [], f"Unexpected console errors: {console_errors}"
            assert page_errors == [], f"Uncaught page errors: {page_errors}"
