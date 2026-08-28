"""Reaching a genuinely blank chat composer, as a shared helper.

Why it is needed rather than defensive: the SPA restores the last-viewed
conversation (see ``ChatPage.navigate_to_chat()``), so a bare
``navigate_to_chat()`` + ``send_message()`` appends to an EXISTING conversation
instead of creating one. Clicking +Chat and then verifying BOTH the id-less URL
and a zero message count -- and verifying they HOLD for a settle window, because
the restore can land after the blank greeting renders -- is what makes "create a
new conversation" a fact rather than a hope.

Provenance. This is the ``_open_genuinely_blank_conversation()`` /
``_poll_blank_state_holds()`` pair that grew, suite-locally, through
``tests/ui/chat/test_invite_users_add_cancel_close.py`` (ELITEA-2175/2176) ->
``tests/ui/chat/test_team_users_mention_and_remove_participants.py`` ->
``tests/ui/settings/test_context_settings_new_conversations_only.py``
(ELITEA-2390). Those three specs are merged and keep their own copies: touching
them would be a non-additive change to shared, already-reviewed code
(Hard Rule 3). This module is the extraction Hard Rule 7 asks for at the fourth
call site, and the three ancestors should migrate onto it opportunistically the
next time each is edited for its own reasons.

The settle window is polled, never slept-then-checked-once: a single sample at
the END of the window only observes the window's final state, so a restore that
lands inside it and is superseded would be invisible -- which is precisely the
race this helper exists to close. Polling also exits the instant either signal
flips, turning a definitive failure into an immediate retry.

``time.sleep`` is safe as the poll interval here (unlike the WebSocket-frame
case in ``.agents/testing.md``): every iteration calls ``get_message_count()``,
a Playwright call, so the sync dispatcher is pumped on each pass.
"""

import logging
import re
import time

logger = logging.getLogger(__name__)

#: ``/chat`` with no conversation id (query string tolerated).
BLANK_URL_PATTERN = re.compile(r"/chat/?(?:\?.*)?$")

BLANK_SETTLE_MS = 1500  # The last-viewed-conversation restore's own timing window
BLANK_POLL_INTERVAL_S = 0.25
GREETING_TIMEOUT = 5000
BLANK_ATTEMPTS = 3


def poll_blank_state_holds(
    chat,
    settle_ms: int = BLANK_SETTLE_MS,
    poll_interval_s: float = BLANK_POLL_INTERVAL_S,
) -> tuple[bool, str]:
    """Poll message-count + URL across *settle_ms*.

    Returns ``(settled, reason)`` -- ``settled`` is False (with a reason) the
    moment either signal flips during the window, True only if both held blank
    for the entire window.
    """
    deadline = time.monotonic() + settle_ms / 1000.0
    while time.monotonic() < deadline:
        time.sleep(poll_interval_s)
        count = chat.get_message_count()
        url = chat.page.url
        if count != 0 or not BLANK_URL_PATTERN.search(url):
            return False, f"blank state reverted mid-settle (url={url!r}, message_count={count})"
    return True, ""


def open_blank_composer(chat, timeout: int = 30000) -> None:
    """Reach a genuinely blank composer (URL ``/chat`` with no id, 0 messages)."""
    last_reason = "unknown"
    for attempt in range(BLANK_ATTEMPTS):
        chat.click_create_conversation(timeout=timeout)
        try:
            chat.new_conversation_greeting.wait_for(state="visible", timeout=GREETING_TIMEOUT)
        except Exception:  # noqa: BLE001 -- retried below, reason recorded
            last_reason = "new-conversation greeting never appeared"
            logger.warning("Attempt %d: %s - retrying", attempt + 1, last_reason)
            continue
        if chat.get_message_count() != 0:
            last_reason = "blank greeting shown but the conversation has message history"
            logger.warning("Attempt %d: %s - retrying", attempt + 1, last_reason)
            continue
        settled, reason = poll_blank_state_holds(chat)
        if not settled:
            last_reason = reason
            logger.warning("Attempt %d: %s - retrying", attempt + 1, last_reason)
            continue
        return
    raise AssertionError(
        f"Could not reach a blank composer after {BLANK_ATTEMPTS} +Chat attempts - "
        f"last reason: {last_reason}"
    )
