---
name: Merge gate — gh pr diff can go stale vs a freshly-pushed base branch
description: Before merging, verify PR file count with local git diff against origin's base ref, not just gh pr view/diff — GitHub's cached PR diff lags a base-branch push
type: feedback
---

## What happened

Issue #19 (2026-07-13): a fix-only PR (#24, 1 file / 14 lines by local `git diff`)
showed as an 18-file diff in `gh pr view`/`gh pr diff` because the local
`automation/base` branch was 2 commits ahead of `origin/automation/base` (those 2
commits had never been pushed — an earlier session committed workflow-doc changes
locally and moved on). The PR branch was cut from that ahead-of-origin local state,
so its history included those 2 commits; GitHub computed the diff against its own
stale `origin/automation/base` tip, inflating the visible file count 18x.

## Why it matters

Squash-merging on the inflated diff would have silently comingled 2 unrelated
workflow-doc commits into the fix's squash commit — a real regression risk in a
"no-review, LGTM, squash" pipeline where the merge gate trusts `gh pr view` at
face value.

## Fix applied

1. `git fetch origin automation/base && git log --oneline origin/automation/base..automation/base` to detect the local-ahead-of-origin gap.
2. `git push origin automation/base:automation/base` (fast-forward only — matches the "never rebase/force-push automation/base" discipline).
3. Independently confirmed the true diff via `git diff origin/automation/base <pr-branch> --stat` locally (1 file, 14 lines) — this is the source of truth, not `gh pr view --json files` or `gh pr diff`, both of which can lag behind a base-branch push even after `mergeStateStatus` recomputes to `CLEAN`.
4. Merged once the local check confirmed the real scope.

## Rule going forward

**Before merging any automation PR, if the reviewer or `gh pr view` reports a
file count that looks larger than the described change, don't trust it at face
value.** Run:

```bash
git fetch origin <base-branch>
git log --oneline origin/<base-branch>..<base-branch>   # local ahead of origin?
git diff origin/<base-branch> <pr-branch> --stat          # the real diff
```

If local `<base-branch>` is ahead, fast-forward push it to origin first, then
re-verify the diff locally before trusting `gh pr view`/`gh pr diff` again (their
cache can take a moment, or may not refresh file-list until a synchronize event
fires on the head branch — don't wait on it, verify with git directly).
