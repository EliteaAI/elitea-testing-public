---
name: An aggregate flake rate can hide two deterministic populations
description: Before accepting "this defect is ~N/M non-deterministic", split the runs by trigger — the rate may be two deterministic classes averaged together.
type: feedback
aliases: [flaky defect determinism, non-deterministic defect, 2/5 run rate, gate exclusion scope, sanctioned-RED bar]
tags: [area/merge-gate, type/classification]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

Known defect #1127 (direct toolkit call narrates the tool call instead of
executing it) was recorded on 2026-08-03 as **non-deterministic at ~2/5**.
That single number drove a real, expensive decision: ELITEA-2215 was
downgraded `ready-for-automation` -> `blocked` and its whole module was
gate-excluded, because a probabilistic defect can satisfy neither the plain
green gate nor `.agents/testing.md` § Merge gate's sanctioned-RED
"deterministic 3/3" bar.

Re-measured 2026-08-27 (two independent rounds, every run a separate pytest
invocation, `--reruns 0`, backend-verified via `ArtifactAPI` rather than from
the DOM), the 2/5 turned out to be an **aggregate over two deterministic
populations split by which tool was called**:

| Trigger | Class | Lifetime |
|---|---|---|
| `create_file` | `TestDirectToolkitCallCompleteFlow` (ELITEA-2215) | 11/11 GREEN |
| `delete_file` | `TestDirectToolkitCallDeleteFileChip` (ELITEA-2210) | 7/7 RED |

Neither class is flaky. The average was.

## What to do differently

- **Before writing "non-deterministic" into a docstring or an AFS, group the
  runs by the variable that differs** (tool name, entity type, user, data row).
  A mixed-trigger sample is not a determinism measurement.
- **A blanket "N/M flaky" claim is a decision input, so it costs real
  coverage when wrong** — here it blocked a deliverable case for three weeks.
- Re-measurement is cheap on this suite (~36 s/run). Six runs bought the
  correction.

## Gate markers must be scoped to what they exclude

The module-wide `GATE_EXCLUDED_REASON` constant became actively misleading
the moment the two classes diverged — it would have wrongly excluded a
gate-eligible spec AND wrongly implied the whole file was expected red. Fix
shape (PR #1844): keep ONE greppable constant, but have its text name the
**node ids** — the excluded one and, explicitly, the non-excluded one, plus
"a red on THIS node id is NOT sanctioned". A grep must not mislead in either
direction.

Related: [[.agents/testing.md § Merge gate]]
