---
name: batch report's per-case outcome "blocked" can still mean LAND IT
description: a sanctioned-RED single-case batch reports gate.verdict "green" but cases[].outcome "blocked" — read the gate verdict + report's own `next` field, not the outcome label
type: feedback
---

## Rule

`batch-build.workflow.mjs`'s report writer uses `outcome: "blocked"` generically
for "the gate ran it but the spec itself is red" — even when that red is the
`.agents/testing.md` § Merge gate **sanctioned-RED exception** (deterministic
3/3 failure, single known cause, linked OPEN defect). In that case `gate.verdict`
is `"green"` (the batch's specs together satisfy the gate) and the top-level
`next` field explicitly says `"Gate green on tests/batch-<slug>. LAND IT: one PR
from tests/batch-<slug> to <base>..."`.

Don't let the case-level `outcome: "blocked"` string read as "park this, add to
`Waiting on`, move the board card to Blocked." Check, in order:
1. `report.gate.verdict` — `"green"` means the batch is landable.
2. `report.next` — the workflow's own authoritative landing instruction.
3. Only if BOTH point to a real blocker (gate red, or `next` says wait) does the
   case actually park.

A sanctioned-RED case that lands this way is `Ready` per `AGENT.md`'s own
definition of done ("clean-green in CI, OR red-for-a-real-product-bug with a
filed, linked ticket") — not `Blocked`. Land it, back-write the TMS, post the
closure record naming the sanctioned-RED exception explicitly, move the card to
`Ready`.

## Seen 1×

#844/ELITEA-2336 — report said `cases: [{"outcome": "blocked", "note": "red by
design pending #1203 — the gate ran it but could not count it; re-enter once the
product ships"}]` while `gate.verdict` was `"green"` (3/3 identical sanctioned-RED
signature, tied to filed #1203) and `next` said to land it. Landed via PR #1205,
TMS back-written, closure record posted, card → Ready.

See also: sanctioned_red_closed_set_variant.md ·
merge_gate_extend_existing_sanctioned_red_needs_step_level_check.md ·
batch_workflow_never_opens_trunk_to_base_pr.md
