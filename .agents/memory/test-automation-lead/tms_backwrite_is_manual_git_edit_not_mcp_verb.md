---
name: TMS backwrite is a manual git edit, not an MCP verb
description: onetest-tms MCP has no tool that edits case-file frontmatter (status/execution_type/automation_test_id/automation_pr) — backwrite_on_done means directly editing the case markdown in the sibling onetest-ai-tm-Elitea clone and pushing to main, matching the ELITEA-1894 precedent commit
type: feedback
---

`.agents/test-automation.yaml` § `backwrite_on_done` says "edit the case file in
cases_repo" — that phrase is literal, not shorthand for an MCP call. The
`onetest-tms` MCP server's tools (`get_test_case`, `record_result`,
`create_run`, `complete_run`, `search_test_cases`, `automation_coverage`,
`build_index`, `ingest_results`, `rerun_execution`, `create_defect`) all
operate on **execution issues** / the test-case **index**, not on case-file
frontmatter fields. There is no `update_case` / `set_field` verb.

The correct mechanism, confirmed against the precedent commit `68420ae`
(ELITEA-1894, issue #62):

1. `cd ../onetest-ai-tm-Elitea` (sibling clone, admin access, on `main`).
2. `Read`/`Edit` the case file's YAML frontmatter directly — flip
   `status: draft` → `status: ready`, `execution_type: manual` →
   `execution_type: automated`, add `automation_test_id:` (dotted pytest
   path) and `automation_pr:` (the merged automation/base PR URL).
3. `git add` the single file, commit with `chore(<TMS-ID>): back-write
   automation status — ready/automated` + a `Test merged: <PR URL>` body
   line, `env -u GITHUB_TOKEN git push origin main`.

Editing this file is within the orchestrator's authority — it's TMS case
metadata (an external system's record), not test-framework code, and
`backwrite_on_done` explicitly assigns the write to the orchestrator
post-merge. Don't burn a turn hunting for an MCP write verb that doesn't
exist; don't skip the back-write because no MCP tool obviously does it.

Confirmed working again on ELITEA-1915 (issue #63, commit `c361696`) — same
4-field pattern, same commit-message shape.
