---
name: Promote a base-only repair to main by cherry-pick (recipe + traps)
description: How to build a main-targeted branch carrying one automation/base repair — strip memory hunks, port base-only page-object deps verbatim, prove the diff, gate on DEV
type: feedback
aliases: [promote to main, cherry-pick to main, promotion gap fix, main-targeted branch, open_first_agent port]
tags: [area/git, type/recipe]
created: 2026-09-15
updated: 2026-09-15
---

## When

A human has authorised a test-repo-only repair to go to `main` by PR (the one
sanctioned exception to "never PR main"). You build the branch; the lead opens
and merges the PR. Worked instance: ELITEA-1869 / #2145, `0ac4d4a50` → `324fabc487`.

## Recipe

1. `git fetch origin && git checkout -b tests/<CASE>-promote-to-main origin/main`
   — **never pipe this command** (`| tail`) and then `&&` the next step: the pipe
   returns tail's rc, a refused checkout is swallowed, and the cherry-pick runs on
   whatever branch you were on (it happened; recovered by path-restoring the 4
   conflicted files only).
2. `git cherry-pick -n <squash-sha>`. Expect conflicts ONLY in `.agents/memory/**`
   (main lags base by hundreds of memory commits). Drop every memory hunk by path:
   `git reset HEAD -- .agents/memory/ && git checkout HEAD -- <UU files> && rm <A/DU files>`.
   Memory is base's source of truth; it never rides to main.
3. **Enumerate every symbol the spec calls** (page-object methods, class fields,
   utils) and `git grep` each on `origin/main`. A base-only dependency (here
   `AgentsListPage.open_first_agent`, added by an unrelated batch) is ported
   **verbatim** — same position, docstring included, plus only the imports it needs.
   Prove it with a Python substring check against `git show origin/automation/base:<file>`.
4. Proofs to paste: `git diff origin/automation/base -- <spec>` empty; `git diff
   origin/main --stat` lists only the expected files; auto-merged page-object hunk
   lines (`grep '^[+-]'`) byte-identical to `git show <sha> -- <file>`.
5. `pytest --collect-only -q <node-id>` on the branch; ruff on the touched files
   compared against the SAME files at `origin/main` — only pre-existing findings allowed.
6. Gate on DEV with the detached `trap`-restore script
   ([[env_test_is_a_symlink_dev_swap_recipe]]); classify any red per
   [[dev_page_goto_flake_is_a_precondition]]. A short wall clock (22 s) is fine —
   prove DEV was hit from the allure containers: `_browser_cookies` / `auth_state`
   take seconds (0 s on localhost) and the cleanup fixtures run (skipped on localhost).
7. Commit by exact path, push, **no PR, no merge**. Return the tree to
   `automation/base`.

## Dirty-tree trap

The lead's uncommitted *tracked* memory files block the checkout when main holds
older versions. Park exactly those with `git stash push -- <paths>` (back them up
to /tmp first), pop on return, and `diff` the restored working-tree diff against
the backup. Report it — never `stash -u`, never `checkout -- .`.

Related: [[websocket_frame_collector_not_on_main]] · [[triple_dot_diff_hides_uncommitted_changes_when_head_equals_base]]
