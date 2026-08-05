# Test Case: Project Context character limit is enforced at 2500 characters

## Metadata
- **TMS ID**: ELITEA-2272
- **Source case**: `.agents/automation/settings-project-params/cases/ELITEA-2272.md`
  (snapshot; TMS module `settings-project-params`)
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter). **pytest marker: `@pytest.mark.p1`**
  — project convention is TMS `high` → AFS `l2_` filename prefix → pytest `p1`
  marker (NOT `p2`; see `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth).
- Project Context is **not currently set** for the active project
  (`${ELITEA_PROJECT_ID}`) — the feature renders an empty-state ("Still no
  Project Context") when unset, and only the empty-state's "Create" flow was
  exercised. Enforce this precondition via API teardown (see § Test Data)
  rather than assuming a clean environment.
- Feature is gated off for the "Public" project (`PUBLIC_PROJECT_ID` — the
  sidebar hides "Project Context" and the route redirects away); the test
  MUST run against a non-Public project. `${ELITEA_PROJECT_ID}` (399,
  "Private") satisfies this on localhost.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399` (the "Private" project selected by default
  on localhost — confirmed via the sidebar project badge and
  `settings.elitea_project_id`)

### generate-per-test (in test setup, cleaned up in its own teardown)
- 2500-character content string (`"A" * 2500`, or any filler char) — entered
  into the Project Context editor, saved, then deleted. Not a server-side
  entity created via API; created through the UI action under test.

### API endpoints used for setup/teardown (not UI, so no testid needed)
- `GET /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  → `{"id": ..., "content": "...", "enabled": true, "updated_at": ...}` when
  set, or `{"id": null, "content": "", "enabled": true, "updated_at": null}`
  when unset. **Confirmed live**: returns HTTP 200 either way (never 404 on
  GET).
- `DELETE /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  → HTTP 200 when a context exists; **HTTP 404
  `{"error": "Project context not found"}` when none exists** — confirmed
  live. Teardown must tolerate 404 (best-effort delete, not an assertion).
  Reachable via the project's generic `APIClient` (`from api import
  APIClient`); no dedicated `ProjectContextAPI` entity client exists yet —
  either add one under `automation/api/` (module-level pattern used by
  `AgentAPI` et al.) or call `APIClient().delete(path)` directly in a fixture.

## Test Steps
1. Ensure a clean precondition: `DELETE` the project's Project Context via
   API (tolerate 404 — "already clean" is a pass, not a failure).
2. Navigate to `${BASE_URL}/settings/project-context` (bare path — no sidebar
   click needed; this is the project's established navigation convention,
   `.agents/testing.md` "page objects call `navigate(...)` with bare paths").
   - **Verify**: the empty-state "Create" button (testid
     `project-context-create-button`) is visible — confirms the page/section
     loaded and the precondition (no existing context) held.
3. Click the "Create" button.
   - **Verify**: URL becomes `${BASE_URL}/settings/project-context?view=create`;
     the CodeMirror editor content area (testid
     `project-context-editor-content`) is visible; Save (testid
     `project-context-save-button`) and Discard/Cancel are both **disabled**
     (no edits yet — `isDirty` false).
4. Click into the editor content, clear it (select-all + Backspace — mirrors
   the established `fill_instructions()` pattern in `skill_form_page.py`),
   then enter **exactly 2500 characters** (paste via clipboard write +
   `Control+V`/`Meta+V` — confirmed live to go through CodeMirror's
   `EditorState.transactionFilter` the same as native typing, and is
   dramatically faster than 2500 individual `keyboard.type()` keystrokes for
   this volume; clipboard permissions are already granted globally in
   `conftest.py`'s `context` fixture).
   - **Verify**: the character counter (testid `project-context-char-counter`)
     reads exactly `0 characters left. You have reached the maximum character
     limit.` — confirmed live, this exact string.
   - **Verify**: the editor content's text length is exactly 2500 (read via
     `.text_content()` on the `project-context-editor-content` testid, same
     pattern as `SkillFormPage.get_instructions()`).
5. **Verify**: Save button (testid `project-context-save-button`) is
   **enabled** at exactly 2500 characters (regression #5667 per the case
   title/step 3).
6. With focus still in the editor (cursor at end), press one additional
   character key (e.g. `B`).
   - **Verify**: no error is thrown, no console error appears.
7. **Verify**: the additional character is silently rejected — content length
   is still exactly 2500 (same `.text_content()` read), and the character
   counter still reads `0 characters left. You have reached the maximum
   character limit.` (unchanged from step 4 — confirmed live: CodeMirror's
   `transactionFilter` clips the insert to the remaining space, which is 0,
   so the transaction becomes a no-op).
8. **Verify**: Save button remains **enabled** (matches case's Expected Final
   State and step 6).
9. Click Save.
   - **Verify**: success toast "Project Context saved" appears; page
     navigates to the saved view (URL reverts to
     `${BASE_URL}/settings/project-context`, no `?view=` query param).
10. (Teardown, not a case step) `DELETE` the Project Context via API to
    restore the empty-state precondition for the next run.

## Expected Results
- Content entry is accepted and reflected in the editor up to exactly 2500
  characters.
- The Save button is enabled at the exact 2500-character boundary, both
  before and after an additional (rejected) keystroke — this is the case's
  named regression (#5667) and its stated Pass criterion.
- Characters beyond the 2500 limit are silently rejected (not appended,
  no error thrown) and a "maximum character limit" warning is shown via the
  character counter.
- Save persists successfully (confirms the enabled Save button isn't a false
  positive — the action it gates actually succeeds).
- No console errors at any step.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Project Context | Target page/section loads successfully | AFS step 2 | `step 2`: Create-button testid visible | asserted |
| 2 Enter exactly 2500 characters in the Project Background editor | Field accepts the input and displays the entered value | AFS steps 3–4 | `step 4`: content length == 2500 via `.text_content()` | asserted *(decomposed: step 3 opens the editor, step 4 enters the text)* |
| 3 Verify the Save button is enabled at exactly 2500 characters (regression #5667) | Condition holds as described | AFS step 5 | `step 5`: Save button `is_enabled()` | asserted |
| 4 Attempt to type additional characters beyond 2500 | Action completes without error and produces the expected UI state | AFS step 6 | `step 6`: no console error after the extra keystroke | asserted |
| 5 Verify additional characters are rejected or a character limit warning is shown | Condition holds as described | AFS step 7 | `step 7`: content length still 2500 AND char-counter text unchanged | asserted *(both halves of the case's "or" are true simultaneously on this live build, not exclusive alternatives)* |
| 6 Verify the Save button remains enabled at the 2500 character boundary | Condition holds as described | AFS step 8 | `step 8`: Save button `is_enabled()`, second read | asserted |
| Objective/Expected Final State: Save button remains enabled at the 2500 character boundary | (restates step 6) | AFS step 8 | `step 8` | asserted *(no separate row needed — identical to step 6)* |

## Axis 2 — Analyst additions
- `step 3` asserts Save/Discard start **disabled** before any edit — *added:
  this is the control condition proving the later "enabled" assertions
  (steps 5/8) are a real state change caused by content entry, not always-on
  buttons.*
- `step 9` clicks Save and asserts the "Project Context saved" toast plus the
  post-save URL — *added: closes the loop on the case's implicit assumption
  that an enabled Save button actually functions; also gives step 10's
  teardown something deterministic to delete.*
- `step 6`/`step 7` assert **no console error** on the rejected keystroke —
  *added: a silent-truncation feature is exactly the kind of interaction
  that can throw an uncaught exception in the editor's transaction pipeline
  without visibly breaking the UI; confirmed live there is none on this
  build.*

## Cleanup
1. `DELETE /elitea_core/project_context/prompt_lib/{ELITEA_PROJECT_ID}/project-context`
   (best-effort — tolerate 404) — both before the test (precondition) and
   after (teardown), so the run is idempotent and repeatable.

## Concrete Handles (discovered during exploration)

All elements below are in `EliteaUI/src/[fsd]/features/settings/ui/project-context/`
unless noted. **None of these testids exist yet — all four are new,
implementer must add via `add-data-testid`** (locator policy is testid-only,
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy).

| Element | File | Recommended testid | How to add |
|---|---|---|---|
| "Create" button (empty state) | `ProjectContextEmptyState.jsx` — `<Button.BaseBtn variant={BUTTON_VARIANTS.elitea} onClick={() => onNavigate('create')}>Create</Button.BaseBtn>` | `project-context-create-button` | Add `data-testid="project-context-create-button"` directly on the `Button.BaseBtn` JSX (matches the established call-site pattern, e.g. `data-testid="skill-save-button"` in `SaveSkillButton.jsx`) |
| CodeMirror editor content node | `ProjectContextEditor.jsx` — `<Field.CodeMirrorEditor value={content} notifyChange={handleContentChange} extensions={markdownExtensions} maxLength={MAX_CHARS} readOnly={!canEdit} />` | `project-context-editor-content` | Add `contentTestId="project-context-editor-content"` to the `Field.CodeMirrorEditor` call — this is the SAME established shared-component prop used by `skill-instructions-editor-content` (`CreateSkillForm.jsx:309`) and `toolkit-raw-json-editor-content` (`ToolCustom.jsx:218`); `CodeMirrorEditor.jsx` wires it onto `.cm-content` via `EditorView.contentAttributes` since CodeMirror renders its own internal DOM. No page-object raw-selector exception needed — this IS the sanctioned pattern for CodeMirror content. |
| Save button (editor header) | `ProjectContextEditor.jsx` — `headerActions` → `<Button.BaseBtn variant={BUTTON_VARIANTS.contained} disabled={!isDirty \|\| isSaving} onClick={handleSave}>Save</Button.BaseBtn>` | `project-context-save-button` | `data-testid="project-context-save-button"` directly on the `Button.BaseBtn` JSX |
| Character counter | `ProjectContextEditor.jsx` — `<Typography variant="bodySmall" sx={styles.charCounter}>{MAX_CHARS - content.length} characters left. {limitReached && '...'}</Typography>` | `project-context-char-counter` | `data-testid="project-context-char-counter"` on the `Typography` |

Not touched by this case (no testid requested — scope discipline,
`.agents/role-overrides.md` "touches" = actually invoked on this test's
executed path):
- "Build with AI" button on the empty state
- Discard/Cancel button (case never discards)
- Edit-mode/Preview-mode toggle, Import-from-file, Copy-to-clipboard toolbar
  buttons
- `ProjectContextSavedView.jsx`'s Edit/Delete/toggle controls — this AFS's
  cleanup uses the **API** DELETE endpoint instead of the UI delete flow, so
  no testid is needed there for this case. (A future case that exercises the
  saved view's own UI — e.g. "delete Project Context via UI" — would need
  its own testids there; do not add them speculatively here.)

## Network Behavior
- `PUT /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  — fires on Save click; body `{content, enabled}`; 200 on success. Wait for
  this response (or the resulting toast) before asserting the post-save URL,
  not a fixed timeout.
- `GET /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  — fires on page load (`useProjectContextQuery`); confirmed live it returns
  200 with `content: ""` when unset (never 404 on GET — only DELETE 404s
  when nothing exists).

## Known Defects Found During Exploration
None found. The case's own regression reference (#5667 — Save button
disabled at the 2500 boundary) does NOT reproduce on this build: `Save` is
gated purely on `isDirty` (any edit at all), independent of character count,
so it stays enabled through and past the boundary. Confirmed live via
clipboard-paste of exactly 2500 chars (Save enabled) and one further
rejected keystroke (Save still enabled) — see the embedded screenshot below.
This is the case passing as authored, not a clarification or reverse-masking
situation — the case's own "Pass" criterion (Save enabled at 2500) is what
was observed.

Evidence: `test-results/screenshots/ELITEA-2272-step-03-2500-boundary-save-enabled.png`
(viewport screenshot at the 2500-char boundary — char counter shows "0
characters left. You have reached the maximum character limit.", Save/Cancel
both enabled).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: no existing page object covers Settings → Project Context.
  Create `automation/pages/project_context_page.py` (new file) rather than
  bolting onto `user_profile_settings_page.py` (that page is scoped to
  `/user-settings/profile` and `/settings/personalization`, a different
  route family, and its existing locators are pre-policy `fallback=`-based
  tech debt — do not pattern-match its locator style for new code).
- Clearing the editor before typing: mirror `SkillFormPage.fill_instructions()`'s
  `select_text()` + `Backspace` pattern (`automation/pages/skill_form_page.py:222`)
  rather than reinventing it — but use clipboard-paste (`Control+V`/`Meta+V`
  after `navigator.clipboard.writeText(...)` via `page.evaluate`) instead of
  `keyboard.type()` for the 2500-char fill itself, for speed. Both are real
  user-input paths that pass through CodeMirror's `transactionFilter`
  identically — confirmed live.
- Reading editor content: mirror `SkillFormPage.get_instructions()` —
  `.text_content()` on the `project-context-editor-content` testid, `.strip()`d.
- Wait strategy: after Save, wait for the toast (`expect(toast).to_be_visible()`)
  or the URL change away from `?view=create`, not a fixed timeout — no
  `page.wait_for_timeout` calls, per `.agents/conventions.md` "No `sleep`/
  `waitForTimeout` — framework waits only" (note: `skill_form_page.py`'s
  `fill_instructions()` uses several `wait_for_timeout` calls — that is
  pre-existing tech debt in a file this AFS explicitly recommends NOT
  pattern-matching for locator style; don't carry the timeout habit over
  either).
- Test data string: any single repeated printable ASCII character (e.g.
  `"A" * 2500`) is sufficient — the feature enforces a character *count*
  limit, not a content-shape constraint (confirmed via `PROJECT_CONTEXT_MAX_LEN
  = 2500` in `projectContext.constants.js`, a plain length comparison).
