# Surface digest — settings-project-params

Covers Settings → Project (section) tabs, starting with **Project Context**.
Originally confirmed live against `http://localhost:5173` (2026-08-05, pre-
ladder/pre-DEV-cutover — see `.agents/role-overrides.md`, that session's
"testid needed" framing is retired language, superseded below). **Re-confirmed
live against `https://dev.elitea.ai/app` (DEV as deployed), project "Private"
(API project id `575`), 2026-10-16** during ELITEA-3252/3253/3254/3255
analysis — the feature has grown substantially since August; see §§ below
marked "NEW (2026-10-16)".

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
  #5667) asserts and confirms passing **as of 2026-08-05**. **⚠ CHANGED
  (2026-10-16, confirmed live on DEV):** Save on the create/edit flow now
  ALSO requires a non-empty `project-context-activation-description` input
  (new field, see below) — `isDirty` on the editor content alone is no
  longer sufficient. Re-verify ELITEA-2272's own test still passes before
  touching this file further; this is a shared-component regression risk.
- Character counter text (visible only while editor focused): exactly
  `"{N} characters left. "` + (`"You have reached the maximum character
  limit."` appended when `content.length >= MAX_CHARS`). Confirmed literal
  string at the boundary: `"0 characters left. You have reached the maximum
  character limit."`.
- **NEW (2026-10-16) — "Activation description" field.** A plain `<input>`
  (not CodeMirror), max 300 chars (counter format `"{n}/300"`), labeled
  "When should this context be used?", testid
  `project-context-activation-description`. Required (non-empty) for Save to
  enable on the create/edit flow. Persisted server-side as
  `activation_description` (see REST endpoints below).
