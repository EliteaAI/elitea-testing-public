---
name: ProjectContextPage navigate() has a THIRD state — the read-only saved view
description: Settings > Project Context, when content already exists, renders a plain-text saved view (Edit/Edit with AI buttons) distinct from both create_button (empty) and editor_content (create/edit flow) — neither ELITEA-3368 nor ELITEA-3369's tests ever hit it, since both reach the editor only via the in-chat chip/Canvas.
type: feedback
---

## What happened (ELITEA-3315)

`ProjectContextPage.wait_for_page_load()` only knew two states: the
empty-state `create_button` (testid `project-context-create-button`) or the
CodeMirror `editor_content` (testid `project-context-editor-content`, only
rendered at `?view=create`/`?view=edit`). ELITEA-3315's own flow calls
`context_page.navigate()` directly on `/settings/project-context` for a
project that ALREADY has content (created via chat in the same test) — DEV
renders neither of those two states; it renders a third, read-only "saved"
view: the content as plain `<p>` text plus "Edit with AI"/"Edit" buttons, no
`data-testid` on either button or the content container as of 2026-10-17.

`wait_for_page_load()` fell through both `try/except` branches and the test
timed out at `editor_content.wait_for(...)` (15s) — not a product bug, a
page-object gap, since no prior test's flow ever reached this state (both
ELITEA-3368/3369 only ever open the editor via the in-chat
generated-entity-chip → Canvas, never by a direct `navigate()` on a
project that already has saved content).

## The fix (now on `ProjectContextPage`, additive)

- `edit_button` — `role="button", name="Edit", exact=True` (NOT "Edit with
  AI", a separate button with a different accessible name — `exact=True`
  disambiguates).
- `saved_content_text` — xpath rung:
  `//button[normalize-space(.)="Edit"]/ancestor::main//p/parent::div` — NOT
  bare `//p`, because multi-paragraph content renders as sibling `<p>` tags
  and a bare `//p` strict-mode-violates on >1 paragraph. The shared
  `parent::div` is confirmed unique.
- `wait_for_page_load()` now tries `create_button` → `editor_content` →
  `edit_button` in that order before giving up.
- `is_saved_view_showing()` / `get_saved_content_text()` / `click_edit()`
  added for callers that land on this state.

If you're writing a NEW Project Context test that calls `.navigate()` after
content already exists (vs. reaching the editor only through the chat
chip/Canvas), use `is_saved_view_showing()` / `get_saved_content_text()`,
not `editor_content` — the latter is absent until you've clicked Edit.
