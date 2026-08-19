---
name: campaign doc edit lost during concurrent workflow subagent git ops
description: an orchestrator's own uncommitted edit to a gitignored campaign doc can be silently discarded by a batch-build Workflow's own subagents doing git checkout/reset on the same shared clone while the workflow is still running
type: feedback
---

## What happened (2026-08-19, wave-15)

Edited `.agents/automation/campaigns/chat-remaining.md` (recording an
in-flight run-state note) via the `Edit` tool while the `batch-build`
Workflow's own subagents were actively running against the SAME shared
clone (no worktree isolation). A later `git status` showed the edit gone —
the file reflected only its last-committed content. The workflow's own
analyst/implementer/reviewer subagents routinely do `git checkout`/branch
switches as part of their normal operation, and since
`.agents/automation/` is gitignored, none of their own scoped diffs would
have shown it as a conflict — it was just silently reset/lost as part of
whatever git operation one of them ran.

## Rule going forward

Treat mid-run edits to the campaign doc (or any other gitignored,
orchestrator-only file) as **at risk** for the duration of an active
Workflow run on the shared clone: they may or may not survive. Two options,
both cheap:
1. Defer non-essential campaign-doc commits until between workflow runs
   (right before dispatch, right after the notification lands) rather than
   mid-run.
2. If you must record something mid-run (e.g. a Task ID for resumability),
   commit it immediately after writing it rather than leaving it as an
   uncommitted working-tree edit — a committed line survives a concurrent
   checkout; an uncommitted one doesn't.

Not a data-integrity risk in the strict sense (nothing load-bearing was
lost — the campaign doc's role is a resumability aid, and the actual state
lives in git history + TMS + the tracker), but it did cost a rewrite. If
something ever DOES need to be authoritative mid-run, don't trust an
uncommitted edit to survive a workflow's own concurrent git activity on the
same clone.
