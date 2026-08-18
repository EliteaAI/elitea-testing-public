---
name: Reviewing a page-wide-testid staleness fix
description: When a fix adds a setup action that pre-produces one occurrence of a page-wide (not per-message) testid, verify it captures a count baseline BEFORE the action under test and asserts a count INCREASE, not a bare .last.wait_for(visible)
type: feedback
---

Context: chat page's `chat-answer-thought-accordion` / `chat-answer-model-chip`
testids are page-wide (one per rendered message, no message-scoped wrapper —
`.agents/testing.md` doesn't cover this per-surface fact, it lives only in
chat_page.py comments). When a test's Setup step sends its own message to
establish an "existing/already-active conversation" precondition (AFS-driven,
e.g. ELITEA-2177/2178/2465, PR #1567), that setup message already renders one
accordion+chip pair BEFORE the step actually under test sends its own message.

**What a correct fix looks like** (verified in PR #1567 fix-round-1,
d6a91f464b5):
- Capture `initial_accordion_count = chat.answer_thought_accordion.count()`
  BEFORE the step-under-test's action (the click/send), not after.
- Assert the NEW occurrence via `expect(locator).to_have_count(initial_count + 1, timeout=...)`
  — this genuinely waits for the step's own response to render, because a
  stale pre-existing occurrence can't satisfy a count INCREASE.
- Only THEN read content off `.last` (correctly resolves to the newest
  occurrence in DOM order, matching the `messages_container.last` idiom
  `get_last_message_text()` already uses).

**What to flag in review:** a bare `locator.wait_for(state="visible")` or
`expect(locator).to_have_class(...)` with no `.last` and no prior count
baseline, right after a setup action already produced one occurrence of the
same page-wide testid — it passes trivially against the STALE occurrence
without ever confirming the step-under-test's own response started. This is
the same class of bug as `positive_existence_wait_cant_assert_negative_transition.md`
(can't assert a transition — appear OR disappear — with a check that's
already true beforehand), just on the "appear" side instead of "disappear".

Also check: whichever `wait_for_ai_response(initial_count=N)`-style helper
gates the later full-response assertion must key off the message-list INDEX
(`initial_count` captured right before the step's own send), not off
presence of "an" AI message — chat_page.py's `wait_for_ai_response` already
does this correctly (`messages_container.nth(initial_count + 1)`).
