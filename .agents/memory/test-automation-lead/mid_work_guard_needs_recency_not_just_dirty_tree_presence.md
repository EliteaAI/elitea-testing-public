---
name: Mid-work guard needs recency, not just dirty-tree presence
description: The unattended sync guard's named conditions (MERGE_HEAD, uncommitted testid work, a `.testid-pr` worktree) are examples, not the exhaustive test — check mtime/last-commit recency to tell live mid-work from stale leftovers before deciding whether to stop-and-report or proceed-and-land
type: feedback
---

Run 31 (2026-07-22, #712) hit a shared tree that was dirty AND checked out on an unrelated
case branch (`tests/ELITEA-2132-...`), plus an active-looking implementer worktree
(`wt-ELITEA-2166-impl`) on another case branch. None of the guard's literally-named
conditions were true: no `MERGE_HEAD` in either repo, no `.testid-pr` worktree, and the
dirty state wasn't "testid work" specifically.

Stopping-and-reporting on literal-match-only would have been wrong here — read that way,
almost any non-trivial factory session leaves *some* dirty state or *some* worktree behind,
and the guard would trip every single run. The named examples in the guard instruction are
illustrations of "a live agent is using this tree right now," not the full test.

The actual signal that mattered: **recency**. Checked `stat` mtimes on the dirty files and
`git log -1` on the worktree — everything was 10-19 hours old, no commits in the last hour,
no lock/merge-in-progress markers. That's stale leftover state from a prior completed (or
long-abandoned) session, not a concurrent live process. Proceeded under the sync skill's own
Step 0 ("a dirty tree is normal here... classify what's there and land it") instead of
aborting.

Rule of thumb for the next run: before invoking "stop and report — never sync over someone's
in-flight work," check recency (mtime of dirty files, last commit timestamp on any suspicious
worktree, presence of an actual lock/MERGE_HEAD). Only treat it as live mid-work — and abort —
if something changed within roughly the last hour, or a merge/rebase is literally in progress.
Otherwise classify and land per Step 0, same as any other sync run.
