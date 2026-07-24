---
name: Isolated worktree's copied .venv is missing the python/python3/python3.13 symlinks
description: The `.venv/` copied into a fresh isolated implementer worktree (per commit a2d857a3, "include .venv/ so isolated worktrees copy it instead of pip-installing fresh") carries every installed package's console-script shims but NOT the `python`/`python3`/`python3.13` interpreter symlinks themselves — `.venv/bin/pytest`'s shebang points at them and fails with "no such file or directory" until they're recreated.
type: feedback
---

Hit on GAP-073's fix round (worktree `wf_fc8ff051-693-45`): `.venv/bin/pytest
--version` failed, `.venv/bin/python --version` failed too ("no such file or
directory"), even though `.venv/bin/` clearly had `pip`, `ruff`,
`playwright`, `ArUFF`, etc. all present and the shebang lines of those
scripts pointed at the WORKTREE's own absolute `.venv/bin/python3.13` path
(not the main repo's — so it's not simply a hardcoded-original-repo-path
problem, the copy mechanism just never carried the interpreter symlinks
themselves).

`.venv/pyvenv.cfg` still names the real source: `home =
/opt/homebrew/opt/python@3.13/bin`. Fix (one-time per fresh worktree, never
part of the diff):

```bash
ln -sf /opt/homebrew/opt/python@3.13/bin/python3.13 .venv/bin/python3.13
ln -sf python3.13 .venv/bin/python3
ln -sf python3.13 .venv/bin/python
```

Verify with `.venv/bin/python --version` before trusting `pytest`/`ruff` to
run. This is the same *family* of gap as the `.env.test` symlink issue
(`isolated_worktree_env_test_symlink_breaks.md`) — worktree copying doesn't
reliably carry symlinks that point at absolute machine paths outside the
copied tree — but a DIFFERENT concrete file (the venv's own interpreter,
not the env file), so check both independently rather than assuming fixing
one fixes the other.
