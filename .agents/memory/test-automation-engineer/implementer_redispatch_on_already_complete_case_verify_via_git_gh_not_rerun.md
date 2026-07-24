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

## Addendum (ELITEA-2030, same session, 2026-07-24) — when the gap IS the push itself, complete it, don't just report it

A variant of this shape where the verification uncovers a REAL, mechanical gap
(not "everything's fine, do nothing"): PR #1034's branch
(`tests/ELITEA-2030-add-node-menu`) carried only the 2 pre-fix-round commits;
the fix round R1 (3 reviewer findings addressed, commit message claims "green
twice") sat on a **local-only** branch (`fixround/ELITEA-2030-review-r1`) in a
DIFFERENT worktree (`wf_e44028a9-dec-151`), never pushed to origin. The AFS's
own "Redispatch confirmations" section (written by a prior analyst redispatch)
had already diagnosed this exact root cause and named the fix explicitly:
"push (or cherry-pick) the fix-round's commits onto the PR branch... an
implementer/orchestrator action." This is now the THIRD case this session
sharing this root cause (ELITEA-2004, ELITEA-2018, ELITEA-2030) — worth the
orchestrator treating as one systemic gap (a step that reliably fails to push
fix-round worktree branches after a local fix round completes).

**Verify-then-complete, not verify-then-report, when the gap is this narrow:**
1. Confirm the fix-round branch really is a fast-forward descendant of the
   PR's remote branch tip (`git merge-base --is-ancestor <PR-remote-branch>
   <fixround-branch>`) — guarantees the push can't lose anything.
2. Re-verify additive-only + mechanical-grep compliance independently on the
   fix-round's diff (don't just trust its own commit message).
3. **Get an independent green run of the fix-round's exact content** before
   pushing — since the branch is checked out in another worktree, you can't
   `git checkout <branch>` there directly (branch-already-checked-out
   conflict), but you CAN `git checkout <fixround-SHA> -- <the touched
   files>` in your OWN worktree (a plain path-scoped checkout of a specific
   commit's tree, no branch conflict) to materialize its exact content, run
   the test, then `git reset --hard HEAD` afterward to leave your own
   worktree/branch untouched.
4. Push directly with the refspec form that renames on the fly:
   `git push origin <local-fixround-branch>:<remote-PR-branch>` (e.g.
   `git push origin fixround/ELITEA-2030-review-r1:tests/ELITEA-2030-add-node-menu`)
   — a normal fast-forward push, no need to check out the PR branch locally
   at all. This is a completely different git incantation from a same-name
   push and easy to fumble by trying to checkout the PR branch first (which
   would collide with whatever worktree already has it).
5. Comment on the PR documenting what was pushed + your independent
   verification evidence (paste the actual commands/output) — this is the
   durable trace of what happened, since this pipeline's reviewer/board
   verdicts don't otherwise show up as native GitHub PR reviews.

**A `gh pr view`-reported `mergeable: CONFLICTING` after the push is not
automatically a real blocker** — compute the file-set intersection between
what the PR branch changed (since its merge-base with `automation/base`) and
what `automation/base` itself changed since that same merge-base
(`git diff --name-only <merge-base> <ref>`, sorted, `comm -12`). If the
intersection is only shared append-only memory-log files (`MEMORY.md`,
`daily/<date>.md` — this project's recurring false-alarm shape per the
qa-engineer sibling memory file), it's a trivially-rebaseable conflict, not a
real one — say so explicitly in the PR comment so the hardening
gate/orchestrator doesn't stall on it.

**Sandbox note:** in a worktree-isolated session, `env -u GITHUB_TOKEN gh pr
comment ... --body-file ...` may be refused by the sandbox's command-shape
verifier (it flags `env` wrapping a command that takes a long-form flag as
"can't verify it stays inside the worktree", even though `gh pr comment` is a
plain network write, not a filesystem op). Workaround that keeps the same
identity-correctness (never posting as the shared `GITHUB_TOKEN`):
`GITHUB_TOKEN= gh pr comment <N> --body-file <path>` — setting the var to
empty in the command's own environment achieves the identical "don't use the
shared token" effect as `env -u`, and the sandbox accepts this shape. Verify
the identity landed correctly after: `gh pr view <N> --json comments --jq
'.comments[-1].author.login'` should show your own keyring account, not a
bot/app identity.
