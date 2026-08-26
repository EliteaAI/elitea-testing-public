---
name: any edit on the shared clone is at risk while a Workflow runs, not just the campaign doc
description: an orchestrator's own uncommitted edit — gitignored campaign doc OR a normal tracked file like testing.md — is at risk while a batch-build Workflow's own subagents are actively doing git checkout/branch-switch on the SAME shared clone; defer or commit-immediately, and never commit without checking the current branch first
type: feedback
---

## What happened (2026-08-19, wave-15; recurred/broadened 2026-08-20, wave-16)

**First occurrence:** Edited `.agents/automation/campaigns/chat-remaining.md`
(a gitignored, orchestrator-only file) via the `Edit` tool while the
`batch-build` Workflow's own subagents were actively running against the
SAME shared clone (no worktree isolation). A later `git status` showed the
edit gone — the workflow's own analyst/implementer/reviewer subagents
routinely do `git checkout`/branch switches, and since the campaign doc is
gitignored, none of their own scoped diffs would ever show it as a
conflict — it was just silently reset/lost.

**Second occurrence, same session, a real tracked file:** Edited
`.agents/testing.md` (a normal, git-tracked project file, NOT gitignored)
mid-run for the same reason (recording a suite-health pointer). This time
`git status` showed the edit still present, but `git branch --show-current`
revealed the shared clone had been switched by a workflow subagent to
`tests/ELITEA-2078-pipeline-flow-editor-discard-llm-node` — a case branch
that isn't mine. Had I committed at that point (as originally planned), the
edit would have landed on the WRONG branch entirely — either silently
absorbed into that case's own PR diff, or lost/conflicting when that
subagent did its own commit/merge. The user caught this before I committed
and told me to revert (`git checkout -- .agents/testing.md`) and re-add
only after the batch landed.

## Why the original framing was too narrow

The first entry scoped the risk to "gitignored, orchestrator-only files" —
true as far as it went, but the actual mechanism is broader: **any
uncommitted edit on a shared (non-worktree) clone is at risk for the
duration of an active Workflow run, tracked or not.** A gitignored file
gets silently reset without ceremony. A TRACKED file survives the
checkout as a dirty diff, which is arguably worse — it looks safe (still
there!) but is now sitting on whatever branch the workflow's subagent last
checked out, one `git commit` away from landing in the wrong place.

## Rule going forward

**Before ANY commit on the shared clone while a batch-build Workflow may
still be running, check `git branch --show-current` first — not just
`git status`.** A clean/present diff is not enough confirmation; confirm
you're actually on the branch you think you are.

Two options for mid-run edits, both cheap, same as before but now stated
for tracked and untracked files alike:
1. **Defer non-essential edits** (doc notes, suite-health pointers, campaign
   doc updates) until between workflow runs — right before dispatch, right
   after the completion notification lands — not mid-run.
2. **If something must be recorded mid-run**, commit it immediately after
   writing it, but only after confirming the current branch is the intended
   one. If the branch has drifted, `git checkout -- <file>` (tracked) or
   just accept the loss (gitignored, no load-bearing state) rather than
   force a commit onto whatever branch happens to be checked out.

Nothing here was load-bearing either time — the real state lives in git
history, TMS, and the tracker — but both times it cost a redo, and the
second time nearly cost a wrong-branch commit. Broaden the check to "any
edit, any file" rather than re-deriving this per file type.
