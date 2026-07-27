---
name: Merge safety is provable via a path-overlap check, not just a liveness verdict
description: Before skipping a sync over a live concurrent process's uncommitted WIP, check whether the incoming merge actually touches the WIP's paths — zero overlap makes the merge provably safe regardless of how "live" the other session is.
type: feedback
---

## What happened (2026-07-22, unattended sync run 32, issue #725)

The immediately preceding run (#724, same day) found a live `claude --agent scout`
process (PID 13551) in the shared elitea-testing-public tree with uncommitted WIP
(`automation/conftest.py` V8/CDP coverage instrumentation, `.gitignore` coverage-ignore
rules, a 1.4GB `coverage/.v8/` fragment dir) and — correctly per the guard's intent —
skipped Part 1 (`automation/base` sync) entirely rather than risk disturbing it.

Run 32 found the exact same live process still running (same PID, later timestamp) and
the exact same WIP still uncommitted. Rather than repeat the blanket skip, checked
first whether the incoming merge would even touch any of the WIP's paths:

```bash
git fetch origin
git diff --name-only automation/base...origin/main
```

This showed the merge would touch exactly one file
(`automation/tests/ui/skills/test_export_agent_no_nested_dependencies.py`), completely
disjoint from `conftest.py`/`.gitignore`/`coverage/`. That makes the merge provably
safe: `git merge` only ever needs to check out a new blob for a path if the merge
result differs from the current HEAD for that path; if origin/main hasn't touched a
dirty path since the merge-base, the merge leaves that path's working-tree content
(dirty or not) completely alone. Ran the merge, verified before and after that the
scout's WIP was byte-identical to before, and the scout process was still alive
throughout.

The same principle resolved a second overlap later in the same run: the push was
rejected non-fast-forward because 6 concurrent commits had landed on
`origin/automation/base` meanwhile, and one of them touched
`.agents/memory/test-automation-lead/MEMORY.md` — the same file I had my own
uncommitted (unrelated) edit sitting in. Diffed both sides
(`git diff -- <path>` for mine, `git diff HEAD origin/automation/base -- <path>` for
theirs) before deciding: both were independent append-only bullet insertions at
different line ranges in the same list, so committing my own edit first (it's my own
deliverable per Step 0) and then merging was safe — git's 3-way merge combined them
with no conflict markers.

## Rule going forward

1. A live concurrent process (confirmed via `ps aux`/`ps -p`) does NOT automatically
   mean "skip the sync." It means "verify the specific paths the merge would touch
   before deciding." Run `git diff --name-only <local>...<remote>` (or
   `git diff HEAD <remote> -- <path>` for a single suspect path) and compare against
   `git status --porcelain`'s dirty/untracked list.
2. Zero overlap → merge is provably safe, proceed with confidence, then re-verify the
   WIP paths are byte-identical afterward as cheap confirmation.
3. Real overlap on a path that's genuinely someone else's in-flight WIP (not your own
   memory/deliverable) → THAT is when the original blanket-skip guard still applies —
   don't force a merge or attempt a stash/pop dance against another session's live file.
4. Real overlap on a path that's your OWN previously-uncommitted deliverable (e.g. your
   own memory file) is a different, resolvable case: diff both sides first — independent
   insertions in different regions merge cleanly once committed; only escalate to manual
   conflict resolution if the diffs genuinely touch the same lines.
5. This check is cheap (one `git diff --name-only`, ~free) — worth running by default
   before invoking the blanket skip, rather than treating "process is alive" alone as
   sufficient grounds to abort Part 1.
