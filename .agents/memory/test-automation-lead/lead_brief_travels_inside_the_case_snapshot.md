---
name: A lead brief travels inside the case snapshot — the only channel every workflow slot reads
description: batch-build has no per-case/lead-notes arg; design constraints reach analyst, implementer AND reviewer only by living in .agents/automation/<slug>/cases/<ID>.md (pointer + verbatim-body marker), and a gate that is green at invocation level can still be impure — read reruns.json + allure status before calling it clean.
type: feedback
---

## Rule

1. **Batch design constraints go in the snapshot.** `batch-build.workflow.mjs` interpolates
   only args and worker results; the case snapshot path is the one file the analyst (721),
   triage/combined (850/920), reviewer (959) and implementer (1063) prompts ALL name. Write
   `.agents/automation/<slug>/LEAD-BRIEF.md`, then prepend to every snapshot:
   `> LEAD NOTE: read the batch brief FIRST — <path> (NOT case text).` + blank +
   `=== TMS CASE BODY (verbatim) — <ID> ===` + the untouched TMS body. The marker matters:
   the reviewer judges fidelity/coverage against the body, not the brief (verified #2301 —
   reviewer explicitly separated them).
2. **A green invocation is not a clean gate.** `3 passed … 1 rerun` + `reruns.json != {}`
   = an absorbed attempt. Open the allure result (`status: broken`, `statusDetails.message`,
   the Failure Evidence screenshot) BEFORE deciding; the screenshot named the real cause
   (#2305 create-picker redirect) in 30 s where the message named the wrong thing
   (`folders-panel-create-btn` not visible).
3. **A transit guard inherits the redirected page's console noise.** Fixing a precondition
   redirect with a retry moves the red from Step 0 to the console axis unless the retry
   branch clears exactly the discarded attempt's messages (canon card #2308). Arming the
   collector late is the wrong shape — it uncovers the real page's own mount.
4. **Randomized-draw specs: record the draw per gate run.** Pull
   `social-folders: entity_type=…` from `reports/allure-results/*-attachment.txt` newer than
   a per-run marker file, or the Step-0 title; the closure record owes the table.

## Seen 1×

- #2301 / ELITEA-3208-3210 (2026-09-15) — brief reached all slots; lead gate run 3 impure
  → #2305; fix PR #2306 three rounds; final gate 3/3 `reruns.json == {}`.
