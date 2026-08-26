---
name: Add-users modal close transition races an immediate Send click
description: Sending a message right after click_add_users_confirm() can silently drop the send click if it fires mid-close-transition — wait for add_users_dialog hidden first.
type: feedback
---

Found while implementing ELITEA-2188 (public-conversation green icon).

**Symptom:** after `open_add_users_modal()` -> `search_and_select_add_user()` ->
`click_add_users_confirm()`, immediately calling `chat.send_message(text,
use_enter=False)` intermittently leaves the message typed in the composer,
never sent — `page.wait_for_url(re.compile(r"/chat/\d+"), ...)` times out
(15s) with no exception from `send_message()` itself (the send button click
"succeeds" per Playwright, just doesn't navigate). Reproduced 2/2 in a clean
`--reruns=0` run; a careful MANUAL Playwright-MCP repro of the identical
sequence did NOT reproduce it, because each MCP tool call has enough natural
round-trip latency to let the modal's close transition finish before the next
action — pytest's back-to-back Python calls don't have that gap.

**Root cause (inferred, not exhaustively proven):** `send_button.click(force=True,
timeout=5000)` in `ChatPage.send_message()` bypasses actionability waits
specifically because MUI overlays can intercept the send button
(documented in that method's own comment) — but `force=True` firing DURING
the "Add users" modal's own MUI Dialog close transition is a plausible
target for a lost click (transient DOM/overlay state mid-animation).

**Fix:** add `chat.add_users_dialog.wait_for(state="hidden", timeout=...)`
right after `click_add_users_confirm()`, before any composer interaction
(fill/send). This is a real framework wait (dialog leaving the DOM), not a
sleep. Apply to ANY flow that sends a message immediately after confirming
the Add-users modal — `test_invite_users_add_cancel_close.py` and
`test_team_users_mention_and_remove_participants.py` may be exposed to the
same race if their own Send happens to land in this same narrow window
(not confirmed either way — they weren't observed failing this way, but
their Send isn't always the very next action after Add confirm).
