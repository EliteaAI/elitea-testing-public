---
name: Deleting a batch trunk auto-closes any unit PR still targeting it
description: cleanup preserves the head branch but GitHub closes the PR whose BASE you deleted — re-target or close out open unit PRs first
type: feedback
created: 2026-08-28
updated: 2026-08-28
---

## What happened (#1398 wave 6 → wave 7)

Wave 6 ended with one unit unlanded: PR **#1945** (ELITEA-2314..2319) was still OPEN
against the batch trunk `tests/batch-settings-w06`. I ran close-out cleanup, which
correctly **KEPT** the head branch (`cleanup.mjs` printed
`KEEP tests/ELITEA-2314-analytics-date-filter — no merged change request names it`)
but deleted the trunk.

**GitHub auto-closes a PR when its BASE branch is deleted.** Next session, #1945 read
`CLOSED`, `mergeable=CONFLICTING` — which looks exactly like an abandoned or rejected
unit.

## Why it was recoverable

The head branch survived with **all 11 commits**, including both prior fix rounds.
Verified before doing anything:

```bash
git ls-remote --heads origin tests/ELITEA-2314-analytics-date-filter   # exists
git log --oneline origin/automation/base..origin/tests/ELITEA-2314-analytics-date-filter
git diff --name-only origin/automation/base...origin/tests/<branch> -- automation/
```

Recovery: new trunk from current base, merge base into the branch (its conflicts are
real — dispatch them), finish the outstanding blockers, re-open a PR against the new
trunk.

## The habit

**Before deleting a batch trunk, check for unit PRs still targeting it.**

```bash
env -u GITHUB_TOKEN gh pr list --repo <owner/repo> --state open \
  --json number,headRefName,baseRefName \
  | python3 -c "import json,sys;[print(p) for p in json.load(sys.stdin) if 'batch-' in p['baseRefName']]"
```

Any hit gets re-targeted (`gh pr edit <n> --base automation/base`) or explicitly closed
with a note — never left to be closed as a side effect. A closed PR is not a lost
branch, but the *next reader* cannot tell that without the check above, and a closed PR
carrying three rounds of review history reads as "rejected".

Add the same check to the end-of-wave close-out, next to the cleanup call.

Related: [[batch_workflow_never_opens_trunk_to_base_pr]] · [[settings_area_backlog_1398]]
