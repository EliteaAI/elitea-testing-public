---
name: A positional assertion over a sorted list is unverifiable unless the sort key has a tie-breaker
description: Ordering can differ between two identical fetches with NO data change, so a positional compare fails with zero mutations; check for tie groups before keeping or sanctioning one
type: feedback
aliases: [positional assertion, order assertion, tie group, tie-breaker, sorted list flake, trending order, ELITEA-2363, ordering nondeterminism]
tags: [area/test-repair, area/triage, type/flake]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

A before/after comparison of a rendered list (`assert after == before`) asserts **membership,
multiplicity AND position** — but the case usually only claims the first two, and position is
the one that breaks. The obvious diagnosis when it goes red is "shared mutable data changed" —
and that can be true *and still not be the whole cause*.

**Ordering can differ between two identical fetches seconds apart with no data change at all**,
whenever the sort key has ties and the backend declares no tie-breaker (or the window the sort
ranks over is moving). Displayed values are equal; positions are not.

## Worked case — ELITEA-2363 (#2179/#2188), CI run 34436416962

The accepted account was "one like landed mid-run → two symptoms". The CI log carried **two
independent deltas**, and only the first fitted it:

1. `...TB0` → `...TB1` — a real like, on an agent at index 20 with **1** like.
2. Indices 3–5 **rotated** — three agents **all showing `4` likes in BOTH snapshots**, inside the
   leading `9,7,5,4,4,4` likes-desc block (the Trending section, `sort_by: likes, sort_order: desc`).

Delta 2 cannot be caused by delta 1: no counter among those three changed, and the agent that
gained a like sits far below that block's floor. So the positional assertion **would have gone red
with zero like events**. The analyst's supporting measurement — "Trending 6/6 identical including
inside every tie group" — is consistent with an instability that needs two fetches to straddle a
boundary; six clean observations did not disprove it.

## The check, before keeping or sanctioning any positional claim

1. **Does the case text claim order at all?** `grep -iE 'order|position|sequence|sort|first|top of'`
   the case file. Usually 0 hits — then position is an over-claim the *implementation* added, and
   dropping it removes nothing the case verifies (that drop is still a human sign-off, § below).
2. **Is the list sorted on a key with ties?** Ties + no declared tie-breaker = order is not a
   function of anything the test controls or can observe. A positional assert there cannot
   distinguish a real regression from normal traffic — it is not a weak assertion, it is an
   **unverifiable** one.
3. **Is the sort key externally mutable, or the window moving?** Likes, recency, trend windows:
   all three make position a moving target between two fetches of the same data.

Compare as a **sorted multiset**, never `set()` — a grid legitimately renders the same entity
twice (Trending + its category: 27 cards / 24 distinct ids), and `set()` stops detecting a
dropped duplicate render.

## Two rails this touches

- **Dropping a positional claim changes WHAT is verified** — human sign-off, not an agent
  declaration (`.agents/role-overrides.md` § declared-improvisation protocol, ceiling 1).
  Reviewer `APPROVED` does not discharge it.
- **If the team wants ordering covered at all, the tie-breaker question is a prerequisite**, not a
  detail: a new case asserting an order that has no tie-breaker is born flaky.

Related: [[a_green_gate_does_not_prove_an_assertion_is_sound]] · [[a_sanctioned_red_can_be_manufactured_by_its_own_precondition]] · [[hardcoded_count_drift_is_rarely_fixed_by_bumping_the_number]]
