---
name: A reviewer CHANGES_REQUESTED can target the AFS's reasoning, not the code
description: on a traceability-only extend (single decorator, zero test-logic change), a reviewer can still legitimately block on a flawed defect-relevance argument inside the AFS itself — route the fix-only round at re-investigating the claim live, not at rewording prose to sound consistent
type: feedback
---

## What happened (ELITEA-1800, issue #177, PR #626)

The implementation diff was as minimal as this pipeline gets: one additive
`@allure.issue(...)` decorator (4 lines) on a pre-existing, already-correct
test — a pure traceability fix, zero test-logic/selector/page-object change.
Easy to assume a diff this small can't draw a real CHANGES_REQUESTED.

It did. The fresh reviewer read the AFS's "GH#607 relevance check" section
(the analyst's argument for why a known truncation defect doesn't threaten
this case's assertions) and found it (a) stated the truncation direction
backwards — claimed the defect "keeps the newest ~100" when it actually
drops the newest and keeps the oldest — and (b) was internally
self-contradictory about whether the restored session was bounded to one
test run's messages or a shared, ever-growing, cross-run conversation (both
claims appeared in adjacent bullets of the same section).

## The lesson

1. **Route the fix at the analyst-authored *reasoning*, not just at
   implementer-authored *code*, when that's where the reviewer's finding
   actually lives.** I dispatched a fix-only implementer round rather than
   editing the AFS myself (AFS edits belong to the implementer's Phase 2
   "amend-in-PR" mechanism, same as any other AFS-drift correction) — but I
   was explicit in the dispatch that the ask was "establish the TRUE safety
   reasoning, don't just reword to sound consistent." That framing mattered:
   a superficial fix would have flipped the truncation-direction sentence
   and softened the session-size claim without ever checking whether the
   case's actual assertion (`final_count > restored_count`) survives real
   truncation.
2. **It didn't — by luck; it did by a specific, checkable mechanism**, and
   the fix-only round found and verified that mechanism live: the truncating
   `GET /conversation/{uuid}` only fires from `select_history_session()`;
   `send_message()`/`wait_for_response()` never re-fire it, so a follow-up
   message appends to the already-rendered (possibly-truncated) DOM instead
   of re-triggering a fresh truncating fetch. Both `restored_count` and
   `final_count` are therefore counts of the *same* view, so the relative
   delta survives truncation regardless of session size — proven by directly
   reproducing GH#607's real truncation against the actual referenced
   conversation (218 groups → restored to 47 → sent a follow-up → network
   capture showed zero re-fetch → count settled at 48; 48 > 47 held).
3. **The re-review (fresh session, full re-triangulation) independently
   reproduced the same experiment and got matching numbers** rather than
   trusting the fix-only round's write-up — this is what "not a rubber
   stamp" looks like in practice on a round-2 pass, not just re-reading the
   diff.

## Generalizes to

Any `extend-existing` AFS whose Gap-assertions/Known-Defects section makes a
claim about *why* a known defect doesn't threaten the case (not just *that*
it doesn't) is a claim a reviewer can and should adversarially check — even
when the code diff itself is trivially small and clearly correct. Small diff
≠ nothing to review. And the corresponding fix-only dispatch should ask for
the same standard: establish truth via live re-verification, not prose
polish that happens to read as internally consistent.
