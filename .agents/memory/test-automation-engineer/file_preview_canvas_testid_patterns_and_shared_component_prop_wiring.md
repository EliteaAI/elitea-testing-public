---
name: File preview/edit canvas testid patterns + shared-component prop wiring
description: ELITEA-1851 established the testid inventory for EliteaUI's file preview/edit editor (PreviewHeader.jsx/PreviewContent.jsx) — reuse these exact testids and the discovered shared-component prop shapes for the sibling cluster (ELITEA-1852/1856/1857/1858/1862) instead of re-deriving them.
type: feedback
---

## What

ELITEA-1851 was the first case to touch the Artifacts file-preview/edit
editor canvas. It had ZERO prior testids (except the pre-existing 3-dot
overflow-menu trigger) and zero page-object coverage. The testids added
there are now the inventory for the whole sibling cluster
(ELITEA-1852/1856/1857/1858/1862) — check this entry before re-adding
any of them.

## Testids added (EliteaAI/EliteaUI@2764045b, `automation/testids`)

| Element | Testid | Source file |
|---|---|---|
| File row Preview/View-Edit icon (dynamic) | `artifacts-file-preview-{filename}-button` | `ArtifactRowActions.jsx` |
| Editor panel close (X) icon | `artifacts-file-editor-close-button` | `PreviewHeader.jsx` |
| Editor panel path-title text | `artifacts-file-editor-header` | `PreviewHeader.jsx` (`canvasTitle`) |
| Language selector | `artifacts-file-editor-language-select` (+ auto `-combobox`) | `PreviewHeader.jsx` (`Select.SingleSelect`) |
| Save button | `artifacts-file-editor-save-button` | `PreviewHeader.jsx` (`Button.BaseBtn`) |
| Discard button | `artifacts-file-editor-discard-button` | `PreviewHeader.jsx` (`Button.DiscardButton`) |
| CodeMirror wrapping container (CODE preview type only) | `artifacts-file-editor-content` | `PreviewContent.jsx` (`codeEditorWrapper` Box) |
| 3-dot overflow-menu trigger (PRE-EXISTING) | `file-preview-overflow-menu-menu-button` | `PreviewHeader.jsx` (DotMenu `id="file-preview-overflow-menu"`) |
| 3-dot dropdown container (PRE-EXISTING, same DotMenu id convention) | `file-preview-overflow-menu-menu` | same |

Page-object side: all live as `LocatorDescriptor`/class-constant fields on
`ArtifactsPage` (`automation/pages/artifacts_page.py`, "File preview/edit
editor canvas (ELITEA-1851)" section) — methods `open_file_preview()`,
`get_file_editor_header_text()`, `get_file_editor_language_label()`,
`is_file_editor_line_numbers_visible()`, `get_file_editor_content_text()`,
`open_file_editor_overflow_menu()`, `get_file_editor_overflow_menu_text()`,
`close_file_preview()`, `get_file_preview_button(filename)` (Locator-
returning getter for direct `expect()` use).

## Shared-component prop shapes discovered (reuse, don't rediscover)

- **`Field.CodeMirrorEditor` supports `contentTestId`** — a FIRST-CLASS prop
  (not a workaround) that lands `data-testid` directly on CodeMirror's own
  `.cm-content` DOM node via `EditorView.contentAttributes.of({'data-testid':
  contentTestId})` (see `CodeMirrorEditor.jsx`). This is the SAME mechanism
  `mcp_form_page.py`'s `raw_json_editor_content` (`toolkit-raw-json-editor-content`)
  already relies on, via `ToolCustom.jsx`'s `contentTestId="toolkit-raw-json-editor-content"`.
  For ELITEA-1851 I deliberately did NOT use this prop and instead put the
  testid on the WRAPPING `Box` (`codeEditorWrapper`) instead — because the
  case also needed to assert `.cm-lineNumbers` (the gutter), which is a
  SIBLING of `.cm-content`, not a descendant, so a testid on `.cm-content`
  alone can't scope it. If a future case (e.g. ELITEA-1852, which edits
  content) needs ONLY `.cm-content` and never the gutter, `contentTestId` on
  `CodeMirrorEditor` itself is the more direct, canonical choice — don't
  default to copying the wrapper-Box shape if you don't need the gutter.
- **`Select.SingleSelect` already accepts a plain `data-testid` prop** and
  auto-derives a `-combobox` suffix on the visible/clickable display element
  via `SelectDisplayProps={{'data-testid': `${dataTestId}-combobox`}}`
  (`SingleSelect.jsx`). Same mechanism `artifacts_page.py`'s
  `bucket_retention_measure_combobox` already relies on. Always locate the
  `-combobox` variant for click/read — the bare (non-suffixed) testid lands
  on the underlying (often visually-hidden) native `<Select>`.
- **`Button.DiscardButton` accepts `dataTestId`** (camelCase prop name,
  forwards to `data-testid` on the underlying `BaseBtn`) — NOT `data-testid`
  directly (that would be swallowed by the component's own prop
  destructuring). `Button.BaseBtn` itself has no such indirection — pass
  `data-testid` straight through, it lands via `{...restProps}` on the MUI
  `Button` root.

## Cluster status after ELITEA-1851

Confirmed live during ELITEA-1851 analysis (not part of that case's own
scope, but relevant to siblings):
- Typing one character flips Save/Discard to enabled (Save turns solid/blue).
- Clicking Discard while enabled opens a SEPARATE, still-un-testid'd
  "Are you sure you want to discard changes?" confirmation dialog — whichever
  case exercises the discard flow (likely ELITEA-1852) needs to add a testid
  there too; it wasn't touched by ELITEA-1851 (visibility-only, never clicked).
- The 3-dot menu's items ("Copy Content"/"Download"/"Delete") have NO
  per-item testid — `DotMenu.jsx`'s `BasicMenuItem` only emits
  `data-testid={testId}-menuitem` when the item object carries a `testId`
  field, and `PreviewHeader.jsx`'s `menuItems` array doesn't set one.
  Deferred to ELITEA-1856 (whichever case actually clicks a specific item).
