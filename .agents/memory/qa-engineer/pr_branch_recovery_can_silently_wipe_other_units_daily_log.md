---
name: PR branch recovery can silently wipe other units' daily-log entries
description: Recovering a closed PR's branch as the base for a redo, without re-merging current base's append-only memory files on top, can delete other units' daily-log lines wholesale — check line counts, not just content correctness
type: feedback
---

## What happened (ELITEA-2428 fix-v2, PR #1450, round 3 review)

PR #1450's own description says it "recovered the prior implementation from
the closed branch's history [PR #1440] and reconciled it onto current
`automation/base`" (the rest of the `skills-remaining-w1` wave had merged in
the meantime via #1449). The code reconciliation was done correctly — but
`.agents/memory/test-automation-engineer/daily/2026-08-12.md` was not: the
PR's diff against `origin/automation/base` **deletes 6 pre-existing daily-log
lines** (work-log entries for ELITEA-2431, 2432, 2433/2434 ×2, 2436 ×2 —
covering separate, real, already-open/merged PRs #1443/#1444/#1446) and
replaces them with only the 2 new entries this fix round wrote. The recovered
branch forked from a point in history *before* those 6 entries existed on
`automation/base`, and the file was carried forward from that old fork point
instead of being re-diffed/appended against current base content. Caught by
reading `git show origin/automation/base:<path>` vs
`git show origin/<pr-branch>:<path>` side by side — line counts alone (8 vs 4)
were the tell.

If merged as-is (this repo squash-merges into `automation/base`), the merge
applies exactly this diff — silently destroying 6 other units' persistent
work-log history. This is precisely the append-only-file collision class
`.claude/skills/memory/SKILL.md` warns about (26/32 merge conflicts in one
campaign traced to `MEMORY.md`/`daily/*.md`) — except here it isn't even a
merge *conflict* (which git would at least surface); it succeeds silently
because a plain content-replacement diff is not a conflict.

## The check to run next time

Whenever a PR's provenance is "recovered from an older/closed branch" (not a
normal same-day sequential fix round): diff **every** touched append-only
memory file (`daily/*.md`, `MEMORY.md`) against current `origin/<base>`, not
just against the recovered branch's own history. A destructive replacement
shows as **deletions of lines you didn't write**, not just additions — an
honest recovery/reconciliation diff on these files should be *pure addition*
at the end of the file, never a removal of someone else's entries. Compare
line counts (`git show <base>:<path> | wc -l` vs `git show <branch>:<path> |
wc -l`) as a fast tripwire before trusting the diff's content.

## Why this is preventive

Any fix round whose branch was recovered/rebuilt from an older ref (a closed
PR, a stashed branch, a stale local checkout) risks carrying a *stale
snapshot* of every append-only file the branch touches — not just the ones
central to the fix. This is a distinct failure mode from the normal
same-session sequential-append pattern the pipeline relies on to keep these
files conflict-free, and it will recur on any future "recover from closed
PR X" fix round unless checked explicitly.
