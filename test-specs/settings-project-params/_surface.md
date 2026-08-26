# Surface digest — settings-project-params

Covers Settings → Project (section) tabs, starting with **Project Context**.
Confirmed live against `http://localhost:5173` on `EliteaUI` `automation/testids`,
project `Private` (`${ELITEA_PROJECT_ID}` = 399). First written 2026-08-05;
**substantially revised 2026-08-26** (ELITEA-2266/2267/2276) — the `?view=` query-param
model is GONE, and the toggle card / saved view are new here.

## Navigation

- Route: `/settings/<tab-id>` (bare path, `APP_PREFIX` empty on localhost).
  `project-context` tab id → `/settings/project-context`.
- Sidebar "Project Context" nav item is HIDDEN on the "Public" project
  (`PUBLIC_PROJECT_ID` guard in `src/[fsd]/pages/settings/index.jsx`) —
  tests targeting this tab must run against a non-Public project.
- No testids exist yet on the Settings sidebar tab items themselves (not
  needed if tests navigate by bare URL rather than clicking the tab).

## Project Context feature (`src/[fsd]/features/settings/ui/project-context/`)

Three views, switched by `ProjectContextContent.jsx` on **route** + whether
`serverData.content` is non-empty. **The `?view=` query param was retired** — there are
now two real routes (`src/routes.js`):

```js
ProjectContext:     '/settings/project-context',
ProjectContextEdit: '/settings/project-context/edit',
```

| View | Component | When shown | Contains |
|---|---|---|---|
| Empty state | `ProjectContextEmptyState.jsx` | `/settings/project-context`, `content` empty | header, "Still no Project Context", **Create** + **Build with AI**. **No toggle, no editor, no Save.** |
| Saved view | `ProjectContextSavedView.jsx` | `/settings/project-context`, `content` non-empty | header + Edit with AI / Edit / dot-menu, **the enable toggle card**, rendered markdown. **No editor, no Save.** |
| Editor | `ProjectContextEditor.jsx` | `/settings/project-context/edit` | breadcrumb `Project Context / Create\|Edit`, **Save** + **Cancel**(create)/**Discard**(edit) in the **header** (top-right, NOT at the bottom), edit/preview tab group, Build-with-AI *or* Edit-with-AI, Import, Copy, line-numbered CodeMirror, char counter. **No toggle.** |

⚠️ **`?view=create` is dead — it broke a merged test.** `ProjectContextPage.click_create()`
and `tests/ui/admin/test_project_context_character_limit.py` still wait for it and time
out (`TimeoutError: waiting for navigation to "**/settings/project-context?view=create"`,
reproduced 2026-08-26). Tracked as **#1794**; fix the page object's route before
extending it.

### Enable toggle (`EnableToggleCard.jsx`) — saved view only

- Renders ONLY when `content` is non-empty. Any test touching the toggle must seed
  content first (API `PUT`), or there is nothing to click.
- **Defaults to ON**; a freshly created context comes back `enabled: true`.
- **There is no Save button for it** — `handleToggle` fires `PUT` immediately
  (auto-save). Confirmed live: flip → `PUT ... => 200`, state survives an in-app nav
  round-trip *and* a full reload.
- Turning it OFF shows a banner, exact text:
  `Project Context is turned off. The project background is not applied to AI responses or workflows.`
- Turning it OFF also **disables Edit and Edit with AI** (`disabled={!enabled}`) — the
  editor is unreachable by clicking. The `/settings/project-context/edit` **route is
  unguarded** though, so direct-URL navigation still opens a working editor.
- **Saving empty content makes the toggle vanish** (`hasContent` false → empty state,
  which has no toggle). Re-creating content brings it back **still OFF** —
  `handleSave` sends `enabled: serverData?.enabled ?? true`. Tracked as **#1793**.
- Card title/description default props, exact:
  `Project Context` /
  `Project-specific background information that the AI uses to generate more accurate and relevant responses, tailored to your workflows, data, and goals.`

### Permissions gate

`PERMISSIONS.projectContext.view` / `.edit`. On some projects (observed on
**"Bugs & Features"**) the saved view renders a banner
*"You don't have permission to edit this setting."* and the toggle is `disabled`.
Project **399 "Private"** has full edit rights — use it. Project options in the
selector carry `data-testid="select-option-<projectId>"`.

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

