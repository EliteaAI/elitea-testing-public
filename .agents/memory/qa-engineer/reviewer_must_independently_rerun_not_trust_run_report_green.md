---
name: Reviewer must independently re-run, not trust Run Report GREEN
description: PR #693/ELITEA-2095 round-2 review caught a real 2/5 flake via a fresh independent live run that the implementer's own "GREEN 3/3" x2 + debug-run claims never surfaced — two genuine race conditions in newly-added code, not environment noise.
type: feedback
---

## What happened

Round-2 reviewer pass on PR #693 (ELITEA-2095, chat "open conversation from
Today section"). The implementer's PR description reported GREEN 3/3 on the
original implementation AND GREEN 3/3 (+ 1 debug run) on the fix-only pass —
four separate claimed-green sessions. Round-1's two findings were genuinely
fixed (verified). Everything on paper said ship it.

Instead of trusting the Run Report, ran the spec independently, fresh,
5 consecutive times against the same live environment
(`../.venv/bin/pytest tests/ui/chat/test_open_conversation_today_section.py -v`,
headless, localhost:5173 + DEV backend). Result: **2 FAILED / 3 PASSED** —
a real ~40% failure rate, with two distinct, mechanistically-explained race
conditions, both in code newly added by this PR:

1. `ChatPage.get_context_budget_messages_count()` /
   `get_context_budget_summaries_count()` — a one-shot `.text_content()`
   read with no poll/retry. `wait_for_context_budget_panel()` only waits for
   the *heading* to appear, not for the Messages/Summaries row values to
   settle. Failure screenshot captured moments after the assert fired
   already showed the correct value rendered — proof the read raced ahead
   of an async update, not a product bug.
2. Missing `wait_for_generation_complete()` between the FIRST and SECOND
   message sends in the test's own setup. The test's own inline comment
   documented this *exact* race class ("`wait_for_message_content_stable()`
   is a text-heuristic; the app's internal streaming/nav-blocking flag can
   trail it briefly") and applied the guard before Step 2 (after the
   *second* message) — but not between messages 1 and 2, where the
   identical race exists and reproduced (`Locator.fill` timeout, "element is
   not enabled").

## Why this matters

A Run Report's "GREEN N/M" is the implementer's **local** observation, not
proof. The `test-automation-workflow` skill's own Run Report template has a
blank "Independent-gate verdict" row precisely because implementer-local
GREEN and reviewer-independent runs are a *real* distinct outcome class —
environment drift, parallel interaction, or (as here) genuine intermittent
races that a handful of local runs simply didn't hit. Four claimed-green
sessions did not surface a 40% failure rate; 5 fresh runs did.

## Actionable rule for future round-2 (and round-1) reviews

When reviewing a test-automation PR and the surface under test is reachable
(local dev server up, credentials available), **actually run the spec
several times fresh** rather than reading the Run Report and moving on to
static checks only (locator grep, additive-only diff, Coverage Map ticking).
Static checks catch policy violations; only a live re-run catches timing
races. This is cheap (single spec, ~55-70s/run) relative to the cost of
merging a test that will flake in CI.

## Related pattern: "text-heuristic wait" vs "authoritative signal" comments

When a test's own inline comment explicitly names a race class and applies
a targeted guard at ONE transition point, check every OTHER structurally
identical transition in the same test for the same guard — the author's own
comment is a confession that the race is real; if it's not fixed
everywhere it applies, it will still fire. (Cousin heuristic to
`raw_read_safe_only_via_inherited_settle_review_heuristic.md` — a bare read
next to a just-fixed polling assertion needs its own check; here it's a bare
transition next to a just-added guard needing the same check.)
