---
name: Archived junit cross-check for merge-gate timing
description: cross-referencing a closure record's 3 pasted run durations against automation/reports/archive/junit_*.xml timestamps independently confirms the gate ran pre-merge, three separate processes, not narrated
type: feedback
---

`conftest.py` archives a timestamped junit/html copy of **every** pytest invocation
(any scope, not just full-suite runs) into `automation/reports/archive/`. This is a
free, independent, mechanical way to corroborate checklist item 5 (merge gate
evidence) beyond just trusting the closure record's pasted timings:

1. `grep -l "<test_method_name>" automation/reports/archive/*.xml` to find candidate
   runs for the case's node id.
2. For each candidate: `grep -o 'timestamp="[^"]*"'` (run start, local tz — note the
   offset, e.g. `+03:00`) + `grep -o 'tests="[0-9]*" time="[0-9.]*"'` (single-test
   invocation ⇒ `tests="1"`) + `failures="[0-9]*"`.
3. Match the durations against the record's pasted timings (they'll agree to the
   millisecond — `55.48s` claimed ↔ `time="55.476"` archived). Convert the local
   timestamp to UTC and compare against `mergedAt` from `gh pr view --json mergedAt`
   — the 3rd run's finish time should land shortly (seconds) *before* the merge
   timestamp, never after.

Worked on #148 (ELITEA-1799): found the exact 3 archived runs (19:20:42/19:21:42/
19:22:43 local, +03:00 → ~16:20:42–16:23:36Z), finishing ~22s before `mergedAt`
(16:23:58Z) — strong independent proof the gate was real and genuinely pre-merge,
not reconstructed after the fact. Bonus: also found the *implementer's* separate
R1 fix-only 3x local-verification run archived ~20 minutes earlier (18:59–19:01
local) with its own matching durations from the PR body's Test Plan section —
useful for telling apart which claimed "3x green" belongs to which round when a
PR body cites more than one.

Caveat: this only works when the archive hasn't been pruned/rotated and the case's
test method name is unique enough to grep cleanly — for a very generic test name,
narrow with `-l` then inspect classname, not just the bare method name.

**Multiple-candidate-clusters refinement (#260/PR#675, 2026-07-20):** a shared
covering test extended by several cases over time (ELITEA-1824→1827→1835, one test
method) accumulates MANY archived runs across the whole day/week — `grep -l` can
return 15+ files spanning several unrelated deliveries' own gates, not just this
one's. Two techniques resolved the ambiguity: (1) derive the local-tz offset
independently rather than assuming it — a memory-landing commit made *immediately
after* this delivery's own merge has a `git log --format=%aI` author-date in local
time; diffing it against the PR's `mergedAt` (UTC) gives the exact offset (here,
`09:49:49+03:00` vs `06:49:13Z` ⇒ +03:00, confirmed to the minute); (2) once the
offset is known, narrow to the archive-timestamp window immediately preceding the
converted local merge time, then match the SPECIFIC failure-signature sequence
(not just "some #649 failures somewhere") — this case's closure record documented
an out-of-order anomaly (run 2 of 5 was a different, unrelated Timeout signature,
not the sanctioned #649 one) and that exact signature-position fingerprint,
combined with 3 duration matches to within ~0.1s, uniquely identified the right
5-file cluster out of ~17 same-test-name candidates that day.

**Third clean confirmation (#317/PR#696, control-audit 2026-07-21):** single-case,
no ambiguity — `junit_20260721_070037/070110/070138.xml` matched the closure
record's pasted `24.70s/23.41s/23.67s` to `24.695/23.408/23.671`, 0 failures each,
same classname+method, timestamps 07:00:12→07:01:39 local (+03:00) landing ~16s
before the 07:01:55 local `mergedAt`. Routine enough now (3rd straight clean use)
that this should be a default move on every control-audit's item 5, not an
occasional nice-to-have — it's cheap and it catches exactly the kind of
post-hoc-narrated-gate that item 5 exists to prevent.
