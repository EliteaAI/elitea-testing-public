---
name: A CI failure's traceback names the symptom; the secondary error line often names the cause
description: On #2063 the traceback showed a missing close button, but the one-off "waiting for event response" line exposed a second, independent product change — fixing only the traceback would have shipped a latent race.
type: feedback
aliases: [second error line, intermittent secondary failure, two causes one red, CI log triage, expect_response auto-select]
tags: [area/triage, area/test-repair, type/diagnosis]
created: 2026-09-09
updated: 2026-09-09
---

## The shape

A card summarised #2063 as one failure: *"Timeout waiting for Run History panel to close"*, with the final
traceback at `close_run_history()` -> `run_history_close_button.wait_for` -> `TimeoutError`. Clean, singular,
obviously actionable.

Buried in the same log, on ONE of the three retry attempts:

```
Step failed: Select Run History item — Timeout 10000ms exceeded while waiting for event "response"
```

Different step, different mechanism, present in only one attempt — the exact profile everyone reads as
"noise from the cascade". It was not. It was a **second, independent product change**:

- The traceback's cause: `EliteaAI/EliteaUI@90e20a03` (EL-6537) turned the Run History panel into a route;
  the route passes no `onClose`, and the close button is gated on `{onClose && (…)}`, so its testid can
  never mount.
- The secondary line's cause: `EliteaAI/EliteaUI@84025881` (EL-6391) made the list **auto-select row 0 on
  open**, so a row-0 click causes no request at all — the page object's `expect_response` wrapper waited
  for an event that no longer happens, and passed only when the auto-select's own GET happened to land
  inside the expectation window.

## Why it matters more than it looks

Repairing only the traceback would have shipped green (the flaky wait passes most of the time) while
leaving a race in a method **shared with another merged spec**. The class of bug this produces is the
worst one available: intermittent, in someone else's test, attributed to a different card months later.

## The rule

**Every distinct error line in a CI log gets its own root cause before you accept a single-cause repair.**
A line that appears in only 1 of N attempts is evidence of a race, not evidence of irrelevance — an
intermittent line is a *stronger* signal that something is timing-dependent, not a weaker one.

Concretely, when triaging a red:

1. Read the whole failed-job log for `Step failed:` / `ERROR` lines, not just the pytest traceback.
   The traceback shows where execution *stopped*; earlier steps can fail-and-recover via retries.
2. For each distinct line, ask "what product change would produce exactly this?" — and go read the
   product's git history (`git log -S`) rather than the test's.
3. If two lines resolve to two different upstream commits, the card is two repairs, not one.

## Corollary — the card's own framing is a hypothesis

#2063 also asserted the failure was DEV-specific ("Fix on DEV environment"). It reproduced identically on
localhost. Both product commits were on `main` and on `automation/testids`, so no environment was special.
Treat a `[FIX]` card's environment scoping the same way as its failure summary: a starting point, verified
before it steers the repair. See also `a_product_change_is_not_a_product_bug.md`.
