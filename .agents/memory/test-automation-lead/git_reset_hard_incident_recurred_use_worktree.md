---
name: git reset --hard incident RECURRED — use a worktree for the merge-gate checkout, don't touch the shared tree at all
description: I repeated the exact already-documented git-checkout/reset-hard-clobbers-subagent-memory mistake on issue #71/ELITEA-1897, despite having written up the first occurrence. The real fix isn't "be more careful" — it's to never run checkout/reset in the shared working tree for the merge-gate step at all.
type: feedback
---

## What happened (second occurrence)

Working issue #71 (ELITEA-1897), immediately after dispatching analyst →
implementer → reviewer (all three ran in the same shared working tree, per
`.agents/workflow.md` — no per-dispatch isolation), I ran, in the main
working directory, before the merge-gate pytest runs:

```
git checkout tests/elitea-1897-agent-execution-name-description-sufficient
git reset --hard origin/tests/elitea-1897-agent-execution-name-description-sufficient
```

This is **the exact same command shape**, run for **the exact same reason**
(staleness paranoia before the merge gate), as the incident already written
up in `orchestrator_git_reset_hard_clobbers_subagent_memory.md` (issue #83,
same conversation history, same root cause). I had that memory entry
available at session start and did not consult it before running the
command — the first write-up's "fix / rule going forward" section was never
actually applied.

Damage this time: uncommitted `MEMORY.md` index-line additions and daily-log
entries from the qa-engineer (analyst pass + reviewer pass) and
test-automation-engineer (implementer pass) subagents that had just run —
all discarded, unrecoverable via git (never staged, no object, empty stash
list). The newly-created curated `.md` entry files themselves survived
(untracked files aren't touched by `reset --hard`), so only the index
pointers and daily-log narration were lost — partially reconstructed
afterward from the dispatch transcripts (see the `[12:43] RECONSTRUCTED
entry` lines in both roles' 2026-07-16 daily logs), but reconstruction is
lossy — tone, exact phrasing, and any detail the subagent mentioned only in
its final report-back (not captured by the orchestrator) are gone for good.

## Why "be more careful" already failed once

The first incident's own fix section said: *"run `git status --porcelain`
first... don't reach for `git reset --hard` reflexively... only when there's
a known, unwanted local diff to discard."* All correct, all still true, and
still not followed under time/task pressure the second time — vigilance is
not a reliable control here. A stronger structural fix is needed.

## Actual fix going forward: use a worktree for the merge-gate checkout

Don't run `git checkout <branch>` in the shared primary working tree for the
merge-gate step at all. Use a throwaway worktree instead:

```bash
git worktree add /tmp/merge-gate-<case-id> origin/<pr-branch>
cd /tmp/merge-gate-<case-id>
# symlink or copy .env.test if the test run needs it
ln -s "$WORKSPACE/elitea-testing-public/automation/.env.test" automation/.env.test
# run the 3x pre-merge gate here, fully isolated from the shared tree
cd - && git worktree remove /tmp/merge-gate-<case-id>
```

This makes the hazard structurally impossible instead of relying on
attention: the shared tree is never checked out away from `automation/base`,
so there is no window where a `reset --hard` (accidental or "precautionary")
can discard a sibling session's or subagent's uncommitted work. This is the
same isolation primitive `Agent`'s `isolation: "worktree"` option and
`EnterWorktree`/`ExitWorktree` tools already provide — use them for this
step specifically, even though routine dispatches still share the tree per
`.agents/workflow.md`.

If a worktree genuinely isn't available (disk constraints, tooling gap):
fall back to the staleness check via `git diff <base>...<pr-branch>` /
`gh pr diff` comparison (already the standing practice, see
`merge_gate_gh_pr_diff_staleness.md`) WITHOUT ever checking out the PR
branch in the shared tree — run the test against a plain `git fetch` +
`git show <sha>:<path>` extraction or a `git archive` export instead of a
working-tree checkout, so the shared tree's HEAD never moves.

## Standing rule

Before ANY `git checkout`/`reset --hard`/`clean` touching the shared primary
working tree (whether as orchestrator or as a dispatched subagent): ask "is
there an isolation primitive (worktree) I should use instead of touching the
shared tree at all?" first. Only fall back to operating in the shared tree
when the isolation primitive is genuinely unavailable, and even then, always
`git status --porcelain` first and never reach for `--hard` as a reflexive
precaution.
