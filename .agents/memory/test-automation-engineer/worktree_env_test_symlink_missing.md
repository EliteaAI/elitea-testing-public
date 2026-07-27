---
name: worktree .env.test symlink missing
description: Fresh implementer worktrees lack automation/.env.test (git-ignored symlink) — auth_state fails with "Login failed: Invalid URL ''"; fix by symlinking the absolute workspace-root path.
type: feedback
---

`automation/.env.test` is a git-ignored symlink in the main checkout
(`automation/.env.test -> ../../.env.test`, correct only because `automation/`
sits exactly 2 directory levels under the workspace root there). A fresh
implementer worktree nested under `.claude/worktrees/<id>/automation/` does
NOT inherit this symlink (worktrees don't copy gitignored files, unlike the
already-fixed `.venv/` case — see commit a2d857a3, "fix(worktrees): include
.venv/ so isolated implementer worktrees copy it instead of pip-installing
fresh on OneDrive") — and even if it were copied, the relative path math
would break anyway at the deeper nesting depth.

**Symptom:** every test using `auth_state` (i.e. every UI test) gets
collect-time SKIPPED with `Login failed: Invalid URL ''`.

**Fix (one-time, per worktree):**
```bash
cd <worktree>/automation
ln -s /<absolute-path-to-workspace-root>/.env.test .env.test
```
Use an ABSOLUTE target, not a recomputed relative one — sidesteps the
nesting-depth problem entirely regardless of how deep the worktree happens
to be. The workspace root is the common parent of `elitea-testing-public/`,
`EliteaUI/`, `onetest-ai-tm-Elitea/` (see `.agents/architecture.md`'s
three-repo topology) — find it via `ls` from the main checkout, since
`../../.env.test` resolution differs between the main repo and any worktree.

Verify with `wc -l automation/.env.test` (should show the real line count,
~16 lines) before running any test — a 0-line or missing file means the
symlink target is still wrong.

Same class of gotcha as the `.venv/` one (both are gitignored, both are
load-bearing for a worktree to run tests at all) — worth folding into the
same worktree-setup fix if/when someone touches that script again.
