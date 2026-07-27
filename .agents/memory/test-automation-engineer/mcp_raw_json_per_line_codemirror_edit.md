---
name: MCP Raw Json per-line CodeMirror edit technique
description: How to reliably edit a single field in the MCP toolkit detail page's Raw Json CodeMirror editor (toolkit-raw-json-editor-content) without whole-document corruption — the fill_raw_json_line() method + its selection-wait gotcha (from ELITEA-1927)
type: feedback
---

## The problem

`toolkit-raw-json-editor-content` (MCP toolkit detail page, Raw Json view) is
a CodeMirror `.cm-content` node rendering **one `<div>` per JSON line**, not
a single contenteditable blob. A whole-document select (`Ctrl+A` /
`Ctrl+Home`+`Ctrl+Shift+End`) followed by delete does **NOT** reliably clear
the entire document in this environment — confirmed live at both the
ELITEA-1927 analyst pass and implementer exploration: one attempt left a
stray character behind (`"headers": nul,` instead of `"headers": null,`),
producing invalid JSON that the app's own "Invalid JSON format" validation
correctly caught (not a product bug — a CodeMirror multi-line-editor
selection quirk).

## The fix: per-line edit

`McpFormPage.fill_raw_json_line(current_line_text, new_line_text)`:
1. Locate the target line's own `<div>` via
   `raw_json_editor_content.get_by_text(current_line_text, exact=True)`.
   `exact=True` still trims/normalizes whitespace, so `current_line_text`
   does NOT need to include the line's leading indentation (e.g.
   `'"description": null,'` matches the DOM's `'  "description": null,'`
   just fine — confirmed live via `page.getByText(..., {exact:true}).count()`
   both with and without the leading spaces, both return 1).
2. Click the line, press `Home`, press `Shift+End` — selects just that
   line's content.
3. Type the full replacement line (including trailing comma/brace) to
   overwrite the selection.

## The selection-wait gotcha

Do NOT reuse `_wait_for_contenteditable_selection_applied` (built for the
Headers editor's whole-document case, no indentation) for the per-line
case — it polls `sel.toString().length === el.textContent.length`, but a
Raw Json line's `textContent` includes leading indentation that `Home`
does NOT select (`Home` moves to the first non-whitespace character).
Confirmed live: a 22-char indented line (`'  "description": null,'`) yields
only a 20-char selection (`'"description": null,'`) — the equality check
never becomes true, `wait_for_function` times out at 10s every time.

Fix: a dedicated `_wait_for_line_selection_applied()` that compares against
`el.textContent.trim().length` instead of the raw (indented) length.

## Reusable for

Any future MCP/toolkit case editing a single field via the Raw Json view
(e.g. `timeout`, `cache_ttl`, `ssl_verify`, `enable_caching` via raw JSON
instead of the Form view's dedicated controls) — reuse
`fill_raw_json_line()` directly rather than re-deriving the per-line
technique or hand-rolling a new selection wait.
