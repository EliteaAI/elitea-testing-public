---
name: Purpose-built handle asserted visible-only, not the text it exists to prove
description: PR #696/ELITEA-2114 — a testid built specifically to route around a known defect and give access to a live-verified string was only checked for visibility, not content; the sibling assertion one block later (same case, same drift reason) does the stronger check. Also documents verifying a menu-item-count assertion against source (array-filter vs CSS-hide) rather than trusting the PR narrative.
type: feedback
---

## What happened

PR #696 (ELITEA-2114, chat conversation deletion) added `delete-confirm-title`
— a new testid on `BaseModal.jsx` via a `titleTestId` prop — specifically to
give a handle for the delete-confirmation dialog's title that doesn't depend
on the broken `#alert-dialog-title` wiring (bug #694). The AFS's own Concrete
Handles table recorded the live-verified text this element holds:
`"Delete confirmation"`.

The shipped test then did:
```python
expect(chat.delete_confirm_title).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
```
— visibility only. One block later, the SAME test asserts the dialog body's
exact text via `to_have_text(...)` for the identical reason (case text is
stale per #695, live text is documented, assert the live value per the
reverse-masking guard). The title assertion just... stopped at presence.

This is not defect-masking (no defect is being hidden) and it doesn't violate
the letter of the Coverage Map (the row honestly says "dialog appearance
asserted," doesn't claim text is checked) — but it's a real, cheap,
overlooked assertion-strength gap: a regression that blanked or changed the
dialog title would sail through green.

## The reusable check

When a PR narrates "we built testid X specifically to get a clean handle for
[value]" and/or the AFS's Concrete Handles table records a live-observed
string for that handle, grep the actual assertion on that handle. `to_be_visible()`
next to a sibling `to_have_text()` for the same reason, on the same dialog, in
the same test, is the tell — the infrastructure work (new prop, new testid,
live-verified string) was done, the assertion payoff wasn't collected.

## Secondary technique used this review, worth keeping

To verify a menu-item-count assertion (`item_count == 5`, not 7) wasn't
silently wrong because "hidden" items are still DOM-present (CSS
`display:none`, so `.count()` would over-count), traced the actual React
source rather than trusting the PR's explanation: `ConversationItem.jsx:251`
does `.filter(item => item.display !== 'none')` on the **array itself**
before it's ever passed to `DotMenu`/`BasicMenuItem` — the filtered-out items
never mount, so `.count()` on the testid prefix selector is counting real
absence, not visually-hidden presence. `DotMenu.jsx`'s own render path
(`splittedChildren.filter(item => item).map(...)`) only drops falsy entries,
doesn't re-implement the display filter — confirms the array passed in is
authoritative. Worth re-running this exact "is `display: 'none'` an
array-filter or a CSS-hide" check any time a menu/list count assertion
depends on a conditional item.
