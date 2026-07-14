# Archived agents

Moved out of `.claude/agents/` on 2026-07-14 (operator-approved, framework-alignment
audit): these encoded a pre-pipeline workflow that competed with the sdlc-bundle
test-automation pipeline (Tal: analyst → implementer → reviewer) and bypassed its
gates (AFS, fresh-session review, live-run merge gate, closure record).

- `ui-test-orchestrator.md` — 6-stage single-session test creation flow. Every stage
  now has a canonical owner in the pipeline. Its load-bearing sub-skills
  (`add-data-testid`, `page-object-generator`, `start-ui-localhost`) remain active;
  `test-scout`, `ui-test-creator`, `test-deduplication`, `test-quality-checker` are
  orphaned (team may retire or rewrite them — team-owned).
- `failure-investigator.md` — superseded by the pipeline's failure triage.

Restore = move the file back into `.claude/agents/` and restart the host.
