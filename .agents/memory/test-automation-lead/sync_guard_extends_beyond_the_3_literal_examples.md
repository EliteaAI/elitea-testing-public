---
name: sync-base-branches guard extends beyond the skill's 3 literal examples
description: A case branch checked out in the shared elitea-testing-public tree, with an open PR and an active factory-loop "works this card" claim comment, is an in-flight-work signal exactly like the 3 named guard conditions (EliteaUI merge-in-progress / uncommitted testid work / a live .testid-pr worktree) — check it every time before Part 1, don't rely on the literal checklist alone.
type: feedback
---

## What happened (2026-07-22, unattended sync run, issue #716)

The `sync-base-branches` skill's guard names 3 literal conditions to check
before syncing: a merge in progress in EliteaUI, uncommitted testid work in
the live tree, or an active worktree at `../.testid-pr`. None of these
literally cover "the elitea-testing-public shared tree is checked out on
someone else's active case branch." I checked all 3 named conditions, found
them clear, and almost proceeded to `git checkout automation/base` in Part 1.

Before doing that I ran `git branch --show-current` out of habit (per
`verify_shared_tree_branch_before_every_merge_gate.md`) and found the tree on
`tests/ELITEA-2132-chat-folder-creation-via-chats-header-icon` — not
`automation/base`. Cross-checking: PR #698 for that branch was OPEN and
MERGEABLE with a commit only 23 minutes old; card #335's own comment thread
had an explicit factory-loop claim ("🔧 Factory (test-automation-lead) works
this card... to take over: stop the loop, then `claude --resume <id>`"); and
that same thread already documented a PRIOR collision from an earlier run of
this exact sync routine (#712) landing unrelated content on the idle branch.

## The generalizable rule

The guard's *intent* ("never sync over someone's in-flight work") is broader
than its 3 literal example conditions. Before Part 1 (`automation/base ←
origin/main`) specifically, always run these 3 checks regardless of what the
named guard conditions show:

1. `git branch --show-current` in elitea-testing-public — is it
   `automation/base`, or a case branch?
2. If a case branch: `gh pr list --state open` for a PR on that exact branch
   name, and check its `updatedAt` recency.
3. `gh issue view <card>` (the card matching that case ID) for a "Factory
   works this card" claim comment and its recency, and read the last few
   comments for any mention of a prior sync collision (a recurring symptom —
   this was the SECOND time the same card got hit by this routine).

If any of these show recent (sub-few-hours) activity, skip Part 1 entirely —
don't force a checkout, don't try to be clever with a worktree to "route
around" it unless you're confident that's genuinely safe. File the tracking
issue noting the skip + the specific evidence (branch, PR number + state,
card comment excerpt) instead of guessing at a merge. Retry next cycle.

This is the 4th confirmed variant of the shared-tree-collision family (after:
own `git reset --hard` x3, an implementer's cleanup checkout, a subagent's
worktree-technique quirk). This variant is specific to the sync routine
itself: run blindly, `sync-base-branches` Part 1 IS a collision source
against in-flight case work on the very same repo it needs to check out —
not just a potential victim of someone else's checkout, but is itself capable
of being the clobbering party against the same person's in-flight work twice
in one day if a fresh run doesn't re-check.
