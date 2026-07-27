---
name: AFS Priority line vs pytest.mark — implementer preflight check
description: Before handing off any new test, grep the AFS's own "Priority: lN" line against the new test's @pytest.mark.pN decorator — a mismatch silently excludes a self-declared high-priority case from the "p0 or p1" CI gate and is invisible to every other check (locators, additive-only diff, live green run). Caught by review on ELITEA-1846/PR #678 after I landed p2 for an AFS-declared "l2 (high)" case sitting next to a p1 covering test in the same file.
type: feedback
---

## What happened

Landed `test_delete_multiple_files_partial_selection` (ELITEA-1846,
`extend-existing` into `test_artifacts_delete_subfolder_checkbox.py`) by
copying the AFS's own § Gap assertions code block verbatim, including its
`@pytest.mark.p2`. The AFS's own metadata block declared
`Priority: l2 (high — as authored in the source TMS case)` — the same label
as the covering test's `@pytest.mark.p1`, and the same label every other
artifacts AFS with "l2 (high)" resolves to `p1`. A fresh reviewer caught it;
I didn't, because the test ran green either way — a marker mismatch has zero
signal in a pass/fail run.

## Why it's easy to miss

None of the standard implementer checks touch markers: locator-identity
grep, `git diff | grep '^-[^-]'` additive-only verification, and the live
2/2 clean-process run all pass regardless of which `pN` marker is attached.
The only way to catch it is a deliberate side-by-side read of the AFS's
`Priority:` field against the compiled `@pytest.mark.pN` — a check that
isn't part of the six-phase loop's Phase-4 "run it green" gate.

## The reusable check — do this before Phase 6 handoff, every time

```bash
grep -m1 "Priority" test-specs/<feature>/l*_<case>.md
grep -n "@pytest.mark.p[0-9]" automation/tests/ui/<feature>/<file>.py
```

Map: AFS `l0`→`p0`, `l1`→`p1` or `l2 (high)`→`p1`, `l3`(medium)→`p2`,
`l4`(low)→`p3` — confirm against 2-3 sibling tests in the same feature
directory if the mapping is ambiguous, don't assume. For `extend-existing`
AFS specifically, the new sibling test sits in the same file/class as an
already-merged covering test — the two markers are directly comparable
line-by-line, so this is a 10-second check with no ambiguity once you know
to run it.

## Outcome

One-line fix (`p2`→`p1`) in a fix-only round, PR #678, commit `e765a0b7`.
Cost nothing to fix; the miss itself would have silently excluded a
self-declared high-priority case from `pytest -m "p0 or p1"`, the
documented CI high-priority run — a real gap that a green test run alone
can never surface. See the companion entry in
`.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`
for the reviewer-side version of this same lesson.
