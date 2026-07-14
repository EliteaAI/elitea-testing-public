---
name: Cherry-pick ancestor check is a false-positive generator
description: Never verify "did this testid commit land on automation/testids" with a hash-based ancestor check on the cherry-picked review-branch commit — cherry-pick always mints a new hash, so it always says NO even when the content landed correctly; verify by diffing patch content or grepping the live tree instead. Also: always confirm the local integration-branch commit was actually pushed, not just committed.
type: feedback
---

## What happened

Issue #28 (ELITEA-1738) rework, PR #206. A fresh reviewer raised a "Critical,
blocking" finding: the testid commit was claimed to never have landed on
`EliteaAI/EliteaUI`'s `automation/testids` integration branch. Their evidence:
`git merge-base --is-ancestor <hash-of-the-cherry-picked-commit-on-the-review-branch> origin/automation/testids`
returned `NO`.

That check is **structurally guaranteed to say NO** in this project's
dual-target testid design (`.agents/workflow.md` § Testid flow): a testid
commit is born on `automation/testids`, then **cherry-picked** onto a
`testids/<case>` review branch cut from fresh `main`. Cherry-pick always
mints a brand-new commit hash for the same patch content — so an
ancestor/hash check on the review-branch commit will return NO even in the
100%-correct case. It is not a signal of anything.

I independently re-verified with the right method and found:
- `git diff <integration-branch-hash> <cherry-picked-hash>` — differed ONLY
  in the commit metadata line (hash), i.e. **byte-identical patch content**.
- A live `grep` of the checked-out `automation/testids` working tree showed
  the new testids present in the JSX.

So the reviewer's stated reason was wrong. **But** chasing it down surfaced a
real, different gap: the implementer's local `automation/testids` branch was
1 commit ahead of `origin/automation/testids` — committed locally, never
pushed. I pushed it (plain FF, no force) before writing the closure record.

## Why it matters

Two lessons, not one:

1. **The correct verification method for "did the testid content land" is
   patch-content diff or a live-tree grep — never a hash-based ancestor
   check across a cherry-pick boundary.** Any reviewer/lead check phrased as
   "is commit X an ancestor of branch Y" is invalid here by construction
   whenever X is a cherry-picked commit. Use `git diff <sha1> <sha2>` (empty
   or metadata-only diff = same content) or `git grep <testid> <ref> --
   src/`.
2. **A wrong reason can still be worth chasing.** Don't dismiss a finding
   just because its stated evidence is flawed — verifying it independently
   (as the orchestrator always must, "claims require pasted output" cuts
   both ways) caught a real unpushed-commit gap that the flawed check
   happened to be adjacent to. The fix: verify from scratch with the right
   method, don't just refute the reviewer's method and stop — confirm the
   actual underlying fact (pushed? content identical? live?) independently.

## What to do differently

- When dispatching implementers/reviewers for testid work, name the correct
  verification method explicitly: "confirm via `git diff <integration-hash>
  <cherry-pick-hash>` (content-identical minus metadata) or a live grep of
  the checked-out `automation/testids` tree — NOT a merge-base/ancestor
  check on the cherry-picked commit's hash."
- Before writing a closure record, always run `git status` / `git log
  --oneline -1 <branch>` vs `origin/<branch>` on `automation/testids` to
  catch a committed-but-unpushed testid, independent of whatever the
  reviewer checked.
