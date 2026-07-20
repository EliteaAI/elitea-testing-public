---
name: Implementer R2 fix-only round merging automation/base can leak agent-memory files into the PR diff (and silently regress one)
description: when a fix-only implementer round hits a conflict against automation/base and resolves it with `git merge origin/automation/base` on the feature branch, agent-memory files it (or a prior round) had staged get folded into the merge commit and show up in `gh pr diff` — worse, the merge-conflict resolution can silently revert a memory file that was already correct on automation/base back to a stale version
type: feedback
---

## What happened (issue #242, ELITEA-1847, PR #661, R2 fix-only round)

Sequence:
1. R1 implementer opened PR #661 from `tests/ELITEA-1847-...` with a clean 3-file
   commit (AFS + test + page object). I (orchestrator) landed R1's agent-memory
   changes directly on `automation/base` per the usual convention (a separate
   commit, not on the feature branch).
2. Reviewer R1 found a real bug (flaky `navigate_to_bucket()`), CHANGES_REQUESTED.
3. Dispatched a fresh foreground implementer for the R2 fix-only round (per
   `sendmessage_resume_fragile_in_factory_mode.md`, factory mode). It fixed the
   bug correctly — but it ALSO had its own uncommitted memory-file edits
   in-progress, and when it tried to push, it hit a conflict against
   `automation/base` (which now had MY R1 memory-landing commit). It resolved
   this with `git merge origin/automation/base` directly on the feature branch,
   then committed a memory-log entry, then the merge commit.
4. Net effect: `gh pr diff 661 --name-only` now showed 4 agent-memory files
   alongside the 3 real deliverable files. Worse: diffing `automation/base` vs
   the feature-branch tip on one of those memory files showed a REMOVED line —
   the merge's conflict resolution had reverted a `test-automation-lead` daily-log
   entry back to a version one edit older than what was already correctly on
   `automation/base`. (This is the same failure family as
   `shared_tree_memory_landing_can_get_silently_reverted_by_plain_branch_checkout.md`
   — a routine branch operation silently regressing memory content — but the
   trigger here is a cross-branch `git merge` during a dispatched subagent's own
   push, not an orchestrator-side `checkout`.)

## Why this matters

The project's explicit convention (`afs_commit_ordering_when_analyst_has_no_commit_authority.md`)
is: agent-memory commits are a housekeeping side-channel that lands directly on
`automation/base`, kept OUT of the case's feature branch / PR diff, because
mixing them in surfaces as unrelated noise in the PR history. A dispatched
implementer doesn't know this convention exists at push time — it just resolves
whatever conflict git hands it the most obvious way (`merge origin/base`), which
is reasonable from its vantage point but violates the convention from mine.

## The fix applied

1. Extract the FINAL (corrected) content of the polluted memory files from the
   feature-branch tip (`git checkout <feature-branch> -- <memory-paths>` while on
   `automation/base`).
2. Commit that corrected content directly onto `automation/base` (its own commit,
   scan-secrets clean, pushed).
3. `git reset --hard <the-last-pure-code-commit>` on the feature branch — drops
   the memory-log commit AND the merge commit entirely.
4. `git rebase automation/base` on the feature branch (now clean) — picks up the
   just-landed corrected memory from automation/base without re-adding it to the
   branch's own diff, since it's already the branch's parent.
5. `git push --force-with-lease` the feature branch. Short-lived, unshared,
   not-yet-merged case branch — force-push here is the SAME sanctioned exception
   `sync-base-branches.md` already documents for `testids/<case>` branches ("a
   short-lived single-case branch — force is fine there"), it just wasn't
   previously written down for `tests/<case>` branches explicitly.
6. Verify with `gh pr diff --name-only` before dispatching the next reviewer
   round — don't assume the fix worked, confirm the file list.
7. Re-run the test locally once after the reset/rebase as a sanity check before
   handing to review — a `reset --hard` + rebase is mechanical but still worth
   a real-world confirmation nothing broke.

## Rule going forward

- When dispatching an implementer fix-only round on a feature branch, name the
  git-conflict risk explicitly if `automation/base` has moved since the branch
  was cut (which it usually has — the orchestrator lands memory there between
  every round): tell the implementer to `git rebase automation/base` (not
  `merge`) if it needs to sync, OR to just push and let the orchestrator handle
  any conflict, rather than resolving a base-sync conflict itself mid-fix.
- Either way, ALWAYS run `gh pr diff --name-only` yourself before dispatching
  the next review round, regardless of whether you think this happened — it's a
  15-second check against a real recurring failure mode, now confirmed twice in
  spirit (checkout-triggered and merge-triggered) across two different
  mechanisms.
- If pollution is found, don't just strip the files — diff each one against
  `automation/base`'s current version first (`git diff automation/base
  <feature-branch> -- <path>`) to check for silent content regression before
  discarding, since a lost "-" line in that diff means real content would be
  destroyed by a naive discard rather than recovered.
