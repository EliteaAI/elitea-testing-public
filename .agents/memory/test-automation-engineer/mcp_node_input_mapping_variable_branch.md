---
name: MCP/Toolkit node Input-mapping — the Variable branch is the ENUM select
description: type=variable makes enumList non-empty, so the row renders the FIRST select branch, not the final one
type: reference
aliases: [input mapping variable branch, InputMappingItem select branch, getEnumList variable]
tags: [area/pipelines, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

`InputMappingItem.jsx` picks its Value widget as
`enumList?.length ? (enum selects) : isStringType ? (TextInputField) : (final SingleSelect)`.

`isStringType = type === 'string' | 'fstring' | 'fixed'`, so it is FALSE for
`variable` — which tempts you to the final `SingleSelect`. Wrong.
`FlowEditorHelpers.getEnumList('variable', …)` returns the state-variable list
(`flowEditor.helpers.js:162`), so `enumList` is NON-empty and the row renders the
FIRST branch (`dataType !== 'array' || type === 'variable'`). A testid placed on
the final select never appears in the DOM.

## Consequence for tests

One testid, two widget shapes (EliteaAI/EliteaUI@7a5fce32 on `automation/testids`):
read a Fixed/F-String row with `input_value()`, a Variable row with
`text_content()`. A `text_content()` read that returns a state-variable name also
PROVES the widget swapped — a text input has no text content.

Related: [[reactflow_control_panel_intercepts_node_clicks]]
