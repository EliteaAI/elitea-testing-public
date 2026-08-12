---
name: Sanctioned-RED merge gate — closed-set variant for compounding known defects
description: codified an amendment to .agents/testing.md § Merge gate so a test with MULTIPLE independently-verified known defects touching the same flow can still merge under the sanctioned-RED exception, without weakening the "no unknown cause slips through" guarantee the original rule protects
type: feedback
---

## The gap (#150, ELITEA-1892, PR #615)

`.agents/testing.md`'s original sanctioned-RED exception required a gate
run's failure to be "(a) deterministic — identical failure 3/3, (b)
single-cause, tied to an OPEN defect issue." This case's test legitimately
hit TWO independently-filed, independently-verified known defects on the
same flow: #611 (console warnings, ~100% deterministic) and #614
(client-side status staleness, ~5-10%/run, confirmed via an API
ground-truth tie-breaker before ever being classified as "known" rather
than a raw failure). A gate run could show either "#611-only" or
"#611+#614," both routing through the identical `soft_failures`/
`pytest.fail()` terminal mechanism — but that's not literally "identical
failure 3/3" under a strict reading, and it's not literally "single-cause"
either.

A fresh reviewer caught this precisely and — correctly — declined to
reinterpret the policy unilaterally. It laid out the exact tension (my own
mandatory 3x gate has real, non-trivial exposure to landing on a
non-identical 3rd run at that occurrence rate) and kicked the call
explicitly to me, framing it as "either run the literal gate honestly, or
amend the policy — don't silently reinterpret."

## The resolution

Amended `.agents/testing.md` § Merge gate with a "closed-set variant":
a gate run may show any subset of a **closed, enumerable set** of known
defects touching the same flow and still count as one sanctioned signature,
PROVIDED:
- every member of the set independently satisfies the original (a)+(b) bar
  on its own (open, filed, soft-asserted),
- every occurrence is verified against independent ground truth (e.g. an
  API response, not just a second DOM read) BEFORE being classified as the
  known defect rather than a raw failure — so a genuinely new/unknown
  cause can never quietly ride into the "known" bucket,
- all terminal failures route through the identical aggregation mechanism
  (one `soft_failures`/`pytest.fail()` call, not separate ad-hoc catches).

What still blocks, unchanged: any raw/uncaught exception reaching the gate,
any case where the API tie-breaker itself contradicts (a real bug, not
staleness), or a defect not in the enumerated set.

In THIS case the gate run came back 3/3 byte-identical anyway (only #611
fired all three times) — the closed-set variant wasn't even needed to
merge. It's codified for the next case that DOES land on a mixed 3-run
result, so that case doesn't have to re-litigate the same policy question
from scratch.

## Why this belongs to the orchestrator, not the reviewer or implementer

`.agents/testing.md` is explicitly in the orchestrator's editable-path
list (framework-architecture decisions). A reviewer correctly recognized
this was a policy question, not a code-review finding, and routed it up
rather than picking a side. This is the right shape for this class of
ambiguity: IC roles surface the tension with evidence, the orchestrator
resolves it in the shared policy doc so it doesn't recur as a fresh
argument on every future case that hits the same shape.

## Reusable pattern

Any project with a "isolated known defect may merge RED" convention will
eventually hit a test where MULTIPLE isolated defects compound on the same
flow. The closed-set variant's three conditions (enumerable set + each
independently verified + shared terminal mechanism) are a general answer,
not specific to this project's Playwright/pytest stack.
