---
name: Duplicate entity names are legal on Personal Tokens — name locators can match >1 row
description: Elitea permits two personal tokens with the same name, so get_row_by_name resolves multiple rows and a hardcoded test name collides with leftovers.
type: feedback
aliases: [duplicate token names, strict mode violation, get_row_by_name multiple rows, ELITEA-2288]
tags: [area/ui, type/locator]
created: 2026-08-27
updated: 2026-08-27
---

## Confirmed live (2026-08-27, ELITEA-2288)

Two `POST /api/v2/auth/token/` creates with an **identical** name both return
`200` with distinct `id`/`uuid`/token. The create form raises no validation
error and Generate stays enabled on the second attempt. Both rows render, with
distinct masked values (`'...' + token.slice(-4)`).

## Two consequences for tests

1. **`get_row_by_name(name)` can resolve MORE THAN ONE row.** Any single-row
   operation must index (`.first` / `.nth(i)`) or Playwright strict mode raises.
   The repo's usual "row by name is one-to-one" idiom does not hold here.
2. **Never hardcode a literal token name.** Because duplicates are legal, a
   leftover from a failed run does not fail loudly — it silently inflates every
   row-count assertion (a `to_have_count(2)` reads 3). Always
   `uuid4().hex[:8]`-suffix, even when the TMS case text names a literal.

Deletion stays unambiguous: the type-to-confirm field matches the **name** (so
either row accepts the same typed text) while the `DELETE` targets the clicked
row's own `uuid`. A `while rows.count() > 0` loop cleans both — verified, `204` each.

Related: [[grid_table_refetch_window_vacuous_assertions]]
