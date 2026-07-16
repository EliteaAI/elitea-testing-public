---
name: Closure record promotability must be pasted even if true
description: A closure record's promotability claim that narrates the conclusion instead of pasting the canon's per-testid verification table FAILs a control audit even when the underlying claim turns out true — narration is the risk factor, not falsity
type: feedback
---

Found auditing issue #71 (ELITEA-1897/PR #561). Distinct from the prior
"reviewer narration" (`reviewer_narration_is_not_pasted_evidence.md`) and
"merge-gate narration" (`merge_gate_narration_needs_artifact_too.md`)
entries — this one is about the **lead's own promotability section inside
the closure record itself**.

The closure record said: *"Promotability — VERIFIED, fully promotable...
All 8 testids... reused pre-existing handles — re-checked fresh (`git fetch
origin` first) against both `origin/main` and `origin/automation/testids`:
all 8 present on both."* No per-testid table, no pasted grep/printf output.

I independently re-ran the canon's exact script
(`.agents/workflow.md` § Closure record, the `git fetch` + per-testid
`printf` loop) and confirmed all 8 genuinely were `YES`/`YES`. The
underlying claim was TRUE. **It still FAILs item 4** — canon states the
verification output "gets PASTED into the record" as non-optional,
specifically because narration is exactly where false rows have hidden
before (#35/#36/#37 copied claims, #19 shipped a stale-clone false 0/12).
The format requirement doesn't have a truthfulness escape hatch: a
narrated-but-true claim this time doesn't establish the delivery actually
ran the check the way canon requires, only that it happened to land on the
right answer.

Lesson for delivery-side work (as implementer/lead authoring a closure
record, not just auditing one): always paste the literal per-testid
`printf "%-32s main:%-3s testids:%s\n"` block, never summarize it in
prose — even a technically-accurate summary reads as unverified to a later
auditor and burns an audit cycle establishing what a paste would have
settled instantly.
