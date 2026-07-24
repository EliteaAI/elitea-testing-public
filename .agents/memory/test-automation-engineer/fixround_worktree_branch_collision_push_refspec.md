---
name: fixround_worktree_branch_collision_push_refspec
description: A fix-round dispatch into a fresh isolated worktree can't checkout the PR's own branch name if it's already checked out in a sibling worktree — branch under a fixround/ name tracking origin's PR branch, then push with an explicit refspec back to the PR branch name
type: feedback
---

**Symptom.** Dispatched as an implementer fix-round for an existing PR, told
to work "on branch `tests/<CASE-ID>-<slug>`" — but `git checkout
tests/<CASE-ID>-<slug>` fails: `fatal: '<branch>' is already used by worktree
at '<path-to-some-other-worktree>'`. Git worktrees are one-branch-one-checkout;
a prior/parallel worktree still has that exact branch name checked out.

**Fix — branch under a different local name, push back to the real one:**

```bash
git fetch origin
git checkout -b fixround/<CASE-ID>-review-r1 origin/tests/<CASE-ID>-<slug>
# ... make the fix-round commits on this local branch ...

# immediately before pushing, re-fetch and confirm the remote hasn't moved
# (no other worktree/session pushed to the PR branch while you worked)
git fetch origin tests/<CASE-ID>-<slug>
git log --oneline -3 origin/tests/<CASE-ID>-<slug>   # should match what you branched from

# push with an EXPLICIT refspec — local-branch-name : remote-branch-name —
# NOT a bare `git push` (which would try to create/push a NEW remote branch
# named `fixround/<CASE-ID>-review-r1`, not update the PR's actual branch)
git push origin fixround/<CASE-ID>-review-r1:tests/<CASE-ID>-<slug>
```

This lands as a fast-forward onto the existing PR branch (same effect as if
you'd committed directly on `tests/<CASE-ID>-<slug>`), so the existing PR
(e.g. via `gh pr view <PR-URL>`) picks up the new commit automatically — no
new PR needed, no `--force` needed, as long as the remote genuinely didn't
move (checked by the immediately-prior fetch).

**Why this matters:** in a factory doing parallel batch work, a case's PR
branch is very often still checked out in the analyst's or the original
implementer's now-idle worktree at fix-round time. Don't ask the orchestrator
to free it up — branch-and-refspec-push is strictly local, costs nothing, and
leaves every other worktree untouched.

**Companion gotcha in the same isolated-worktree setup:** `automation/.env.test`
is a symlink (`../../.env.test` in the main checkout) that resolves relative
to the checkout's OWN depth — a worktree nested under
`.claude/worktrees/<name>/` sits several directories deeper, so the same
relative symlink target is wrong/missing there. Recreate it pointing at the
TRUE workspace root's `.env.test` (find the root by walking up until you see
the sibling `EliteaUI/`, `onetest-ai-tm-Elitea/` folders) — it's gitignored
(`**/.env*`) so this is a pure local fix, never a tracked change:
```bash
ln -s "<true-workspace-root>/.env.test" automation/.env.test
```
Likewise `.venv/bin/pytest`'s shebang is a copied venv's absolute path back to
the MAIN checkout's `.venv/bin/python3.13` (not this worktree's own copy) —
that's fine and expected as long as the main checkout's venv still exists at
that path; no action needed, just don't be surprised the interpreter path in
`pytest -v`'s banner points at the main checkout, not the worktree.

**Variant: the fix-round finding is "your PR's base branch moved" (stacked
surface-train PRs), not just "the branch name collides" (ELITEA-2005 fix
round, PR #1022, one level up the stack from the ELITEA-2006 case above).**
When a PR is deliberately built on ANOTHER case's branch instead of
`automation/base` (a "surface train" — reuses the base case's page-object
methods/testids), and that base branch gets its own fix round after your PR
was cut, your PR's `mergeable` flips to `CONFLICTING` even though your OWN
diff never touched the conflicting region. Confirm this mechanically before
touching anything: `gh pr view <N> --json baseRefName,mergeable`, then
`git diff origin/<old-base-tip>...origin/<your-branch>` — if that diff never
touches the region the base's fix round changed, it's a clean rebase, not a
rewrite. Same branch-collision constraint applies (the head branch is
probably checked out in a sibling worktree too), so combine both patterns:

```bash
git fetch origin
git checkout -b fixround/<CASE-ID>-review-r1 origin/tests/<CASE-ID>-<slug>
git rebase --onto origin/tests/<BASE-CASE-ID>-<slug> <old-merge-base-sha>
# resolve conflicts (memory/index-style append-only files are the likely
# hits — resolve additively, keep every entry from both sides) —
# `git merge-base <old-branch> <base-branch>` finds <old-merge-base-sha>
# ... git rebase --continue ...

git fetch origin tests/<CASE-ID>-<slug>   # re-confirm remote hasn't moved
git push origin fixround/<CASE-ID>-review-r1:tests/<CASE-ID>-<slug> \
  --force-with-lease="tests/<CASE-ID>-<slug>:<old-remote-tip-sha>"
```

**`--force-with-lease` (scoped to the exact old tip), not a bare `--force`,
and not a bare `git push`** — a rebase rewrites the branch's commit SHA
(unlike the pure-append case above, which fast-forwards), so the remote
genuinely needs a force-update; the lease's expected-old-value makes it
safe (fails loudly instead of clobbering if someone else pushed in the
meantime, rather than trusting the pre-push fetch alone). Verify
`gh pr view <N> --json mergeable` flips to `MERGEABLE` after the push.

**Simpler variant when the colliding worktree is genuinely stale, not just
idle (ELITEA-2007 fix round, PR #1038): remove it instead of branching
around it.** If the sibling worktree holding the PR's branch belongs to a
PRIOR implementer dispatch that already finished (its own commits are
already pushed — check `git log --oneline <worktree-path-branch>` shows
nothing your dispatch needs to preserve) and `git worktree list` shows it
**unlocked** (no `locked` suffix), you don't need the `fixround/`-branch
dance at all:

```bash
git worktree remove ../<stale-worktree-name>     # from YOUR OWN worktree —
                                                  # this is a plumbing op, not
                                                  # a cd into the other worktree,
                                                  # so the isolation sandbox allows it
git fetch origin tests/<CASE-ID>-<slug>
git checkout tests/<CASE-ID>-<slug>              # now free, normal checkout
```

Then work exactly as if you'd been handed the branch directly — plain
`git push origin tests/<CASE-ID>-<slug>` at the end, no refspec gymnastics,
no force. This is strictly simpler than the branch-and-refspec-push pattern
above and should be tried FIRST; fall back to the `fixround/`-branch dance
only if the worktree is locked, or its own uncommitted changes look like
they matter (check `git status --short` there — you can read another
worktree's status via `git -C <path> status --short` even under the
isolation sandbox, since that's a read, not a cd). Don't reflexively assume
a same-branch collision means "branch around it" — check whether the
colliding worktree is simply done and removable first.
