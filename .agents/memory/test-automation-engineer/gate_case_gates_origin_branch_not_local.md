---
name: gate-case.mjs gates origin/<branch>, never your local commits
description: A conflict fix committed locally keeps re-conflicting — the gate checks out origin/<branch>; push before re-running
type: reference
aliases: [gate conflict loop, gate-case origin branch, hardening gate conflict, MEMORY.md merge conflict gate]
tags: [area/gate, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## What happens

`scripts/gate/gate-case.mjs` resolves the branch with
`git checkout --detach ${remote}/${branch}` — it gates **`origin/<branch>`**, and
falls back to the local ref only when origin has none. So a merge-conflict
resolution you commit locally is invisible to it: the gate re-merges the base
into the *remote* tip and returns the identical `verdict: "conflict"` every time,
with no hint that your fix exists.

## The loop, and how to break it

1. Gate returns `verdict: conflict`, `conflictFiles: [...]`, tree left DETACHED at
   the remote branch tip.
2. `git checkout <branch>` → `git merge origin/<base>` → resolve → commit.
3. **`git push origin <branch>`** — this is the step that is easy to skip, and
   without it step 4 reproduces step 1 exactly.
4. Re-run the gate.

Observed 2026-08-23 on `tests/batch-artifacts-w04`: two full gate invocations
burned on the same conflict before the push.

## What the conflict almost always is

`.agents/memory/<role>/MEMORY.md` — every role appends index lines at the end of
the same file, so a trunk that has moved and a base that has moved collide there
and nowhere else. Resolution is a pure **union** (keep every line from both
sides, base's block then the branch's); it is bookkeeping, never a semantic
collision, and it is explicitly in the gate agent's remit
("mechanical unions only") per the script's own conflict note.

Related: [[soft_asserted_spec_is_red_not_green]]
