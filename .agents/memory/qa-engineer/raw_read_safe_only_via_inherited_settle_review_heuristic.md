---
name: A bare sync read next to a just-fixed polling assertion needs its own race check
description: When reviewing an extend-existing PR where one gap assertion (e.g. GA3) needed to move from a synchronous .is_enabled()/.is_disabled() read to a polling expect(...).to_be_enabled()/to_be_disabled() to fix a real SPA-navigation race, check every SIBLING raw read on the same button/element in the same diff — it may only be safe today because it inherits an incidental settle (a fixed sleep + networkidle + visibility wait) baked into the method it follows, not because the underlying transition is actually synchronous.
type: feedback
---

## What happened

Reviewing PR #682 (ELITEA-2090, extend-existing onto
`test_create_conversation_via_ui_button`), GA3 (`sidebar-create-button`
re-enables on Send) had already been fixed by the implementer from a bare
`assert chat.create_conversation_button.is_enabled()` to
`expect(chat.create_conversation_button).to_be_enabled(timeout=NAVIGATION_TIMEOUT)`,
because `send_message(use_enter=True)` returns as soon as the Enter keypress
is dispatched — before the SPA's async `/chat` → `/chat/{id}` navigation
completes — so the raw read raced it (documented as an AFS in-PR amendment).

GA1, in the same diff, is still a bare synchronous
`assert chat.create_conversation_button.is_disabled()`, read immediately
after `chat.click_create_conversation()` returns. Same button, same kind of
raw read GA3 just got bitten by. Worth checking whether GA1 has the same
exposure.

## What I checked

Read `click_create_conversation()`'s actual body
(`automation/pages/chat_page.py:1065-1093`): it clicks the button, then does
`self.page.wait_for_timeout(1000)` (a fixed 1s sleep — pre-existing
tech debt, unrelated to this PR), then a best-effort `wait_for_network()`,
then an explicit `self.message_input.wait_for(state="visible")` before
returning. By the time GA1's read runs, ~1s+ of settle has already elapsed
and the message input's visibility has already been confirmed — so GA1 is
empirically safe *today*, but only because it free-rides on another
method's incidental internal waits, not because the disabled-state
transition is itself synchronous with the click.

Independently re-ran the test (3 green runs total across a solo run and a
full-class run) to confirm GA1 doesn't flake in practice. It didn't. But the
robustness argument is different from GA3's — GA3 is robust because the
assertion mechanism (`expect(...).to_be_enabled()`) tolerates the race
directly; GA1 is robust only because an *upstream* method happens to
already wait long enough. If that upstream method's fixed sleep ever gets
trimmed (a very plausible future cleanup, since fixed sleeps are exactly the
anti-pattern this project's own rules discourage elsewhere), GA1 could start
flaking with no visible connection to the change that caused it.

## Reusable review heuristic

When a PR fixes one raw-read race with a polling assertion, grep the same
diff for every other raw `.is_enabled()`/`.is_disabled()`/`.is_visible()`
read on the *same* element or button. For each one, trace what happens
*between* the last action and the read — if the apparent safety comes from
an incidental wait in a called method rather than the assertion's own
mechanism, flag it as a non-blocking robustness note (not necessarily
CHANGES_REQUESTED if it's currently green under real evidence), so a future
"harmless" cleanup of that upstream wait doesn't reintroduce the exact race
class the PR just fixed elsewhere.
