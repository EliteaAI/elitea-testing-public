---
name: Sanctioned-RED merge gate requires ONE failure signature, not just one root cause
description: A test that soft-asserts a known defect (pytest.fail() at the end) but ALSO has a separate, unrelated hard-failure path (a raw AssertionError/timeout elsewhere in the same test) tied to a second known defect does not qualify for the sanctioned-RED merge-gate exception even though both failure paths reference filed, open defects — the gate requires the SAME failure 3/3, and two different failure messages is "flaky, multi-cause" by the gate's own definition.
type: feedback
---

## The pattern (found reviewing PR #615 / ELITEA-1892)

`.agents/testing.md` § Merge gate's Sanctioned-RED exception text:

> a spec whose failure is (a) deterministic — identical failure 3/3, (b)
> single-cause, tied to an OPEN defect issue linked in the test... may merge
> RED... **Anything else red — flaky, multi-cause, no linked defect — blocks.**

A test can satisfy "tied to an open defect issue" at EVERY failure point it
has, and still fail this gate, if it has more than one *distinct* failure
point. ELITEA-1892's test:

- Terminal `pytest.fail()` via `soft_failures` — fires deterministically
  every run (known defect #611, Stepper console warnings). This alone would
  be sanctioned-RED eligible.
- BUT `wait_for_publish_status_menuitem()` (a page-object retry-poll helper
  working around a *different* known defect, #614, client-side status
  staleness) has its own hard `raise AssertionError(...)` after exhausting
  its retry budget — observed ~1/10 local runs by the implementer. This is a
  SECOND, structurally different failure (different exception, different
  message, fires at a different point in the test) tied to a DIFFERENT
  defect.

Even though both paths cite real, open, filed defects, the test as a whole
does not have a single deterministic failure signature — it has two. Whether
a given 3-run merge-gate window sees `pytest.fail()` 3/3 or a mix of
`pytest.fail()` and the `AssertionError` is a coin-flip weighted ~90/10 per
run. That is exactly "flaky, multi-cause" by the gate's own text, even though
every individual failure is legitimately explained.

## Reviewer checklist takeaway

When reviewing a test that relies on the sanctioned-RED exception:

1. Find EVERY place in the test (and any page-object method it calls) that
   can raise/fail, not just the one obvious `pytest.fail()` at the end.
2. Ask: if this test fails, is the failure message/type ALWAYS the same? If
   a helper method has its own internal retry-then-raise path for a
   *different* known defect, that's a second failure signature even if it's
   well-labeled and traceable.
3. If there are two+ signatures, the fix is either (a) drive the secondary
   failure rate to ~0 so it's not practically observable, or (b) route ALL
   failure paths through the SAME soft-assertion mechanism so the test has
   exactly one terminal failure shape — restoring "identical failure 3/3"
   eligibility.
4. This is exactly the class of risk the orchestrator's independent 3x gate
   exists to catch — flag it explicitly in the review even without
   personally reproducing the flake; a documented ~10% rate from the
   implementer's own Run Report is sufficient evidence to flag.

## Round 2 update (same PR #615, commit e858110d)

The implementer routed the second failure path (`wait_for_publish_status_menuitem`)
through the SAME `soft_failures`/`pytest.fail()` mechanism as #611 (API-tie-breaker
pattern: catch the AssertionError, independently confirm via API before
soft-asserting as known-#614, else hard-fail as a genuinely new bug), AND
generalized the same pattern to a second call site (`select_version_by_name`)
that surfaced the same #614 staleness class in a 14-run verification batch.
Directly verified via `/tmp/elitea-1892-runs-r2b/` (18 runs, post-fix): 17/18
`#611`-only, 1/18 `#611`+`#614` — **both content variants terminate through the
identical `pytest.fail()` mechanism**, zero raw exceptions.

My round-2 verdict: still **two signatures under the CURRENT gate text**, not
one — the fix collapsed "two mechanisms" into "one mechanism, two possible
cause-counts" (#611-only vs #611+#614), but `.agents/testing.md`'s clause (b)
is "single-cause", not "single mechanism". A dual-cause run routed through one
`pytest.fail()` is still dual-cause on a plain reading; the gate's own text
names "multi-cause" as an independent disqualifier from "flaky", not a subset
of it. **Sharing a terminal mechanism does not collapse a cause count.** If a
future orchestrator wants "closed, enumerable, independently-API-verified
defect set sharing one terminal mechanism" to count as gate-equivalent, that
needs an explicit `.agents/testing.md` amendment, not an implicit reviewer
reinterpretation — flag this distinction explicitly rather than rubber-stamping
either "obviously fine, one mechanism" or "obviously blocks, two causes".

Compounding wrinkle found this round: the "single cause" (#614) itself may be
an umbrella over 2-3 never-cross-confirmed symptoms (auto-nav-revert per the
issue's own filed text, vs. actions-menu lag, vs. `select_version_by_name`
DOM-convergence failure — all attributed to #614 by "responds to a reload"
pattern-match, never posted back to the issue as a comment). Check
`gh issue view <N> --json comments,body` for scope-creep like this whenever a
single issue number is stretched to cover a hardening pattern applied to a
second/third call site — it undermines the "single known cause" claim even
when the code-level engineering (API tie-breaker, reverse-masking guard) is
sound.
