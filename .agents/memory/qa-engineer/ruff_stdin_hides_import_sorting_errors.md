---
name: ruff --stdin-filename hides first-party import-sorting errors
description: Verify lint by PATH, not stdin — `ruff check --stdin-filename x.py -` reports clean where `ruff check x.py` reports I001
type: feedback
aliases: [ruff stdin, I001 false clean, lint verification, organize imports]
tags: [area/tooling, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## What happened

Reviewing PR #1972 (settings-w09) I wanted to know whether an `I001`
("Organize imports") error on `automation/pages/admin_users_page.py` was
introduced by the branch or pre-existing on `automation/base`. Piping both
versions through `../.venv/bin/ruff check --stdin-filename
pages/admin_users_page.py -` returned **"All checks passed!" for BOTH** —
while checking the same on-disk file by path returned the `I001` error.

## Why

ruff's isort rules resolve first-party vs third-party from the real file
tree (`src`/package detection). Reading from stdin the file does not exist
at that path, so the grouping decision differs and the error disappears.

## The rule

To attribute a lint error to a branch, write the other version to a **real
file inside the same package directory** and check it by path, then delete it:

```bash
cd automation
git show automation/base:automation/pages/admin_users_page.py > pages/zz_check_tmp.py
../.venv/bin/ruff check pages/zz_check_tmp.py; rm -f pages/zz_check_tmp.py
```

(That attribution mattered: the `I001` is pre-existing on `automation/base`,
so it was a note, not a blocker.)

Related: [[project_briefing]]
