---
name: ruff --fix reorders `pages.*` imports wrongly, and --stdin-filename hides the error
description: pyproject has no ruff src/known-first-party, so `pages.*` reads as third-party — never blanket-apply `ruff --fix` to an import block under automation/
type: feedback
aliases: [ruff I001, import block un-sorted, ruff fix imports, known-first-party, stdin-filename]
tags: [area/lint, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## The trap

`pyproject.toml` `[tool.ruff]` sets only `target-version`, `line-length` and
`select = ["E","F","I","W","UP"]` — there is **no `src`** and **no
`known-first-party`**. So ruff cannot tell that `pages`, `components`, `api`,
`utils` are first-party, and its `I001` "fix" folds them into the third-party
block alphabetically:

```python
# what the repo convention wants (.agents/conventions.md: stdlib -> third-party -> local)
import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

# what `ruff check --fix` rewrites it to
import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect
```

**Never blanket-apply `ruff --fix` to an import block under `automation/`.**
Fix real `I001` hits by hand, or scope `--fix` to a file with no local imports.
`ruff check tests/` reports **314 pre-existing errors** repo-wide (measured
2026-08-23), so a non-zero ruff exit on a touched file is not by itself
evidence that you introduced anything — diff against `HEAD`'s version of the
same file before acting.

## The second-order trap: --stdin-filename gives a false PASS

Checking the pre-change version via stdin says "All checks passed" while the
identical bytes at a real path report `I001`:

```bash
../.venv/bin/ruff check --stdin-filename tests/ui/x/test_y.py - < old.py   # All checks passed  (WRONG)
../.venv/bin/ruff check tests/ui/x/test_y.py                                # Found 1 error      (truth)
```

First-party inference depends on the file's real location on disk, which stdin
does not have. To decide "did I introduce this lint error?", restore the old
bytes **at the real path** (`git checkout HEAD -- <path>`, check, then restore
your copy) — never via `--stdin-filename`.

Related: [[afs_priority_vs_pytest_mark_preflight_check]]
