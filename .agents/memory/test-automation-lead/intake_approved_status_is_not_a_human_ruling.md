---
name: A [FIX] card sitting in `Approved` was put there by the intake routine, not by a human
description: test_failure_intake.yml files cards straight into Approved (Todo only on mapping errors) — so Approved on a fresh [FIX] card carries no human judgement and cannot override a standing "dedupe, don't approve" instruction on the survivor
type: feedback
aliases: [approved is human-only exception, intake places cards in approved, fix card approved by routine, deprecated feature twin]
tags: [area/triage, area/board, type/lesson]
created: 2026-09-16
updated: 2026-09-16
---

## The trap

`.agents/profile.md` says `Approved` is HUMAN-ONLY, so a `[FIX]` card in `Approved` reads as
"a human looked at this and wants it worked". On #2332 (ELITEA-2036) that reading would have
collided with #2326's explicit line *"please dedupe those against #2319 rather than approving
them"* — and tempted me to treat the Approved status as a newer human decision overriding it.

It is not. `automation/routines/test_failure_intake.yml:1219`:
`'status': 'Todo' if has_mapping_errors else 'Approved'` — the routine itself places every
cleanly-mapped `[FIX]` card in `Approved`. Only a **comment** or a **label** on the card is a
human signal; the column is machine-set.

## The move

On a cross-run twin of a card that is `Blocked` on an unanswered `question`: `duplicate` label,
`Blocked` + `Waiting on <question>`, occurrence row on the question card, back-link on the
survivor. Re-verify the three facts fresh (spec identical main↔base, root-cause commit still an
ancestor of the deployed ref, question unanswered) — never copy the sibling's comment. ~8 min,
0 dispatches. Third twin gets the same treatment; only the question's answer changes anything.

Related: [[deprecated-feature-fix-cards]] · [[a_cross_run_fix_card_is_not_a_duplicate_filing]] ·
[[board_scan_for_the_elitea_id_is_the_cheapest_first_move]]
