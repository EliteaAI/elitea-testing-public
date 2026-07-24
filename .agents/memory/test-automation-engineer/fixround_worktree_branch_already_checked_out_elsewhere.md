---
name: Fix-round worktree targets a branch already checked out in the original implementer's worktree
description: A fix-round dispatch gets a brand-new isolated worktree, but the PR's branch is still checked out in the ORIGINAL implementer worktree (git worktree list shows both) — git refuses a second checkout of the same branch. Create a differently-named local branch from origin's tip and push it back onto the PR's actual branch name.
type: feedback
---

## The problem

`git checkout -b tests/ELITEA-XXXX-slug origin/tests/ELITEA-XXXX-slug` fails with
`fatal: 'tests/...' is already used by worktree at '<other-worktree-path>'` — the
original implementer's worktree (e.g. `wf_e44028a9-dec-111`) is still alive on disk
and still holds that branch checked out, even though its own dispatch finished and
the PR is already open. `git worktree list` (no `-C`, safe from within the new
worktree) shows every worktree + branch across the whole repo and confirms this.

## The fix

1. `git fetch origin` (fresh tip).
2. `git checkout -b fixround/<CASE-ID>-review-r1 origin/tests/<CASE-ID>-<slug>` — a
   **differently-named** local branch, tracking the remote PR branch. Naming
   convention observed across this project's other fix rounds:
   `fixround/<CASE-ID>-review-r1` (matches `fixround/ELITEA-2005-review-r1`,
   `fixround/ELITEA-1890-review-r1`, etc. — visible in `git worktree list` output).
3. Do the fix, commit normally.
4. `git push` alone fails (`upstream branch does not match current branch name`).
   Use `git push origin HEAD:tests/<CASE-ID>-<slug>` — pushes this worktree's
   commits as a fast-forward onto the SAME remote branch the PR already tracks,
   updating the PR without opening a new one.
5. Post the fix-round summary as a **PR comment** (not a tracking-issue work-log
   comment — confirmed by checking an already-completed fix round's tracking issue,
   e.g. issue #442/ELITEA-2005, which has exactly ONE comment total, predating its
   own fix round; the fix-round narrative lives only on the PR).

## Also re-confirmed same session (ELITEA-2021 fix round, 2026-07-24)

- A brand-new isolated worktree has **zero filesystem path** to a sibling repo like
  `../EliteaUI` at all (not just git-blocked — the relative path literally doesn't
  resolve, since the worktree sits nested under
  `<repo>/.claude/worktrees/<name>/`). If a prior round's finding was "JSX edits are
  uncommitted in the shared tree, only this session's git is blocked," re-verify
  the actual remote state via `gh api repos/<org>/<repo>/contents/<path>?ref=<branch>`
  (hits GitHub directly, no local clone needed) rather than assuming nothing changed.
- The shared local dev server (`http://localhost:5173`) stays reachable via plain
  `curl`/Playwright from a new isolated worktree even though the worktree can't
  reach `../EliteaUI`'s filesystem — it's a separate long-running process on a
  network port, not something worktree git-isolation touches. So "re-run the spec
  green once" is still possible and meaningful even when a testid gap is still
  unresolved upstream — it re-confirms the shared tree hasn't been reset since the
  last round, it doesn't resolve the gap itself.
- `env -u GITHUB_TOKEN gh pr comment ...` can trip the same worktree-isolation
  guard as `env -u GITHUB_TOKEN gh pr create --base ...` (memory:
  `isolated_worktree_cross_repo_git_block_and_env_test_symlink_gap.md`). Checked
  identity both ways this round (`gh api user --jq '.login'` plain vs
  `GITHUB_TOKEN= gh api user --jq '.login'`) — both returned the correct keyring
  account (`bermudas`) even though `GITHUB_TOKEN` (a real `ghp_...` token) IS set in
  the shell env, meaning `gh`'s own stored auth took priority over the env var in
  this environment. Plain (unprefixed) `gh pr comment` was safe here — but CHECK
  identity with `gh api user --jq '.login'` first each time rather than assuming;
  this could differ on a different machine/session.
