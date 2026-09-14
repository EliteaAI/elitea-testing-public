---
name: A human hotfix on main can half-execute an open question — merge it, don't extend it, don't revert it
description: When a human ratifies one side of an open question by committing directly to main, the sync brings it to base as-is; the factory neither completes the option nor reverts it — it measures the resulting split and routes it back to the question card
type: feedback
aliases: [reverse promotion gap, main ahead of base, human commit on main, half-executed decision, localhost red DEV green, testid value split, chat-participant-row]
tags: [area/triage, area/sync, type/lesson]
created: 2026-09-14
updated: 2026-09-14
---

## The situation (#2279, ELITEA-1793, 3rd [FIX] card)

#2142 parked on question #2167: EliteaUI `main` had changed the `chat-participant-row-*` testid VALUE
(bare id) while `automation/testids` kept ours (composite). Options: (A) UI team restores composite on
main; (B) ratify bare-id in the page objects + drop our re-add on the integration branch.

A human answered by ACTION, not by comment on #2167: committed `f5d23743e` straight to `main`
(`remove_agent_participant()` → bare id, 1 of 3 affected methods), closed #2142, AND filed
elitea_issues#6621 asking the UI team for option (A). Both directions in flight at once.

## Two traps this creates

1. **Reverse promotion gap.** `main` was 8 ahead of `automation/base`. The sync merge CONFLICTED on
   exactly that hunk (base had evolved the method). Resolving for base would make the NEXT
   `automation/base → main` promotion silently revert a human's `main` commit. Ruling: on a hunk a
   human touched on `main`, **main wins**; keep base's signature/extras around it.
2. **The split just flips.** Page object now matches `main`'s value; the integration branch still
   renders ours ⇒ the spec is GREEN on DEV 3/3 and RED on localhost 3/3, same commit, same hour. A
   "fix" on either side alone flips which environment is red — it is not a defect to repair, it is
   the unanswered question made concrete.

## The move

- Merge the human fix to base as-is (dispatched — conflicts are never mine). Do NOT complete the
  option (convert the other methods / drop the re-add) and do NOT revert — both are the human's call.
- Resolve the integration-branch conflict by § Divergence rule bullet 1 when main's change is purely
  structural (check `diff -w :1: :3:` is empty) — value question stays with the card.
- Gate on the environment the [FIX] card is for (DEV) AND run one localhost control; post the
  two-row table on the question card with the now-concrete cost of each option. Card → Ready
  (DoD met on DEV); nothing parked; no new question (dedup: the card exists).
- Note the loose ends the half-execution leaves (dead param, sibling methods, stale AFS § Blocked
  Steps) on the question card, not on the [FIX] card.

Related: [[a_fix_card_can_have_no_work_in_it]] · [[ancestry_check_is_the_first_move_on_a_fix_card]] ·
[[no_edit_guardrail_repo_agnostic]] · [[the_devenv_plugin_is_the_factory_safe_dev_gate]]
