---
name: The shared working tree can switch branches mid-task — make edits fail loudly
description: A parallel dispatch moved the single working tree to automation/base while I was mid-edit; an assert-before-write script is what prevented silent clobbering.
type: feedback
aliases: [branch switched under me, parallel dispatch same tree, lost edits, wrong branch, working tree collision]
tags: [area/git, type/hazard]
created: 2026-08-27
updated: 2026-08-27
---

## What happened

During ELITEA-2215 fix round 1, between two consecutive Bash calls, the
working tree moved from my branch `tests/ELITEA-2215-unblock` back to
`automation/base`. The coordinator had dispatched the analyst **in parallel**
to fix `test-specs/` files while I was editing `automation/` — same single
clone, no worktrees (project rule), so one checkout serves everyone.

Symptom: a `sed -n` read showed my edited content, and the very next call
showed the pre-edit file with different line numbers. Easy to misread as
"my edits vanished".

## Why nothing was lost

My replacement script asserted each `old` string occurred **exactly once**
before writing anything:

```python
def rep(old, new):
    n = s.count(old)
    assert n == 1, f"expected 1 occurrence, found {n}"
```

It hit `found 0`, raised, and never reached `open(p, "w")`. A `sed -i` or a
best-effort `str.replace` would have silently written a mangled or empty-diff
file onto the wrong branch.

## Habits this earns

1. **Never blind-write.** Any scripted edit asserts its anchors exist (and are
   unique) before writing. Fail loudly, write nothing.
2. **Commit and push early.** My work survived because both commits were
   already on `origin`; recovery was one `git checkout`.
3. **Re-check the branch after any surprising read.**
   `git rev-parse --abbrev-ref HEAD` costs nothing and explains a whole class
   of "impossible" file states. Cheap to fold into the same batched call.
4. **Say so in the Run Report.** Parallel dispatches into one tree are a
   coordination decision the lead owns; they cannot fix what they do not see.

Related: [[docs_only_fixes_must_include_runtime_message_literals]]
