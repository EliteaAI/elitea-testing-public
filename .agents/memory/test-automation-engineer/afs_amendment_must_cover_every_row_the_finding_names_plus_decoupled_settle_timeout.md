---
name: AFS amendment must cover every row the finding names, plus a decoupled settle-timeout pattern
description: ELITEA-1877 fix round (PR #1001) — a docs(afs) amendment commit fixed the heading-row PROVENANCE but left the sibling row-item PROVENANCE at "needs-adding" even though both testids landed in the same add-data-testid pass; plus a reusable pattern for hardening a one-shot attribute read without regressing a caller's negative-path latency.
type: feedback
---

## Partial AFS amendment (reviewer Finding 1)

The prior implementer session's `docs(afs)` commit (`fc83143b`) amended the AFS's
Concrete Handles table for TWO testid findings discovered during Phase 2 explore
(`run-history-panel-heading` and `run-history-item-{id}`), and both testids did
land on `automation/testids` in the same `add-data-testid` pass (confirmed via
`git grep` on `origin/automation/testids` — SHAs `1a684045` and `8d25a19c`
respectively). But the commit only actually rewrote the HEADING row's PROVENANCE
column to the "added — Amendment (implementer exploration, `docs(afs)` commit)"
style; the ROW-ITEM row was left with the original "needs-adding" blocking-gap
text untouched — even though the implementer's own daily-log entry claimed
"amended the AFS in-place... to record BOTH findings."

**Lesson:** when a single amendment pass addresses N related findings in the
same AFS section, verify EACH row got the actual edit, not just that the
commit's diff touches the file and the prose narrates all N. A partial
application is invisible in a quick self-check ("I amended the AFS") but very
visible to a reviewer who reads row-by-row against the PR body's own claims (the
PR body listed BOTH SHAs; the AFS table only reflected one). Same family as
`afs_testid_can_name_a_real_but_wrong_component.md`'s addenda (declaring an
improvisation ≠ amending the AFS) — this is the sibling failure mode: amending
ONE instance of a repeated finding ≠ amending ALL instances.

**Fix mechanics:** mirror the row that WAS done correctly — same "Amendment
(implementer exploration, `docs(afs)` commit)" bold lead-in, same SHA-citation
style, same "on `automation/testids` (awaiting human promotion to `main`)"
PROVENANCE phrasing — rather than inventing new wording per row.

## Decoupled internal settle-timeout for a boolean state-read (reviewer Finding 3, nit)

A boolean "is this attribute true?" page-object method that needs
race-hardening against a one-shot `get_attribute()` read (same class as
`chat_css_generated_content_and_stale_sidebar_participant_count.md`'s
`data-has-icon` case) has a real tradeoff if you swap in
`expect(...).to_have_attribute()` naively: **the negative case (attribute
genuinely never becomes the target value) now costs the FULL caller-supplied
timeout**, because Playwright's `expect` only returns early on a MATCH, not on
a stable non-match. For a method called once per "should be true" row and once
per "should be false" row in the same test (this case's
`is_run_history_item_selected` — checked on both the clicked and non-clicked
row), that's a real, measurable regression (up to +timeout ms, e.g. +10s) for
zero added correctness when the current call sites are already safe by
construction.

**Pattern:** decouple two timeouts —
- the EXISTING `timeout` param keeps governing the element's own visibility
  wait (unrelated to the attribute race);
- a SEPARATE, short, INTERNAL settle timeout (`min(timeout, 2000)` here) governs
  the `expect(...).to_have_attribute(..., timeout=settle_timeout)` call, wrapped
  in `try/except AssertionError: return False`.

This gives real retry-safety for the genuine-race case (the attribute flip is a
synchronous React commit, not a network round trip, so 1-2s is generous
headroom) without taxing the already-correct negative-path call sites with the
caller's full external timeout. Worth reaching for whenever a reviewer's
"switch to the retrying idiom for consistency" nit would, if applied literally,
turn a query method's failure path into a full-timeout wait.
