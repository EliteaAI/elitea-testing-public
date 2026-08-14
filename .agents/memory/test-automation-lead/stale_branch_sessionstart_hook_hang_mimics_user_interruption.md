---
name: A stale-branch SessionStart hook hang can look exactly like a user interrupting the dispatch
description: 8 consecutive "[Request interrupted by user for tool use]" failures at the identical Agent() dispatch, across ~4 separate session restarts, were actually a SessionStart-hook performance bug on a branch cut before the fix landed — not the user stopping anything
type: feedback
---

## What happened (#335/ELITEA-2132, PR#698)

Dispatching the round-4 (closing) reviewer failed 8 times in a row, always with the
identical tool result `[Request interrupted by user for tool use]`, never after any
partial output. This happened across roughly 4 separate factory-mode session
restarts (not just retries within one turn) — a genuinely stable, reproducible
pattern. I told the user directly: *"something on your end is halting that subagent
dispatch each time... that's genuinely your signal to give."* That was wrong, and I
said so as soon as I found the real cause — but I should not have asserted it as
fact without more skepticism first, given how confidently-worded "interrupted by
user" reads.

## Root cause

The dispatch spawns a fresh subagent session, which runs its own SessionStart hook.
This project's hook (`.claude/hooks/sdlc-skills/lib.sh`) had a quadratic-time bash
string-substitution bug in `escape_for_json` (the same class of bug already flagged
on a sibling function, `is_blank`, but never fixed here) — a 63KB context payload
(this project's `.agents/` context, or a large persistent-memory dump like mine)
took **minutes** to escape via bash's `${s//a/b}` global substitution on bash 3.2.
The hook runs `async:false`, so the whole session start blocks on it. A perf fix
(swap to a single `perl -0777 -pe` pass, ~0.01s for the same payload) had already
landed on `automation/base` (commit `b231fc35`, landed earlier in THIS SAME
session while resolving an unrelated collision) — but my feature branch
(`tests/ELITEA-2132-...`) had been cut/merged from an OLDER `automation/base`
snapshot, predating that fix. Every checkout of that branch resurrected the slow
`lib.sh`. Every `Agent()` dispatch from that checkout hung ~600s on the new
subagent's own SessionStart hook and got killed at Claude Code's own dispatch
ceiling — which surfaces to the caller as `[Request interrupted by user for tool
use]`, indistinguishable from an actual human pressing stop.

## How it was actually found

Not by suspecting the hook — by noticing an unexplained commit
(`39abf170 fix(hooks): bring perl escape_for_json fix onto this branch`) sitting on
my local branch ref, authored by a **different concurrent session** (a separate
unattended sync run that itself hit the same stall while working a different card,
diagnosed it, and self-fixed by porting the base-branch fix onto whatever branch
happened to be checked out in the shared tree at the time — see the companion
`unattended_sync_run_lands_content_on_idle_pr_branch.md` entry for that side of the
story). Reading that commit's own message is what explained the whole pattern
retroactively.

## The fix

Confirmed the ported `lib.sh` content was byte-identical to `automation/base`'s
current tip (`git diff origin/automation/base -- .claude/hooks/sdlc-skills/lib.sh`
→ empty) before trusting it — this matters because a *squash* merge of the branch
into `automation/base` will contribute **zero net diff** for that file (verified
both via direct two-dot diff pre-merge and by checking the post-merge base's file
list, which correctly omitted it). Retried the exact same dispatch once more — it
completed normally in ~11 minutes with full output, no further interruption.

## Standing rule

When a subagent dispatch is repeatedly and identically cut off with no partial
output, before concluding "the operator is stopping this" or filing it as
inexplicable infra noise: check whether the CURRENT branch's copy of
`.claude/hooks/**` (or any other SessionStart-hook-relevant file) has drifted stale
relative to `automation/base`'s tip, especially if the branch has sat idle across
several session restarts (each restart re-triggers the SessionStart hook on
whatever's checked out). `git diff automation/base -- .claude/hooks/` is a cheap,
fast check worth running before accepting an interruption pattern as
unexplainable — and before telling the user it's their own doing.
