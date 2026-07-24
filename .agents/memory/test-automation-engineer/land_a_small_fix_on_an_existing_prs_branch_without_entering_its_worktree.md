---
name: Land a small fix on an existing PR's branch without entering (or removing) its worktree
description: When an implementer redispatch finds a real, small, verified fix needed on a branch that's still checked out in ANOTHER worktree you can't enter (EnterWorktree looks like it succeeds but the sandbox still refuses commands there), don't remove that worktree — check out a differently-named local branch off the remote tip in YOUR OWN worktree, commit there, and `git push origin <local-branch>:<remote-branch-name>` to fast-forward the shared remote ref directly.
type: feedback
---

## The situation (ELITEA-1978, second implementer dispatch, batch cov60, 2026-07-24)

Redispatched to the implementer slot for a case whose branch+PR (#1008,
`tests/ELITEA-1978-credential-duplicate-mismatch-validation`) already existed,
complete and sanctioned-RED, sitting in a DIFFERENT worktree
(`wf_e44028a9-dec-56`) from a prior implementer session. Verification (per
`implementer_redispatch_on_already_complete_case_verify_via_git_gh_not_rerun.md`)
found the branch/PR solid, but a genuine, small, verified gap: the test's
`pytest.mark.p2` should be `p1` (case priority "high" per `pytest.ini`'s own
documented mapping + 5 sibling credentials tests — see
`afs_priority_vs_pytest_mark_preflight_check.md`).

Tried `EnterWorktree(path=".../wf_e44028a9-dec-56")` to fix it there directly
— the tool call returned a normal success confirmation, but every subsequent
`Bash` call still errored `"isolated in the worktree wf_e44028a9-dec-52"`.
Confirmed via `pwd` mid-session: cwd was still my own worktree. This matches
`fixround_dispatch_collides_with_stale_prior_worktree_same_branch.md`'s note
that a pinned subagent can't actually act inside another worktree despite the
tool's claim — but that entry's fix (`git worktree remove` on the OTHER
worktree, then check out the branch fresh in your own) assumes the other
worktree is safely abandoned/orphaned. I didn't want to assume that here (no
positive evidence it was safe to remove, and removing it wasn't necessary for
what I needed).

## The simpler alternative

Since git branches are refs shared across ALL worktrees of the same repo
(only the *checkout* — the working directory — is exclusive per branch name),
you don't need the SAME local branch name to touch the SAME remote branch:

```bash
# From YOUR OWN worktree — re-enter it first if EnterWorktree took you
# somewhere your Bash calls can't actually reach:
#   EnterWorktree(path="<your-own-worktree>")

git fetch origin
# a DIFFERENTLY-named local branch, based on the PR branch's remote tip —
# does NOT collide with the other worktree's checkout of the same-NAMED
# local branch, because the local branch NAME is different:
git checkout -b fix/<case>-<slug> origin/tests/<case>-<slug>

# make the verified fix, commit normally
git add <file>
git commit -m "fix(<CASE>): <what>"

# push your local branch's tip directly onto the REMOTE branch name the
# PR tracks — a plain fast-forward, since your branch's parent IS that
# remote tip. This updates PR #<N> without ever touching the other
# worktree's working directory.
git push origin fix/<case>-<slug>:tests/<case>-<slug>
```

Confirmed via `gh pr view <N> --json headRefOid` that the PR's head moved to
the new commit immediately — GitHub tracks the branch by NAME, not by which
local ref/worktree produced the push.

## When this is the right call vs. `git worktree remove`

- **Use this (push-only, no removal)** when: the fix is small/verified, you
  don't have positive evidence the other worktree is abandoned, or removing
  it would lose something (e.g., its own uncommitted exploration state,
  even if the branch itself is fully pushed). Zero blast radius — you never
  touch the other worktree at all.
- **Use `git worktree remove`** (the sibling entry's approach) when you
  actually need to WORK inside that worktree's existing files going forward
  (e.g., a fix-round with more than one small change, or when the other
  worktree is confirmed stale/unlocked and reusing its exact state matters).

## Bonus: this also side-steps needing the worktree's own `.venv`/`.env.test` fixes

Since you never enter the other worktree, none of its potential environment
gaps (`redispatch_reverify_by_running_the_implementer_worktree_test.md`'s
missing-`.venv`/broken-`.env.test`-symlink issues) matter — you verify and
re-run from your OWN worktree's already-working environment instead.
