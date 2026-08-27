---
name: Shared-worktree branch race on parallel dispatch
description: Another live session can switch the branch under you mid-task; verify the branch at commit time and that the push actually moved the ref
type: feedback
aliases: [branch race, wrong branch commit, everything up-to-date, shared working tree, parallel session checkout]
tags: [area/git, type/hazard]
created: 2026-08-27
updated: 2026-08-27
---

## What happened

Dispatched (analyst slot, docs-only) to commit on `automation/base` while an
implementer session was working `tests/ELITEA-2215-unblock` **in the same
working tree**. I checked out `automation/base`, edited, committed, pushed.

`git push origin automation/base` answered **"Everything up-to-date"** — and it
was telling the truth. Between my checkout and my commit the implementer's
session had switched the tree back to `tests/ELITEA-2215-unblock`, so my commit
landed on *their* branch. `git checkout` earlier in the session proves nothing
about which branch you are on now.

## The rule

1. **Re-read `git branch --show-current` in the same command block as the
   commit** — never rely on a checkout from an earlier turn.
2. **A push that says "Everything up-to-date" after you just committed is a
   RED FLAG, not a success.** Verify the remote ref actually moved:
   `git log --oneline -1 origin/<branch>`.
3. Also watch for foreign modifications appearing in `git diff --stat` for
   paths you never touched — that is the other session writing beside you.
   Stage **by exact path**, never `git add -A`.

## Relocating a misplaced commit without disturbing the other session

Do **not** checkout/reset a branch another session is live on. Build the commit
with plumbing (no working-tree touch), then move the ref:

```bash
export GIT_INDEX_FILE=/tmp/relocate-idx
git read-tree <target-branch-tip>
for p in <paths>; do
  git update-index --cacheinfo "$(git ls-tree <my-commit> -- "$p" | awk '{print $1","$3}'),$p"
done
TREE=$(git write-tree)
NEW=$(git commit-tree "$TREE" -p <target-branch-tip> -m "<msg>")
git update-ref refs/heads/<target-branch> "$NEW" <target-branch-tip>   # old-value guard
```

`git update-ref` with the **old-value argument** is the safe primitive — it
fails instead of clobbering if someone moved the ref meanwhile. Same guard when
rewinding your stray commit off the other branch; if HEAD has moved again,
**skip the rewind** and leave their branch alone. A duplicated, byte-identical
docs commit on both branches merges as a no-op — verify with
`git diff <branchA> <branchB> -- <paths>` returning empty. That is strictly
better than fighting a live session for the tree.

Related: [[git_worktree_can_leave_main_checkout_on_wrong_branch]]
