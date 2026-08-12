---
name: Shared tree's checked-out branch can change mid-dispatch because ANOTHER concurrent factory session shares the exact same working tree — not just my own actions or a subagent's verification technique
description: On #369/ELITEA-2166, verified branch=automation/base immediately before dispatching the analyst, then ~23 minutes later (after the analyst returned) found the shared tree checked out on tests/ELITEA-2132-...  — a DIFFERENT case's branch, with a genuinely unrelated uncommitted diff (a hook-script perf fix) mixed in among my own analyst's legitimate uncommitted memory writes. Root cause: this factory runs multiple conversations concurrently, ALL sharing the same physical git working directory (no per-conversation isolation) — a concurrent session working ELITEA-2132 checked out its own branch and left its own uncommitted work sitting there while my dispatch was in flight.
type: feedback
---

## What happened

Session-start: confirmed `git branch --show-current` → `automation/base`, ran
`sync-base-branches`, confirmed clean. Immediately before dispatching the
qa-engineer analyst for ELITEA-2166, re-checked `git branch --show-current`
→ still `automation/base`. Dispatched the analyst (`run_in_background:
false`, foreground per factory-mode rules) — it ran for **1,392,166 ms
(~23 minutes)** and returned a complete AFS.

Next action: `git checkout -b tests/ELITEA-2166-... automation/base` — as
the FIRST command in a combined bash block that also ran `git add` + `git
commit` unconditionally after it. The checkout FAILED (uncommitted changes
would be overwritten), so git never moved off whatever branch was already
checked out — and a `git branch --show-current` run as the very first line
of that SAME command block had already printed `tests/ELITEA-2132-chat-
folder-creation-via-chats-header-icon`, not `automation/base`. Because the
verify-step's output wasn't inspected before the destructive steps ran (all
chained in one bash call), `git add` + `git commit` executed against the
wrong branch, landing my AFS-only commit onto a DIFFERENT, unrelated case's
feature branch.

## Root cause — genuinely new variant

Prior memory entries in this file documented: my own reflexive `reset
--hard` (3 recurrences), a subagent's own git-cleanup checkout clobbering
sibling memory, and a *dispatched reviewer's own sanctioned worktree
add/remove* leaving the shared tree on a third branch. This is a **fourth,
distinct** root cause: nothing in *this* conversation's own tool calls (mine
or my dispatched analyst's) explains the branch change or the unrelated
`.claude/hooks/sdlc-skills/lib.sh` diff — that diff was a hook-script perf
fix neither I nor the qa-engineer analyst had any reason to write. The only
coherent explanation is a **separate, concurrent factory conversation**
(per `.agents/workflow.md`'s "One conversation per issue" model — implying
MANY conversations run concurrently across different issues) working
ELITEA-2132 in this same physical directory, which checked out its own
branch and left its own in-progress uncommitted edit sitting there, all
while my 23-minute analyst dispatch was in flight. `Agent()` dispatches
share the parent's working tree with **zero host-level isolation**
(`references/orchestration-playbook.md` § How to dispatch a subagent) — and
apparently that "parent's working tree" is ALSO shared across sibling
top-level conversations, not just within one conversation's own subagent
fan-out.

## Why this is worse than the prior variants

The previous entries could all be traced to a single conversation's own
tool calls (mine, a dispatched subagent's, or a reviewer's sanctioned
technique) — meaning "review what I/my subagents did" was a sufficient
diagnostic. Here, the actor is fully invisible from inside this
conversation: no tool call in this transcript explains the `lib.sh` change.
Any long-running dispatch (minutes, not seconds) is enough exposure window
for a sibling conversation to have altered the shared tree's HEAD and left
its own dirty state mixed into `git status` by the time the dispatch
returns.

## The fix applied (safe, no data lost)

1. **Never `git reset --hard` / `checkout -f` to "clean up"** — the dirty
   state (a concurrent session's uncommitted `lib.sh` change) is not mine to
   discard, and my own AFS-only commit's damage is one commit deep, cheaply
   reversible without touching anything else.
2. **`git reset <mixed> HEAD~1`** (default mode, NOT `--hard`) to undo just
   my own erroneous commit. Mixed reset only moves the branch ref + index —
   it does NOT touch working-tree files outside that commit's own diff, so
   the concurrent session's `lib.sh` diff and my analyst's own memory-file
   diffs survived completely untouched. Verified with `git status
   --porcelain` before and after: identical set of modified/untracked files
   minus the AFS (now back to untracked).
3. **Did the actual branch-creation + commit + push in an isolated `git
   worktree`** (`git worktree add /tmp/wt-X -b <new-branch> automation/base`
   — NOT the `EnterWorktree` tool, which is gated to explicit user/CLAUDE.md
   instruction and whose `baseRef: fresh` resolves against the repo's git-
   configured default branch, ambiguous for a project like this one whose
   *working* default is `automation/base`, not `main`), so the primary
   shared tree's HEAD never moved a second time. Copied the untracked AFS
   file into the worktree, committed, pushed, removed the worktree.
4. Left the concurrent session's `lib.sh` diff and my own qa-engineer
   memory diffs (`MEMORY.md`, daily log, the new curated `.md` file)
   completely alone in the primary tree — not mine to commit or discard.

## Standing rule — strengthens, doesn't replace, the existing ones

- **Never chain a branch-state verification command in the SAME bash
  invocation as the destructive action that depends on its result.** Run
  `git branch --show-current` / `git status --porcelain` ALONE, actually
  read the output, THEN decide the next command. This incident happened
  precisely because verify + `checkout -b` + `add` + `commit` were one
  combined call — the verify output arrived too late to gate anything.
- **After ANY dispatch that runs for more than ~a minute** (not just at
  merge-gate time, not just after a subagent's own worktree technique):
  re-verify the shared tree's branch before your very next git write. A
  long dispatch is exposure time for a sibling conversation to have moved
  the shared HEAD, independent of anything this conversation did.
- **When a "wrong branch" is discovered with a mix of your own recent
  commit and unrelated foreign uncommitted diffs**: undo only your own
  commit via mixed `reset`, and do your actual work in a worktree instead
  of trying to get the primary tree back to the "right" branch — getting
  it there would require checking out away from the foreign dirty state,
  which either fails loudly (safe) or requires force (never do this).
