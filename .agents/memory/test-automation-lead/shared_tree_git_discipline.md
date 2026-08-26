---
name: Shared working tree — git discipline
description: All factory sessions, their subagents, AND other concurrent conversations share one physical git tree; reset --hard, bare checkouts and cross-branch merges silently destroy uncommitted work. Worktrees are BANNED as the remedy — commit/stash, verify branch before every load-bearing step.
type: feedback
---

## Rule

One physical tree, many actors — including **other top-level conversations** you
cannot see from inside this one. Any destructive or branch-moving git command can
silently destroy another actor's uncommitted work (usually `.agents/memory/**`
writes a subagent just made; `reset --hard` leaves untracked NEW files behind, so
the damage looks partial and gets missed).

- **Never** `git reset --hard` / `checkout -f` / `git clean` in the shared tree.
  No stash, no reflog, unrecoverable.
- **Worktrees are NOT the fix.** Banned by operator ruling 2026-07-24
  (`.agents/workflow.md` § No git worktrees, `.agents/role-overrides.md`). Three
  earlier entries prescribing `git worktree add` for the merge-gate checkout are
  **superseded and deleted** — do not re-derive that fix. Read other branches with
  `git show <branch>:<path>`, `git diff <branch>...HEAD`,
  `git grep <id> origin/main -- src/`.
- **Remedy:** `git status --porcelain` **alone**, read it, then commit or stash
  foreign work (never discard) before switching. Undo only your own bad commit with
  a **mixed** `git reset HEAD~1` — it leaves other actors' working-tree diffs intact.
- **Never chain a verification command with the destructive action that depends on
  it** in one Bash call — the output arrives too late to gate anything.
- **Re-verify `git branch --show-current` immediately before every load-bearing
  step** (merge gate, commit, push, branch-dependent read) and after any dispatch
  longer than ~a minute. Not once at session start.
- **A plain `git checkout <branch>` is lossy too.** After landing memory on
  `automation/base` and switching back, the feature branch's older copy silently
  replaces it and the next subagent appends onto stale content. Stay on
  `automation/base` for the accumulation phase, or re-check
  `git diff automation/base -- <path>` after switching. A refused checkout ("local
  changes would be overwritten") is git catching the divergence — reconcile by hand
  (`git show <branch>:<path>` + splice), never `-f` or stash-around it.
- **Memory commits land on `automation/base`, never the PR branch.** Re-check
  `gh pr view --json mergeable` AND `gh pr diff --name-only` immediately before
  `gh pr merge` — a memory-landing commit can conflict an open PR or leak into its
  diff. `.agents/memory/**`-only conflicts are yours to splice (keep both entries,
  chronological order); anything under `automation/**` / `test-specs/**` goes back
  to the implementer. Before discarding leaked files, diff each against
  `automation/base` — a "-" line means real content would be destroyed.

## Seen 11×

- #83/ELITEA-1963 — own `reset --hard` before the gate wiped implementer + reviewer memory.
- #71/ELITEA-1897 — identical command, 2nd time, same "staleness paranoia" trigger.
- #293/ELITEA-2090/PR#682 — 3rd time; destroyed the reviewer's just-written index line.
- #1399/wave-01 (2026-08-12) — different shape: a routine `git add -f && commit && push
  origin automation/base` for campaign-card docs landed on whatever branch the workflow's
  own subagents had checked out at that instant (a live case branch, mid fix-round) —
  because I trusted my OWN last branch check from several tool calls earlier instead of
  re-verifying immediately before this specific commit. Caught by re-checking
  `git branch --show-current` right after; recovered clean with `git reset HEAD~1`
  (mixed) — the implementer's uncommitted WIP on that branch was completely untouched
  (unrelated files). Lesson stated in the rule above ("not once at session start") — this
  is the case that shows it also means "not once a few tool calls ago, either."
- …plus 7 earlier occurrence(s) — full per-case detail in the source entries below.

See also: orchestrator_git_reset_hard_clobbers_subagent_memory.md ·
subagent_git_checkout_can_clobber_sibling_session_memory.md ·
shared_tree_memory_landing_can_get_silently_reverted_by_plain_branch_checkout.md ·
shared_tree_branch_changed_by_concurrent_session_mid_dispatch.md ·
verify_shared_tree_branch_before_every_merge_gate.md ·
concurrent_subagent_memory_commits_can_cause_a_real_pr_conflict.md ·
implementer_r2_merge_can_leak_memory_files_into_pr_diff.md

Deleted 2026-07-30 (worktree remedy superseded by the 2026-07-24 ban):
git_reset_hard_incident_recurred_use_worktree.md ·
git_reset_hard_third_recurrence_worktree_now_mandatory.md ·
gitignored_worktree_reports_archive_explains_missing_junit_cross_check.md
