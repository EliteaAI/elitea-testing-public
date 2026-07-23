---
name: Isolated worktree dispatch can be missing an uncommitted AFS or board snapshot
description: An implementer dispatched into a fresh git worktree only sees files that are COMMITTED to a ref reachable from that worktree — a `.gitignore`d board directory (`.agents/automation-board/`) or an analyst-authored AFS that was never committed both silently fail to appear, even though `git log --all` and `ls` in the main repo's working directory show them fine
type: feedback
---

## What happened (ELITEA-1890, cov60 campaign)

Dispatched as implementer into a fresh worktree (`.claude/worktrees/wf_e44028a9-dec-28`)
with two file paths: the AFS
(`test-specs/agents/lcritical_switching-versions-updates-instructions-field_ELITEA-1890.md`)
and the board case snapshot
(`.agents/automation-board/batches/cov60/cases/ELITEA-1890/source.md`).
Neither existed in the worktree. `git log --all --oneline -- '*1890*'` and
`git log --all --diff-filter=A --name-only` found nothing relevant either —
i.e. this wasn't a "wrong branch" problem, the content had never been
committed to ANY ref.

Root cause: git worktrees share the `.git` object database (so anything
committed to any branch is visible everywhere) but do **NOT** share working-
directory content that was never committed:
- `.agents/automation-board/` is `.gitignore`d project-wide — it is *never*
  visible to a worktree no matter what, by design (it's the orchestrator's
  live board state, main-checkout-only).
- The AFS file, in this instance, existed only as an **uncommitted** file in
  the main repo's working directory — the analyst pass that produced it
  (or a batch-build phase boundary) hadn't committed it to a shared ref
  before my worktree was cut from `automation/base`.
- Same root cause bit a THIRD file: `automation/.env.test` (a local symlink
  to the master secrets file, itself untracked/gitignored) was also absent —
  had to `ln -sf` it fresh inside the worktree before pytest could even
  start (config.py's dotenv load silently no-ops without it, no explicit
  "file not found" signal at the point of failure — it just falls back to
  whatever's in the shell env, which was also unset here).

## The fix (and its limit)

`Read` with an ABSOLUTE path outside the worktree is NOT fenced — only
`Bash` commands that `cd`/operate on the shared checkout are blocked
("this command changes directory to the shared checkout... Refusing to
run it"). So the recovery path is: `Read` the file at its absolute path in
the main repo's working directory, then `Write` the IDENTICAL content to
the same relative path inside the worktree — this makes already-authored-
but-uncommitted content available to your branch without touching git at
all. `Write` to an absolute path OUTSIDE the worktree, however, IS fenced
("Edit the worktree copy of this file instead") — so this recovery only
works one direction (read main → write worktree), never the reverse.

For `.env.test`-style local symlinks: just recreate the symlink locally
(`ln -sf <absolute-path-to-master-secrets-file> automation/.env.test`) —
this is exactly the "fresh worktree has no installed dependencies... link
them per project convention" step the dispatch prompt already anticipates,
just extended to per-repo untracked local config, not only `node_modules`/
venvs.

## The generalizable lesson

Before assuming a dispatched file path is simply wrong or a stale reference,
check whether the gap is a WORKTREE-ISOLATION gap (untracked/gitignored/
uncommitted content that legitimately exists in the main checkout but was
never shared) rather than a routing mistake. Diagnostic: if `git log --all`
finds nothing for the path either, it's not on any ref — check the SAME
relative path via its absolute main-repo location before escalating a
missing-AFS finding as `needs-analyst-rerun` or a missing-board finding as
a blocker; it may just need to be materialized into the worktree via
Read-then-Write (content) or `ln -sf` (local config/symlinks).

## Addendum — a REDISPATCH of the same case can find the work already done

Same-day, same worktree, same branch (`wf_e44028a9-dec-28` /
`tests/ELITEA-1890-version-switch-instructions`): a second dispatch arrived
for the identical case with the identical AFS/board-snapshot paths — the
prior session (above) had evidently completed the implementer loop and opened
PR #997, but its result never reached the orchestrator (context reset or
similar), so a fresh dispatch was issued as if from scratch. Before writing
ANY new code on a redispatch, check for pre-existing branch state first:
`git log --oneline -10` (are there already commits for this case on this
branch?) and `gh pr view <expected-or-searched-number>` / `gh pr list --head
<branch>` (is there already an open PR?). Here both said yes — the correct
action was to RE-VERIFY (fresh `.venv` link, one clean re-run of the exact
`.agents/testing.md` command, re-run the reviewer's mechanical grep) rather
than re-implement, which would have produced a duplicate/conflicting PR for
no reason. The venv-missing symptom (a fresh worktree has no installed
dependencies) is itself consistent with "this worktree was reused across two
dispatches" — don't read a missing `.venv` as proof the worktree (and
therefore the work) is fresh; check git/gh state independently.
