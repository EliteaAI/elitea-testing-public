---
name: Trunk→base PR can use a stale head, missing the report-writer's commit
description: gh pr create right after a workflow-completion notification can resolve --head to a remote ref one commit behind the trunk's real tip — the report-writer's own commit lands on origin a beat after the notification, so the squash-merged PR silently omits report.json
type: feedback
---

Observed 2026-08-06, ELITEA-2397/#905 (batch-build run `wf_d47f9ad0-6cd`). The
workflow's report phase is last: it commits `.agents/automation/<slug>/report.json`
to the batch trunk and pushes. `TaskOutput` returned `report_written: true` with
the full result, and I immediately did `git fetch origin` → `gh pr create --base
automation/base --head tests/batch-<slug>` → squash-merged it. The merged PR's
file list (`gh pr view <N> --json files,commits`) turned out to be missing
`.agents/automation/<slug>/report.json` — its commit (the report-writer's own)
simply wasn't on `origin/tests/batch-<slug>` yet at the moment `gh pr create`
resolved the head ref, even though my local clone (freshly fetched) already had
it as an ancestor of the local branch tip. A second `git fetch` a few minutes
later showed the same discrepancy — the remote branch was already gone (PR
merged + `--delete-branch`), so there was nothing left to re-diff against; I only
caught it by checking `gh pr view --json files` post-merge.

**Fix applied:** dispatched a tiny follow-up (`test-automation-engineer`) to
`git checkout <report-commit-sha> -- .agents/automation/<slug>/` from the still-
present LOCAL batch-trunk branch (not yet pruned) and land it as its own commit
on `automation/base`. Worked because the local branch survived the remote
deletion; would not have if I'd deleted the local branch first.

**What to do next time, before creating the trunk→base PR:** compare the local
trunk branch tip against what `gh pr create` will actually use —
`git log -1 --format=%H tests/batch-<slug>` vs
`git ls-remote origin tests/batch-<slug>` — and if they differ, `git push origin
tests/batch-<slug>` yourself before opening the PR. Cheaper still: after the PR
merges, always run `gh pr view <N> --json files` and confirm
`.agents/automation/<slug>/report.json` is in the list before treating the batch
as landed — catches this and any other stale-head short-count silently.
