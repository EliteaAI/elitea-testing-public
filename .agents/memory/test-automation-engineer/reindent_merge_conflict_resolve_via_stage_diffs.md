---
name: Re-indent merge conflict — resolve via stage diffs, not the hunk
description: Prove a whitespace-only conflict resolution dropped nothing by diffing the :1/:2/:3 stages, not by reading the hunk git shows
type: feedback
aliases: [structural conflict, re-indent conflict, diff -w stages, automation/testids sync conflict, testid re-add]
tags: [area/git, area/testids, type/feedback]
created: 2026-09-14
updated: 2026-09-14
---

## The trap

When `main` re-indents/rewraps a whole component (EL-6612 on `ParticipantNormalCard.jsx`, 2026-09-14),
git's conflict hunk is misleading: OURS spans the whole body, THEIRS shows only a few lines, and the rest
of main's re-indented text is already sitting *after* `>>>>>>>`. Resolving by eye inside the hunk — or with
`git checkout --ours/--theirs` — either keeps stale indentation or drops our additive testids.

## The recipe (worked, #2279)

```bash
git show ":1:$F" > /tmp/base; git show ":2:$F" > /tmp/ours; git show ":3:$F" > /tmp/main
diff -w /tmp/base /tmp/main     # EMPTY  => main's change is pure whitespace
diff -w /tmp/ours /tmp/main     # => exactly OUR additive lines (import + testid attrs)
```
Resolve the hunk to THEIRS, re-add those lines at main's indentation, then prove it:
`diff /tmp/main $F` shows only our lines; `diff -w /tmp/ours $F` is empty. Nothing lost either direction.

## Two follow-on checks

- "File differs from both parents" is NORMAL for a merged file — it is not evidence the pre-commit
  hook (lint-staged: eslint --fix + prettier) rewrote it. Detect hook rewrites by filtering
  `git diff origin/main HEAD -- <file>` to non-testid lines and tracing each one to `HEAD^1`.
- Run the testid-loss guard against the *committed* HEAD (`git grep … HEAD -- src/`), after the hook ran.

Related: [[additive_only_grep_scope_your_own_unmerged_commits]] · `.agents/workflow.md` § Sync divergence rule
