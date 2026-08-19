---
name: Dynamic testid suffix collides with sibling prefix selector
description: Deriving a child testid as `${itemTestId}-suffix` makes it match any `^=` prefix selector already scoped to `itemTestId`'s base string, corrupting count-based item locators
type: feedback
---

## The trap

A common dynamic-testid pattern (`.agents/testing.md` § Locator policy) derives
a per-card testid from a stable base: `chat-hash-search-item-{project_id}_{id}`.
When you then need to disambiguate CONTENT inside that card (a type subtitle, an
icon, a state chip) and derive THOSE testids the same way —
`` `${testId}-type`, `${testId}-icon`, `${testId}-public-label` `` — you've just
created three new elements whose `data-testid` ALSO starts with the literal
`chat-hash-search-item-` prefix.

If the page object already has a `[data-testid^="chat-hash-search-item-"]`
PREFIX selector (the standard "count all items" idiom, e.g.
`get_hash_search_items()`), that selector now matches the nested sub-elements
too — not just the outer cards. On live verification (ELITEA-2206, fix round 1,
2026-08-19) this inflated a ~6-card result set to **188 "items"**, corrupting
every index-based `.nth(i)` lookup and causing a `text_content()` timeout in a
totally unrelated step (Step 2/3 subtitle read), because `items.nth(0)` and
`items.nth(1)` were no longer "card 0" and "card 1" — they were "card 0" and
"card 0's own `-icon` div".

## The fix

Add a `:not()` exclusion for every known child suffix to the prefix selector —
still testid-exact-match only, still a compliant class-level constant:

```python
HASH_SEARCH_ITEM_PREFIX = (
    '[data-testid^="chat-hash-search-item-"]'
    ':not([data-testid$="-type"])'
    ':not([data-testid$="-icon"])'
    ':not([data-testid$="-public-label"])'
    ':not([data-testid$="-name"])'
)
```

## CONFIRMED RECURRENCE (ELITEA-2208/2470 implementation, 2026-08-19)

This EXACT trap fired again on the SAME constant, same day this entry was
first written. The ELITEA-2207/2469 unit (implemented immediately before
this one, same session) added `HASH_SEARCH_ITEM_NAME = '[data-testid="{}-name"]'`
for its own composer-chip/popover-row name assertion — a perfectly
reasonable, correctly-named sub-testid — but did NOT add a matching
`:not([data-testid$="-name"])` exclusion to `HASH_SEARCH_ITEM_PREFIX`
alongside it, even though the sibling `-type`/`-icon`/`-public-label`
exclusions (added for the exact same reason, days earlier) sat two lines
above the new testid's own definition in the same file.

**Why the agent-scoped test that added it never caught its own gap:** its
`next(...)` scan for the first AGENT-type card happened to match at index
0 (the doubled-count "card, card's-own-name-child, card, ..." sequence
means every real card is now an EVEN index) — so the loop never advanced
into an ODD index (a `-name` leaf) that would have raised the
`text_content()` timeout. The bug shipped green because the specific test
that introduced it got lucky on ordering; the NEXT test that scans past
index 0 (a pipeline-scoped search, since the first card wasn't pipeline-
type) hit it immediately.

**The sharpened rule:** adding a new `${testId}-suffix` sub-testid to an
item family is not complete until the SAME commit also updates every
`^=`-prefix `:not()` exclusion list for that family — grep
`HASH_SEARCH_ITEM_PREFIX` (or the equivalent for whatever family you're
touching) in the SAME diff, not "I'll add it if a test fails." A test that
happens to select index 0 will not catch a missing exclusion; only a test
that must skip past index 0 will — and you don't control which case gets
written next.

## The check that would have caught it before shipping

Before trusting a prefix-based `get_X_items()` idiom after adding ANY new
testid that shares its base string, print `.count()` on the prefix locator and
sanity-check it against the visible item count. A 3x–30x inflation is instant
and obvious; a `text_content()` timeout three steps later, on an unrelated
assertion, is not. Even better: grep the prefix constant's OWN definition in
the same PR that adds a new derived sub-testid, and update its `:not()` list
in the same commit — don't wait for a future test to surface the gap.

## Generalizes to

Any time a per-item testid gets NEW sibling-derived sub-testids (`${itemId}-X`)
AFTER a prefix-matching locator already exists for that item family — not
specific to hash-search or to this project's naming convention. Confirmed
twice now on the exact same constant within one session — treat "did I
update the sibling exclusion list" as a standing checklist item whenever you
add a testid of the shape `${existingTestId}-<suffix>`.