## Testids (verified 2026-08-26, fresh `git fetch origin` in ../EliteaUI)

**Present** — the four from ELITEA-2272 landed and are now on **`origin/main`** too:

| Testid | main | automation/testids |
|---|---|---|
| `project-context-create-button` | YES | YES |
| `project-context-editor-content` (via `contentTestId` prop on shared `CodeMirrorEditor`) | YES | YES |
| `project-context-save-button` | YES | YES |
| `project-context-char-counter` | YES | YES |
| `ai-edit-project-context-open-button` | YES | YES |
| `settings-content` | no | YES |
| `settings-nav-item-project-context` / `-project-general` (dynamic, `settings-nav-item-${tab.id}`, `SettingsDrawer.jsx:102`) | no | YES (grep-invisible — composed at runtime) |
| `project-context-actions-menu-button` (from `DotMenu id="project-context-actions"`; menu items `delete-menuitem`, `delete-confirm-button`) | — | YES |

**Still needed** (requested by the ELITEA-2266/2267/2276 AFS trio, none added yet):
`project-context-page-title`, `project-context-toggle-card`,
`project-context-toggle-card-title`, `project-context-toggle-card-description`,
`project-context-enable-toggle`, `project-context-disabled-banner`,
`project-context-edit-button`, `project-context-discard-button`,
`project-context-import-button`, `project-context-mode-edit-button`,
`project-context-mode-preview-button`, `project-context-editor-wrapper`,
`project-context-loader`.

Note: the enable **Switch**, the **Banner** and the **TabGroupButton** are all
`shared/ui` components — their testids must be **caller-supplied props** wired at the
project-context call site, never hardcoded inside `shared/` (`.agents/testing.md`
§ Locator policy).

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

## Editor toolbar & content (confirmed live 2026-08-26)

- Toolbar, left→right: mode tab group (`</>` = *Edit mode*, eye = *Preview mode*), then
  **Build with AI** (empty content) *or* **Edit with AI** (non-empty content — the
  component swaps on `content.trim()`), then an icon button with accessible name
  `Import from markdown file`, then one with `Copy to clipboard`.
- Save is gated on `isDirty` only; the sibling button is **Cancel** in create mode and
  **Discard** in edit mode (the ELITEA-2272 AFS mentions them only jointly).
- Line numbers: CodeMirror's `.cm-gutters`, a **library-internal** node — #579 exception
  2 applies. Scope the raw handle to a real app testid on the wrapper `Box`
  (`project-context-editor-wrapper`, still to be added).
- Char counter with an empty editor reads exactly `2500 characters left. ` (trailing
  space before the conditional limit clause — normalize whitespace when comparing).
  It is `visibility: hidden` unless the editor has focus.

## Deleting a context through the UI

Saved view → `project-context-actions-menu-button` → `delete-menuitem` → confirmation
dialog *"Are you sure you want to delete Project Context?"* → `delete-confirm-button`.
Useful when an API teardown isn't wired; the API `DELETE` is still the cheaper path.

## No "Project Background" section exists

The case texts for this module describe a *"Project Background"* section with a
goals/terminology/workflows/constraints subtitle. `grep -rn "Project Background" src/`
on both `origin/main` and `automation/testids` returns exactly two hits, neither a
section heading (a label in `GenerateProjectContextReviewForm.jsx`, a placeholder in
`AIEditProjectContextModal.jsx`). Do not go looking for it. Tracked as **#1792**.

## Resolved/added during ELITEA-2266/2267/2276 implementation (test-automation-engineer, 2026-08-26)

