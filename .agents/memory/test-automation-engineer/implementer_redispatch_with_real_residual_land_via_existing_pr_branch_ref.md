---
name: Implementer redispatch onto an already-far-along case with a REAL residual — land it via the existing PR's remote branch ref, don't open a duplicate PR
description: Sibling case to implementer_redispatch_on_already_complete_case_verify_via_git_gh_not_rerun.md — this time the redispatch found a genuine unfinished gap (not just staleness to verify), already diagnosed by a same-session analyst redispatch. Fixing it means pushing onto the EXISTING PR's branch, not creating a new one.
type: feedback
---

## The situation

ELITEA-1937 (MCP Test Settings — select and run a tool) implementer-slot
dispatch arrived in a brand-new isolated worktree with the generic prompt
("implement per the AFS"). Ground truth on inspection: `origin/tests/
ELITEA-1937-test-settings-select-run-tool` already existed with PR #1005
OPEN, and a local `fixround/ELITEA-1937-review-r1` branch (2 commits ahead
of the PR branch tip) had already addressed the reviewer's `[Important]`
finding by amending stale AFS prose (steps 2/5/8/10) to match the
already-correct shipped test code — **but left the Coverage Map (Axis 1)
table cells for steps 8 and 10 unsynced**, still contradicting the prose a
few lines above. A same-session `qa-engineer` analyst redispatch had
already diagnosed this exact residual (see its
`analyst_redispatch_on_already_complete_case_check_board_git_then_bounded_
spotcheck.md` § "Ninth/Thirteenth confirmed instance") and staged the
2-cell fix — uncommitted, since the analyst slot has no commit authority —
explicitly naming the implementer as the correct actor to land it.

This is distinct from the sibling entry's "verify only, don't reimplement"
shape: here there really was something to do, just small and already fully
scoped by someone else's diagnosis.

## What NOT to do

Don't spin up a brand-new branch + a fresh PR for the same case — that
creates two competing deliverables for the orchestrator to reconcile and
violates "one PR, one purpose" (the PR already exists and already carries
most of the correct history).

## The mechanics that worked

1. **Can't `git checkout` the branch with progress directly** if it's
   already checked out in ANOTHER worktree (`git worktree list | grep
   <branch>` to confirm) — create a NEW local branch name pointing at the
   same commit instead: `git checkout -b <scratch-name>
   fixround/<case>-review-r1`.
2. Apply the actual residual fix (here: 2 Coverage Map table cells, pure
   doc sync — verified the test code was ALREADY correct at the exact
   line numbers the analyst's diagnosis cited before touching anything).
3. Run the real test green once (hit the by-now-recurring missing-
   `automation/.env.test`-symlink worktree gap — see
   `worktree_env_test_symlink_missing_despite_worktreeinclude.md` — same
   fix, same absolute-path recipe).
4. Run the mechanical raw-locator grep on the FULL PR diff (`git diff
   automation/base...HEAD -- automation/pages/ automation/tests/`), not
   just your own new commit — every hit must trace to a testid-backed
   UPPER_CASE class constant. Paste the command+output in the Run Report.
5. **Land it by pushing your local branch onto the EXISTING PR's remote
   branch NAME via an explicit refspec**, not a same-named local checkout
   (blocked by step 1's collision):
   ```bash
   git push origin <scratch-local-branch>:<pr-branch-name>
   ```
   Confirm ancestry first (`git merge-base --is-ancestor
   origin/<pr-branch-name> HEAD`) — this must be a genuine fast-forward,
   never a force-push, onto a branch this same pipeline owns.
6. `gh pr view <N>` afterward may show `mergeable: CONFLICTING` purely
   because `automation/base` moved on with OTHER cases' commits in the
   interim. Before treating that as a blocker: compute the file-set
   intersection between the PR branch's own changes and `automation/base`'s
   own changes since their merge-base (`git diff --name-only <merge-base>
   <ref>` on each side, `comm -12` the sorted sets). If the intersection is
   only shared append-only memory-log files (`MEMORY.md`, `daily/*.md`),
   it's trivial rebase-at-merge-time noise, not a real conflict — this is
   the SAME technique the qa-engineer redispatch memory documents
   (`analyst_redispatch_on_already_complete_case_...md`, Tenth/Eleventh
   instances) for the reviewer/analyst slots; it applies identically here.

## A wrong move caught and reverted

Ran `ruff check --fix` on the PR's new test file to silence an `I001`
(import-order) hit. This actually REORDERED a third-party import
(`playwright.sync_api`) to sort after local-package imports — before
committing, checked whether the identical `I001` fires on an
ALREADY-MERGED sibling test in the same directory
(`test_mcp_load_tools_discovery.py`, ELITEA-1933) that uses the
conventions.md-prescribed 3-blank-line-separated stdlib/third-party/local
block shape — it does, identically. That proves the lint config and the
documented convention disagree REPO-WIDE (pre-existing tech debt, same
category as "existing raw handles in automation/pages/ are tracked tech
debt, not precedent"), not something this PR introduced or should
uniquely "fix" into a different, non-conforming shape. **Reverted the
`--fix`** (`git checkout -- <file>`) rather than ship an inconsistent
import style. General lesson: before applying an auto-fixer to silence a
lint hit in someone else's already-written code, check whether the
identical hit exists on an already-merged neighbor first — if so, it's
baseline noise, not your PR's problem.

## Generalized lesson

"Implementer redispatch on an already-far-along case" splits into (at
least) two shapes needing different responses: (a) truly nothing left to
do → verify via git/gh, report, don't touch anything (the sibling entry);
(b) a real, already-diagnosed-by-someone-else residual → land it via the
EXISTING PR's branch ref (this entry), never a parallel branch/PR. Telling
them apart is one `gh pr view` + one `git log <branch>..<fixround-branch>`
away — always check before assuming either.
