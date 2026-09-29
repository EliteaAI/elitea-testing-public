---
name: A squash/cherry-pick-promoted fix still shows as UNPROMOTED in git log — only the content diff is decisive
description: git log main..base -- <file> keeps listing the base-side SHA after a cherry-pick promotion, so it reads "not on main" while the file is byte-identical; diff the content, never count the log
type: feedback
aliases: [log says not promoted, cherry-pick breaks ancestry, squash hides promotion, content diff vs git log, re-promoting an already-promoted fix, false promotion gap]
tags: [area/triage, area/promotion, type/process]
created: 2026-09-29
updated: 2026-09-29
---

## The trap (#2274, ELITEA-1901)

The repair was authored on base as `76cc6fa1f` (PR #2125) and promoted to `main` as a
**`cherry-pick -x` squash-merged** to `d89cb6018` (PR #2288). Two commands, opposite answers:

```bash
git log  origin/main..origin/automation/base --oneline -- <spec>   # lists 76cc6fa1 → "NOT on main"
git diff origin/main origin/automation/base  --  <spec> | wc -l    # 0 → byte-identical, IS on main
```

The log is not wrong, it is answering a different question: `76cc6fa1` genuinely is not an ancestor
of `main`, because the promotion rewrote it into a new SHA. **Ancestry tracks commits; a promotion
gap is about content.**

## Why it matters more than it sounds

Believing the log here means concluding "promotion gap, needs promoting" for a fix that is already
on `main` — so the delivery would be a redundant promotion PR on top of a repair CI is already
running. The failure mode is doing work, not skipping it, which is why no gate catches it.

This is the mirror image of the #2175 trap: there, a spec-scoped log was **empty** and falsely said
"no repair exists" (the repair was in a page object on the call path). Here a spec-scoped log is
**non-empty** and falsely says "repair not promoted". A log over a squash-merging repo cannot
answer either question reliably.

## The order to run

1. `git grep -nF '<failure message>' origin/main -- automation/` — 0 hits ⇒ already on main
   (cheapest; needs no SHA — see [[a_fix_card_can_be_filed_after_its_fix_already_merged_to_main]]).
2. `git diff origin/main origin/automation/base -- <path> | wc -l` — 0 ⇒ content identical.
3. `git merge-base --is-ancestor <fix-sha> <ci-commit>` — NO ⇒ the run predates the fix, which is
   what makes the card a re-detection rather than a regression.
4. Only then `git log` — to **name** the promotion PR, never to decide whether one happened.

Related: [[ancestry_check_is_the_first_move_on_a_fix_card]] · [[a_fix_card_can_be_filed_after_its_fix_already_merged_to_main]] · [[a_fix_card_can_have_no_work_in_it]] · [[a_promotion_gap_fix_card_can_still_hide_real_work]]
