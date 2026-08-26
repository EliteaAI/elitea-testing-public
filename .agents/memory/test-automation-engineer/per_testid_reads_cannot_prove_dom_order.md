---
name: Per-testid reads cannot prove DOM order
description: A helper that resolves each element by its own testid and returns caller order is blind to ordering — use a CSS union (document order) instead
type: feedback
aliases: [column order, DOM order assertion, order assertion blind spot, testid loop order]
tags: [area/locators, type/anti-pattern]
created: 2026-08-26
updated: 2026-08-26
---

## The anti-pattern

Under the testid-only locator policy the obvious way to read a list of labels is
one query per element:

```python
def column_header_texts(self, fields):
    return [self.column_header(f).inner_text().strip() for f in fields]   # BLIND to order
```

The caller then writes `assert rendered == EXPECTED_LABELS` and the assertion
message says "in DOM order". **It is not an order assertion.** The result is the
*argument* order relabelled — swap the columns in the product and it still
passes. This shipped in ELITEA-2255 (Notifications Center) and was caught at
review, fix-round 1 (PR #1783).

It generalises past columns: any "in this order" expectation read via N
per-testid lookups (table columns, nav items, tabs, toolbar buttons, list rows)
has the same hole.

## The fix — one CSS union, document order

Playwright matches plain CSS with `querySelectorAll` semantics, so a
comma-joined union returns its matches in **document order** and the argument
order cannot leak in:

```python
union = ", ".join(self.NOTIFICATION_COLUMN_HEADER.format(f) for f in fields)
headers = self.page.locator(union)
headers.first.wait_for(state="visible", timeout=timeout)
return [t.strip() for t in headers.all_inner_texts()]
```

Locator-policy clean: the union is built from an UPPER_CASE class constant whose
definition is a `[data-testid="…"]` template, so the reviewer's mechanical grep
passes on the one-hop rule. **No new testid and no scoped-parent testid are
needed** — which is why this beats the tempting alternative of adding a
container testid to a shared component just to scope a `[data-testid^=` prefix
match.

Verified live 2026-08-26 against localhost:5173.

## Sibling shape that is already correct

`get_rendered_row_ids()` reads row ids via `locator(...).evaluate_all(...)` —
`evaluate_all` also yields document order, so that one was honest. Reach for
`.all_inner_texts()` / `.evaluate_all()` when order matters, never a Python loop
over per-element queries.

## Pin it

Order guarantees are invisible at the call site, so a later "simplification"
back to the loop reads identically. Pin the union shape with a unit test using a
fake page — `automation/tests/unit/test_notification_column_header_dom_order.py`
asserts (a) exactly one query is issued and (b) a *reversed* argument list still
returns DOM order. Red-green verified against the pre-fix body.

Related: [[delete_entity_button_testid_lands_on_wrapper_span]]
