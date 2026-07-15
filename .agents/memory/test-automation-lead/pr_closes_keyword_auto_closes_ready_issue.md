---
name: PR "Closes #N" keyword auto-closes an issue that should stay OPEN at Ready
description: Implementers' PR-tool defaults often insert "Closes #N" — strip/replace it before merge, since factory-mode Ready is agent-terminal and issue-close is human-only
type: feedback
---

## What happened

Issue #18 (2026-07-15, ELITEA-1796 rework): the implementer's PR #289 body ended
with `Closes #18` — a standard GitHub convention their PR-authoring habit/template
defaults to. Caught it before merge: `.agents/workflow.md` + factory-mode delta #6
require the issue to stay OPEN at `Ready` — `Done` and issue-close are HUMAN-ONLY.
A squash-merge with that keyword intact would have auto-closed #18 the moment the
merge landed, silently violating the terminal-state contract with no error, no
warning — GitHub just does it.

## Fix applied

`gh pr edit <N> --repo <repo> --body "$(gh pr view <N> ... -q .body | sed 's/^Closes #18$/Refs #18 (factory mode: issue stays OPEN at Ready; humans close it)/')"`
before merging — same-repo edit, no scope creep, no functional change to the PR.

## Rule going forward

**Before merging any automation PR in a project where `Ready` must leave the issue
open, grep the PR body for the auto-close keyword set** (`Closes|Fixes|Resolves #N`,
case-insensitive, GitHub's full list) and neutralize any hit pointing at the
originating issue. Do this as a standing step in the pre-merge checklist, not just
when it happens to catch your eye — implementers reach for "Closes #N" by habit
(it's the GitHub-native, PR-template-encouraged pattern) and won't know to avoid it
unless the dispatch prompt says so explicitly, which is easy to forget to include.
Cheapest fix: add this grep to the orchestrator's own pre-merge gate script/checklist,
not just implementer instructions (instructions get missed; a gate doesn't).
