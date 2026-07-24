---
name: Implementer redispatch on an already-approved-static case — rebase and reverify, never reimplement
description: When an implementer-slot dispatch lands on a case whose PR is already fully built, reviewed, fix-rounded, and approved-static (a bogus orchestrator bounce, not a real fix-round), the correct action is a ground-truth check + trivial-conflict rebase + one fresh green run — never a from-scratch reimplementation, which would duplicate approved work and risk a second competing PR.
type: feedback
---

## The situation

ELITEA-1880's board `case.md` History showed a case that had ALREADY completed
the full cycle — `analysis` → `ready-for-automation` → `implementing` →
`ready-for-review` → `approved-static` (01:00:26Z) — then bounced back to
`analysis` ~5h later with **zero recorded reason** (no CHANGES_REQUESTED note,
no board comment), cycled through the analyst slot again (who correctly did
zero live re-exploration per the existing qa-engineer redispatch playbook —
see `analyst_redispatch_on_already_complete_case_check_board_git_then_bounded_spotcheck.md`
§ Tenth instance for the analyst-side handling of this exact case), and landed
back on the **implementer** slot a third time. This is the analyst-side
"bogus bounce" pattern's implementer-side twin — it can hit either slot.

## Diagnostic sequence (before writing/touching any code)

1. `git worktree list` / `git branch -a | grep -i <case-id>` — does a branch
   for this case already exist?
2. `gh pr view <N> --json state,headRefName,baseRefName,mergeable,mergeStateStatus`
   (once you find the PR number, e.g. from the board `case.md`'s `PR:` field
   or `gh pr list --search <case-id> --state all`) — is it OPEN, and what's
   its real mergeability?
3. If a PR exists and looks complete: read the actual diff (`git diff
   <merge-base> <branch>` scoped to the case's real paths, ignoring
   unrelated churn from other cases that landed on `automation/base` in the
   interim) and spot-check it against the AFS/locator-policy/allure.step
   conventions — a bounded review, not a full re-implementation.
4. If it's genuinely solid (compliant locators, matches AFS steps, was
   already reviewed), the only thing possibly still needed is confirming it
   still runs green against the CURRENT `automation/base` tip.

## Why NOT reimplement

Rewriting a test that's already implemented, reviewed, and approved:
- Duplicates real work for zero benefit.
- Risks producing a SECOND branch/PR for the same case, which the
  orchestrator then has to reconcile — worse than the bounce itself.
- Violates the "reuse before create" Hard Rule and the team's "one PR one
  purpose" discipline.

## The actual gap, and how to close it safely

The real (and only) gap was `automation/base` had moved 35 commits ahead
since the PR's merge-base, producing `mergeStateStatus: DIRTY` /
`mergeable: CONFLICTING`. Before treating that as a real blocker, diff the
PR branch's changed-file set against `automation/base`'s own changed-file
set since their common ancestor and intersect — if the overlap is just
shared append-only files (this team's per-role `MEMORY.md` +
`daily/<date>.md`, touched by many parallel worktrees), it's a trivial
merge, not a real conflict (this is the same triage step already documented
for the analyst slot).

**The branch-collision wrinkle**: the PR's actual branch name
(`tests/<case>-<slug>`) is usually still checked out in the ORIGINAL
implementer's (or a fix-round's) still-existing worktree, so a fresh
dispatch's `git checkout <branch>` fails. Reuse the already-established
fix-round pattern (`fixround_worktree_branch_already_checked_out_elsewhere.md`):

```bash
git checkout -b impl/<case-id>-resume origin/tests/<case>-<slug>   # new LOCAL name, same tip
git merge origin/automation/base --no-edit                          # surfaces the conflict
# resolve conflicts (union both sides for append-only log files)
git add <resolved files> && git commit --no-edit
git merge-base --is-ancestor <old-tip> HEAD && echo "FF-safe"        # confirm before pushing
cd automation && HEADLESS=true ../.venv/bin/pytest <node-id> -v -p no:cacheprovider
git push origin impl/<case-id>-resume:tests/<case>-<slug>            # updates the EXISTING PR, no force
```

The `merge-base --is-ancestor` check before pushing is the safety net: if
true, the push is a plain fast-forward (a merge commit added on top of the
existing tip) and needs no `--force` — much safer than rebasing an
already-approved branch's history.

## What to report back

The dispatch contract asks for "the actual branch name, the PR number, and
your rerun count." Report the REAL PR branch name (`tests/<case>-<slug>`,
what `gh pr view` shows as `headRefName`) — not your local working-branch
name (`impl/<case-id>-resume`), which is a throwaway local label per the
same convention the fix-round entry already established. Rerun count is 0
when nothing actually failed — a conflict-resolution + reverification pass
is not a debug round.
