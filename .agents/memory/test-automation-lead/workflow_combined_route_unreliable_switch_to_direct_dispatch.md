---
name: Workflow tool's "combined route" and retry-cluster resumes proved unreliable — switch to direct dispatch after 2 failures
description: On #1391 (2026-08-11), batch-build.workflow.mjs hit 2 full hard crashes (StructuredOutput retry cap exceeded, once inside a "combined route → needs-analyst-rerun" handoff) and 3 consecutive harness deaths on the SAME case across two separate Workflow attempts. Abandoning the Workflow tool for direct single-agent Agent() dispatches (implementer → reviewer → lead's own gate) worked reliably for all 6 remaining cases.
type: feedback
---

## What happened

Retrying a batch of RETRY/remainder cases (cases carried over from a prior
failed/blocked batch attempt) through `batch-build.workflow.mjs` a second and
third time hit two distinct hard-failure shapes beyond the already-documented
single-harness-death-then-resume pattern
(`workflow_hard_failure_can_still_have_landed_real_work.md`):

1. **A full script crash**, not caught by the per-case try/catch:
   `TelemetrySafeError: agent({schema}): StructuredOutput retry cap (5)
   exceeded — 5 failed calls with no valid output`. Journal showed this fired
   inside the workflow's own triage step deciding to route several
   retry-cases to a "combined" (analyst+implementer-in-one) dispatch based on
   language in my `extraContext` that framed them as "AFS already exists,
   route: combined" — the combined agent hit a case needing genuine
   re-analysis, returned `needs-analyst-rerun`, and the script's handling of
   that specific transition threw instead of routing cleanly.
2. **Repeated per-case harness deaths on the SAME case** (ELITEA-2353: 1st
   attempt, then again on a 2nd `resumeFromRunId` retry, then again on a 3rd
   fresh dispatch inside a different combined-route batch) — 3 consecutive
   deaths on one specific case across two separate Workflow invocations,
   despite the plain-resume protocol (`subagent_wait_and_resume_mechanics.md`)
   working fine for every OTHER case in the same runs.

Both single-resume (the standard first response to one death) and a full
re-dispatch with much more explicit per-case guidance were tried before
concluding the tool itself, not the case content, was the variable.

## What worked: direct dispatch, same pipeline contracts

Switched to plain `Agent()` calls — implementer → fresh-session reviewer (→
fix rounds as needed) → the lead's own independent gate — one case at a time,
foreground, exactly the manual-loop shape the orchestration playbook
describes for "no Workflow tool" hosts. This is the SAME contract, just
executed by the lead instead of the script. Ran 6 consecutive cases this way
(ELITEA-2360, 2361, 2362, 2370, 2355, 2353) with zero harness deaths — every
single dispatch returned a real, complete result.

## The rule

**After 2 hard failures of the Workflow tool on the same batch (not counting
ordinary single-case harness deaths that a plain resume fixes) — stop trying
to force it back into the workflow.** Don't burn a 3rd/4th retry hoping the
next attempt is clean; switch to direct per-case `Agent()` dispatches for the
remainder. The contracts (AFS gate, fix-round loop, R2 cap, merge gate) are
identical either way — nothing about quality or process changes, only who
executes the loop. This is NOT a verdict that the Workflow tool is broken in
general — it worked fine for the FIRST batch attempt in this same session
(8-case run, only one harness death, resumed cleanly once). The specific
trigger this time looks tied to "combined route" + retry-cluster framing in
the dispatch's own `extraContext`, not a universal failure mode — but
diagnosing the tool's internals is not the lead's job; recognizing "2 strikes,
switch approach" is.
