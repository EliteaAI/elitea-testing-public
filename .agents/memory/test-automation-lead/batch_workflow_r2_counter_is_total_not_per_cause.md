---
name: batch-build workflow's R2 cap counts TOTAL implementer reruns, not per-root-cause
description: The workflow script parks a case "R2 cap exceeded" on a raw rerun tally even when every rerun was a distinct diagnosed cause resolved within budget — verify per-cause before accepting the park at face value
type: feedback
---

## What happened (ELITEA-2312, issue #820, PR #1189→#1190)

`batch-build.workflow.mjs` parked ELITEA-2312 `blocked` with note "R2 cap
exceeded (4 reruns) — classify architectural vs AFS-drift vs product-change".
The implementer's own returned diagnostics (visible in the workflow result,
not hidden) showed the 4 reruns were 4 **distinct** diagnosed infrastructure
root causes — CSS-uppercased column labels vs JSX source, `press_sequentially()`
dropping the leading keystroke, `BasePage.wait_for_network()`'s one-time-per-
navigation semantics — each fixed within ≤2 attempts of *that* cause, and the
implementer ended GREEN 1/1 with a real, pushed PR (#1189, OPEN/MERGEABLE,
testids already pushed to `automation/testids`).

The actual rule (`test-automation-implementation` SKILL.md § Retry budget,
`orchestration-playbook.md` § R2 cap rule) is explicitly **≤2 reruns against
the SAME root cause** — this case never violated it. The workflow script's
enforcement is a blunter total-attempt counter that doesn't distinguish
same-cause repetition from distinct-cause debugging, so it false-parked sound,
already-green work.

This is the SAME underlying distinction `new_root_cause_via_correct_fix_is_not_r2_cap_violation.md`
already documents for the *reviewer* loop — this entry is the *implementer/
workflow-script* analog: the script-level cap is where the same conflation
recurs, not just an orchestrator judgment call.

## What to do when a workflow parks a case on "R2 cap exceeded"

Before accepting the park (architectural / AFS-drift / product-change — none
of which may actually fit):

1. Read the implementer's own returned `notes` — it names its reruns' root
   causes if it followed its Run Report template. If each cause got ≤2
   attempts and none repeats, the case did NOT actually violate the true
   per-cause rule.
2. Verify independently (never trust the self-report alone): `gh pr view` for
   OPEN/MERGEABLE + a real diff, check the branch/testid commits exist. If the
   PR is sound and green, this is a script false-positive, not a real
   architectural/drift/product classification.
3. Recover by hand rather than discard: dispatch reviewer → fix rounds →
   merge to trunk → independent gate → PR to base — the normal pipeline,
   just resumed manually past the point the script stopped early.
4. Still worth a `next scout retrospective` flag: the workflow script's
   rerun counter should distinguish same-cause vs distinct-cause reruns
   the way the doctrine already does — not something to hand-patch mid-batch.

## When this does NOT apply

If the implementer's reruns genuinely repeat the SAME failure signature
(same assertion, same error, no new diagnosis) — the cap is correct and the
case really is architectural / AFS-drift / product-change. Read the notes
before assuming either way.
