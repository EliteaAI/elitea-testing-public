---
name: Sync-time framework-code merge conflicts also get dispatched, not resolved by me
description: The no-edit guardrail on automation/** applies to git-merge-conflict resolution during sync-base-branches exactly as much as to PR-time implementation work — abort my own conflicted merge attempt and dispatch the implementer to redo it with a resolution direction, don't resolve it myself with git/Edit even though it's "just a sync"
type: feedback
---

## What happened

Issue #128 (ELITEA-1911). Session-start `sync-base-branches` Part 1
(`automation/base ← origin/main`) hit a real conflict in
`automation/api/client.py`: our side carried the #563 temperature/reasoning_effort
fix (`temperature: None`), `origin/main` carried a newer, independently-authored
fix for the same underlying bug (`_default_llm_settings()` helper,
`reasoning_effort: "none"` + `temperature: 0.6`, landed by a human teammate the
same day). Both are valid fixes; picking wrong (or hybridizing) would reintroduce
#563.

Instinct was to resolve it myself via `git merge`/manual edits since sync is
"infrastructure work," not "implementing a case." Caught it before acting: the
conflict lives inside `automation/api/client.py`, which is squarely inside the
no-Edit/no-Write guardrail's forbidden path list (`automation/**`) regardless of
*why* I'm touching it — sync-time vs PR-time is not a distinction the guardrail
makes. `git merge --abort`'d my own attempt and dispatched the implementer with
an explicit resolution direction (take main's newer fix, don't hybridize — with
the reasoning spelled out so the implementer wasn't just guessing either).

The implementer resolved cleanly and caught a bonus issue my own read would
likely have missed: a 5th call site (`create_pipeline_with_mcp_node`) that merged
*without* a conflict — because it didn't exist on `origin/main`, so there was no
3-way overlap for git to flag — but still carried the stale inline-dict pattern
from the original #563 fix. Left as-is it would have silently reintroduced the
exact bug both sides had independently already fixed. Git's conflict detector
only catches textual overlap, not "one side added new code using an old pattern
after the other side already deprecated that pattern."

## Rule going forward

1. **A framework-code merge conflict during `sync-base-branches` is dispatched
   work, exactly like a PR review finding** — abort my own conflicted `git
   merge` attempt the moment the conflicted file falls inside `automation/**`
   (or any other forbidden path), then dispatch the implementer with: the
   conflict location, both sides' content + authorship/timing context, and an
   explicit resolution direction if I have one (I'm allowed to make the *call*,
   just not touch the *file*).
2. **After a conflict resolution job, ask the implementer to scan for
   call sites that merged silently but carry the same stale pattern** — git's
   3-way merge can't see "no textual conflict, but semantically stale," and an
   implementer doing a full read of the resolved area is well-positioned to
   catch it while already in context.
3. This generalizes the existing framework-architecture division of labour
   (§ Framework architecture in the orchestration playbook) to the sync step
   specifically — it's easy to mentally file `sync-base-branches` under
   "orchestrator housekeeping" and forget the same file-path guardrail applies.
