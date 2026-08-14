# Surface digest — settings-project-params

Covers Settings → Project (section) tabs, starting with **Project Context**.
Confirmed live against `http://localhost:5173` on `EliteaUI` `automation/testids`,
project `Private` (`${ELITEA_PROJECT_ID}` = 399), 2026-08-05.

## Navigation

- Route: `/settings/<tab-id>` (bare path, `APP_PREFIX` empty on localhost).
  `project-context` tab id → `/settings/project-context`.
- Sidebar "Project Context" nav item is HIDDEN on the "Public" project
  (`PUBLIC_PROJECT_ID` guard in `src/[fsd]/pages/settings/index.jsx`) —
  tests targeting this tab must run against a non-Public project.
- No testids exist yet on the Settings sidebar tab items themselves (not
  needed if tests navigate by bare URL rather than clicking the tab).

## Project Context feature (`src/[fsd]/features/settings/ui/project-context/`)

Three views, switched by `ProjectContextContent.jsx` based on `?view=` query
param + whether `serverData.content` is non-empty:

| View | Component | When shown |
|---|---|---|
| Empty state | `ProjectContextEmptyState.jsx` | no `?view=`, `content` empty |
| Editor (create/edit) | `ProjectContextEditor.jsx` | `?view=create` or `?view=edit` |
| Saved view | `ProjectContextSavedView.jsx` | no `?view=`, `content` non-empty |

- `MAX_CHARS` = `PROJECT_CONTEXT_MAX_LEN` = **2500**, defined in
  `src/[fsd]/features/settings/lib/constants/projectContext.constants.js`.
- The CodeMirror editor's `maxLength` prop wires
  `EditorState.transactionFilter` (`CodeMirrorEditor.jsx:13-63`) which
  **silently truncates** any insert that would exceed the limit — confirmed
  live via clipboard-paste of 2500 chars then one more keystroke: content
  stays at exactly 2500, no toast/error, no console error.
- Save/Discard/Cancel buttons are gated purely on `isDirty` (any edit at
  all made this session), **NOT** on character count — Save stays enabled
  through and past the 2500 boundary. This is what ELITEA-2272 (regression
  #5667) asserts and confirms passing.
- Character counter text (visible only while editor focused): exactly
  `"{N} characters left. "` + (`"You have reached the maximum character
  limit."` appended when `content.length >= MAX_CHARS`). Confirmed literal
  string at the boundary: `"0 characters left. You have reached the maximum
  character limit."`.

## REST endpoints (`src/api/projectContext.js`)

Base: `/elitea_core/project_context/prompt_lib/{project_id}/project-context`

| Method | Behavior (confirmed live) |
|---|---|
| GET | Always 200. `{"id": null, "content": "", "enabled": true, "updated_at": null}` when unset. |
| PUT | Body `{content, enabled}`. 200 on success. Fires on Save click. |
| DELETE | 200 when a context exists. **404** `{"error": "Project context not found"}` when none exists — teardown fixtures must tolerate this. |

Reachable via the generic `automation/api/client.py` `APIClient` (Bearer
token) — no dedicated entity client exists yet for Project Context. Useful
for test **setup/teardown** (guarantee empty-state precondition, clean up
after) without needing any UI testids in `ProjectContextSavedView.jsx`.

## Testids (as of 2026-08-05)

None exist in `src/[fsd]/features/settings/ui/project-context/` yet. Four
requested by ELITEA-2272's AFS (all `testid needed`, not yet added):
`project-context-create-button`, `project-context-editor-content` (via
`contentTestId` prop — same pattern as `skill-instructions-editor-content` /
`toolkit-raw-json-editor-content`), `project-context-save-button`,
`project-context-char-counter`. `ProjectContextSavedView.jsx`'s
Edit/Delete/toggle controls are untouched so far (API-based cleanup avoids
needing them) — a future case exercising the saved view's own UI will need
its own testids there.

## Gotchas

- Clipboard-paste (`navigator.clipboard.writeText` via `page.evaluate` +
  `Control+V`/`Meta+V`) is a fast, real (non-synthetic) way to fill large
  CodeMirror content — goes through the same `transactionFilter` as
  keystroke typing. `conftest.py`'s `context` fixture already grants
  `clipboard-read`/`clipboard-write` globally, so no extra permission setup
  is needed in a new page object.
- `keyboard.type()` also works (established pattern in
  `SkillFormPage.fill_instructions()`) but is much slower for 2500+ chars —
  prefer paste for large fills, typing for small/short-input tests where
  keystroke-level events matter.
