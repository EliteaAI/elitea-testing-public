---
name: Slash-mention zero-tools panel still renders (#1596)
description: Toolkit/MCP with zero tools still opens an empty "available tools" panel in the '/' dropdown — deterministic, source-confirmed, not just an MCP thing.
type: feedback
---

## What
Selecting a Toolkit or MCP participant from the chat `/` slash-mention
dropdown that has **zero configured tools**
(`settings.available_mcp_tools`/`selected_tools == []`) still opens the
`"{name} available tools"` panel — header renders, zero rows underneath,
no empty-state message either. Filed as
[#1596](https://github.com/EliteaAI/elitea-testing-public/issues/1596)
(found while analysing ELITEA-2205/2468, 2026-08-19).

## Root cause (read from source, don't re-derive — just re-check it hasn't shipped a fix)
`EliteaUI/src/[fsd]/features/chat/ui/slash-suggestion-list/SlashSuggestionList.jsx`:
```js
// only hides when a typed tool-name FILTER matches nothing — not when the
// toolkit/MCP genuinely has zero tools and no filter was typed:
if (!isToolsFetching && toolQuery && filteredTools.length === 0) return null;
```
`ToolList.jsx` then always renders its header `Box`, and only conditionally
renders a loader OR `tools.map(...)` — an empty `tools` array just renders
nothing under an otherwise-present header.

## Why this matters for future cases
- Applies identically to a Toolkit participant with zero `selected_tools` —
  NOT MCP-specific, despite being filed from an MCP case.
- The case-text phrase "no tools or disconnected" collapses into ONE UI code
  path — `availableTools` reads `settings.available_mcp_tools` regardless of
  WHY it's empty. No need to simulate a genuinely-unreachable MCP server to
  cover the "disconnected" wording; a plain zero-tools toolkit (created via
  `ToolkitAPI.create_remote_mcp_toolkit(..., tools=[])`) is sufficient and
  honest (real API resource, not a UI substitution).
- If a case ever asserts "no panel/list appears" for an empty-result state
  elsewhere on this surface, check whether the guard condition is
  filter-scoped like this one before assuming the whole panel is
  conditionally hidden.

## Reusable mechanism note (unrelated to the defect, save yourself a re-derivation)
`ChatPage.select_slash_mention_toolkit()` (added ELITEA-2204) works
UNCHANGED for MCP cards (docstring already says "toolkit/MCP card") — BUT it
waits for the first tool-item row to ATTACH, so it will **time out** against
a zero-tools participant. Needs an inline variant or an additive
`wait_for_first_tool` param for that branch.
