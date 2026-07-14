---
name: Isolated-defect tests are expected to run red, not a stop signal
description: A red isolated-defect test (expect.soft() tracking a known, already-filed bug) is normal and merge-safe — don't confuse it with a blocking defect that should park the card
type: feedback
---

## The distinction

`.agents/profile.md` § Bug filing defines two defect categories with different
handling:

- **Isolated defect** → `expect.soft()` around just the affected assertion,
  ticket linked in a comment, everything else in the flow hard-asserted.
  The overall test **will still report red** whenever the underlying product
  bug reproduces — that's the correct, intended behavior (`expect.soft()`
  aggregates failures and still fails the run at the end; it just doesn't
  abort execution early). This is "never a hidden green" in practice: the
  defect stays visible in CI, linked to its ticket, until the product fixes it.
- **Blocking defect** → natural fail + `Blocked` card status. Reserved for
  defects that prevent the flow from completing at all (can't get past a
  step to exercise the rest of the case).

## Why this matters for orchestration

Seeing an implementer report "RED 0/3" or "RED 3/3" is not, by itself, a
reason to park the card or treat the pipeline as stalled. First check
**why** it's red:

1. Read the AFS's "Known Defects" section (or the implementer's Run Report)
   — is the red caused by a single soft-assertion tied to an already-filed,
   already-referenced bug ticket?
2. Confirm no masking (`grep` for `skip`/`xfail`/`test.fail()` beyond the one
   legitimate soft-failure aggregation call).
3. Confirm every *other* assertion in the flow is a real hard `assert` and
   passed.

If all three hold, this is a normal isolated-defect test — proceed through
review and merge exactly as if it were green. Only escalate to "blocked" if
the defect actually prevents the rest of the flow from running, or if no
prior handling guidance/precedent exists for a NEW bug (that's a fresh
judgment call needing the question/bug-issue-and-park treatment, not this one).

## Case history

- Issue #26 (ELITEA-1735, PR #39): defect #38 filed fresh, soft-assert
  pattern established, 3/3 independent gate happened to come up GREEN
  (defect's ~1/3 rate didn't fire in those particular runs).
- Issue #27 (ELITEA-1736, PR #41): same defect #38 re-confirmed in a second
  code path (chat-participant vs. agent-level), reproduced 3/3 — test merged
  RED, by design, per the same policy. Reviewer independently re-ran and
  confirmed the single failure cause before approving.
