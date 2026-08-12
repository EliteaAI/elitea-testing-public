---
name: Recurring LocatorDescriptor bypass for card-name list locators
description: Implementers repeatedly fix/add multi-match card-name testid locators (entity-card-name, entity-card) via a raw string class-constant + inline page.locator() inside the method body instead of a class-level LocatorDescriptor(testid=...) — check this specifically on any list-page review
type: feedback
---

Seen twice now, same shape both times:

- **PR #537 (ELITEA-1974)** — `credentials_list_page.py` added `ENTITY_CARD_SELECTOR`/
  `ENTITY_CARD_NAME_SELECTOR` raw string constants + `page.locator()` for the static
  `entity-card`/`entity-card-name` testids, instead of `LocatorDescriptor`.
- **PR #545 (ELITEA-1869)** — `agents_list_page.py`'s `get_agent_card_names()` fix
  replaced a broken CSS selector with `ENTITY_CARD_NAME = '[data-testid="entity-card-name"]'`
  + `self.page.locator(self.ENTITY_CARD_NAME)` inline in the method body — same
  anti-pattern, different file.

Why it happens: implementers seem to reach for a raw constant + inline `page.locator()`
specifically for **multi-match "get all card names" style locators**, maybe out of an
assumption that `LocatorDescriptor` only fits single-element locators. It doesn't —
`LocatorDescriptor.__get__` resolves via `page.get_by_test_id(self.testid)`, which
returns a normal multi-match `Locator` supporting `.count()`/`.nth()`/`.all()` exactly
like a raw `page.locator(...)` would. Confirmed 36 existing `.count()`/`.nth()` call
sites elsewhere in the codebase already using `LocatorDescriptor` for lists — there's
no technical reason to bypass it.

The correct fix in both cases would have been a one-line class field:
```python
card_name = LocatorDescriptor(testid="entity-card-name", description="Entity card name")
```
then `cards = self.card_name` in the method body.

**Reviewer check going forward:** whenever a PR fixes/adds a card-name or card-list
locator (`get_*_card_names()`-style methods), grep the diff for
`self.page.locator(` inside a method body — that's the exact tell, distinct from a
`LocatorDescriptor` class field declared above `__init__`/methods. `.claude/rules/page-objects.md`
is explicit that locators live only as class-level fields, never constructed in method
bodies, and PR authors' own descriptions have twice overstated this as "brings it into
compliance with the testid-only policy" when it doesn't actually adopt the sanctioned
mechanism.
