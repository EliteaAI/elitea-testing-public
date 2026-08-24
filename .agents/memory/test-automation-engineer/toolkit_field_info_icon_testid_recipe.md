---
name: Toolkit field info-icon testid recipe (ToolBaseProperty per-key allow-list)
description: How to add an info-icon testid to any schema-driven toolkit/MCP field in one additive line
type: reference
aliases: [info icon testid, tooltipTestId, ToolBaseProperty tooltip, toolkit-field-info-icon]
tags: [area/mcp, area/toolkits, type/testid]
created: 2026-08-24
updated: 2026-08-24
---

## The recipe

Every schema-driven toolkit/MCP field (url, client_id, timeout, cache_ttl, …) renders its
label's info icon through `ToolBaseProperty.jsx` → `Input.StyledInputEnhancer` → `InputBase`
→ `InfoLabelWithTooltip` → `InfoTooltip`. The plumbing is complete; only the CALL-SITE prop
is per-key gated. Add a field's icon testid with one additive spread beside the pre-existing
`k === 'bucket'` one (`src/[fsd]/features/toolkits/ui/form/ToolBase/ToolBaseProperty.jsx`):

```jsx
{...((k === 'timeout' || k === 'cache_ttl') && {
  tooltipTestId: `toolkit-field-${k}-info-icon`,
})}
```

Done for `timeout` / `cache_ttl` at ELITEA-1956/1957 — EliteaAI/EliteaUI@25c47d7d on
`automation/testids`.

- Pass **only** `tooltipTestId` unless a case actually OPENS the tooltip; the
  `tooltipContentTestId` sibling would be an unreferenced testid (#511).
- Keep it **per key** — a generic `tooltipTestId` for every field is the blanket-add ban.
- Zero functional impact: no new DOM node, no hook, no removed line — clears all three
  `add-data-testid` § Step 5.5 greps.

## Related detail-page facts (MCP)

- `save_and_wait_for_updated()`'s returned PUT body carries the whole `settings` object, so
  a persisted value is assertable straight off the save response — no extra GET.
- `expand_configuration_section()` is required again after every reload AND after
  `switch_to_form_view()` coming back from Raw Json.

Related: [[mcp_toolkit_create_form_implementer_quirks]]
