---
name: Fix-round dispatch lands in a NEW worktree while the PR branch is checked out in the ORIGINAL one
description: A fix-round implementer dispatch gets a fresh isolated worktree, but git refuses to check out the PR's branch there because it's already checked out in the original implementer's (still-existing) worktree — resolve by branching from the same tip under a fixround/ name and pushing back to the PR's branch name.
type: feedback
---

## The problem

A "fix round" dispatch (after reviewer CHANGES_REQUESTED) names the branch to
fix (e.g. `tests/ELITEA-1880-llm-selector-settings-dialog-persist`) and hands
you a fresh isolated worktree. But `git checkout <branch>` fails:

```
fatal: '<branch>' is already used by worktree at '<path-to-other-worktree>'
```

The original implementer's worktree (from the FIRST pass) is often still on
disk with that exact branch checked out — nobody cleaned it up between the
review round and the fix-round dispatch.

## Resolution (confirmed safe, matches existing team convention)

1. **Verify the other worktree's branch has nothing unpushed** — compare the
   LOCAL branch ref (visible from your own worktree, since refs are shared:
   `git log --oneline <branch> -5`) against `origin/<branch>` (`git fetch
   origin` first). If they match exactly (`git diff <branch>
   origin/<branch>` empty), it's safe to build on the origin tip — the other
   worktree has nothing lost.
2. **Create a NEW local branch in your own worktree from that same tip**,
   named `fixround/<CASE-ID>-review-r1` (confirmed team convention — see
   already-merged precedent: `fixround/ELITEA-1890-review-r1`,
   `fixround/ELITEA-1851-review-r1`, `fixround/ELITEA-1851-review-r1-axel`):
   `git checkout -b fixround/<CASE-ID>-review-r1 <sha-of-branch-tip>`.
3. **Commit your fixes there.**
4. **Push it to the ORIGINAL branch name at origin** (updates the existing
   PR as a fast-forward, since your new branch's parent IS that tip):
   `git push origin fixround/<CASE-ID>-review-r1:<original-branch-name>`.
   Confirmed precedent: `origin/tests/ELITEA-1890-version-switch-instructions`
   contains the ELITEA-1890 fix-round commits, while
   `origin/fixround/ELITEA-1890-review-r1` was never pushed under its own
   name — i.e. the `fixround/*` name is a LOCAL working name only; the PR
   branch name is what actually gets updated at origin.

Do NOT try to remove/force the other worktree to free up the branch name —
unnecessary and riskier than just branching from the same tip.

## Also hit this session: fresh worktree missing `automation/.env.test`

A brand-new implementer/fix-round worktree does not automatically get the
`automation/.env.test -> ../../.env.test` symlink (it's gitignored, so it
isn't part of the worktree checkout). Symptom: `pytest` collects the test
but immediately SKIPs it with `Login failed: Invalid URL '': No scheme
supplied` (Base URL resolves empty). Fix: create the symlink yourself,
pointing at the real workspace-root file directly (absolute path is
simplest and robust across worktrees):

```bash
ln -s "<workspace-root>/.env.test" "<this-worktree>/automation/.env.test"
```
