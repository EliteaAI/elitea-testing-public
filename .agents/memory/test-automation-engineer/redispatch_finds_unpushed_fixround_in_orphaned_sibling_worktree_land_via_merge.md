---
name: Redispatch finds an unpushed fix-round sitting in an orphaned sibling worktree — land it via merge, don't reimplement
description: A plain "implement <CASE> from scratch" dispatch can land on a case whose fix-round is ALREADY DONE but stuck unpushed in a different (now-idle) worktree, because automation/base drifted since that fix-round's merge-base. The correct move is git-native picking-up-and-landing, not a third implementation.
type: feedback
---

## The situation (ELITEA-2004, worktree wf_e44028a9-dec-63)

A fresh implementer-slot dispatch named an AFS path
(`test-specs/pipelines/l2_configure-llm-node-system-task-chat-history_ELITEA-2004.md`)
and a board case-source snapshot — **both 404'd** in the isolated worktree
(known gap, see `afs_file_uncommitted_in_main_repo_isolated_worktree_gap.md` —
but this time the AFS truly wasn't anywhere, not even uncommitted in the main
repo's working tree; it turned out to already be committed on the CASE's own
branch, invisible to a worktree cut fresh from `automation/base`).

`git branch -a | grep 2004` + `gh pr list --head <branch>` showed:
- `tests/ELITEA-2004-configure-llm-node-system-task-chat-history` — pushed,
  PR #1012 OPEN (original implementation).
- `fixround/ELITEA-2004-review-r1` — a LOCAL-ONLY branch (no `remotes/origin/`
  counterpart), two commits ahead, sitting in a DIFFERENT worktree
  (`wf_e44028a9-dec-83`) that was not "locked" (i.e. its session had already
  ended after committing — the classic "committed locally, orchestrator was
  supposed to land it" shape from `fixround_dispatch_collides_with_stale_prior_worktree_same_branch.md`,
  except THIS time nobody ever re-dispatched to finish landing it).

This is a **new, third shape** distinct from the two already-documented
patterns:
- NOT `implementer_redispatch_on_already_complete_case_*` (that one: the fix
  round was already pushed/reflected on the PR — correct move is verify-only,
  zero commits).
- NOT `fixround_dispatch_collides_with_stale_prior_worktree_*` (that one: YOU
  are dispatched explicitly for the fix round, and the stale worktree blocks
  your OWN checkout of the named branch — fix is `git worktree remove` then
  work directly on that branch name).
- THIS one: you're dispatched as a **plain fresh implementer** (no "fix
  round" framing at all), the fix round is a **complete, self-contained,
  unpushed** side branch that nobody landed, and — critically —
  `automation/base` has MOVED ON since that branch's merge-base (other
  batch cases merged in the meantime), so a naive `git push --force` or
  reusing the stale branch as-is risks being built on a stale foundation.

## The procedure that worked

```bash
# 1. Confirm the fix-round branch is a clean descendant of the PR's PUSHED tip
git rev-parse remotes/origin/<pr-branch>          # e.g. 13a61c37
git rev-parse <fixround-branch>                   # e.g. 5a5f1f78
git merge-base --is-ancestor remotes/origin/<pr-branch> <fixround-branch> && echo YES

# 2. Check how far automation/base has drifted from the fixround's own merge-base,
#    and whether that drift touches the SAME shared files this case's diff touches
git merge-base automation/base <fixround-branch>
git diff <merge-base> automation/base -- <shared-page-object-path>   # empty = zero conflict risk

# 3. Create a NEW local branch from the fixround tip (the branch NAME is checked
#    out in another worktree, so you can't reuse it — but you don't need to;
#    you're going to fast-forward-push its content onto the origin ref anyway)
git checkout -b <scratch-integrate-branch> <fixround-branch>
git merge automation/base -m "merge automation/base into <CASE> fix-round before push"
# resolve any conflicts (in this case: only in MY OWN memory/daily-log files,
# a trivial union-merge — zero conflicts in the actual test/page-object code)

# 4. Run the implementer's normal verification (ruff, mechanical locator grep,
#    additive-only check on shared files, ONE green pytest run)

# 5. Fast-forward push the scratch branch's content onto the ORIGIN branch
#    name the PR already tracks — this updates the EXISTING PR in place,
#    it does not open a new one
git push origin <scratch-integrate-branch>:<pr-branch-name>
gh pr view <N> --json headRefOid,mergeable   # confirm it moved + still MERGEABLE
```

Zero force-push needed anywhere — the whole chain (origin tip → fixround tip
→ merge-commit) is a straight-line fast-forward from origin's perspective,
because the fixround branch was always a strict descendant of what was
already pushed, and merging `automation/base` IN (not rebasing onto it) keeps
that ancestry intact.

## Takeaway for the next "plain implement" dispatch that turns out non-trivial

Before writing a single new line: `git branch -a | grep <case-id>` AND
`gh pr list --search <case-id>` (or `--head <expected-branch-name>`). Three
possible findings, three different correct responses:
1. Nothing exists → this dispatch really is fresh, proceed normally.
2. PR exists, fully reflects a complete fix round → verify-only, zero commits
   (`implementer_redispatch_on_already_complete_case_*`).
3. PR exists but a complete fix round is stranded, unpushed, in an idle
   sibling worktree → THIS entry's procedure: merge current base into it,
   verify, fast-forward-push onto the existing PR branch. Never open a
   second PR/branch for the same case — that hands the orchestrator two
   competing deliverables to reconcile instead of one finished one.
