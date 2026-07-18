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
