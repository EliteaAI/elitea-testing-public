---
name: open_card_by_name leaves the detail page unwaited — reads race the "Edit MCP" placeholder
description: After McpListPage.open_card_by_name(), a spec MUST call McpFormPage.wait_for_page_load() before any bare title/field read
type: feedback
aliases: [open_card_by_name wait, Edit MCP placeholder race, toolkit-detail-title placeholder, mcp reopen flake]
tags: [area/mcp, area/toolkits, type/flake-trap, type/review-check]
created: 2026-08-24
updated: 2026-08-24
---

## The review check

`McpListPage.open_card_by_name()` only does `card.click()` + `wait_for_network()`
and its own docstring states the caller owns the destination page's ready state.
The MCP/toolkit detail page renders `toolkit-detail-title` as a static
placeholder (`"Edit MCP"` / `"Edit Toolkit"`, see `DETAIL_TITLE_PLACEHOLDERS`)
until the tool-detail GET is applied to component state — one React tick AFTER
the network goes idle. That is exactly why `McpFormPage._wait_for_detail_data_rendered()`
polls the title text rather than trusting the network wait.

So any spec line of the shape

```python
listing.open_card_by_name(name)
assert form.get_detail_heading_text() == name          # ← races the placeholder
assert form.name_input.input_value() == name           # ← same race
```

is a latent intermittent red. The compliant shape (as shipped in
`test_mcp_delete_remote.py` Step 3) inserts `form.wait_for_page_load()` between
the click and the first read. Retrying `expect(...)` assertions are the other
acceptable form; a bare `text_content()` / `input_value()` read is not.

Caught on PR #1716 (ELITEA-1925) at review; the sibling spec in the same folder
already did it correctly, so "the neighbours" cut both ways here — cite the
page-object docstring, not a neighbour.

Related: [[toolkit_detail_header_lags_save]]
