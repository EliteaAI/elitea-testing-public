---
name: CodeMirror markdown editor handling (Elitea)
description: Type multi-line markdown into CodeMirror and it rewrites your list items; textContent has no newlines either
type: feedback
aliases: [codemirror, cm-line, markdown editor, project context editor, paste markdown]
tags: [area/ui, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## Two traps, both confirmed live (2026-08-26, ELITEA-2268)

**1. Never type multi-line markdown key by key.** CodeMirror's `markdown()` extension
auto-continues list items on Enter. `pressSequentially("## H\n- a\n- b\nplain")` produced
`- - b` and `  - plain` — the editor rewrites your input, and the test then asserts
something the user never wrote. A clipboard paste is a single transaction with no Enter
keypresses and lands the text byte-for-byte, while still passing through CodeMirror's own
`EditorState.transactionFilter` exactly like typing. `ProjectContextPage.paste_markdown()`
is the shape.

**2. `.cm-content`'s `textContent` has NO newlines.** Every line is its own `.cm-line`
div, so the content node reads `"## Project Overview- First bullet"` and
`expect(editor_content).to_have_text("a\nb")` can never pass. Assert per line against the
`.cm-line` list — `ProjectContextPage.editor_lines()`, a #579 exception-2 raw handle
scoped to an app-owned testid parent, same discipline as the gutter handle. Blank lines
come back as `""`.

Bonus: the line-number gutter renders a hidden width-measuring element with the text
`"9"` (`visibility: hidden`) alongside the real numbers — `:visible` in the selector
drops it (`EDITOR_LINE_NUMBERS`).

Related: [[project_context_editor_navigation_semantics]]
