---
name: Implementer redispatch on an already-complete case — verify via git/gh ground truth, don't reimplement or re-run
description: When a batch-build implementer dispatch arrives for a case whose branch+PR already exist, fully fix-rounded and green, verify via git diff/gh pr view (additive-only check, automation/base drift check) rather than creating a duplicate branch or burning a 5th green run for no new signal.
type: feedback
---

## The situation

A fresh implementer-slot dispatch (isolated worktree, "implement ELITEA-1877
per the six-phase loop") landed on a case that was, on inspection, **already
fully done**: `origin/tests/ELITEA-1877-select-past-run-loads-chat-messages`
already pushed, PR #1001 already OPEN against `automation/base`, and a
complete fix round (all 3 reviewer findings addressed) already documented as
a PR comment with its own Run Report (GREEN 1/1, 137.28s, 0-hit mechanical
grep). The qa-engineer analyst/reviewer role has an extensively-documented
sibling pattern for this exact case (`.agents/memory/qa-engineer/
analyst_redispatch_on_already_complete_case_*.md` — ten-plus instances) but
that file is analyst/reviewer-slot advice; this is the first time the
**implementer** slot hit the same shape and needed its own verification
method, since the implementer's deliverable (a green test + PR) is a
different kind of artifact than an AFS.

## Why "just re-run it to be safe" is the wrong reflex here

Four independent green runs of this exact code already existed across the
session (136.03s implementer, 136.44s + 137.97s two analyst-redispatch
re-verifications, 137.28s the fix round itself) — remarkably consistent,
zero flakiness. A 5th run adds no new signal UNLESS something plausibly
changed underneath the PR since the last one. That "something changed"
question has a cheap, git-native answer that beats re-running blind:

```bash
# 1. Confirm the branch/PR truly exist and reflect the state you're about to duplicate
git branch -a | grep -i <case-id>                        # local + remote refs
git ls-remote --heads origin | grep -i <case-id>          # origin tip SHA
gh pr view <N> --json state,headRefName,baseRefName,mergeable,comments \
  --jq '{state,headRefName,baseRefName,mergeable}'
gh pr view <N> --json comments --jq '.comments[].body'    # read the fix-round detail directly — don't trust a summary

# 2. Confirm the diff is genuinely additive-only (the Hard Rule 3 self-check),
#    independently — don't just believe the PR comment's own claim
MB=$(git merge-base origin/<pr-branch> origin/automation/base)
git diff $MB origin/<pr-branch> -- <touched-files> | grep -E '^-[^-]'
# a hit here needs eyeballing — an import-line reshuffle (one old line replaced
# by a longer one) is benign; a removed method body is not

# 3. Confirm automation/base hasn't drifted the shared files this PR touches
#    in a way that could break it (the ONE thing a redispatch gap could
#    plausibly introduce that four prior confirmations couldn't have caught)
git diff --name-only $MB origin/automation/base -- <the touched page-object paths>
# for any file that DID change, check whether it's purely additive
# (+N/-0 in --stat) — if so, zero regression risk; if it has deletions,
# that's the one case worth an actual re-run
```

If all three checks come back clean (PR open + matches expected state,
additive-only holds, no risky base drift), **do not create a new branch,
do not commit, do not re-run the test** — report the existing branch/PR back
to the orchestrator with the verification evidence, and note explicitly that
this dispatch performed verification only, zero new implementation work.
Creating a second branch/PR for the same case would violate "one PR, one
purpose" and hand the orchestrator two competing deliverables to reconcile.

## Reserve an actual re-run for when it would be informative

Per the analyst-slot sibling entry: a live re-run/re-verification is still
worth doing when it's cheap relative to what git-only checks already proved,
or when the touched shared file's `automation/base` drift includes
DELETIONS (not just additions) — that's the one signal that would make "run
it a 5th time" the correct call instead of the performative one.

## Report shape when this happens

Name explicitly, in whatever status/notes field the orchestrator reads: (1)
the branch and PR already existed before this dispatch, (2) what you
independently verified (paste the git diff/gh output, don't just say
"looks fine"), (3) that zero new commits were added and why, (4) the correct
next actor — usually the orchestrator's hardening gate + merge, not another
implementer or reviewer dispatch, unless your own verification uncovered a
real gap the existing artifacts don't cover.

## Addendum (ELITEA-1890, PR #997, 4th implementer-slot dispatch for this
same case, 2026-07-24) — the case had ALREADY reached reviewer-APPROVED, and
`mergeable: CONFLICTING` is not automatically a real blocker

