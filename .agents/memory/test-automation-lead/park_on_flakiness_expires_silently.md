---
name: A park on flakiness expires silently — re-gate before you re-argue
description: A case parked because a flaky/unstable area blocked its N×-green gate needs one thing first — re-run the gate; nobody announces that a flake stopped
type: feedback
aliases: [parked on flake, blocked on instability, render instability park, quiescent bug, gate unreachable, re-gate a parked case, sanctioned RED not needed, testid promoted since]
tags: [area/planning, type/lesson]
created: 2026-08-27
updated: 2026-08-27
---

## The rule

When a case is parked because an **unstable area** made the 3×-green gate
unreachable, the first action on resuming is **run the gate again** — before
reading the bug, before drafting a sanctioned-RED argument, before deciding
anything. A flake has no fix event and no notification: the blocking bug can sit
OPEN and untouched while the symptom simply stops appearing.

The trap is that the blocking bug's `state: OPEN` reads as *"still blocked"*. It
is not evidence about today; it is evidence that nobody closed an issue.

## ELITEA-2088 / #437 (2026-08-27)

Parked 2026-08-04 on #1142 — intermittent React `Maximum update depth exceeded`
plus post-edit re-render instability in the Mermaid canvas flow; 3 of ~5 gate
runs then failed on some symptom. On resume, **4 invocations produced none of
#1142's three signatures**; the gate passed 3 consecutive clean (`reruns.json ==
{}`, ~22 s each). Elapsed: ~15 minutes of pytest against a 3-week park.

**Two things had changed silently, and neither would ever be announced:**

1. The instability went quiescent — no commit touched the component. #1142 stays
   OPEN as a product observation; *quiescent is not fixed*, and the closure
   record must say so rather than implying a fix.
2. The case's testids had reached EliteaUI `main` via a human's bulk promotion
   (`bf4a13ad`, "promote 400 accumulated data-testids"). The old closure record's
   `on-automation/testids only` row was simply stale — which is exactly why the
   promotability row is re-verified with a fresh `git fetch`, never copied.

## Two things not to do

- **Don't reach for sanctioned-RED before measuring.** It was unavailable here
  anyway (intermittent fails the *deterministic* criterion) and unnecessary — the
  case was plain green. Building the argument first wastes the session.
- **Don't accept the flake run.** Run 1 failed with a raw `TimeoutError` at Step 3
  (trigger-side: the LLM never produced a renderable diagram on a cold first
  invocation). Raw uncaught assertions upstream of the case's observable are never
  members of a sanctioned-RED set — discard the run and re-run, never 2-of-3.

Related: [[a_parked_case_is_a_hypothesis_not_a_verdict]] · [[flake_rate_may_be_an_aggregate]] · [[blocker_premise_symptom_vs_cause]]
