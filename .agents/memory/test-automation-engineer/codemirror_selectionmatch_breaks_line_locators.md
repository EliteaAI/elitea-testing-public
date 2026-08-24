---
name: CodeMirror selectionMatch breaks per-line locators
description: Re-resolving a get_by_text line locator after Home/Shift+End raises strict-mode violation; resolve the ElementHandle first
type: feedback
aliases: [selectionMatch, cm-selectionMatch, fill_raw_json_line, delete_raw_json_line, raw json editor, strict mode violation]
tags: [area/mcp, area/codemirror, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## Symptom

`McpFormPage.fill_raw_json_line()` / `delete_raw_json_line()` fail with
`Locator.element_handle: Error: strict mode violation:
get_by_test_id("toolkit-raw-json-editor-content").get_by_text("...", exact=True)
resolved to 3 elements` — one `.cm-line` div plus two `<span class="cm-selectionMatch">`.

## Cause

The click + `Home` + `Shift+End` selection triggers CodeMirror's **selectionMatch**
extension, which wraps every OTHER occurrence of the selected text in a
`cm-selectionMatch` span. The selection wait then re-resolves the SAME locator and
finds three matches. It only bites when the line text recurs in the document — which
is every tools-loaded MCP, because a tool name appears both in `selected_tools`
(`"ask_question",`) and in `available_mcp_tools` (`"value": "ask_question",`, whose
match span is exactly `"ask_question",`).

## Fix (shipped 2026-08-24, ELITEA-1935)

Resolve the `ElementHandle` BEFORE the click, then wait on the handle:

```python
line_handle = self.raw_json_editor_content.get_by_text(text, exact=True).element_handle()
line_handle.click()
self.page.keyboard.press("Home"); self.page.keyboard.press("Shift+End")
self._wait_for_line_selection_applied_handle(line_handle)
```

Same pattern applies to any editor helper that selects text then re-resolves a
text-based locator — `PipelineDetailPage.edit_yaml_line` and
`ChatDiagramCanvasPage`'s mirror of it are the obvious next candidates (not yet
hit, not yet fixed).

Related: [[mcp_toolkit_create_form_implementer_quirks]]