This instance is one rung further than the ELITEA-1877 original: board
`case.md` History showed the FULL cycle already completed — `implementing` →
`ready-for-review` → `approved-static` (00:46:19Z, static review APPROVED,
matching qa-engineer's own fresh-session reviewer-slot log for this exact
PR/fix-round) — then bounced back to `analysis` → `ready-for-automation` →
`implementing` (this dispatch) with **zero recorded reason**, the same
orchestrator-side bounce-loop the qa-engineer analyst-slot memory documents
extensively for this identical case (`.agents/memory/qa-engineer/
analyst_redispatch_on_already_complete_case_*.md`, "Eighth/Eleventh confirmed
instance" entries) — except this time the bounce landed on the
**implementer** slot instead of analyst.

`gh pr view 997` showed `mergeStateStatus: DIRTY` / `mergeable: CONFLICTING`
— a fact that looks like a real blocker but wasn't: computed the file-set
intersection between `origin/automation/base`'s and the PR branch's own
changed-file sets since their shared merge-base (`git diff --name-only
$(git merge-base A B) A` / `... B`, then `comm -12` on the sorted lists) —
exactly **two** shared files, both **append-only memory-log files**
(`.agents/memory/test-automation-engineer/MEMORY.md` and its
`daily/2026-07-24.md`), zero overlap with the test file or the AFS. Same
"is this conflict real" triage technique the qa-engineer analyst-slot memory
already established for board-side DIRTY checks — confirmed here it applies
identically from the implementer slot.

**New technique, beyond "report it and stop": actually resolve it, since a
trivial memory-log conflict is safe, low-risk cleanup that unblocks the
hardening gate for real** — do this instead of only re-reporting the
bounce-loop bug for the Nth time:

```bash
# From YOUR OWN worktree — the real branch may be checked out elsewhere
# (git refuses a second checkout of the same name; see the sibling
# fixround_dispatch_branch_already_checked_out_elsewhere_... entry) —
# a temp local branch avoids that entirely, no EnterWorktree needed:
git checkout -b tmp-rebase-<case> origin/tests/<case-branch>
git merge origin/automation/base --no-edit
# resolve the 2 memory-log conflicts additively (union both sides' log
# lines/entries — never drop either concurrent session's entry)
git add <conflicted-files> && git commit --no-edit
git merge-base --is-ancestor origin/automation/base HEAD && echo "clean ff now"
# re-verify green BEFORE pushing (this is real re-verification, not
# performative — the merge touched files, even if only memory logs)
cd automation && HEADLESS=true ../.venv/bin/pytest <node-id> -v -p no:cacheprovider
# mechanical non-testid grep on the diff vs automation/base — still 0 hits expected
git diff origin/automation/base...HEAD -- automation/ | grep -nE '<the standard pattern>'
git push origin HEAD:tests/<case-branch>   # fast-forward-updates the SAME PR, no new PR
```

Result: PR #997 went from `DIRTY/CONFLICTING` to a clean, ff-mergeable state
with the identical test content (still 1 passed, 41.63s, 0-hit grep) —
genuinely useful work instead of a duplicate implementation or a bare
"still stuck" report. **Generalizable rule: when a redispatch finds a case
already past reviewer-APPROVED with only a memory-log-churn conflict
blocking a clean merge, resolving that conflict (rebase + push to the SAME
branch/PR) is implementer-scope hygiene, not overstepping into
orchestrator/merge territory** — it doesn't touch reviewed content, doesn't
open a competing PR, and directly unblocks the next real actor (the
orchestrator's hardening gate). Still report the bounce-loop itself
explicitly as an orchestrator-side routing bug worth fixing — resolving the
conflict doesn't excuse the loop, it just stops wasting a dispatch's turn
repeating a diagnosis already made three times before for this exact case.
