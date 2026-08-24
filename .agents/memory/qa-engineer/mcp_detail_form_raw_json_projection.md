---
name: MCP detail Form ⇄ Raw Json is a live two-way projection
description: Unsaved raw-JSON edits show in the Form instantly; view switches re-serialise the JSON, so assert parsed values
type: reference
aliases: [raw json toggle, toolkit-raw-json-view-toggle, CodeMirror fill trap, description null empty string]
tags: [area/mcp, type/ui-quirk]
created: 2026-08-24
updated: 2026-08-24
---

## Facts confirmed live (toolkit 3134, 2026-08-24)

- The two views **swap** — the inactive view's inputs are UNMOUNTED (`to_have_count(0)`),
  not hidden. Toggle state reads via `aria-pressed`.
- An **unsaved** Raw-Json edit appears in the Form view immediately and survives a round
  trip back. Save + Discard flip to enabled the moment the edit lands.
- **Every view switch re-serialises the JSON from the form model** (30 → 29 → 30 lines
  observed), normalising CodeMirror's auto-indent. ⇒ assert on
  `json.loads(get_raw_json_full())[...]`, never on raw line text.
- `description: null` in JSON ⇄ `""` in the Form input. Seed a NON-EMPTY description when
  "reverts to the original value" must be a real observable.
- Discard (after the #1718 modal confirm) reverts **both** views and leaves the active
  view unchanged. No `PUT`/`POST`/`PATCH` fires anywhere in the flow.

## The `.fill()` trap, in Playwright MCP form

`browser_type` maps to `locator.fill()`, which replaced the whole 30-line CodeMirror
document with one line — invalid JSON, Save stays disabled, only a reload recovers.
Use `browser_run_code_unsafe` with `page.keyboard.type()` after clicking the `.cm-line`
and `End` → `Shift+Home` (this is real keyboard input, not synthesized DOM events).
In-repo equivalent: `McpFormPage.fill_raw_json_line()`.

Related: [[mcp_type_picker_vs_dashboard_type_filters]]
