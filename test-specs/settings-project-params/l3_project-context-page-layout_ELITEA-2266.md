# Test Case: Project Context page loads with correct layout and components

## Metadata
- **TMS ID**: ELITEA-2266
- **Source case**: `.agents/automation/settings-w03/cases/ELITEA-2266.md`
  (snapshot; TMS module `settings-project-params`)
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter). **pytest marker: `@pytest.mark.p2`**
  — project convention: TMS `medium` → AFS `l3_` prefix → pytest `p2`.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399), 2026-08-26
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Clarification filed**: #1792 (case text describes a single-page layout the product
  does not have)
- **Blocking suite defect (pre-existing, not this case)**: #1794 — the merged
  ELITEA-2272 spec + `ProjectContextPage.click_create()` still wait for the retired
  `?view=create` URL and time out. **The implementer must fix the page object's route
  before building on it** (see § Known Defects).

## Classification note — declared improvisation (reverse-masking guard)

The case text describes **one** page containing a toggle card, a "Project Background"
section (title + subtitle), a Build-with-AI button, upload / `</>` / eye icon buttons, a
line-numbered editor, and Save + Discard **at the bottom**. Executed live, the product
renders **three** views and no single view holds all of that:

| View | Route / condition | Holds |
|---|---|---|
| Empty state | `/settings/project-context`, `content` empty | header, "Still no Project Context", **Create**, **Build with AI** |
| Saved view | `/settings/project-context`, `content` non-empty | header + Edit with AI / Edit / dot-menu, **the toggle card**, rendered markdown |
| Editor | `/settings/project-context/edit` | breadcrumb, **Save** + **Cancel**(create)/**Discard**(edit) in the **header**, edit/preview tab group, Build with AI, Import, Copy, **line-numbered CodeMirror**, char counter |

Per the reverse-masking guard the **product is correct and the case text is stale**, so
this AFS asserts the **live** contract: the test walks Saved view → Editor and asserts
each of the case's listed components where the product actually renders it. The two case
elements that exist nowhere ("Project Background" section title; its goals/terminology/
workflows/constraints subtitle) get a `clarification` disposition in the Coverage Map —
they are **not** asserted and **not** silently dropped. Clarification #1792 filed.

## Preconditions
- User is logged in (localhost dev-token auth).
- The feature is hidden on the **Public** project (`PUBLIC_PROJECT_ID` guard in
  `src/[fsd]/pages/settings/index.jsx`) — the test MUST run against a non-Public
  project. `${ELITEA_PROJECT_ID}` = 399 ("Private") satisfies this.
- **A Project Context with non-empty content must exist** for the active project, because
  the toggle card only renders in the saved view. Establish it in setup (see § Test Data)
  and delete it in teardown.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399` ("Private"). Confirmed live: the project selector's
  option carries `data-testid="select-option-399"` for this project.

### generate-per-test
- A short seed string for the Project Context body, e.g.
  `"ELITEA-2266 layout seed."` — content **value** is irrelevant to every assertion
  here; only its non-emptiness matters (it is what makes the saved view render).

### API used for setup/teardown only (never for the case's own observable)
- `PUT /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  body `{content, enabled}` → 200. **Transit substitution** (§ Fidelity Declaration):
  seeds the precondition only.
- `DELETE /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  → 200 when set, **404 `{"error": "Project context not found"}` when unset** —
  teardown must tolerate 404. The existing `clean_project_context` fixture
  (`automation/fixtures/data_fixtures.py:2521`) already does exactly this and should be
  reused/extended rather than re-derived.

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Precondition seeding of a non-empty Project Context via `PUT` instead of typing it in the editor | **Transit** | The case's observables are *which components render*, all read off the live rendered UI. The seed only reaches the saved view. **Every** asserted value in this spec is produced by the product. |

No other substitution. No `route.fulfill`, no `page.evaluate` state injection.

## Test Steps

1. **Setup** — `DELETE` any existing Project Context (tolerate 404), then `PUT`
   `{content: "<seed>", enabled: true}` for `${ELITEA_PROJECT_ID}`.
2. Navigate to `${BASE_URL}/settings/project-context` (bare path — project convention).
   - **Verify**: `settings-content` is visible.
   - **Verify**: the page header reads exactly **`Project Context`**
     (`project-context-page-title`, *testid needed*).
3. **Toggle card** (saved view, top of the content area).
   - **Verify**: `project-context-toggle-card` (*testid needed*) is visible.
   - **Verify**: its title reads exactly `Project Context`
     (`project-context-toggle-card-title`, *testid needed*).
   - **Verify**: its description reads exactly
     `Project-specific background information that the AI uses to generate more accurate and relevant responses, tailored to your workflows, data, and goals.`
     (`project-context-toggle-card-description`, *testid needed*) — confirmed live,
     byte-identical, default prop in `EnableToggleCard.jsx`.
   - **Verify**: the toggle `project-context-enable-toggle` (*testid needed*) is
     **checked** — enabled by default. Confirmed live: a freshly created context comes
     back `enabled: true`.
   - **Verify**: the "turned off" banner `project-context-disabled-banner`
     (*testid needed*) has count **0** while the toggle is ON (absence assertion —
     first-class per `.agents/testing.md` § Locator policy).
4. Open the editor: click **Edit** (`project-context-edit-button`, *testid needed*).
   - **Verify**: URL is `${BASE_URL}/settings/project-context/edit`.
   - Note for the implementer: **do not** reuse `ProjectContextPage.click_create()`
     until #1794's route fix lands — it waits for the retired `?view=create`.
5. **Editor toolbar** — verify each of the case's listed controls, in the editor:
   - **Verify**: an AI button is present. With non-empty content the product renders
     **"Edit with AI"** (`ai-edit-project-context-open-button`, **pre-existing**), not
     "Build with AI" — `ProjectContextEditor.jsx` swaps `GenerateProjectContextButton`
     for `AIEditProjectContextButton` when `content.trim()` is truthy. Confirmed live.
   - **Verify**: the upload/import icon button `project-context-import-button`
     (*testid needed*) is visible. Its tooltip/accessible name is
     `Import from markdown file` (confirmed live).
   - **Verify**: the code-view (`</>`) mode button `project-context-mode-edit-button`
     (*testid needed*) is visible **and** is the selected mode on load
     (`[data-testid="project-context-mode-edit-button"][aria-pressed="true"]` — state as
     a `data-*`/ARIA attribute filter on a stable testid, per `.agents/testing.md`;
     never a state-switched testid).
   - **Verify**: the preview (eye) mode button `project-context-mode-preview-button`
     (*testid needed*) is visible and `aria-pressed="false"`.
6. **Editor with line numbers**.
   - **Verify**: `project-context-editor-content` (**pre-existing**) is visible and
     carries the seeded text.
   - **Verify**: the line-number gutter is rendered. CodeMirror owns that DOM, so this
     is a **#579 exception 2** (third-party editor internal render node): add
     `project-context-editor-wrapper` (*testid needed*) on the editor's wrapper `Box`
     and scope the raw handle to it —
     `self.editor_wrapper.locator(GUTTERS)` with a class constant
     `GUTTERS = ".cm-gutters"`. Document the exception in the method docstring
     (which node, why no testid can be placed, and the do-not-extend boundary).
     Confirmed live: `.cm-gutters` exists and renders `1` for a single-line document.
7. **Save and Discard**.
   - **Verify**: `project-context-save-button` (**pre-existing**) is visible and
     **disabled** (no edit yet — `isDirty` false).
   - **Verify**: `project-context-discard-button` (*testid needed*) is visible, its text
     is exactly **`Discard`** (edit mode; it reads `Cancel` in create mode — confirmed
     live both ways), and it is **disabled**.
   - **Note**: both buttons sit in the page **header**, not "at the bottom" as the case
     says — asserted by presence + label, never by position (see #1792).
8. **No error / no permanent loading state**.
   - **Verify**: no console errors across the whole run — use
     `automation/utils/console_errors.py`'s `collect_console_errors(page)` (the
     URL-capturing helper), not the hand-rolled URL-less shape.
   - **Verify**: no `CircularProgress` spinner remains in `settings-content`
     (absence assertion on `project-context-loader`, *testid needed* on the
     `ProjectContextContent.jsx` loading `Box`) — this is the case's literal
     "no permanent loading state" observable.
9. **Teardown** — `DELETE` the Project Context (tolerate 404).

## Concrete Handles

| Element | Handle (testid) | Provenance | Verified |
|---|---|---|---|
| Settings content pane | `settings-content` | on `automation/testids` only (awaiting human promotion to main) | live 2026-08-26 |
| Settings sidebar → Project Context | `settings-nav-item-project-context` (composed `settings-nav-item-${tab.id}` in `SettingsDrawer.jsx:102`) | on `automation/testids` only | live 2026-08-26 |
| Empty-state Create button | `project-context-create-button` | **on-main ✓** | live 2026-08-26 |
| Editor content (`.cm-content`) | `project-context-editor-content` (via `contentTestId` prop) | **on-main ✓** | live 2026-08-26 |
| Editor Save button | `project-context-save-button` | **on-main ✓** | live 2026-08-26 |
| Char counter | `project-context-char-counter` | **on-main ✓** | live 2026-08-26 |
| "Edit with AI" button | `ai-edit-project-context-open-button` | **on-main ✓** | live 2026-08-26 |
| Saved-view dot menu | `project-context-actions-menu-button` (from `DotMenu id="project-context-actions"`) | on `automation/testids` (generic DotMenu pattern) | live 2026-08-26 |
| Page header title | `project-context-page-title` | **needs-adding** (`DrawerPageHeader` title in `ProjectContextSavedView.jsx` / `ProjectContextEmptyState.jsx`) | — |
| Toggle card container | `project-context-toggle-card` | **needs-adding** (`EnableToggleCard.jsx` root `Box`) | — |
| Toggle card title | `project-context-toggle-card-title` | **needs-adding** (`EnableToggleCard.jsx` title `Typography`) | — |
| Toggle card description | `project-context-toggle-card-description` | **needs-adding** (`EnableToggleCard.jsx` description `Typography`) | — |
| Enable toggle (switch input) | `project-context-enable-toggle` | **needs-adding** — `Switch.BaseSwitch` is a **shared** component, so pass a caller-supplied `testId`-style prop from `EnableToggleCard.jsx` (feature-scoped call site); never hardcode a feature testid inside `shared/ui` | — |
| "turned off" banner | `project-context-disabled-banner` | **needs-adding** (`Banner.BannerMessage` in `ProjectContextSavedView.jsx`; shared component ⇒ caller-supplied prop) | — |
| Saved-view Edit button | `project-context-edit-button` | **needs-adding** (`ProjectContextSavedView.jsx`) | — |
| Editor Discard/Cancel button | `project-context-discard-button` | **needs-adding** (`ProjectContextEditor.jsx`, the `isCreate ? handleCancel : handleDiscard` button) | — |
| Import-from-markdown icon | `project-context-import-button` | **needs-adding** (`ProjectContextEditor.jsx` toolbar) | — |
| Edit-mode (`</>`) tab button | `project-context-mode-edit-button` | **needs-adding** (`TabGroupButton` `arrayBtn` entry `value: 'edit'`; shared component ⇒ caller-supplied prop per entry) | — |
| Preview-mode (eye) tab button | `project-context-mode-preview-button` | **needs-adding** (same, `value: 'preview'`) | — |
| Editor wrapper (gutter scope) | `project-context-editor-wrapper` | **needs-adding** (`ProjectContextEditor.jsx` `styles.editorWrapper` `Box`) | — |
| Loading spinner | `project-context-loader` | **needs-adding** (`ProjectContextContent.jsx` `isLoading` `Box`) | — |

**Not touched by this case** (add no testid): "Copy to clipboard" toolbar button,
dot-menu Copy/Delete items, the empty-state "Create"/"Build with AI" pair (this case
runs against the saved view), the breadcrumb links.

**Provenance verified with a fresh fetch**: `cd ../EliteaUI && git fetch origin` ran
2026-08-26, then the two-stage grep from `.agents/workflow.md` § Closure record against
`origin/main` and `origin/automation/testids`. Output:

```
settings-nav-item-project-context          main:no   testids:no   (dynamic — composed `settings-nav-item-${tab.id}`, SettingsDrawer.jsx:102; substring grep cannot see it. Present on automation/testids, confirmed live.)
settings-content                           main:no   testids:YES
project-context-create-button              main:YES  testids:YES
project-context-editor-content             main:YES  testids:YES
project-context-save-button                main:YES  testids:YES
project-context-char-counter               main:YES  testids:YES
ai-edit-project-context-open-button        main:YES  testids:YES
```

## Coverage Map

### Axis 1 — every case element

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Navigate to Settings → Project Context | page loads | Step 2 | `settings-content` visible | covered |
| 2 | Page header shows "Project Context" | header text | Step 2 | exact-text on `project-context-page-title` | covered |
| 3 | Toggle card shown at top | card visible | Step 3 | `project-context-toggle-card` visible | covered (saved view only — #1792) |
| 4 | Title "Project Context" | exact text | Step 3 | `project-context-toggle-card-title` | covered |
| 5 | Description text explaining the feature | exact text | Step 3 | `project-context-toggle-card-description` | covered |
| 6 | ON/OFF toggle, enabled by default | checked | Step 3 | `project-context-enable-toggle` checked | covered |
| 7 | "Project Background" section shown below | — | — | — | **clarification #1792** — no such section exists in the product |
| 8 | Section title "Project Background" | — | — | — | **clarification #1792** — string exists only inside the AI-generate review modal, never as a section title |
| 9 | Subtitle (goals, terminology, workflows, constraints) | — | — | — | **clarification #1792** — no such subtitle anywhere |
| 10 | "Build with AI" button | present | Step 5 | `ai-edit-project-context-open-button` ("Edit with AI" when content is non-empty) | covered, label differs — declared in Step 5 |
| 11 | Upload file icon button | present | Step 5 | `project-context-import-button` | covered |
| 12 | Code view (`</>`) icon button | present + selected | Step 5 | `project-context-mode-edit-button`, `aria-pressed="true"` | covered |
| 13 | Preview (eye) icon button | present | Step 5 | `project-context-mode-preview-button` | covered |
| 14 | Code/markdown editor with line numbers | editor + gutter | Step 6 | `project-context-editor-content` + scoped `.cm-gutters` (#579 exc. 2) | covered |
| 15 | Save and Discard present at the bottom | both present | Step 7 | `project-context-save-button` + `project-context-discard-button`, exact label `Discard` | covered by presence; **position not asserted** (they are in the header — #1792) |
| 16 | No errors, no permanent loading state | clean | Step 8 | console-error collector + absence of `project-context-loader` | covered |
| P | Precondition: user logged in | — | Setup | `auth_state` | covered |

### Axis 2 — observables asserted beyond the case

| Observable | Why |
|---|---|
| `project-context-disabled-banner` count 0 while the toggle is ON | The banner is the visible consequence of the toggle's state; asserting its absence in the ON state turns "enabled by default" into a test-enforced invariant rather than a single checkbox read, and satisfies the #511 both-branches-referenced rule for the banner testid that ELITEA-2267 asserts positively. |
| Save/Discard **disabled** on load | Free control condition: proves the two buttons were found in their real initial state, not merely present in the DOM. |
| `aria-pressed` on the two mode buttons | Distinguishes "the tab group rendered" from "edit mode is the default", which is what makes step 14's editor assertion meaningful. |
| URL is `/settings/project-context/edit` after Edit | Pins the route that #1794 shows is easy to drift; a future rename fails here loudly instead of silently. |

## Known Defects

- **#1794 (suite, pre-existing, BLOCKS reuse)** — `ProjectContextPage.click_create()`
  and `tests/ui/admin/test_project_context_character_limit.py` still expect
  `?view=create`. Reproduced live 2026-08-26:
  `TimeoutError: waiting for navigation to "**/settings/project-context?view=create"`.
  Not caused by this case; the implementer must repair the page object's route
  (one line) before extending it.
- **#1792 (case text)** — layout drift, above.

## Blocked Steps
None — every step above was executed live and observed.
