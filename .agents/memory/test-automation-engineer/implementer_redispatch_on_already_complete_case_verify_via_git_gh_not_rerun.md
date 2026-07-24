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
