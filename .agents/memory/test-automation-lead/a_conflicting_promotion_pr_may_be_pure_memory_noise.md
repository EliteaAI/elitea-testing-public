---
name: A CONFLICTING promotion PR may be blocked by nothing but memory logs
description: Check the conflict scope before assuming a stale promotion PR needs re-work — .agents/memory logs conflict constantly
type: feedback
---

`.agents/memory/**` is **tracked and committed** in this repo (not gitignored,
despite CLAUDE.md — see #2000/#1761). `MEMORY.md` and `daily/<date>.md` are
append-at-the-end files every role writes, so two work streams touching the same
day collide on every cross-branch merge.

**Consequence:** a promotion PR can sit `CONFLICTING`/`DIRTY` for days with a
perfectly clean deliverable. PR #2056 (ELITEA-1899 repair → `main`) was blocked
purely by three append-only logs; the test, AFS and page object all auto-merged.

**Check the scope before concluding anything** — one command, no checkout:

```bash
git merge-tree --write-tree --name-only origin/main origin/<branch> | sed -n '2,40p'
```

If every conflicted path is under `.agents/memory/`, the fix is mechanical:
merge, resolve by **union** (they are append-only; HEAD-first is usually
chronological), commit. Then verify the deliverable was untouched rather than
asserting it — diff each deliverable file against the pre-merge branch and
against the gated `automation/base` copy; byte-identical is the evidence.

**Still run a control** if the merge pulls new executable code into a file the
spec uses (main added +215 lines to `agent_detail_page.py` here). One run
confirming a byte-identical signature beats reasoning about inertness.

Updating an existing PR auto-fires CodeQL `Analyze`. That is unavoidable and
uses no DEV environment — it does not violate a card's "do not trigger
workflows" instruction, but say so explicitly.
