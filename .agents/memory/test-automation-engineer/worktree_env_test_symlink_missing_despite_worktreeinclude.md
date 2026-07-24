---
name: Worktree env.test symlink missing despite .worktreeinclude
description: An isolated implementer worktree can be provisioned without automation/.env.test even though .worktreeinclude lists it — recreate the symlink by hand with an ABSOLUTE target, since relative-depth from the main clone doesn't hold under .claude/worktrees/<name>/automation/.
type: feedback
---

Hit during ELITEA-1937 fix round R1 (worktree
`.claude/worktrees/wf_e44028a9-dec-57`). `pytest` failed every test
immediately with `Login failed: Invalid URL '': No scheme supplied` — this is
`config.py`'s `elitea_url: str = ""` default firing because the pydantic-
settings `env_file` (`automation/.env.test`) didn't exist in this worktree.

**Root cause:** `.worktreeinclude` (repo root) lists `automation/.env.test`
(and `.env`, `**/.env*`) as paths the worktree-provisioning step should copy
in from the main clone — same mechanism that fixed the `.venv/` stall
(commit a2d857a3). In this worktree, `.venv/` (207M) WAS copied correctly,
but `automation/.env.test` was not — `ls automation/.env.test` → "No such
file or directory", and no `.env`/`.env.test` anywhere in the worktree tree
(`find . -maxdepth 3 -iname "*.env*"` found only the tracked
`.env.test.example`). Didn't root-cause WHY the copy step skipped this one
file specifically (possibly a timing/ordering issue, possibly this worktree
predates a `.worktreeinclude` update) — flagging the gap rather than
guessing further, per the workflow's honesty-over-speculation stance.

**Fix applied:** recreated the symlink by hand —
```bash
cd automation
ln -s "/Users/Alexander_Bychinskiy/Library/CloudStorage/OneDrive-EPAM/Github/EliteaAutomationFactory/.env.test" .env.test
```
**Use an ABSOLUTE path, not the main-repo's relative `../../.env.test`.** The
main clone's `automation/.env.test` sits 2 levels below the workspace root
(`elitea-testing-public/automation/` → `../../.env.test` reaches
`EliteaAutomationFactory/.env.test` correctly). An implementer worktree's
`automation/` sits under `elitea-testing-public/.claude/worktrees/<name>/automation/`
— 5 levels below the workspace root — so copying the main repo's relative
symlink target verbatim resolves to the wrong place (inside
`.claude/worktrees/`, not the workspace root). Confirm depth with `pwd` before
choosing a relative target, or just use an absolute path (safer, and this
file is gitignored/worktree-local anyway so portability across machines
isn't a concern within one session).

**Diagnostic signal to recognize this fast next time:** any pytest run in a
worktree that fails ALL tests instantly (not slow, not flaky) with a URL-
parsing error naming an empty string is almost certainly a missing/broken
`.env.test`, not a real product or test bug — check
`ls automation/.env.test` before investigating further.
