---
name: Grid-table refetch window makes to_have_count(0) vacuous
description: After any create/delete the whole grid-table unmounts, so an absence assertion can pass while nothing is rendered — assert the total count first.
type: feedback
aliases: [refetch window, table unmounts, vacuous absence assertion, isFetchingTokens, to_have_count(0) trap]
tags: [area/ui, type/assertion-quality]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

Components built on the shared `grid-table` render
`!isFetching ? <table> : <spinner>` (e.g. `TokensTable.jsx:150`). After a
create or delete the RTK-Query `refetch()` flips `isFetching` true and the
**entire table unmounts** — every row locator resolves to 0 for a moment.

Measured live twice on Settings → Personal Tokens (2026-08-27): row count read
**0** immediately after landing back from a create, and **0** immediately after
a delete's `204`, before settling at 9 and 8.

## Why it matters

`expect(deleted_row).to_have_count(0)` **passes vacuously** inside that window —
it would pass against a delete that never happened, because *nothing* is
rendered. Same for reading names/values right after a create.

## The shape that is not vacuous

```python
expect(page_obj.row)  .to_have_count(rows_before - 1, timeout=ROW_WAIT_TIMEOUT)  # table came back
expect(page_obj.get_row_by_name(name)).to_have_count(0)                          # which row went
```

Assert the **total** count first (it cannot be satisfied while unmounted), then
pin the specific row. Generalise to any `isFetching`-gated list, not just tokens.

Related: [[personal_tokens_surface_notes]]