**Testids added** — EliteaAI/EliteaUI@b05bbc9a on `automation/testids`, pushed; awaiting
the human cherry-pick to `main`. All thirteen render live (verified in-browser before the
commit), and all thirteen are referenced on an executed test path (#511):

| Testid | Where | How it is wired |
|---|---|---|
| `project-context-page-title` | `ProjectContextSavedView.jsx` | `DrawerPageHeader`'s **pre-existing** `titleTestId` prop — no component change |
| `project-context-toggle-card` / `-title` / `-description` | `EnableToggleCard.jsx` | new caller-supplied `testId` / `titleTestId` / `descriptionTestId` props (default `undefined`, so `MidturnInjection.jsx` — the card's other caller — is unaffected) |
| `project-context-enable-toggle` | `EnableToggleCard.jsx` → shared `Switch.BaseSwitch` | caller-supplied `switchTestId` threaded through `slotProps.switch.slotProps.input`, so it lands on the **real `<input type="checkbox">`** and `to_be_checked()` works directly. A plain spread would have put it on the MUI root `<span>`, where checked state is unreadable. |
| `project-context-disabled-banner` | `ProjectContextSavedView.jsx` → shared `BannerMessage.jsx` | new `testId` prop **defaulting to the pre-existing `credential-warning-banner`**, so the ~6 merged callers and the tests reading that testid are untouched |
| `project-context-edit-button` | `ProjectContextSavedView.jsx` | plain `data-testid` |
| `project-context-discard-button`, `-import-button`, `-editor-wrapper` | `ProjectContextEditor.jsx` | plain `data-testid` |
| `project-context-mode-edit-button` / `-mode-preview-button` | `ProjectContextEditor.jsx` `modeButtons` | `TabGroupButton`'s **pre-existing** `item.buttonProps` spread (`TabButtonItem.jsx`) — no shared-component change; MUI `ToggleButton` supplies `aria-pressed` for selected state |
| `project-context-loader` | `ProjectContextContent.jsx` | plain `data-testid` on the `isLoading` Box |

**#1794 RESOLVED.** `ProjectContextPage.click_create()` and the merged ELITEA-2272 spec
both now wait for `/settings/project-context/edit` instead of the retired
`?view=create`. `click_create()` had exactly one caller (that spec), enumerated and
re-run green.

**Gotcha — Vite's file watcher does not see edits on this OneDrive checkout.** JSX edits
under `../EliteaUI/src` did NOT hot-reload and were NOT served even after a hard browser
reload and `touch`; `curl http://localhost:5173/src/…/File.jsx | grep <new-testid>`
returned 0 while the file on disk clearly had it. **Restarting the dev server is the fix**
(`pkill -f "node .*node_modules/.bin/vite" && npm run dev`, ~25 s to ready). Verify with
that same curl before concluding a testid "didn't work" — the DOM is not the ground truth
here, the served module is.

**Char counter on an empty editor** reads exactly `2500 characters left.` after
whitespace normalization. Use a retrying `expect(...).to_have_text(...)` rather than a
one-shot `text_content()`: the counter is a separate element whose state update lags the
CodeMirror transaction slightly.

**TMS case files for this module live under `settings/project-params/`, not
`settings-project-params/`.** The merged ELITEA-2272 spec's `allure.issue` link pointed at
the latter (and at a truncated slug) and 404'd; repaired in the same commit. Verify the
path with `find ../onetest-ai-tm-Elitea/tests -name "*<id>*"` before writing a case link.

**New fixture: `project_context_seed`** (`automation/fixtures/data_fixtures.py`, registered
in `conftest.py`). Yields `(content, enabled=None) -> dict`; deletes before and after,
tolerating the API's 404. Use it for any test touching the toggle or the saved view — the
toggle only exists while `content` is non-empty.

⚠️ **Seed CONTENT, not the enable flag** (settled in ELITEA-2266/2267/2276 review round 1,
2026-08-26). The one `PUT` carries both `content` and `enabled`, and on this surface the
flag is frequently the *case's own observable* — "the toggle is ON by default"
(ELITEA-2266 step 6, ELITEA-2267 step 2) or the result of a user ACTION, "Turn the Project
Context toggle ON" (ELITEA-2276 step 6). Seeding `enabled=True` and then asserting the
switch is checked is a **terminal substitution**: the assertion reads a value the test
wrote, and it looks perfectly healthy (deterministic, exact-equality, green).

So `enabled` defaults to `None` = **carry the product's own flag forward**: the callable
`GET`s the resource and echoes its value back, mirroring the product's own
`serverData?.enabled ?? true` (`ProjectContextSavedView.jsx:27`,
`ProjectContextEditor.jsx:157`). On a freshly-deleted resource the `GET` returns the
server's own default, so "ON by default" is *observed*. Pass an explicit `enabled=` only
to establish a **precondition** you then act on — ELITEA-2276 Phase B seeds
`enabled=False` to restore the OFF state its own earlier click produced, then clicks the
toggle ON for real. Declare any explicit flag in the spec docstring **and** the AFS
§ Fidelity Declaration; pinned by
`automation/tests/unit/test_project_context_seed_enabled_flag_not_authored.py`.
