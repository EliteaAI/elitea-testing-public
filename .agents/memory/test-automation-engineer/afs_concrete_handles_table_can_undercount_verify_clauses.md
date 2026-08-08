---
name: AFS Concrete Handles table can undercount Verify-clause targets
description: A case Verify clause can name a target with no row in the AFS's own Concrete Handles table — check every step's Verify text, not just the table
type: feedback
---

## What happened (ELITEA-1906, batch #1298)

The AFS's Concrete Handles table asked for exactly 2 new testids (Welcome
Message input, per-index Chat-starter input) and its own "Summary for the
implementer" line said "2 new testids needed". But case Step 9's Verify text
also required asserting **"the section header 'Chat starters:' is visible"**
— and that header had zero row in the table and zero existing testid in the
JSX. Writing that assertion the "easy" way (`page.get_by_text("Chat
starters:")`) would have been a bare-locator policy violation caught at
review; instead a 3rd testid (`generate-agent-review-starters-header`) had
to be added mid-implementation.

## The lesson

An AFS's Concrete Handles table is the analyst's best-effort inventory, not
a closed set. Before starting `add-data-testid` work (or writing any
assertion), walk every case step's **Verify** text line by line and ask "is
there a handle for this specific target?" — not just "does the table's row
count match my intuition of how much testid work this needs." A Verify
clause that names a UI text/section/label the table never mentions is a gap
the table itself won't surface by omission — you have to go looking for it.

## How to catch it early

When reading the AFS in Phase 1/2, for each step's Verify clause, mentally
tag it against a table row. Any Verify target with no tag is either (a)
already covered by an existing testid used elsewhere in the flow, or (b) a
gap to add via `add-data-testid` before you reach Phase 4. Catching it in
Phase 2 costs one extra JSX edit; catching it in Phase 4 costs a stalled
test with no compliant locator, and catching it at review costs a whole
fix round.

## Related

- `afs_is_a_work_order_not_gospel.md` — the general "verify each claim, don't
  treat the AFS as complete" principle this is a specific corollary of.
