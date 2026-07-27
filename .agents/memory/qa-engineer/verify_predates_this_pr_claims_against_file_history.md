---
name: Verify "predates this PR" claims against actual file history
description: A fix-summary's claim that a lint/style nit "predates this PR" needs a git-log check against the specific file's own history, not just trust — for a brand-new file the correct framing is narrower ("not introduced by this edit"), and checking that narrower claim is what the reviewer should actually verify.
type: feedback
---

## What happened

PR #670/ELITEA-1866, round-3 re-review (fresh session, HEAD `a3040242`). The
implementer's round-2 fix summary claimed: "the pre-existing import-sort nit
on `toolkit_test_settings_page.py:17` predates this PR's first commit and is
out of scope for this fix-only round." The dispatch explicitly asked the
reviewer to verify this via `git blame` or comparing against the file's state
before the PR's first commit.

Ran `ruff check` myself and then `git log --follow -- automation/pages/toolkit_test_settings_page.py`:
the file has exactly TWO commits in its entire history, both from this PR —
`5f5b34d2` (the PR's own original implementation commit, which is where the
file was CREATED) and `a3040242` (round-2's fix commit). There is no
"before this PR's first commit" state to compare against — the file didn't
exist then. So the literal claim is false: nothing can "predate" the very
commit that created it.

## The correction

What IS true, and what the dispatch was actually trying to get at: does
round-2's OWN edit (`a3040242`) introduce or worsen the nit? No — `git show
a3040242 -- <file>` touches only the two new methods (lines 146+), never the
import block at the top. So the unsorted-import nit was present unchanged
since the file's original creation in `5f5b34d2`, and round-2's fix commit
is innocent of it.

The substantively-correct, narrower claim is "not introduced by this round's
edit" — which is verifiable via a single `git show <commit> -- <file>` and
doesn't require the file to have existed before the PR at all. "Predates
this PR" is a stronger, less accurate claim that happens to gesture at the
same conclusion (leave it out of scope) but is technically wrong for any
file the PR itself created.

## Reusable technique

When a fix-summary or PR description claims something "predates this PR" or
"is pre-existing tech debt, out of scope":

1. `git log --follow --oneline -- <path>` on the SPECIFIC file/line first.
   If the file's oldest commit is itself inside the PR's own commit range,
   "predates this PR" is categorically false — don't accept the wording,
   even if the underlying "not this PR's fault" conclusion is directionally
   right.
2. Separately check whether the SPECIFIC commit under review (not the PR as
   a whole) introduced or touched the flagged lines — `git show <commit> --
   <file>` and look at the hunk. This is the narrower, actually-checkable
   claim, and usually what the author meant.
3. Don't stop at the one line the fix-summary names — run the same checker
   (`ruff check`, in this case) across ALL files the PR touched. This round
   turned up two MORE lint issues (`toolkit_creation_page.py:26` I001,
   `toolkit_detail_page.py:17` F401 unused `re`) that were undisclosed but
   genuinely pre-existing (confirmed via `git show automation/base:<file>`
   already flagging them) — the implementer's spot-check of one line left
   two more unaudited, and a reviewer who only re-checks the named line
   misses that gap.

Both misclassifications point the same way here (all three nits legitimately
don't block this PR), but the verification method matters: "trust the
wording" vs "check the file's actual history" would have produced a false
positive if the underlying fact pattern had been different (e.g. if round-2's
edit HAD touched the import block).
