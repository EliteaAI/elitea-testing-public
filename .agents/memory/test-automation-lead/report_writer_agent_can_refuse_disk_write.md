---
name: Report-writer agent can refuse the disk write
description: batch-build's report-writer subagent often returns written:false ("subagent policy") instead of writing to disk, AND .agents/automation/ is gitignored anyway — lead reconstructs/verifies report.json by hand every single run
type: feedback
---

Recurring across the campaign (logged 2026-08-05, reconfirmed 2026-08-06 on
#876, again on `elitea-2392-ai-configuration-page`, and again 2026-08-14 on
`skills-buildwithai-fidelity-rework` — that run's report writer returned
`written:false` on its SECOND attempt too, right after the gate agent it
depends on had also failed twice; see
`workflow_internal_gate_two_failures_run_it_yourself.md` for that sibling
pattern): two separate but compounding facts, both requiring the same fix.

1. **The report-writer subagent frequently doesn't write.** It can return
   `{"written": false, "detail": "## Batch Report ... Report files not
   written to disk — subagent policy. Provide this content to the
   test-automation-lead for disk writes."}` instead of actually writing
   `.agents/automation/<slug>/report.{json,md}` — even though the workflow
   docs describe this as "the run's single disk write."
2. **`.agents/automation/` is gitignored** (`.gitignore` line ~67) — so even
   on a run where the file DOES get written, it will never survive a
   `git checkout`/branch-switch elsewhere in the same session, and it never
   shows up in `git status`/`git add`. This is intentional (local-only run
   state), not data loss — don't treat a missing copy after a branch switch
   as something to recover.

**What to do, every batch, no exceptions:** after the workflow completes,
`ls .agents/automation/<slug>/` and open `report.json`. If absent, or present
but built from an earlier/interrupted write (check for the literal string
`[clipped; full text in the unit's receipt under .agents/automation/_returns/]`
— a sign of a stale partial write), reconstruct it yourself from the
workflow's returned top-level `result` object (same shape: `batch`/`base`/
`integration_branch`/`gate`/`cases`/`totals`/etc.) — squarely within the
lead's own `.agents/automation/**` edit allowance, no dispatch needed. For
any finding whose text got clipped in the top-level result, pull the full
text from `journal.jsonl`'s `report:<slug>` (or the originating unit's)
agent entry before writing the final file.
