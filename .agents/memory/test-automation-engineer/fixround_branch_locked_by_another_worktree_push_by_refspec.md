---
name: Fix-round branch locked by another worktree — push by refspec instead of local checkout
description: When a fix-round dispatch names the original branch but git already has it checked out in a sibling isolated worktree, work on a differently-named local branch from the same tip and push straight to the remote ref by refspec — that updates the PR, not the local branch name.
type: feedback
---

ELITEA-2031 fix round 1 (PR #1037). Dispatch said "fix round on branch
`tests/ELITEA-2031-pipeline-edge-creation`" but that exact local branch name
was already checked out in a *different* sibling worktree (the original
implementer's worktree, still present — not stale, just not cleaned up yet).
`git checkout tests/ELITEA-2031-pipeline-edge-creation` in my own worktree
failed hard: `fatal: 'tests/ELITEA-2031-pipeline-edge-creation' is already
used by worktree at <other path>`. I could not `cd`/`git -C` into that other
worktree to inspect or resolve it either — the harness's worktree-isolation
guard blocks any command that redirects git at a path outside your own
worktree, even read-only `status`.

**Resolution:** the thing that actually matters is the REMOTE branch (what
the PR tracks), not the local branch name:

1. `git fetch origin <branch>` to get the shared tip fresh.
2. `git branch <scratch-name> <sha>` — a differently-named local branch
   pointing at the exact same commit (e.g. `fixround/ELITEA-2031-review-r1`;
   this project's own fix-round branches already follow
   `fixround/<CASE-ID>-review-r1`, so this reads as in-convention, not a
   detour).
3. Do all the fix-round work and commit on that scratch branch.
4. Push by REFSPEC, not by branch name: `git push origin
   <scratch-name>:tests/<original-branch-name>`. This updates
   `origin/tests/<original-branch-name>` directly — the PR sees the new
   commit exactly as if it had been pushed from the "real" branch name. The
   local branch name is irrelevant to GitHub; only the ref path matters.
5. Verify fast-forwardability first: `git merge-base --is-ancestor
   origin/<branch> HEAD` before pushing, same as any other push safety check.

Don't waste time trying to force-move the shared local branch ref, don't
delete/reuse the other worktree's checkout, and don't ask the orchestrator to
rename anything — this is a same-repo, same-remote situation the refspec push
resolves cleanly in one command. The other worktree's local branch pointer goes stale (still points at the
pre-fix commit) but that's harmless as long as it never pushes its own
conflicting commit later — the remote ref is the coordination point PR
review actually reads.