- **NEW (2026-10-16) — "Build with AI" (empty-state entry point, distinct
  from "Edit with AI").** Button on `ProjectContextEmptyState.jsx`
  (`get_by_text("Build with AI", exact=True)`, no testid yet) opens a modal:
  textarea (placeholder "Describe your project: architecture, design
  decisions, workflows, terminology, constraints, coding standards,
  deployment process, or other important information.", no testid) +
  "Generate Draft" button (no testid, disabled until textarea non-empty).
  On success (200), transitions to a review step: an editable "Project
  Background" textarea pre-filled with the draft (no testid) + "Apply"
  button (no testid, role+name "Apply") + "Back to prompt" button. On 422
  (draft would exceed 2500), shows an inline `role="alert"` MUI Alert with
  the exact text (confirmed live, `{N}` = actual generated length, varies by
  run): `"Project background is {N} characters, the maximum is 2500. Try
  generating again, or ask for a narrower scope."` — prompt textarea stays
  populated and editable, nothing is saved.
- **NEW (2026-10-16) — "Edit with AI" (saved-view entry point).** Button
  `ai-edit-project-context-open-button`, visible directly on the saved view
  (`ProjectContextSavedView.jsx`) — **no separate "Edit" click needed first**
  (that older "Edit" → "Edit with AI" two-step some TMS case text still
  describes does not match this build: "Edit" and "Edit with AI" are two
  independent, adjacent buttons). Opens a modal (testid
  `ai-edit-project-context-modal`) with a prompt input (testid
  `ai-edit-project-context-prompt-input`), Cancel (testid
  `ai-edit-project-context-cancel-button`), Generate (testid
  `ai-edit-project-context-generate-button`), close/X (testid
  `ai-edit-project-context-close-button`). On success, shows the edited
  draft + "Apply & Save" (applies and saves in one action, unlike the
  create flow's separate Apply-then-Save) — confirmed live: an edit request
  that stays within budget succeeds (200) and the resulting content is
  correctly ≤2500.
- **NEW (2026-10-16) — Chat `project_context_builder` module.** Already
  wired in `ChatPage.MODULE_TOGGLE_ORDER` (`("project_context_builder",
  "Project Context Builder")`) — no page-object changes needed, just use
  `click_module_toggle`/`is_module_toggle_checked`/`close_modules_panel`.
  Confirmed live: a chat message that both describes the project AND asks to
  save (not just "generate") makes the AI invoke a tool whose live
  invocation-chip text reads `"Elitea Project Context:
  put_project_context_project-context"` (NOT `generate_project_context_draft`
  as some TMS case text names it) — content is correctly generated AND
  persisted (`PUT .../project-context` fires), length ≤2500 confirmed via a
  follow-up API GET. A message with NO project description in it (just
  "Generate a project context for this project") makes the AI ask a
  clarifying follow-up instead of invoking any tool — always include a
  description in the same chat message.

## REST endpoints (`src/api/projectContext.js`)

Base: `/elitea_core/project_context/prompt_lib/{project_id}/project-context`

| Method | Behavior (confirmed live) |
|---|---|
| GET | Always 200. `{"id": null, "content": "", "enabled": true, "activation_description": null, "updated_at": null}` when unset — **`activation_description` field NEW (2026-10-16)**, not present in the 2026-08-05 shape. |
| PUT | Body includes `content`, `enabled` (and `activation_description` from the create/edit UI flow). 200 on success. Fires on Save click AND directly from the chat `project_context_builder` tool (`put_project_context`). |
| DELETE | **CHANGED (2026-10-16): confirmed live 204** on success (2026-08-05 digest said 200 — re-verify which is current if asserting the exact code; either way it's a success status, teardown's tolerate-non-2xx-as-ok contract is unaffected). 404-on-empty behavior from 2026-08-05 not independently re-confirmed this session — carry forward as unconfirmed. |
| POST `generate_project_context_draft/prompt_lib/{project_id}` | **NEW (2026-10-16).** Fires on "Generate Draft" (Build-with-AI) and the Edit-with-AI modal's generate action. 200 + draft payload on success. **422** on overflow with body `{"error": "Project background is {N} characters, the maximum is 2500. Try generating again, or ask for a narrower scope.", "details": [{"type": "string_too_long", "loc": ["project_background"], "msg": "String should have at most 2500 characters", "ctx": {"max_length": 2500}}], "raw": {"activation_description": "...", "project_background": "..."}}` — confirmed live across 4 separate overflow runs (N = 4303/4423/5253/2638). |

Reachable via the generic `automation/api/client.py` `APIClient` (Bearer
token) — no dedicated entity client exists yet for Project Context. Useful
for test **setup/teardown** (guarantee empty-state precondition, clean up
after) without needing any UI testids in `ProjectContextSavedView.jsx`.

## Testids (as of 2026-10-16 — ladder era, DEV as deployed)

**Historical note:** the 2026-08-05 digest below described a pre-ladder,
pre-DEV-cutover "testid needed" state where none of these existed yet. As of
2026-10-16, DEV serves ALL of the testids the ELITEA-2272 AFS once requested,
plus many new ones for the expanded feature. Per the current locator policy
(`.agents/testing.md` § Locator policy), "testid needed" is retired language —
this section simply lists what DEV serves today.

Confirmed on DEV (`https://dev.elitea.ai/app/settings/project-context`):
`project-context-create-button`, `project-context-editor-content` (via
`contentTestId` prop), `project-context-save-button`,
`project-context-char-counter`, `project-context-activation-description`
(NEW), `ai-edit-project-context-open-button` (NEW),
`ai-edit-project-context-modal` (NEW), `ai-edit-project-context-close-button`
(NEW), `ai-edit-project-context-prompt-input` (NEW),
`ai-edit-project-context-cancel-button` (NEW),
`ai-edit-project-context-generate-button` (NEW),
`project-context-actions-menu-button` (NEW, not yet exercised by any
automated case).

**Still testid-less (confirmed via live `[data-testid]` enumeration, both
states):** the empty-state "Build with AI" button, and every control inside
its dialog (prompt textarea, "Generate Draft", the review step's "Apply"/
"Back to prompt", and the inline 422 error `role="alert"` Alert). Ladder rung
used instead: `role`+`name` / `label`+placeholder (all confirmed unique) —
see the ELITEA-3252/3253/3254/3255 family AFS
(`l1_project-context-char-limit-enforced-across-surfaces_ELITEA-3252.md`) for
the exact `suggested_testid=` hints.

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
