---
name: ruff --stdin-filename gives a FALSE clean in this repo
description: Comparing a merge result against its parents via stdin reported both parents clean when neither was
type: feedback
aliases: [ruff stdin, --stdin-filename, false clean, I001 baseline, lint baseline compare]
tags: [area/lint, type/gotcha]
created: 2026-09-09
updated: 2026-09-09
---

## What happened

Resolving a merge conflict in `automation/pages/base_page.py` (2026-09-09 sync), I wanted
to know whether `I001` + `W293` were mine or pre-existing. I baselined the two parent
versions with:

```bash
git show origin/main:automation/pages/base_page.py > /tmp/bp_main.py
../.venv/bin/ruff check --stdin-filename pages/base_page.py - < /tmp/bp_main.py
# -> "All checks passed!"     ← WRONG
```

Both parents came back **clean**, which framed my resolution as having *introduced* two
findings. It hadn't.

## The truth

Written to real files inside `automation/pages/` and checked normally, **both parents
carry the identical `I001` + `W293`** — same two codes as the merged result. The repo-wide
baseline is 679 findings, so nothing here was clean to begin with.

`--stdin-filename` does not resolve the project's isort `src`/first-party config the way a
real path does, so the local-import block (`from config …`, `from utils.actions …`) is
classified differently and `I001` silently disappears.

## Rule

**Never baseline a lint comparison through stdin in this repo.** Write the candidate
versions to real files under the directory they belong to and run `ruff check` on the
paths. Cheap, and it is the difference between "the merge broke lint" and "this file was
never clean".

Corollary that mattered: because the two findings were pre-existing on both sides, the
correct action was to **leave them alone** — reformatting `base_page.py`'s imports would
have been unrelated churn on a file with hundreds of dependents, during a sync.

Bonus signal: `F401` (unused import) is in the enabled rule set, so a clean F401 on the
merged file is mechanical proof that every name in a union-resolved import block is
actually used.
