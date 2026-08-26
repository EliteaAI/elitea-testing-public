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

## Resolved/added during ELITEA-2268/2273/2274/2275 analysis+implementation (test-automation-engineer, 2026-08-26)

**Testids added (two).** `project-context-saved-content` on the SAVED view's content
`Box` (`ProjectContextSavedView.jsx`) — EliteaAI/EliteaUI@452a21a2 — is the app-owned scope
for asserting the saved view's rendered markdown (react-markdown's `<h2>`/`<li>` carry no
testid of their own, and the settings page renders other headings outside it). And
`project-context-preview` on the editor's markdown-preview `Box`
(`ProjectContextEditor.jsx`, the `mode !== 'edit'` branch). EliteaAI/EliteaUI@5681f22e on
`automation/testids`, pushed; awaiting the human cherry-pick to `main`. Plain attribute on
the existing node — no new DOM node, no hook, no component change. It is **required**, not
convenience: the app sidebar renders its own `<li>` elements, so an unscoped assertion on
the rendered markdown cannot disambiguate.

**Editor toolbar modes — confirmed live.** `</>` (`project-context-mode-edit-button`) is the
default (`aria-pressed="true"` on load) and renders CodeMirror; the eye
(`project-context-mode-preview-button`) swaps the whole pane for
`<Markdown renderHtml={false}>`. **The two panes are mutually exclusive** — in preview mode
`project-context-editor-content` AND `project-context-editor-wrapper` are both absent from
the DOM (count 0), and in edit mode `project-context-preview` is. Switching back restores
the raw source verbatim (state lives in `content`, not in the DOM).

⚠️ **Keystroke typing MANGLES multi-line markdown — paste instead.** CodeMirror's
`markdown()` extension auto-continues list items on Enter: `pressSequentially` of
`"## H\n- a\n- b\nplain"` produced `- - b` and `  - plain` (confirmed live 2026-08-26).
A clipboard paste is one transaction with no Enter keypresses and lands the text
byte-for-byte. New page-object method `paste_markdown()` does this and waits per-line;
`set_editor_content_via_paste()` (single-line, merged caller) is untouched.

⚠️ **CodeMirror `.cm-content` has NO newlines in `textContent`** — each line is its own
`.cm-line` div, so `expect(editor_content).to_have_text("a\nb")` can never pass. Assert
per line against the `.cm-line` list instead (`ProjectContextPage.editor_lines()`, a #579
exception-2 raw handle scoped to `project-context-editor-wrapper`, same discipline as the
gutter). The gutter also renders a hidden sizing element (text `"9"`) alongside the real
numbers — filter to digits, or assert the numbers you expect are present.

⚠️ **Discard LEAVES the editor.** `handleDiscard` = `setIsDirty(false)` + `onNavigate('saved')`
→ back to `/settings/project-context`. It does NOT stay put showing reverted text, so
"the editor reverts" and "the buttons go inactive again" are only observable on the editor
you next open. Same for **Save** (`onNavigate('saved')`), so a post-save "the editor still
shows…" reading of any case is wrong on this surface. The sibling button is `Cancel` in
create mode and calls `handleCancel` → **empty state**, a different flow: assert the label
before trusting which one you are exercising.

**Save/Discard gating** — `disabled={!isDirty || isSaving}` on both. Confirmed: disabled on
a freshly-opened editor (create AND edit), enabled after a single character, disabled again
on the editor re-opened after a Discard. `isDirty` is set by ANY edit, never cleared by
editing back to the original text.

**Markdown blank lines are load-bearing in the case bodies.** `- item\nPlain text.` renders
as ONE `<li>` (CommonMark lazy continuation), so a plain-text-paragraph assertion needs a
blank line before it. Confirmed live in the preview pane.

**Pre-existing console error on this surface (not ours):** React's
`Warning: React does not recognize the 'disableUnderline' prop on a DOM element` fires
around the settings pages. Observed once via Playwright MCP when switching to preview mode; whether it
reaches a pytest run's `collect_console_errors` is run-dependent. If a spec on this
surface trips it, it is
app noise unrelated to project-context — investigate before filtering, never filter blind.

## Resolved/added during ELITEA-2269/2270/2271 analysis+implementation (test-automation-engineer, 2026-08-26)

**The Build-with-AI flow is the SHARED `GenerateEntityModal`** — the same component the
Agents/Skills "Build with AI" flows use (`entities/generate-entity-with-ai/`), wrapped by
`GenerateProjectContextButton` → `GenerateProjectContextModal` →
`GenerateProjectContextReviewForm`. So `automation/pages/generate_entity_modal_page_base.py`
applies here unchanged: the shell steps are INPUT → LOADING → REVIEW, `Generate Draft` is
also the retry control, and the review step's actions are `Back to prompt` + `Apply`.

**Testids added (seven, all caller-supplied on props the shared components ALREADY
accepted — no shared-component change).** EliteaAI/EliteaUI@d6eb52b6 on
`automation/testids`, pushed; awaiting the human cherry-pick to `main`:

