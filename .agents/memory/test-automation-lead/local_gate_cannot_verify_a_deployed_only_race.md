---
name: A local gate cannot verify a deployed-only race — say so instead of implying it did
description: When the bug's window only exists on DEV, 3x local green proves non-regression only; state the gap in the PR and closure record rather than letting the green table imply verification
type: feedback
aliases: [DEV-only race, local green proves nothing, unfalsifiable locally, non-regression only, deployed-only failure]
tags: [area/test-repair, area/ci, type/gate]
created: 2026-08-27
updated: 2026-08-27
---

## The situation (ELITEA-1886 / #1812, 2026-08-27)

`chat_send_button.click(force=True)` silently no-ops when the composer was populated
**programmatically** (starter-chip click → `chatInput.setValue()`), because `disabledSend`
is an 8-term disjunction with **network-bound** members and `force=True` skips the
actionability wait. On `localhost:5173` the button settles in **~2 ms** — the window does
not exist. Measured: the *unrepaired* spec was **5/5 green locally**.

So every local gate — the implementer's 3, mine 3 — proves **non-regression only**. This
class of bug is *structurally* uncatchable by the local loop.

## The rule

When the failing mechanism is environment-dependent, **a green gate table is actively
misleading** unless the gap is named. Do all four:

1. Put the honest caveat in the **PR body**, the **closure record**, and the **spec's own
   docstring** — the next reader reads the test, not the ticket.
2. Get a second, *independent* axis of evidence that isn't the gate. Here the reviewer
   verified the new oracle **at the product source** (`ApplicationAnswer.jsx:523/708` —
   `shouldRenderAnswerBlock` gated on `!!answer`, so the loading placeholder cannot satisfy
   it). Source verification beats another green run.
3. Ask the implementer for a **red-green check** — deliberately break the new assertion and
   confirm it fails. On a repair whose whole subject is an *inert assertion*, a pass proves
   nothing; only a demonstrated failure does.
4. Name the exact command a human should run once the environment is back.

## Merging without the verification — when it's defensible

I merged with DEV verification unobtainable (#1850). Auditable reasoning, worth reusing:

- the mechanism is **understood** and the repair **removes** it, not tolerates it;
- the strongest new assertion rests on **source**, not on a local observation;
- the prior state was already red on DEV *and* **vacuously green** whenever the agent
  failed to answer — leaving it had an ongoing cost;
- if a new assertion misbehaves, it now fails **fast and by name** (missing POST / missing
  answer element) instead of a 60 s timeout on the wrong line.

The deciding factor is the last one: prefer shipping a change whose *failure mode* is
diagnostic. Then say plainly that the evidence is weaker than usual — do not let the table
imply otherwise.

Related: [[ci_green_can_mean_zero_tests_ran]], [[repaired_test_may_become_inert]]
