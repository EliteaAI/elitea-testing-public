---
name: MCP numeric settings fields — value type asymmetry + missing info-icon testid
description: Timeout/Cache TTL persist numeric when untouched, string once edited; the label info icon has no testid but the plumbing exists.
type: reference
aliases: [timeout field, cache_ttl, cache ttl, info icon testid, toolkit-field-timeout-input, InfoTooltip testId]
tags: [area/mcp, area/toolkits, type/handle]
created: 2026-08-24
updated: 2026-08-24
---

## Value type asymmetry (confirmed live 2026-08-24, toolkit 3247)

A Remote MCP's `settings.timeout` / `settings.cache_ttl`:

- untouched default → JSON **number** `300`
- value typed in the UI → JSON **string** (`"60"`, `"600"`)

Same in the create POST body, the update PUT body and the Raw Json view. Editing one
field never changes the sibling's type. Assert `str(raw["settings"][k]) == "<v>"` plus
`isinstance(..., str)`. TMS case texts print bare numbers — that is case-text drift
(filed as clarification #1745), not a defect.

The field's `placeholder` is ALSO the schema default ("300"), so a genuinely empty field
still *looks* like 300 — assert `input_value()`, never the placeholder.

## Info icon next to a schema field label has no testid

Live DOM: `<span data-info-tooltip="true"><svg …/></span>` inside the field `<label>`.
Plumbing is complete — `ToolBaseProperty.jsx` → `StyledInputEnhancer` → `InputBase` →
`InfoTooltip`, which accepts `testId`/`contentTestId`. `ToolBaseProperty.jsx:615-618`
already passes them but only for `k === 'bucket'`. Adding one for another field = extend
that per-key allow-list with two additive props (zero functional impact). Never make it
generic — blanket-add ban.

## Trap

`McpFormPage.is_save_button_disabled()` binds the CREATE form's
`toolkit-form-save-button`; on `/mcps/all/{id}` it times out after 30 s. Use
`detail_save_button.is_disabled()` there.

Related: [[mcp_detail_page_configuration_collapsed]]
