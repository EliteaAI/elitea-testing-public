---
name: A shared diagnostic helper covers CALL SITES, not endpoints — check the one your spec depends on
description: FIX #2078's _expect_applications_response was wired to 4 /public_applications/ sites and missed the /agent_categories/ await, which was the oracle for a different spec
type: feedback
aliases: [diagnostic wrapper gap, expect_response bare timeout, one method away, categories await]
tags: [area/triage, area/page-objects, type/lesson]
created: 2026-09-10
updated: 2026-09-10
---

## The shape

A previous card (#2078) diagnosed that a bare `expect_response` timeout "names only
the predicate's source location" — the shape that, per ledger entries #2074/#2076,
named the WRONG subsystem and cost a full session. Its fix added
`_expect_applications_response`, a recorder that reports what the endpoint family
actually returned while the wait was pending.

It was wired to the **four `/public_applications/` call sites**. The Catalog page
also awaits **`/agent_categories/`** — same `expect_response`-around-`navigate()`
shape, same 45 s budget, raw and undiagnosed. That await is the oracle for
`test_empty_state.py`'s whole filter-rail assertion.

**A fix that lands "on the helper" is not a fix that lands "on the hazard".** Ask
which *endpoints* the hazard applies to, then which call sites got the treatment.
The delta is where the next session gets burned.

## How it surfaced (the #2168 heuristic, second consecutive hit)

The card was a clean promotion gap: `main` still had the hardcoded
`assert chip_count == 11`, `automation/base` had the derived version, verified 3/3
green on DEV. The obvious move is a paperwork closure.

Q1 of `a_promotion_gap_fix_card_can_still_hide_real_work.md` — *did another test in
that same CI job fail on a mechanism that also exists on my spec's path?* — is what
found the work. The `agent_hub` job had **three** failures, not the one the card
named, and the middle one (`navigate_and_capture_applications`, `expect_response`
15 000 ms, `agent_hub_page.py:575`) was my spec's Step 1 shape exactly.

**Read the whole job log, not your card's test.** The intake pipeline files one card
per test; the *correlation between them* is not in any card and is where the real
finding lives. Two cards in a row now (#2168, #2169) turned from paperwork into real
repairs on that one question.

## Also: a status-filtered response predicate hides the failure

`_is_categories_response` required `response.status == 200`. A non-200 therefore
never matched, so the wait burned its full 45 s and reported nothing — while the
sibling predicate (no status filter) failed fast and honestly. Measured on DEV:
45.05 s blind timeout vs 7.37 s naming status + URL.

But dropping the filter has a real cost the reviewer caught and I had not seen:
`expect_response` fires for **redirect responses**, and EliteaUI's `fetchBaseQuery.fetchFn`
follows a forward-auth 302 and re-fetches. So an unfiltered predicate lets a 302 win
the wait and hard-fails a run that used to survive a re-auth. Correct shape is
`and not (300 <= response.status < 400)` — exclude 3xx on the predicate, never
`redirected_from`, and let the recorder (which has no status filter) preserve the
diagnostic. See qa-engineer's `unfiltered_response_predicate_matches_redirects.md`.

Related: [[a_promotion_gap_fix_card_can_still_hide_real_work]] ·
[[ci_red_check_base_for_an_existing_fix_first]]
