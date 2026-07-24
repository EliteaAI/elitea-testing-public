---
name: Isolated worktree's automation/.env.test symlink breaks (relative target, wrong depth)
description: A fresh implementer worktree's automation/.env.test does not exist at all — the main repo's relative symlink (../../.env.test) can't resolve from the deeper .claude/worktrees/<name>/automation/ path — tests SKIP with a cryptic auth error until you recreate it locally.
type: feedback
---

The main repo's `automation/.env.test` is a **relative** symlink:
`automation/.env.test -> ../../.env.test` (correct from `elitea-testing-public/automation/`,
resolving to the workspace-parent's master `.env.test`).

An isolated implementer worktree lives at
`elitea-testing-public/.claude/worktrees/<name>/automation/` — two levels
deeper than the main repo's `automation/`. Since the worktree tool copies
tracked files (git-aware) but a relative symlink to an **untracked,
gitignored** file (`.env.test` matches `**/.env*` in `.gitignore`) isn't
part of any commit, it simply doesn't exist in a fresh worktree at all —
`ls automation/.env.test` reports "No such file or directory".

Symptom: every test SKIPs (not fails) with
`Authentication failed — check TEST_USER_EMAIL and TEST_USER_PASSWORD:
Login failed: Invalid URL '': No scheme supplied. Perhaps you meant
https://?` — because `config.py`'s dotenv load silently finds nothing and
`ELITEA_URL` resolves to an empty string. This looks like a credentials
problem; it is actually a missing-file problem.

**Fix (one-time, per worktree, before the first pytest run):**
```bash
cd <worktree>/automation
ln -s "<workspace-parent-absolute-path>/.env.test" .env.test
```
Find `<workspace-parent-absolute-path>` by checking where the MAIN repo's
`automation/.env.test` symlink resolves (`readlink` + `realpath`), or by
listing the workspace-parent directory (sibling of `elitea-testing-public`,
`EliteaUI`, `onetest-ai-tm-Elitea`, `elitea_assistant`).

This is pure local environment setup (the target file is gitignored) —
never part of the implementer's diff/PR, and safe to redo identically for
every future isolated-worktree dispatch. Same class of gotcha as the
`.venv/` copy-vs-fresh-install fix already made for worktrees (commit
a2d857a3) — the .venv's own `pytest`/`ruff` scripts have ABSOLUTE shebangs
pointing at the MAIN repo's `.venv/bin/python3.13`, which still resolves
fine (that symlink is a plain absolute-target one, unaffected by depth) —
only the RELATIVE `.env.test` symlink breaks with worktree depth.
