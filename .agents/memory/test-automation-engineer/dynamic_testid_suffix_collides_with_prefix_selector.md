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
)
```

## The check that would have caught it before shipping

Before trusting a prefix-based `get_X_items()` idiom after adding ANY new
testid that shares its base string, print `.count()` on the prefix locator and
sanity-check it against the visible item count. A 3x–30x inflation is instant
and obvious; a `text_content()` timeout three steps later, on an unrelated
assertion, is not.

## Generalizes to

Any time a per-item testid gets NEW sibling-derived sub-testids (`${itemId}-X`)
AFTER a prefix-matching locator already exists for that item family — not
specific to hash-search or to this project's naming convention.
