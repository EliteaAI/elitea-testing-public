---
name: CodeMirror auto-closes quotes/brackets — use colon removal for invalid YAML
description: edit_yaml_line()'s real keyboard.type() auto-closes a typed opening quote/bracket, silently producing VALID YAML; colon removal doesn't
type: feedback
---

## What happened (ELITEA-2068, 2026-08-05)

Testing "invalid YAML syntax" in the pipeline YAML editor (`PipelineDetailPage`),
the obvious approach — edit `transition: END` to an unterminated quote
(`transition: "END`) via `edit_yaml_line()` — looked invalid in an ad-hoc
Playwright-MCP exploration session, but the ACTUAL production code path (real
`keyboard.type()` keystrokes) auto-closed the quote via CodeMirror's YAML mode
auto-close-brackets/quotes extension, silently turning it into the VALID quoted
scalar `transition: "END"`. The pipeline then SAVED SUCCESSFULLY (200, success
toast) instead of the expected 400 — a false pass that only surfaced when
actually running the pytest test (`TimeoutError: Timeout 15000ms exceeded while
waiting for event "response"` — the `expect_response(r.status >= 400)` predicate
never matched because the response was 200/201).

**Root cause of the mismatch:** the MCP exploration session's `browser_type` tool
executed a `.fill()` call on the CodeMirror line (no real keystrokes → no
auto-close), while the real page-object method does `Home` → `Shift+End` →
`keyboard.type(new_line_text)` (real keystrokes → CodeMirror's editor extensions
fire, including auto-close). **Exploration technique and production code path can
disagree** when the surface has editor-level keystroke interception.

## The fix / rule

For invalid-YAML edits via `edit_yaml_line()` (or any real-keystroke CodeMirror
edit), **use colon removal, not unterminated brackets/quotes** — e.g.
`transition END invalid_no_colon_xyz123` instead of `transition: "END`. No
bracket/quote character means nothing for CodeMirror to auto-pair, and it
reliably breaks the YAML block-mapping structure. This also matches the TMS
case text's own suggested technique ("remove a colon, add random text") when a
case gives you a choice.

**General lesson:** when exploring via MCP tools before writing the real
page-object call, verify the FINAL test by running the actual method
(`edit_yaml_line()`, not a substitute `.fill()`), especially for editor-widget
surfaces (CodeMirror/Monaco/ProseMirror) that have auto-formatting extensions —
an MCP shortcut that bypasses real keystrokes can silently produce different
DOM content than the shipped test will.