| Testid | Where | How it is wired |
|---|---|---|
| `project-context-build-with-ai-button` | `ProjectContextEmptyState.jsx` | plain `data-testid` |
| `generate-project-context-open-button` | `GenerateProjectContextButton.jsx` | `GenerateEntityButton`'s pre-existing `buttonTestId` |
| `generate-project-context-modal` / `-prompt-input` / `-loading-indicator` / `-submit-button` / `-cancel-button` / `-approve-button` | `GenerateProjectContextModal.jsx` | `GenerateEntityModal`'s pre-existing `modalTestId` / `promptInputTestId` / `loadingIndicatorTestId` / `generateButtonTestId` / `cancelButtonTestId` / `approveButtonTestId` props (all were `undefined` for project context until now) |
| `generate-project-context-review-background-input` | `GenerateProjectContextReviewForm.jsx` | `slotProps.htmlInput['data-testid']` — lands on the real `<textarea>`, so `input_value()` reads the draft directly |

`ai-edit-project-context-*` (modal, prompt-input, cancel/generate/refine/apply, open-button,
close-button, error-alert, loading-indicator) were **already** fully wired in
`AIEditProjectContextModal.jsx` — nothing to add for the Edit-with-AI flow.

⚠️ **The toolbar's AI control SWAPS on content** (`ProjectContextEditor.jsx`:
`content.trim() ? <AIEditProjectContextButton/> : <GenerateProjectContextButton/>`).
Empty editor ⇒ **Build with AI**; one character of content ⇒ **Edit with AI**, and the
Build-with-AI button is gone from the DOM entirely. Confirmed live 2026-08-26. This makes
ELITEA-2270's literal step order ("enter manual content, then click Build with AI")
unexecutable — filed as clarification **#1797**. They are two different dialogs:
Build with AI generates a draft from a project description
(`POST /elitea_core/generate_project_context_draft/prompt_lib/{project_id}`),
Edit with AI refines the content already in the editor.

**Two mount points for the SAME Build-with-AI modal.** The empty state's Build-with-AI
button navigates with `onNavigate('create', { openAi: true })`; `ProjectContextEditor`'s
first-render effect then opens a *separate* `GenerateProjectContextModal` instance
(rendered at the component's bottom, ~line 370) — not the toolbar button's. Only one is
ever mounted: `Modal.BaseModal` has **no `keepMounted`**, so a closed dialog's testid count
is 0 (verified). The shared testids therefore never collide.

⚠️ **`page.goto('/settings/project-context/edit')` can re-open the AI modal.** The browser
restores the history entry's router state on a same-URL reload, so a goto after an
`openAi: true` navigation lands with the dialog already open. Reach the editor via the
empty state's **Create** button when you need a closed dialog.

⚠️ **Navigating away from a DIRTY editor fires a native `beforeunload` dialog** (the
`useNavBlocker` + `blockCondition: isDirty` wiring). Playwright MCP surfaces it as a modal
state that blocks `browser_navigate`; in pytest, avoid navigating while dirty, or handle
the dialog. Teardown via the API (`clean_project_context`) is unaffected.

**Live generate-draft latency**: ~5–20 s observed. `POST .../generate_project_context_draft/prompt_lib/399`
→ 200 with `{"project_background": "<markdown>"}`. The response body IS the oracle — assert
the review field and the editor against it (`.agents/testing.md` § nondeterministic producer),
never against a hand-written payload. Apply does **not** save: after Apply the API `GET` still
reports `content: ""` and Save merely becomes enabled.

**Import from markdown file** (`project-context-import-button`) opens a real OS file chooser
via a hidden `<input type="file" accept=".md,text/markdown">` clicked programmatically —
drive it with Playwright's `expect_file_chooser()` (the `<input>` itself has no testid and
should not get one: it would be unreferenced, #511). `handleFileUpload` normalises CRLF→LF,
rejects >2500 chars with a toast, **replaces** (never appends) the editor content, and sets
`isDirty`. Cursor lands at the END of the imported text. Fixture file committed at
`test-data/project-context/elitea-2271-import.md`.

**New page object: `GenerateProjectContextModalPage`** (`automation/pages/generate_project_context_modal_page.py`)
— third subclass of `GenerateEntityModalPageBase`, alongside the Agent and Skill ones.

**Follow-up testid commit (same wave).** EliteaAI/EliteaUI@aacfb6e adds
`generate-project-context-title` and `ai-edit-project-context-title` so a spec can assert
WHICH AI dialog opened without a raw `<h2>` handle (the editor toolbar hosts two). Both
ride `Modal.BaseModal`'s **pre-existing** `titleTestId` prop; the shared
`GenerateEntityModal` gained a single additive `titleTestId` pass-through (default
`undefined`) — no other caller is affected, no DOM node, hook or removal.

**Deliberately NOT given testids on this dialog** (#511 — unreferenced testids inflate the
presence-based coverage metric): `Back to prompt`, the close (X) button and the
generate-failure alert. Consequence: `GenerateEntityModalPageBase.wait_for_review_form()`
cannot be used as-is here (it waits on `back_button`), so
`GenerateProjectContextModalPage` overrides it to key on `Apply` + the populated
Project Background field. Wire the missing testids only when a case actually exercises them.
