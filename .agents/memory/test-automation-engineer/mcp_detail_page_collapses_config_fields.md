---
name: MCP detail page collapses its configuration fields
description: /mcps/all/{id} renders NO toolkit-field-* element until 'show more' is clicked — unlike the create form
type: reference
aliases: [toolkit-configuration-show-more, expand_configuration_section, toolkit-field-url-input missing, MCP detail page fields]
tags: [area/mcp, area/toolkits, type/product-behaviour]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

The Remote MCP **create form** (`/mcps/create/mcp`) renders every schema-driven field
inline. The **detail** page (`/mcps/all/{id}`) does **not** — it renders no
`toolkit-field-*` element at all until `toolkit-configuration-show-more` is clicked.

Verified live 2026-08-24: polled a freshly created MCP's DOM for 15 s → **zero**
`toolkit-field-*` testids. After clicking show-more, `toolkit-field-url-input` appeared
holding the persisted value.

Symptom when you miss it: `Locator.input_value` / `Locator.is_checked` timeout after 10 s
on a field you can plainly see in the create form.

Fix: `McpFormPage.expand_configuration_section()` (added ELITEA-1923/1924). No-op when
already expanded — the toggle unmounts once clicked, so call it unconditionally.

## It already broke three merged specs

Confirmed RED on `automation/base` by control runs against the unmodified base page
object: both tests in `test_mcp_create_remote.py`, plus
`test_mcp_edit_toggle_enable_caching.py`. Each needs one `expand_configuration_section()`
call — that is an `adjust-automated-test` unit, not a drive-by fix inside another case's PR.

## Sibling defect found at the same time

`_wait_for_detail_data_rendered()` excluded only the `"Edit Toolkit"` placeholder.
EliteaUI keeps one `fallbackLabel` per entity type
(`src/[fsd]/shared/lib/constants/breadcrumb.constants.js`: `"Edit Toolkit"` line 15,
`"Edit MCP"` line 47), so the wait was a **no-op on every MCP detail page** and callers
read `"Edit MCP"` as the toolkit name. Now driven by `DETAIL_TITLE_PLACEHOLDERS`; extend
that tuple if a new entity type appears.

Related: [[toolkit_form_helper_text_testids]] · [[save_button_gating_is_dirty_based]]
