---
name: CodeMirror markdown editor — multiline typing/reading gotchas
description: keyboard.type() corrupts multi-line list Markdown in CodeMirror; text_content() drops line breaks — use insert_text()/inner_text() instead
type: feedback
---

Found while automating ELITEA-2432 (skill instructions Edit/Preview toggle),
`automation/pages/skill_form_page.py`. Applies to any `Field.CodeMirrorEditor`
instance with `extensions=[markdown()]` — skill instructions today; likely
also agent instructions / Project Context editor, which reuse the same
component per in-source comments.

**Gotcha 1 — list auto-continuation corrupts `keyboard.type()`.** The
`@codemirror/lang-markdown` extension auto-inserts a fresh `"- "` on the line
after a list-item line whenever Enter fires (a real editor UX feature).
`page.keyboard.type(text)` dispatches a discrete Enter keydown per `\n` in the
typed string, so typing `"- Item one\n- Item two"` renders as
`"- Item one\n- - Item two"` — corrupted. Fix: `page.keyboard.insert_text(text)`
instead — one atomic op, no discrete Enter keydown, the continuation keymap
never fires, and it still triggers the editor's real input handling (confirmed
live: char counter + React form state update correctly).

**Gotcha 2 — `text_content()` drops line breaks on multi-line content.**
CodeMirror renders each line as its own `<div class="cm-line">` with no
newline text node between them, so `Locator.text_content()` (raw text-node
concatenation) flattens a multi-line source into one unbroken string.
`Locator.inner_text()` is layout-aware (Playwright inserts a newline between
adjacent block-level elements) and reconstructs the real line breaks with no
new selector needed.

**Gotcha 3 — a blank line (`"\n\n"`) double-counts via `inner_text()`.** An
empty `cm-line`'s inner `<br>` seems to contribute its own break beyond the
normal block-separator one. Sidestep by using single `\n` line breaks in test
data rather than blank-line paragraph separators — `marked` (the app's
Markdown preview renderer) still parses lists correctly without one.

**Neither gotcha affects existing single-line-instructions tests** — the
existing `fill_instructions()` / `get_instructions()` on `SkillFormPage` are
correct for that case and were left untouched (additive-only); new
`fill_instructions_markdown()` / `get_instructions_multiline()` methods added
alongside for multi-line/Markdown content.
