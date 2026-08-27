---
name: Personal-tokens table unmounts during the post-mutation refetch
description: After every create/delete the whole tokens table unmounts, so a row-absence assertion can pass vacuously
type: feedback
aliases: [tokens table refetch window, vacuous row absence, TokensTable unmount]
tags: [area/settings, area/waits]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

`TokensTable.jsx:150` renders `!isFetchingTokens ? <table> : <spinner>`, so the WHOLE table
unmounts while the post-create/post-delete `refetch()` is in flight. `token-row` count reads
**0** for a moment. Therefore `expect(deleted_row).to_have_count(0)` passes **vacuously** in
that window — it would pass against a delete that never happened.

## The shape that is not vacuous

```python
expect(tokens_page.token_row).to_have_count(rows_before - 1, timeout=ROW_WAIT_TIMEOUT)  # first
expect(tokens_page.get_row_by_name(token_name)).to_have_count(0)                        # then
```

The total-count assertion cannot be satisfied while the table is unmounted; the named-row check
then pins *which* row went. Same rule mirrored for a create (`rows_before + 1`).

Verified in ELITEA-2281/2283/2288, 2026-08-27. Duplicate names are legal on this surface, so
`get_row_by_name()` may resolve >1 row — index with `.first`/`.nth()` or strict mode raises.
