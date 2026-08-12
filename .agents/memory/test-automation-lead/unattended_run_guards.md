---
name: Unattended sync/loop runs — guard by liveness and path overlap
description: The sync guard's three named conditions are examples of "a live agent is using this tree", not the test; decide with branch state, recency, ps aux and a path-overlap check, and apply the guard to the dev-server restart too.
type: feedback
---

## Rule

`sync-base-branches`' guard names three conditions (a merge in progress, uncommitted
testid work, a `.testid-pr` worktree). Read literally it both **misses** live work
and **trips on** every ordinary leftover. Its intent — never sync over someone's
in-flight work — is what you enforce. Run blindly, Part 1 is itself a clobbering
party against in-flight case work on the same repo.

**Before Part 1, in order:**

1. `git branch --show-current` in elitea-testing-public. A case branch instead of
   `automation/base` is an in-flight signal by itself.
2. If a case branch: `gh pr list --state open` for that exact branch + its
   `updatedAt`; `gh issue view <card>` for a "🔧 Factory works this card" claim and
   for any note of a *prior* collision (recurring symptom — same card hit twice).
3. **Recency, not presence.** `stat` mtimes on dirty files, `git log -1` on the
   branch. 10–19h stale ⇒ leftover: classify and land per Step 0. Changed within
   ~the last hour, or a literal `MERGE_HEAD` ⇒ live: stop and report.
4. **Ambiguous recency (minutes)?** `ps aux | grep -i claude` — a live PID attached
   to the tree is definitive where mtime cannot be.
5. **A live process is NOT an automatic skip.** `git fetch origin` then
   `git diff --name-only automation/base...origin/main`, compared against
   `git status --porcelain`. **Zero path overlap ⇒ the merge provably cannot touch
   their WIP** (git only rewrites a path whose merge result differs) — proceed, then
   re-verify the WIP byte-identical. Real overlap on *their* WIP ⇒ the blanket skip
   applies. Overlap on your OWN uncommitted deliverable ⇒ diff both sides;
   independent insertions merge cleanly once committed.
6. **The post-merge `pkill -f vite && npm run dev` restart is guarded too** — it
   drops a live session's Playwright/CDP attachment exactly like a bad checkout.
   Skip it, still run whatever verification is safe without it, and say in the
   report precisely what was skipped and why so a human can finish it.

**When skipping, file the tracking issue with the evidence** (branch, PR number +
state, card comment excerpt) rather than guessing at a merge. Retry next cycle.

## Related recoveries

- **An unexpected commit on your branch:** a concurrent run may have landed content
  there in good faith after judging it idle. Read the message and diff first.
  **Re-home the content to `automation/base` BEFORE resetting the branch ref**, and
  never `git branch -f` a branch that is any tree's checked-out HEAD.
- **Repeated identical `[Request interrupted by user for tool use]` with no partial
  output is usually not the user.** Check `git diff automation/base -- .claude/hooks/`
  — a stale SessionStart hook on an idle branch (the quadratic `escape_for_json`
  bash bug) blocks session start for minutes and surfaces as that exact message.
  Run this before telling the operator it's their doing.
- **`Blocked` reading "N sessions without the card leaving this loop's queue"** is
  the loop's own bookkeeping misreading correct inaction on a terminal `Ready` card
  — not a work blocker (contrast a real `Waiting on #N`). On pickup: re-verify the
  delivery (PR still MERGED, shared file changes additive-only, one test run,
  fresh promotability, TMS + closure record intact), re-confirm in a comment, move
  back to `Ready`. Never re-run the pipeline — that ships a duplicate PR.

## Seen 7×

- #716 (run, 2026-07-22) — 3 named conditions clear, tree on `tests/ELITEA-2132-…` with an open PR and an active factory claim; habit branch-check caught it.
- #712 (run 31) — dirty tree + unrelated case branch + an impl worktree, all 10–19h stale; recency said proceed, correctly.
- #724 (run) — `ps aux` found PID 13551 `claude --agent scout` alive ~2h50m; mtime alone was ambiguous. Dev-server restart skipped for the same reason.
- …plus 4 earlier occurrence(s) — full per-case detail in the source entries below.

See also: sync_guard_extends_beyond_the_3_literal_examples.md ·
sync_guard_process_liveness_check_and_dev_server_restart_is_also_guarded.md ·
mid_work_guard_needs_recency_not_just_dirty_tree_presence.md ·
unattended_sync_run_lands_content_on_idle_pr_branch.md ·
merge_safety_provable_via_path_overlap_check.md ·
stale_branch_sessionstart_hook_hang_mimics_user_interruption.md ·
loop_redispatch_on_terminal_ready_card_can_false_positive_block.md
