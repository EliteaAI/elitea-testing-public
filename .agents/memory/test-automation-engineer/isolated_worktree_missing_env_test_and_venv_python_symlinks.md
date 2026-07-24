---
name: Isolated worktree missing .env.test and venv python symlinks
description: Deeply-nested implementer worktrees (.claude/worktrees/wf_.../) can silently lack a working .env.test and a python binary in .venv/bin even though .worktreeinclude lists both — fix by recreating the .env.test symlink locally and NOT touching python (pytest's shebang already points at the main repo's working python3.13).
type: feedback
---

Hit on ELITEA-2004 fix round R1 (isolated worktree `wf_e44028a9-dec-83`).

## Symptom

- `automation/.env.test` doesn't exist at all in the worktree (not even a
  broken symlink) → `config.py`'s pydantic-settings silently falls back to
  empty defaults (`elitea_url=""`, `elitea_project_id=0`) instead of erroring
  — the failure mode is a confusing test error deep in a page-object method
  (wrong base URL, `NoneType`/empty-string navigation), not an obvious
  "config missing" message.
- `.venv/bin/` has real script files for `pytest`/`ruff`/`pip`/etc. but
  **zero** `python`/`python3`/`python3.13` file or symlink — running
  `../.venv/bin/python -c ...` fails with `no such file or directory`.

## Root cause (inferred, not confirmed against the copy tooling's source)

`.worktreeinclude` at the repo root DOES list `.venv/` and `**/.env*` for
copying into isolated worktrees (per the `a2d857a3` fix commit "include
.venv/ so isolated implementer worktrees copy it instead of pip-installing
fresh on OneDrive"). But both of the missing things are **symlinks pointing
OUTSIDE the repo tree**:
- `automation/.env.test` → `../../.env.test` (workspace-parent master file)
- `.venv/bin/python3.13` → `/opt/homebrew/opt/python@3.13/bin/python3.13`

Whatever mechanism populates these nested worktrees (OneDrive-hosted repo —
already a known-fragile combo with symlinks per existing project notes)
appears to drop symlinks that resolve outside the copied subtree, while
copying real files/symlinks-within-tree fine.

## Fix that worked (this session)

1. **`.env.test`** — just recreate the symlink locally, pointing at the
   REAL master file (NOT the relative `../../.env.test` pattern the main
   repo uses — that relative path resolves wrong from inside a worktree
   nested 3 levels deeper than the main repo):
   ```bash
   ln -s "<workspace-parent>/.env.test" automation/.env.test
   ```
   This file is gitignored (`**/.env*` in `.gitignore`) — nothing to commit,
   pure local environment repair. Verified working (`config.py`'s
   `_ENV_FILE = Path(__file__).parent / ".env.test"` resolves relative to
   the worktree's own `automation/`, so once the symlink exists it Just
   Works).
2. **python** — **no fix needed.** `.venv/bin/pytest`'s shebang line is
   `#!<MAIN-REPO-ABSOLUTE-PATH>/.venv/bin/python3.13` (baked in at
   `pip install` time in the ORIGINAL clone, unchanged by copying the venv
   directory elsewhere). That exact path still exists and works on the main
   repo's own checkout, so `../.venv/bin/pytest` run from inside the
   worktree's `automation/` executes correctly via the shebang — the
   worktree's own `.venv/bin` never needs a working python. Same trick
   works for any other `.venv/bin/*` console-script (`ruff`, `pip`, etc.) —
   only a *bare* `python`/`python3` invocation (no such file in this
   worktree) fails; anything with a shebang pointing at the main repo works.

## For next time

If a fresh isolated-worktree implementer session gets a confusingly-empty
`ELITEA_URL`/`elitea_project_id=0` (test fails at a weird step with a blank
base URL, not a loud config error) or a `no such file or directory:
../.venv/bin/python`, check for this FIRST before assuming a real product/
environment defect:
```bash
ls -la automation/.env.test   # missing entirely? symlink broken?
ls .venv/bin/ | grep -i python  # any file/symlink present?
```
Recreate `.env.test`'s symlink per above; don't bother fixing python — the
shebang trick already covers every `.venv/bin/*` script.
