---
name: The cheapest promotion-gap proof is grepping the ASSERTION MESSAGE, not walking ancestry
description: Present on origin/main and absent on origin/automation/base means the repair already landed and rewrote that message — no repair commit, no call-path file list needed
type: technique
aliases: [promotion gap proof, message string grep, already fixed on base check, fix card 30 second triage]
tags: [area/triage, area/promotion, type/technique]
created: 2026-09-10
updated: 2026-09-10
---

## The move

`ancestry_check_is_the_first_move_on_a_fix_card.md` says scope the ancestry walk to the whole CALL
PATH (`-S"<symbol>"`), because a spec-only check lies (#2175). True — but there is a cheaper step
that comes **before** it, and it needs neither the repair commit nor the file list:

```bash
git grep -n "<assertion message quoted in the card>" origin/main -- automation/             # hit
git grep -n "<assertion message quoted in the card>" origin/automation/base -- automation/  # no hit
```

**Present on `main`, absent on `automation/base` ⇒ the repair already landed on base and rewrote that
message.** Done. You then identify the repair commit only to *name* it in the closure record, not to
reach the verdict.

Worked verbatim on #2180 (ELITEA-2024): the card quoted
`'Card elements (entity-card-name) should render again after switching to card view'`; one grep pair
settled it before a log was opened. `6855dc3f4` / PR #2148 (board #2118) had replaced that assertion.

## Why it beats the ancestry walk as the FIRST move

- **No call-path enumeration.** #2175's trap is that the repair lives in a page object, not the spec —
  the message grep is immune, because it searches the whole tree for the string the card itself quotes.
- **No commit identification.** You do not need to guess which commit or which symbol to `-S`.
- **The card supplies the input.** Every assertion-failure `[FIX]` card quotes its message verbatim.

## The even cheaper prior

A `[FIX]` card whose ELITEA-id already has a card in `Ready` is almost certainly the same red
re-detected. #2118 was in `Ready` the whole time #2180 was filed. Check the board first — but note
this is a **triage prior for the human**, not an intake bug: see
`a_cross_run_fix_card_is_not_a_duplicate_filing.md` for why a later-run card is a true re-detection
that no dedup key prevents.

## Limits

Only works when the repair CHANGED the message text. A repair that fixes a precondition while leaving
the assertion string untouched is invisible to this grep — fall back to the call-path ancestry walk.
