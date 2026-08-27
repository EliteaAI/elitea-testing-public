---
name: Assertions behind a failing wait are never evaluated — check ORDER on every sanctioned-RED spec
description: A wrong assertion downstream of a wait that always times out never fires, so no gate can catch it
type: feedback
aliases: [assertion order, unreachable assertion, dead assertion, primary observable order, sanctioned-RED order]
tags: [area/review, type/triangulation-trap]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

A spec can carry a **factually wrong** assertion for as long as it likes, provided
something upstream of it fails first. The wrong assertion is never evaluated, so it
never turns red, so no gate — implementer green run, reviewer static read, N×-green
merge gate — ever sees it.

Worked case: ELITEA-2213 (`test_hitl_sensitive_action_authorization.py`,
`TestSensitiveActionBlock`). Merged shape was:

```
wait_for_message_content_stable(...)      # times out at 60 s on OPEN #1834
assert seeded_file in list_bucket_files() # THE CASE'S PRIMARY OBSERVABLE — never ran
...
expect(chat.answer_tool_chip).to_have_count(0)  # factually wrong — never ran either
```

The chip assertion asserted a state the product never enters (`ActionView.jsx:407`
renders the chip from the tool-CALL ATTEMPT, no execution predicate — count is 1
before AND after Block). It survived review + merge purely because it was
unreachable.

## The reviewer move

On any spec that is red — sanctioned or not — read the step order and ask, per
assertion: **can this line be reached on the failing path?** Specifically:

1. Is the case's **primary observable** upstream of every step known to fail?
   If not, the case is not being verified at all, which is worse than red.
2. Does an assertion downstream of a known-timing-out wait exist? Treat it as
   **unverified** — it has never executed, so its correctness is an untested claim.
3. A `try/except` that soft-routes the failing wait is what makes the downstream
   steps reachable again. Its absence is the tell.

## The inverse, same review

Moving an assertion EARLIER can also break it. `to_have_count(0)` is satisfied the
instant the count is already 0, so an "it stays gone" check evaluated ~1 s after the
element correctly disappeared passes vacuously and silently drops its defect from the
closed set. Late placement (after the response window, state settled) is what makes it
fire deterministically. Order is an assertion-strength property, not a style choice —
judge it explicitly in both directions.

Related: [[to_have_count_zero_is_not_an_absence_window]] · [[absence_assertions_can_pass_vacuously]] · [[absence_assertion_needs_a_proven_detector]]
