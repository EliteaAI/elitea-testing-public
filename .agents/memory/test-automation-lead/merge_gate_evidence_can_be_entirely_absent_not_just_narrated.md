---
name: Merge gate evidence can be entirely absent, not just narrated
description: A stricter failure shape than the known narrated-not-pasted anti-pattern — item 5 evidence can be missing from the tracker altogether; the PR body's own "orchestrator fills in" placeholder staying literally unfilled through merge is a reliable, grep-able tell
type: feedback
---

Prior memory (`closure_record_must_paste_merge_gate_output`,
`merge_gate_narration_needs_artifact_too`) covers the case where the lead's
own 3x pre-merge gate genuinely ran but the closure record only *narrates*
it ("3/3 GREEN, 3 separate invocations") instead of pasting the output —
that still FAILs item 5. #252/PR#668 (2026-07-20, control-audit) surfaced a
**stricter version of the same gap**: the merge-gate step wasn't narrated
OR pasted — it was **absent from the tracker entirely**. The closure record
had no merge-gate section at all (table, promotability, defects, TMS
back-write — no gate). Zero inline PR review comments. `pulls/N/reviews`
empty (expected/architectural, not a signal here).

The reliable mechanical tell: **implementer PR bodies in this repo's
template carry a placeholder field for exactly this** —
`**Independent-gate verdict:** _(left blank — orchestrator/lead fills after
the independent 3x gate run)_`. Checking `gh pr view N --json body` at
audit time and finding that placeholder **still literally unfilled**,
unchanged from the implementer's original draft through the merge-time body
edit, is strong corroborating evidence the step was never recorded publicly
— even before checking anything else. Grep for it directly:
`gh pr view <N> --json body --jq '.body' | grep -A2 "Independent-gate"`.

Local archived-junit timestamps (`automation/reports/archive/junit_*.xml`)
CAN still corroborate that 3 genuine separate runs happened pre-merge (as
they did on #252 — 04:37:27/04:37:56/04:38:22 local, before the 01:38:30Z
UTC merge) — that's useful context and rules out "the gate never ran at
all," but per the evidence principle it does NOT rescue the FAIL: item 5's
proof of record has to live in the issue/PR the human actually reads, not
in a local report directory or the agent's own private memory log (which
may independently narrate the same 3 runs in detail — as #252's delivering
session's own daily log did — without that narration ever reaching GitHub).
Always check the tracker artifact itself, never accept "my memory says it
ran" as sufficient during a control audit — that applies to the auditor's
own memory just as much as the delivery's.
