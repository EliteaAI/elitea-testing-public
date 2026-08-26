---
name: Project Context editor — Save and Discard both LEAVE the editor
description: Any case step saying "after Save/Discard the editor shows X" is asserting on a page that no longer exists
type: feedback
aliases: [project context, discard, save, handleDiscard, onNavigate saved]
tags: [area/settings, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The semantics (EliteaUI `ProjectContextEditor.jsx`, confirmed live 2026-08-26)

- `handleSave` → `onNavigate('saved')`. `handleDiscard` → `setIsDirty(false)` +
  `onNavigate('saved')`. **Both leave `/settings/project-context/edit`** for the saved
  view. Nothing stays put showing reverted or saved text.
- So a TMS step like "verify the editor reverts" or "verify the buttons become inactive
  again" is only observable on the editor the user **next opens** — plus, for
  persistence, a full reload (which defeats the RTK-Query cache). Assert both; do not
  weaken the step to fit the page you happen to be on.
- The sibling button is **`Cancel` in create mode** and calls `handleCancel` →
  **empty state** — a different flow. Assert its label (`Discard`) before trusting that
  a test exercised the edit-mode path.
- Both buttons: `disabled={!isDirty || isSaving}`. `isDirty` is set by ANY edit and is
  never cleared by editing the text back to its original value.

Related: [[codemirror_markdown_editor_handling]]
