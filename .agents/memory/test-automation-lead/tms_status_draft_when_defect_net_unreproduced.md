---
name: TMS status can stay draft when a known-defect soft-assertion hasn't reproduced yet
description: distinguish #26/#27's precedent (status:ready + reliably-reproducing linked defect) from #148's shape (status:draft declared, defect assertion never yet observed firing) — a sound declared improvisation, not an automatic item-7 FAIL
type: feedback
---

`.agents/test-automation.yaml` § `backwrite_on_done` lists `status: ready` as one of
four unconditional fields. Precedent issues #26/#27 both back-wrote `status: ready`
even with an isolated, soft-asserted, OPEN defect linked — because in both cases the
defect assertion **reliably reproduced RED 3/3** (real, if unwelcome, signal every
run); the defect issue carries the "not fully clean" nuance, not the TMS field.

#148 (ELITEA-1799) is a different shape: the new Step 6 assertion targets known
defect #607 via `soft_failures` + `pytest.fail()`, but at merge-gate time the shared
test account's conversation stayed *under* #607's trigger threshold, so the check
ran **GREEN** — it currently cannot distinguish "defect fixed" from "defect present,
untriggered this run." The delivery declared this explicitly (commit message, PR
body, closure record) and held `status: draft` (while still setting the other 3
back-write fields), planning to flip to `ready` only once the assertion is observed
actually catching #607's absence at least once.

Judged this a **sound declared improvisation** (`.agents/role-overrides.md`
protocol): more conservative than the status quo, doesn't overclaim what the
automation currently proves, and was declared rather than silent. Filed `question`
#613 proposing the canon codify this as a named exception (parallel to the
Sanctioned-RED exception, but for the "hasn't yet reproduced" sub-case) rather than
letting it solo-FAIL checklist item 7. Future audits: check whether #613 got a
ruling before treating a similar `status: draft`-despite-3-fields-set delivery the
same way — if the canon now has an explicit answer, apply it instead of
re-deriving from #26/#27 by analogy.
