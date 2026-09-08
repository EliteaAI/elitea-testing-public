---
name: ruff --stdin-filename gives a FALSE clean in this repo
description: Comparing a merge result against its parents via stdin reported both parents clean when neither was
type: feedback
aliases: [ruff stdin, --stdin-filename, false clean, I001 baseline, lint baseline compare]
tags: [area/lint, type/gotcha]
created: 2026-09-09
updated: 2026-09-09  # 2nd confirmation same day, sharper mechanism
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

`--stdin-filename` does not resolve the project's config the way a real path does.

**The mechanism is broader than "isort src detection" (measured 2026-09-09, 2nd
occurrence — `agent_detail_page.py`, the fix/2052 merge).** Stdin drops the *entire
configured rule selection* and falls back to ruff's built-in default. Same file, same
cwd (`automation/`), same binary:

| invocation | findings |
|---|---|
| `ruff check pages/agent_detail_page.py` | **7** — E501 ×1, F401 ×2, F541 ×1, I001 ×1, UP008 ×2 |
| `… --stdin-filename pages/agent_detail_page.py -` | **3** — F401 ×2, F541 ×1 |

The four that vanished are exactly the families outside ruff's default `["E4","E7","E9","F"]`:
`I001` (I), `UP008` (UP), `E501` (E5). `pyproject.toml` selects `["E","F","I","W","UP"]` at
the **repo root**, and stdin never picks it up. So it is not that isort classifies imports
differently — it is that `I`, `UP`, `W` and `E501` are **not being checked at all**.

## Rule

**Never baseline a lint comparison through stdin in this repo.** Write the candidate
versions to real files under the directory they belong to and run `ruff check` on the
paths. A `trap 'rm -f $TMP' EXIT` keeps the scratch file from ever being committed.

**One-line self-test before trusting any stdin baseline:** run the *same, unmodified*
file both ways. If the counts differ, stdin is not applying the project config and every
comparison built on it is void. In the 2026-09-09 case this turned an apparent
"4 NEW findings — the merge regressed lint" into the correct verdict, **exact parity with
`automation/base`**. Cheap, and it is the difference between "the merge broke lint" and "this file was
never clean".

Corollary that mattered: because the two findings were pre-existing on both sides, the
correct action was to **leave them alone** — reformatting `base_page.py`'s imports would
have been unrelated churn on a file with hundreds of dependents, during a sync.

Bonus signal: `F401` (unused import) is in the enabled rule set, so a clean F401 on the
merged file is mechanical proof that every name in a union-resolved import block is
actually used.
