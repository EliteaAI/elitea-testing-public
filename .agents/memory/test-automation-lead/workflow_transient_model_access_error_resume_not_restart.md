---
name: Workflow agent failure "issue with the selected model" is transient — resume, never restart
description: batch-build agents can fail with a model-access error unrelated to the work itself; check git (analysis AFS already landed), then resumeFromRunId — never re-dispatch fresh
type: feedback
---

## What happened (ELITEA-2875/2876/2877/2878, #2455, 2026-10-17)

A `batch-build.workflow.mjs` run returned `status: "failed"` with two agent
failures in the `<failures>` block:

```
[implement:...] failed: There's an issue with the selected model
  (eu.anthropic.claude-sonnet-5). It may not exist or you may not have access
  to it. Run --model to pick a different model.
[report:...] failed: There's an issue with the selected model
  (eu.anthropic.claude-haiku-4-5-...). It may not exist or you may not have
  access to it.
```

Both the Build and Report agents hit this on two DIFFERENT models — not a
model-choice problem in the work itself, but an infra-layer hiccup (likely a
transient auth/availability blip on the model-serving side). The error has
nothing to do with the AFS, the diff, or any actual defect.

## What to do (confirmed working)

1. **Don't trust the failure's apparent severity.** `status: failed` with a
   model-access message reads like "something is broken," but per
   `workflow_hard_failure_can_still_have_landed_real_work.md`, check git
   FIRST: `git fetch origin && git log origin/tests/batch-<slug> --oneline`.
   In this case the analyst's AFS + surface digest + memory commits were
   already on the trunk, untouched by the later failure.
2. **Resume with the SAME `resumeFromRunId`** — do not re-dispatch a fresh
   `Workflow` call with new args. The analysis step (already cached) replayed
   instantly; only the failed Build+Report agents re-ran live, this time
   against a model that was available again (no `--model` override needed —
   the retry on an unmodified prompt simply succeeded).
3. On resume, the implementer found a **complete-but-uncommitted
   implementation already in the working tree** (the first attempt's
   in-progress work, orphaned by the model-access failure mid-session) and
   correctly treated it as inherited work to verify/fix rather than discard —
   see `verify_feature_branch_before_first_commit.md` (implementer-side
   memory) for that sub-pattern.

## Rule

A `Workflow` agent failure whose message is literally about model
access/existence (not a tool error, not a schema violation, not a logic
error) is an infra transient. Resume via `resumeFromRunId` with unchanged
args before considering anything else — no `--model` override, no manual
rebuild. If it recurs on the SAME agent after a resume, escalate as a real
infra blocker; one occurrence resolved cleanly on the first resume here.
