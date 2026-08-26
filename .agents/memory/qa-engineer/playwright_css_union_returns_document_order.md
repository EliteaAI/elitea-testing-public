---
name: Playwright comma-joined CSS unions return matches in document order
description: A `A, B, C` locator is routed through Playwright's `is` engine and sorted with sortInDOMOrder — so a union read IS a valid DOM-order assertion
type: reference
aliases: [css union order, dom order assertion, column order assertion, sortInDOMOrder]
tags: [area/playwright, type/verified]
created: 2026-08-26
updated: 2026-08-26
---

## The fact

`page.locator('[data-testid="a"], [data-testid="b"], [data-testid="c"]')` returns its
matches in **document order**, regardless of how the branches were ordered in the
selector string. Verified 2026-08-26 by reading the bundled driver
(`.venv/.../playwright/driver/package/lib/coreBundle.js`):

- `SelectorEvaluatorImpl.query()`: `if (Array.isArray(selector)) return this._queryEngine(isEngine, context, selector);`
  — a comma-separated CSS list parses to an array.
- `isEngine.query()`: `return args.length === 1 ? elements : sortInDOMOrder(elements);`

## Why it matters to a reviewer

An "in that DOM order" claim in an AFS is only backed by code if the read cannot be
influenced by the caller's argument order. **Resolving each element by its own testid
and returning them in the caller's order is NOT an order assertion** — it relabels the
argument list, so a swapped-element regression passes while the failure message still
says "in DOM order". This is invisible at the call site: both shapes read
`assert rendered == EXPECTED`.

Worked example: ELITEA-2255 (`NotificationCenterPage.column_header_texts()`, PR #1783)
shipped the per-testid shape first; the fix reads all three headers through one union
and is pinned by `automation/tests/unit/test_notification_column_header_dom_order.py`.

A prefix selector (`[data-testid^="prefix-"]`) is the stronger variant of the same
trick — it also catches an element that was ADDED to the group, which a fixed union of
N branches cannot.

Related: [[per_testid_reads_cannot_prove_dom_order]]
