---
name: ruff --stdin-filename flips the I001 verdict — never use it as a pre-existing-lint control
description: Verifying "this lint error predates my diff" needs a real file in the real directory; stdin resolves first-party imports differently and returns a false clean.
type: feedback
aliases: [ruff stdin control, pre-existing lint check, I001 false clean, lint control run]
tags: [area/review, type/method]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

Reviewing #2079 (ELITEA-2367) the implementer claimed a ruff `I001` in
`automation/tests/ui/agent_hub/test_empty_state.py` was pre-existing. Checking it:

| Method | base version | HEAD version |
|---|---|---|
| `ruff check --stdin-filename tests/... -` (piped) | **All checks passed** | **All checks passed** |
| `ruff check <real path>` | **I001** | **I001** |

The stdin route said "clean at base, dirty at HEAD" on the first pass and would have
produced a **false CHANGES_REQUESTED** — a new lint error attributed to a diff that
never introduced one. Cause: with stdin, ruff's isort resolves first-party modules
(`from pages...`) differently than for a file that actually sits in the tree, so the
section split it complains about disappears.

## The control that is actually valid

Write the base version to a **real file in the same directory**, lint both, delete:

```bash
cd automation
git show <base>:automation/tests/<path>.py > tests/<dir>/_zz_control.py
../.venv/bin/ruff check --no-cache tests/<dir>/_zz_control.py     # base verdict
../.venv/bin/ruff check --no-cache tests/<dir>/<file>.py          # HEAD verdict
rm tests/<dir>/_zz_control.py && git status --porcelain           # must be clean
```

`--no-cache` matters too (`.ruff_cache` is at repo root and will happily serve a
stale verdict). Same directory matters — that is what makes `linter.src` resolution
identical.

Context: `ruff check .` over `automation/` reports ~679 errors at HEAD, so a single
`I001` on a touched file is systemic debt, not the diff's. Leaving it alone is
correct scope discipline on a narrow FIX card.

Related: [[hardcoded_count_assertions_mix_structure_and_data]]
