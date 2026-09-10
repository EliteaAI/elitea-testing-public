---
name: Judging an identity-keyed settle — enumerate the slip-throughs, then check the explicit assert catches them
description: A two-assertion identity wait is reviewed by tabulating every wrong grid state against both assertions; the combination neither catches must be caught by the caller's own assert
type: feedback
aliases: [identity settle review, union locator to_have_count, multiset vs set review, terminal wait review, ELITEA-2363, "#2179"]
tags: [area/ui, type/review-technique]
created: 2026-09-10
updated: 2026-09-10
---

## The review technique

When a settle is expressed as N auto-retrying assertions over a collection's IDENTITY (rather than
its count), reading the docstring's claims is not a review. Build the table: every wrong grid state
× each assertion. The shape shipped in `AgentHubPage.wait_for_agent_card_ids()` (ELITEA-2363/#2179):

1. `expect(locator(<CSS union of AGENT_CARD_BY_ID.format(id) over the baseline's DISTINCT ids>))
   .to_have_count(len(expected_ids))`
2. `expect(locator(AGENT_CARD_PREFIX)).to_have_count(len(expected_ids))`

| Wrong state | (1) | (2) |
|---|---|---|
| card dropped | fails | fails |
| duplicate render dropped (id still present once) | **fails** | fails |
| extra card, id OUTSIDE baseline | passes | **fails** |
| extra card, id INSIDE baseline | **fails** | fails |
| one baseline card missing **+** one baseline id duplicated | **passes** | **passes** |

Only the last row slips through — and it is caught by the caller's own
`sorted(restored) == sorted(baseline)`. That is what makes the docstring's "both required, neither
sufficient" honest rather than decorative. **Always find the row that slips through and name where
it is caught.** If nowhere, the settle is the verdict and the assertion is theatre.

Note the union count is over DOM ELEMENTS, not over selectors, so de-duping the ids inside the
union (`sorted(set(...))`) is correct while comparing against the non-deduped `len(expected_ids)`
is also correct — 24 distinct id selectors match 27 elements. Check that arithmetic explicitly;
a `set()` on the wrong side of it is the exact defect this repair removed.

## Vacuity and stale-state reachability

Two questions, both cheap, both required for any settle (`.agents/testing.md` #1847/#2196/#2168):
can it be satisfied by the state the transition is LEAVING (here: the 6-card filtered set — no,
the union needs all 27), and can it be satisfied MID-transition (here: 12 of 27 — no)?

## The trap that is not in the code

An AFS can impose a **human sign-off rail** on a comparison change. `APPROVED` does not discharge
it — a reviewer is not the human, and no agent message is user consent. Verify the PR body carries
the declaration and say explicitly in the verdict that the rail is still open, or the lead merges
on an approval that was never authority for the change.

Related: [[a_settle_can_be_fragile_and_vacuous_at_once]] · [[passing_assertion_may_prove_nothing]]
