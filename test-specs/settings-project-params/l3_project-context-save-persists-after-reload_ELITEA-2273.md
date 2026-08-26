# Test Case: Save button persists Project Background content after page reload

## Metadata
- **TMS ID**: ELITEA-2273
- **Source case**: `.agents/automation/settings-w03/cases/ELITEA-2273.md`
  (snapshot; TMS module `settings-project-params`; TMS file
  `settings/project-params/ELITEA-2273_save-button-persists-project-background-content-after-page-r.md`)
- **Linked Story**: none
- **Priority**: l3 (medium) → **`@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399), 2026-08-26
- **User set**: `${TEST_USER}` (localhost `auth_state`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation

## Classification note — declared divergence (reverse-masking guard)

Two, both confirmed live 2026-08-26:

1. **"Project Background"** is not a name the product uses — the control is the
   **Project Context** editor (clarification **#1792**, already filed).
2. **Case step 6 assumes you are still in the editor after the reload.** You are not:
   `handleSave` calls `onNavigate('saved')`, so a successful Save leaves the editor and
   lands on `/settings/project-context`, whose saved view shows the content **rendered
   as markdown**, not the raw source. Reloading that page reloads the saved view.

   The case's observable — *the content survived the reload* — is fully preserved and
   asserted **twice**, on both honest readings: after the reload the **saved view**
   renders the content, and re-opening the **editor** shows the raw source verbatim.
   Nothing is weakened; only the assumed location of the observable moved. No new ticket
   (#1792 already covers this module's case-text drift).

## Preconditions
- User is logged in (localhost dev-token auth).
- Non-Public project (`${ELITEA_PROJECT_ID}` = 399 "Private").
- **No Project Context exists** for the project, so `/settings/project-context` renders
  the empty state and its **Create** button — the case's entry point. Pre-existing
  `clean_project_context` fixture establishes and tears this down (tolerates 404).

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399`.

### generate-per-test
- The case's literal body: `## Project Overview. This is a test project.`
  Single line — no blank-line handling needed, and it survives a paste verbatim.

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Nothing | — | The content is entered in the real editor and saved with the real Save button; persistence is read back after a **full page reload** (which defeats the RTK-Query cache), so the asserted value comes from the server through the product. |

`page.evaluate` is used only to put the text on the system clipboard for the paste
gesture (pre-existing reviewed pattern, ELITEA-2272) — it does not write application
state. The Save assertion additionally reads the product's **own** `PUT` response
status via `page.expect_response` (never a fabricated one).

## Test Steps

1. **Setup** — `DELETE` any existing Project Context (tolerate 404) so the empty state
   renders.
2. Navigate to `${BASE_URL}/settings/project-context`; click **Create**
   (`project-context-create-button`) — case step 1.
   - **Verify**: URL is `${BASE_URL}/settings/project-context/edit`, the editor is
     visible, and **Save is disabled** (nothing typed yet — the control condition that
     makes step 4's "enabled" meaningful).
3. Paste `## Project Overview. This is a test project.` into the editor — case step 2.
   - **Verify**: the editor's rendered line equals that string exactly (the field
     accepted and displays the entered value).
   - **Verify**: `project-context-save-button` is now **enabled**.
4. Click **Save**, waiting on the product's own `PUT` — case step 3.
   - **Verify**: that `PUT` returned **200**.
5. **Success confirmation** — case step 4.
   - **Verify**: the toast `toast-message` is visible and reads exactly
     `Project Context saved` (confirmed live; literal in `ProjectContextEditor.handleSave`).
   - **Verify**: the app left the editor for `${BASE_URL}/settings/project-context`
     (the product's own post-save navigation).
6. **Reload the page** — case step 5. A real browser reload of
   `${BASE_URL}/settings/project-context`.
   - **Verify**: the saved view renders (`project-context-toggle-card` visible), i.e.
     the server still reports non-empty content after the reload.
7. **The previously entered content is shown** — case step 6, asserted on both readings.
   - **Verify (saved view)**: the rendered markdown shows a heading whose text is
     `Project Overview. This is a test project.` — the `##` line rendered as `<h2>`.
     react-markdown output ⇒ **#579**, scoped to `settings-content`.
   - **Verify (editor)**: click **Edit** (`project-context-edit-button`); the editor's
     rendered line is byte-identical to the string pasted in step 3 — raw markdown,
     `##` included. This is the case's literal "the editor shows the previously entered
     content".
   - **Verify**: on that freshly-opened editor **Save and Discard are both disabled**
     again — the loaded content is the saved content, nothing is dirty.
8. **Teardown** — `DELETE` the Project Context (tolerate 404).

## Concrete Handles

| Element | Handle (testid) | Provenance | Verified |
|---|---|---|---|
| Empty-state Create button | `project-context-create-button` | **on-main ✓** | live 2026-08-26 |
| Editor content | `project-context-editor-content` | **on-main ✓** | live 2026-08-26 |
| Save button | `project-context-save-button` | **on-main ✓** | live 2026-08-26 |
| Success toast | `toast-message` | pre-existing, app-wide | live 2026-08-26 |
| Saved-view toggle card | `project-context-toggle-card` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| Saved-view Edit button | `project-context-edit-button` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| Discard button | `project-context-discard-button` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| Settings content pane (render scope) | `settings-content` | on `automation/testids` only | live 2026-08-26 |
| Rendered heading | *(no testid — #579)* `h2` scoped to `settings-content` | react-markdown-internal | live 2026-08-26 |

## Coverage Map

### Axis 1 — every case element

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Navigate to Settings → Project Context | page loads | Step 2 | empty state → Create → editor route | covered |
| 2 | Enter `## Project Overview. This is a test project.` | field accepts + displays it | Step 3 | per-line equality on the editor | asserted |
| 3 | Click Save | control responds | Step 4 | the product's own `PUT` returns 200 | asserted |
| 4 | A success confirmation is shown | holds | Step 5 | toast exact text `Project Context saved` | asserted |
| 5 | Reload the page | completes, expected UI state | Step 6 | real reload; saved view renders | asserted |
| 6 | Editor shows the previously entered content | holds (final state) | Step 7 | rendered `<h2>` in the saved view **and** byte-identical raw line in the re-opened editor | asserted (location divergence declared) |
| P | Precondition: user logged in | — | Setup | `auth_state` | covered |

### Axis 2 — observables asserted beyond the case

| Observable | Why |
|---|---|
| Save **disabled** before typing, **enabled** after | The control condition for step 3; without it "Save persisted the content" could pass on a button that was always live. Cheap, and it is the product's own dirty-state signal. |
| The `PUT` status code (200) | The toast alone is a UI claim; the status is the product's own transport-level evidence that the save reached the server — and it is what makes the later reload assertion a *persistence* check rather than a cache read. |
| Post-save navigation to `/settings/project-context` | The product's real behaviour after Save; pinning it means a future regression that strands the user in the editor fails loudly instead of silently. |
| Save/Discard disabled on the re-opened editor | Proves the reload produced a *clean* editor rather than a stale dirty one — the difference between "the content is there" and "the content is saved". |
| No console errors across the run | Standard side-channel check on this surface. |

## Known Defects
- **#1792 (case text)** — "Project Background" naming + the post-save location
  assumption. Pre-existing, not re-filed.

## Blocked Steps
None — every step above was executed live and observed 2026-08-26.
