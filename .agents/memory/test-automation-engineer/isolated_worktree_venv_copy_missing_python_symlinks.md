---
name: Isolated worktree's copied .venv is missing its python/python3 interpreter symlinks
description: A fresh implementer worktree's .venv/ (copied per commit a2d857a3 so worktrees don't pip-install fresh on OneDrive) has pip/pytest/playwright/ruff scripts but NO python/python3/python3.13 symlinks — `.venv/bin/python*` resolves to nothing and every pytest invocation fails with "no such file or directory: .venv/bin/python".
type: feedback
---

Hit in an ELITEA-2010 fix-round dispatch (worktree `wf_e44028a9-dec-133`): `.venv/bin/`
had `pip`, `pip3`, `pip3.13`, `pytest`, `py.test`, `playwright`, `ruff`, `dotenv`,
`slugify`, `httpx`, `idna`, `normalizer`, `pygmentize`, and the `activate*` scripts —
but zero `python`/`python3`/`python3.13` entries. Whatever copies `.venv/` into a
fresh isolated worktree (the a2d857a3 fix — "include .venv/ so isolated implementer
worktrees copy it instead of pip-installing fresh") drops the interpreter symlinks
specifically, while keeping every console-script symlink pip installed.

**Fix (one-liner, no reinstall needed):** the venv's `pyvenv.cfg` still has the
absolute path — read `executable = ...` from `.venv/pyvenv.cfg`, then:
```bash
cd <worktree>/.venv/bin
ln -s <that absolute executable path> python3.13   # or whatever version pyvenv.cfg names
ln -s python3.13 python3
ln -s python3.13 python
```
This is a plain symlink to a SYSTEM path (e.g. `/opt/homebrew/opt/python@3.13/bin/python3.13`
via `/opt/homebrew/Cellar/python@3.13/.../bin/python3.13`), not worktree-specific — safe
to recreate identically every time this gotcha recurs. After this, `.venv/bin/python -c
"import playwright, allure, pytest"` succeeds immediately; no `pip install` needed since
every package + console script was already copied correctly.

**Takeaway:** before assuming a copied `.venv` needs a full `pip install -e ".[reporting]"`
re-run (slow on OneDrive), first check `ls .venv/bin/python*` — if it's just the
interpreter symlinks missing (everything else present), the fix above is seconds, not
minutes.
