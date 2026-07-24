---
name: Redispatch verification must check PR mergeable state, not just base-drift on the touched code files
description: The existing ground-truth-verification checklist for an already-complete redispatched case checks additive-only + automation/base drift on the touched CODE files — but a batch's parallel branches all append to the SAME shared memory-log files (MEMORY.md, daily/<date>.md), which conflicts even when the code has zero overlap. Add `gh pr view --json mergeable,mergeStateStatus` as a cheap first check; a CONFLICTING/DIRTY PR needs a merge (usually a trivial union-resolve on the memory files) before it can proceed to the hardening gate.
type: feedback
---

## The situation

ELITEA-2021's implementer slot was redispatched a THIRD time (`implementer_redispatch_on_already_complete_case_verify_via_git_gh_not_rerun.md` and its own `docs(memory)` predecessor cover rounds 1–2 of this same case). PR #1029 was already fully implemented, fix-rounded (review r1 addressed), and — per the existing redispatch checklist — verified clean: additive-only held on the 3 touched files (0 real deletions), and `automation/base` hadn't drifted the two touched page objects at all.

But `gh pr view 1029 --json mergeable,mergeStateStatus` returned `CONFLICTING` / `DIRTY`. The existing checklist doesn't run this check at all — it infers mergeability indirectly from base-drift-on-touched-files, which missed this because the actual conflict was on files the checklist wasn't looking at.

## Root cause

This batch runs many implementer cases in parallel, each in its own worktree, each branch cut from a slightly-earlier `automation/base`. Every implementer/fix-round session ALSO appends entries to two **shared, append-only, git-tracked memory files**:
- `.agents/memory/test-automation-engineer/MEMORY.md` (index)
- `.agents/memory/test-automation-engineer/daily/<date>.md` (daily log)

Three other same-batch cases (ELITEA-2082/2083/2080, ELITEA-2170, ELITEA-1877) merged into `automation/base` in the meantime, each having appended their own lines to these same two files. Git sees this as a real content conflict (a content conflict on MEMORY.md, an add/add conflict on the daily log if the branch created that day's file before it existed upstream) even though there is **zero conflict in the actual test/page-object code** — the two conflict classes are on completely disjoint file sets.

## The fix — add one cheap check to the existing redispatch checklist

Before (or alongside) the additive-only + base-drift checks in `implementer_redispatch_on_already_complete_case_verify_via_git_gh_not_rerun.md`, run:

```bash
gh pr view <N> -R <owner>/<repo> --json mergeable,mergeStateStatus,additions,deletions,changedFiles
```

- `MERGEABLE` / `CLEAN` → proceed as that entry describes (verification only, no new commits needed).
- `CONFLICTING` / `DIRTY` → don't panic-assume a code regression. First isolate WHICH files conflict:
  ```bash
  git fetch origin
  git merge --no-commit --no-ff origin/automation/base   # on the PR's own branch, in your worktree
  git status --short   # UU/AA lines are the conflicting files
  ```
  If the conflicts are confined to the shared memory-log files (the common case in this batch shape), resolve as a **union merge** — keep every line from both sides, don't drop either side's entries, preserve each side's own internal ordering, place blocks in a sensible chronological position. These files are markdown line-item logs, not structured code — a mechanical union is always correct here, never a "pick one side" resolution.
  If a conflict appears in an actual test/page-object file, that's the signal to stop and actually investigate (which is what the original entry's "reserve an actual re-run for when it's informative" carve-out already covers) — don't blindly union-merge code.
- Commit the merge (plain `git commit`, no flags needed once conflicts are staged), push the branch, and re-check `gh pr view` shows `MERGEABLE`/`CLEAN` before reporting the case as verification-complete.
- **Re-run the covering test once after the merge** even though the code itself didn't change — it's cheap (this project's specs run in the 30–200s range) and confirms the merge commit didn't somehow break anything, closing the loop before handing back to the orchestrator.

## Why this matters going forward

Every case in a parallel batch that writes to per-role memory files as part of its own branch (this project's established pattern — see the sibling entries in this same file for examples of "New curated entry: ..." being committed as part of an implementer's own PR) will hit this exact shape once ANY other same-batch case merges first. It is expected, mechanical, and safe to resolve — but only if you check for it. A redispatch verification that stops at "additive-only + base-drift on the touched code" will report a case as done when its PR is actually blocked from merging.
