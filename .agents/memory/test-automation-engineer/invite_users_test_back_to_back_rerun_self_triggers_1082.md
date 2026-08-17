---
name: Invite-users test back-to-back rerun self-triggers #1082
description: Re-running test_invite_users_add_cancel_close.py repeatedly without a pause reliably reproduces the #1082 stale-conversation flake on its own.
type: feedback
---

`tests/ui/chat/test_invite_users_add_cancel_close.py::TestInviteUsersAddCancelClose::test_invite_users_add_persists_cancel_and_close_discard`
(ELITEA-2167, covers ELITEA-2168/2169 too via already-covered dispositions) is
NOT safe to re-run back-to-back in the same session with no pause between runs,
for `already-covered` live-reconfirmation passes.

**Mechanism:** the test's own Step 1 asserts a brand-new conversation has NO
participants badge yet (reverse-masking guard vs. the case text). If a PRIOR
run failed at or after this point, `conv_id` is only set once a later step
actually persists the conversation server-side (first Send) — so a run that
fails before that point leaves its just-created, still-blank conversation
un-cleaned (the `finally` cleanup skips it, since `conv_id` is falsy). The next
run's `_open_blank_conversation()` retry-guarded helper can then pick up that
orphaned conversation instead of a genuinely fresh one, and it already has a
stale participants badge from residual state — Step 1's "no badge yet"
assertion fails. This is exactly the already-tracked #1082 flake
("invite-users test fails only in a full run — project-switch settling leaves
a stale/deleted conversation"), reliably self-triggered by 2+ consecutive
invocations with no cleanup pause, observed live 2026-08-15 (chat-remaining-w10,
ELITEA-2169 already-covered pass — 3 runs: 1 clean, 2 hit exactly this).

**What to do:** when live-reconfirming this covering test for an
`already-covered` disposition, ONE clean run is sufficient evidence (don't
chase a green streak by re-running immediately — you'll manufacture #1082
yourself). If you must re-run, either (a) accept a single run as your evidence
and stop, or (b) manually verify/clean project 471's conversation list between
runs first. A Step-1 failure on re-run N>1 in the SAME session is #1082, not a
new regression — don't file a duplicate.

**Update (ELITEA-2175/2176, same day):** the SAME underlying mechanism —
`ChatPage.navigate_to_chat()`'s own docstring: "the SPA may redirect to the
last-viewed conversation stored in the browser session" — also fires on a
genuinely FRESH session (not just self-triggered reruns), reproduced 4/4
times, and as a DELAYED effect (fires ~1-2s AFTER a blank greeting + 0
message count are already observed, not synchronously with the +Chat
click). `_open_blank_conversation()`'s single check (greeting visible) is
provably insufficient — confirmed the ORIGINAL merged
`TestInviteUsersAddCancelClose` test now fails consistently (2/2) on this in
the current environment, unrelated to any rerun of my own. Fix used
(additive, does not touch that shared helper): a sibling
`_open_genuinely_blank_conversation()` in the same test file — click +Chat,
verify greeting + message count 0, THEN wait ~1.5s and RE-verify both
message count AND `page.url` (must stay bare `/chat`, no numeric id) before
proceeding, retrying up to 3x. A future dispatch that fixes
`_open_blank_conversation()` itself needs the shared-file regression
protocol (enumerate + re-run every caller: at minimum ELITEA-2167's own test
plus this file's two new ones).

**Update (ELITEA-2188, 2026-08-15): NOT reunder-only — a SECOND back-to-back
`+Chat` click within ONE test run (no rerun involved) reliably hits it too.**
A test creating two fresh conversations (open blank -> send -> open blank
AGAIN for a second one) needs the `_open_genuinely_blank_conversation`-style
settle-and-retry guard on EVERY `+Chat` click, not just the first. Confirmed
live: the first click after a completed Send landed back on the just-sent
conversation (greeting not visible) on the very first attempt, self-correcting
only on the retry. Generalize this guard to "any test opening 2+ fresh
conversations", not "tests that get rerun".
