---
name: Gate's blast-radius run can go UNOBSERVED (not red) — lead re-runs it before landing
description: distinct from a red blast-radius (which doesn't block); an unobserved one means the gate never actually checked — the lead must run it, not skip it
type: feedback
---

## What happened

ELITEA-2374 (#882, 2026-08-06): the gate agent ran the N×3 green on the new
spec cleanly (verdict `green`), but its own **one** blast-radius pass (3 specs
sharing `user_profile_settings_page.py`) got backgrounded by the environment's
120s foreground-command threshold and never produced a result before the
agent's `StructuredOutput` call was forced — the gate's own notes explicitly
said "BLAST-RADIUS RUN DID NOT REACH A CONFIRMED OUTCOME IN THIS SESSION...
Do NOT read this as 3 green or 3 red — it is simply unobserved" and asked the
lead to re-run it.

## Rule going forward

This is **not** the same situation as `blast_radius_red_does_not_block_gate_verdict.md`
(a completed run that came back red doesn't block landing). Here the run never
completed at all — there is no signal, red or green, so the merge-gate's own
"plus one run of the specs the batch could have broken" requirement
(`.agents/testing.md` § Merge gate) is simply unmet. `gate.verdict: green`
being scoped to the new-spec N-count only does not excuse skipping this —
**the lead must actually run the blast-radius scope themselves** (foreground
`pytest` on the listed specs, backgrounded via `run_in_background: true` +
polled with `TaskOutput(block:true)` if long) before opening the trunk→base
PR. On ELITEA-2374 this surfaced 6 passed / 2 skipped (pre-existing) / 0
failed — clean — but that had to be actually observed, not assumed from a
green `gate.verdict`.
