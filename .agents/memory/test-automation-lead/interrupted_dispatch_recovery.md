---
name: Interrupted dispatch recovery
description: After an orchestrator turn is interrupted mid-dispatch, check git/PR/branch state before re-dispatching — the subagent may have already completed and landed real work even though the orchestrator never saw the result
type: feedback
---

## What happened

Issue #19 (2026-07-14, second rework round): I dispatched `test-automation-engineer`
with a large rework prompt (Agent tool call). The turn was interrupted by the user
("Request interrupted by user for tool use") before I ever saw a result. The next
dispatch of this session started fresh, with no memory of whether that agent call had
actually run.

Before blindly re-dispatching the same work (which would have duplicated effort, or
worse, produced two divergent branches/PRs for the same fix), I checked `git status` /
`git branch --show-current` / `git log` in the working tree — and found a real commit
(`76f4995`) on a pre-existing branch `tests/ELITEA-1737-testid-rework`, with a detailed
commit message matching exactly what I'd asked for, plus 3 real companion PRs already
opened on `EliteaAI/EliteaUI` (#525 extended, #526, new #535), all already merged into
`automation/testids`.

The subagent had run to completion in the background; the interruption only cut off
*my* turn's ability to receive and act on its result, not the subagent's own execution.

## Why it matters

Re-dispatching blind would have either (a) wasted a full implementer pass duplicating
already-done work, or (b) produced a second, divergent attempt at the same fix,
creating merge conflicts or contradictory PRs to reconcile.

## Rule going forward

**After any interruption during or after an Agent dispatch, before re-dispatching:**

1. Check `git status` / `git branch --show-current` / `git log --oneline <base>..<branch>`
   in the working tree for uncommitted or committed work matching the interrupted
   task's description.
2. Check for any PRs (this repo and any companion repos, e.g. `EliteaAI/EliteaUI` for
   testid work) opened since the interruption whose title/branch name matches.
3. If real work is found: **verify it** (read the diff, run the tests) rather than
   trusting the commit message at face value, then continue the pipeline from wherever
   that work left off (e.g. straight to review) instead of re-dispatching from scratch.
4. Only re-dispatch fresh if the check comes back empty.

This is the same "trust but verify" instinct as checking a subagent's self-report, just
applied one layer up — to whether the subagent ran at all.
