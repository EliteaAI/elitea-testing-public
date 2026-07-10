# Test Case: Import Skill (Base Version)

## Metadata
- **TMS ID**: ELITEA-1737
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills → Import feature is available from the Skills list page toolbar.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Source skill name: kebab-case, e.g. `elitea-1737-export-skill` — **must be
  lowercase letters/digits/hyphens only, no leading/trailing hyphen** (live
  client-side validation; the case's own example `"Test Export Skill"` fails
  this rule — see Known Defects / clarification #20).
- Source skill description: any non-empty string, e.g. `"Automation test
  skill for base version export/import round trip (ELITEA-1737)"`.
- Source skill tag: any string committed via Enter in the Tags combobox,
  e.g. `"regression"`.
- Source skill instructions: any non-empty string under the 2500-char limit,
  e.g. `"You are a test skill created for ELITEA-1737 export/import base
  version verification. Always respond with the single word CONFIRMED."`
- Downloaded export file: `${skill-name}.md`, written to the Playwright
  download directory — read back and re-uploaded in the same test.

No `reuse-existing` or `generate-shared-with-cleanup` data applies — export/
import is inherently a fresh-state round trip (source skill + its exported
file + the resulting imported skill), so everything is generated per test
and torn down in the same test's teardown.

## Test Steps
1. Navigate to `${BASE_URL}/skills/create`.
   - **Verify**: form loads (`skill-name-input` visible), Save button
     initially disabled.
2. Fill Name, Description, Tags (commit tag with Enter), Instructions.
   - **Verify**: Save button becomes enabled once all required fields are
     valid (name must pass kebab-case validation — see Test Data note).
3. Click Save.
   - **Verify**: nav-blocker "unsaved changes" dialog may appear — confirm
     it if present (existing `save_and_wait_for_navigation` page-object
     method already handles this). URL settles on `/skills/all/{id}`; note
     the source skill ID (e.g. `28`).
4. Open the skill's overflow/controls menu (three-dot button) and click the
   version-scoped **"Export"** menu item (distinct from the skill-scoped
   "Share"/"Pin to top"/"Delete skill" items further down the same menu).
   - **Verify**: a file downloads with a `.md` extension, named
     `${skill-name}.md`.
5. Read the downloaded `.md` file.
   - **Verify**: YAML frontmatter contains `name`, `description`, `tags`
     (as a list); the markdown body (after the closing `---`) is the
     instructions text. **No explicit `version:` key exists in the file**
     — this is expected live behavior, not a bug (see clarification #21);
     do not assert for a `version:` frontmatter key.
6. Navigate to `${BASE_URL}/skills/all`. Click the **"Import"** button in
   the page toolbar (top-right, next to the view toggler).
   - **Verify**: a native file-chooser opens (`browser_file_upload` /
     Playwright `page.on('filechooser')`).
7. Upload the exported `.md` file.
   - **Verify**: an "Import parameters" dialog opens showing PROJECT,
     the entity name, and `Type: Skill | Version: base`. The dialog's
     entity card also has a collapsed "Show details" section
     (`IWModalEntityCardWrapper`/`SkillImportModal.jsx`, `defaultExpanded=
     false`) that, once expanded, renders Description and Instructions
     preview fields matching the source skill — expand it and verify
     both.
8. Click the dialog's **"Import"** button.
   - **Verify**: navigation to `/skills/all/{new-id}`; a success toast
     "Skill imported successfully." appears; `new-id` ≠ source skill ID.
9. On the imported skill's detail page, verify:
   - VERSION selector shows `base`.
   - Name, Description, Tags match the source skill exactly.
   - Instructions textbox content matches the source skill's instructions
     exactly.
   - Skill ID (Information section) is unique vs. the source skill ID.
10. Edit a field slightly (e.g. append text to Description) to enable the
    Save button, then click Save.
    - **Verify**: Save completes with no validation error text, no failed
      network response, and no new console errors; Save/Discard buttons
      return to disabled state (dirty flag cleared) confirming a clean
      save.

## Expected Results
- A new Skill entity is created from the exported `.md` file with a
  unique ID different from the source.
- The imported Skill's `base` version is present and its
  name/description/tags/instructions match the source skill's exported
  content.
- Saving the imported Skill (after a further edit) completes without
  validation or network errors.
- `POST /elitea_core/skill_import/prompt_lib/{project}/` returns `201`.
- `PUT /elitea_core/skill/prompt_lib/{project}/{id}` (and the accompanying
  `PUT .../{id}/{versionId}`) return `200` on the final Save.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Test Data: "any descriptive name, e.g. 'Test Export Skill'" | name accepted | step 2 | step 2: Save enabled only after kebab-case name | clarification *(case example name fails live validation — filed [#20](https://github.com/EliteaAI/elitea-testing-public/issues/20))* |
| Test Data: exported file contains "version" field | version field present | step 5 | step 5: frontmatter inspected | clarification *(no `version:` key in file; round trip still correct via UI-inferred version — filed [#21](https://github.com/EliteaAI/elitea-testing-public/issues/21))* |
| 1 Create a Skill with instructions, description, name, tags | Skill created and saved with all fields populated | steps 1–3 | step 3: URL settles on `/skills/all/{id}` | asserted |
| 2 Export the base version | file downloads, `.md` extension | step 4 | step 4: download event + filename extension | asserted |
| 3 Open exported file, verify contents | name, description, version, tags, instructions present | step 5 | step 5: frontmatter + body parsed | asserted *(version sub-clause: clarification, see above)* |
| 4 Skills → Import → import the file | import completes, new Skill entry appears | steps 6–8 | step 8: success toast + navigation to new id | asserted |
| 5 Verify imported Skill has new unique ID | new ID ≠ source ID | step 9 | step 9: Skill ID compared to source | asserted |
| 6 Verify base version + instructions present and match | `base` version present, instructions match | step 9 | step 9: VERSION selector + instructions textbox content | asserted |
| 7 Save the imported Skill | saves without errors | step 10 | step 10: no validation text, Save/Discard revert to disabled, no console errors | asserted |

### Axis 2 — Analyst additions

- step 7 asserts the import-parameters dialog previews Description and
  Instructions matching the source skill (dialog's expandable details show
  Description/Instructions text equal to source skill) —
  `SkillsListPage.expand_import_preview_details()` +
  `dialog.get_by_text(skill_description/skill_instructions)` after expanding
  "Show details" — *added: decomposes case step 4 ("Import completes without
  errors"); the case's own step 7 is "Save the imported Skill," not a
  dialog-preview check, so this is an AFS-only addition, not a traceable case
  element. Confirmed live against `SkillImportModal.jsx`/`IWModalEntityTextField.jsx`
  in implementer Phase 2 — previously the AFS listed this in step 7's Verify
  text but the shipped test only asserted `Type: Skill | Version: base` and
  the name — corrected in the same PR that added the assertions.*
- step 9 also asserts Description and Tags match the source (case step 6
  only names "instructions" explicitly) — *added: the case's Expected Final
  State section says "all fields (name, description, tags, instructions)
  correctly populated", so this belongs to the same acceptance criterion
  carried in the case's own description, not scope creep.*
- step 10 asserts zero new console errors during the final Save — *added:
  standard side-channel check per skill discipline; silent JS errors on
  save are the kind of defect a green assertion would otherwise hide.*
- step 4 explicitly disambiguates the version-scoped "Export" menu item
  from the skill-scoped items in the same overflow menu (the menu shows
  two logical groups: `VERSION` — Export/Share/Fork/Publish/Delete, and
  `SKILL` — Share/Pin to top/Delete skill) — *added: this menu structure
  is not obvious from the case text and is a required handle for the
  implementer to pick the right item.*

## Cleanup
1. Delete the imported skill via the overflow menu → "Delete skill" →
   type the skill name to confirm → click Delete. (Verified in this run:
   deletes cleanly, redirects to `/skills/all`.)
2. Delete the source skill the same way.
3. Alternatively/preferably for automated cleanup, use the existing
   `skill_api` fixture (`automation/fixtures/api_fixtures.py`,
   `SkillAPI.delete_skill(skill_id)` in `automation/api/client.py:1182`)
   in test teardown for both the source and imported skill IDs — mirrors
   the `clean_skill` fixture pattern already used in
   `test_skill_management.py`. Track both IDs (source from step 3,
   imported from step 8/9) and delete both, tolerating "already gone"
   errors the way `clean_skill` does.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skill create form (name/description/tags/instructions/save) | Already covered by existing `SkillFormPage` (`automation/pages/skill_form_page.py`) — `name_input`, `description_input`, `instructions_editor`, `save_button` `LocatorDescriptor`s | n/a — reuse existing page object, do not duplicate |
| Skill detail page (ID, version, controls menu) | Already covered by existing `SkillDetailPage` (`automation/pages/skill_detail_page.py`) — `controls_menu_button`, `get_skill_id()` | n/a — reuse existing page object |
| Overflow-menu **Export** item (version-scoped) | `page.get_by_test_id("export-version-menuitem")` — confirmed present at runtime (the click was made via this testid per the recorded Playwright code: `page.getByTestId('export-version-menuitem').click()`) | `page.get_by_role("menuitem", name="Export")` — **not unique**, disambiguate by scoping to the first "Export" occurrence (VERSION group) since a second "Publish Soon" item exists but no second "Export"; still prefer the testid |
| Skills list **Import** button | `page.get_by_role("button", name="Import")` — visible, unique on `/skills/all` toolbar | needs a `data-testid` (e.g. `skills-import-button`) added via the `add-data-testid` skill for stability — **not yet present**, flagging per Automation Hints below |
| Import-parameters dialog **Import** (confirm) button | `page.get_by_role("button", name="Import")` scoped to the dialog (`page.get_by_role("dialog").get_by_role("button", name="Import")`) — the toolbar button and dialog button share the same accessible name, so scoping to the dialog is required to disambiguate | none needed if scoped correctly |
| Skill controls overflow menu button | Existing `SkillDetailPage.controls_menu_button` (`data-testid="skill-controls-menu-button"`) | n/a |
| Delete-skill menu item | `page.get_by_test_id("skill-delete-menu-item")` (confirmed via recorded Playwright code) | `page.get_by_role("menuitem", name="Delete skill")` |
| Delete-confirmation name field | `page.get_by_role("dialog").get_by_role("textbox")` (single unlabelled textbox in the Delete confirmation dialog) | needs a `data-testid` for stability — flagging per Automation Hints |
| Delete-confirmation confirm button | `page.get_by_role("dialog").get_by_role("button", name="Delete")` | none needed |
| Success toast after import | `page.get_by_text("Skill imported successfully.")` | none needed — text is stable per this run |

## Network Behavior
- `POST /elitea_core/skill_import/prompt_lib/{project_id}` — fires on
  clicking Import in the import-parameters dialog; returned `201 Created`
  in this run.
- `GET /elitea_core/skills/prompt_lib/{project_id}?...` — list refetch
  after import (wait for this, or for the toast, before asserting the new
  skill appears in the list).
- `GET /elitea_core/skill/prompt_lib/{project_id}/{id}` — detail fetch when
  landing on the imported skill's page.
- `PUT /elitea_core/skill/prompt_lib/{project_id}/{id}` and
  `PUT /elitea_core/skill/prompt_lib/{project_id}/{id}/{versionId}` — both
  fire on Save; both returned `200` in this run.
- The **Export** request itself was not captured in this run's network log
  (a `page.goto()` between the export click and the next `browser_network_requests`
  call rotated the log). It triggers a file **download**, not a plain XHR the
  test can assert a JSON body on — implementer should assert on the
  Playwright `download` event (filename + `.md` extension) rather than
  hunting for the underlying request. If a request URL is needed, capture it
  fresh with `page.on('download')` / `page.waitForEvent('download')` plus a
  network listener that does NOT navigate away before reading it (by analogy
  with `skill_import`, likely something like
  `GET /elitea_core/skill_export/prompt_lib/{project_id}/{id}?version=base`
  — **unconfirmed, re-verify before hard-coding**).

## Known Defects Found During Exploration
None (no functional defects). Two case-text drift clarifications filed
per the reverse-masking guard (live product is correct; case text is
stale) — not blocking, both `ready-for-automation`:
- [#20](https://github.com/EliteaAI/elitea-testing-public/issues/20) —
  case's example skill name (`"Test Export Skill"`) fails the live
  kebab-case name validation.
- [#21](https://github.com/EliteaAI/elitea-testing-public/issues/21) —
  exported `.md` has no explicit `version:` frontmatter key, even though
  the case's Test Data table lists "version" as an expected field; the
  round trip still works correctly (Import dialog correctly shows
  `Version: base`).

## Blocked Steps
None — all 7 case steps executed end-to-end successfully in this run
(source skill id `28`, imported skill id `29`, both created and cleaned
up during this analysis).

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. New file:
  `automation/tests/ui/skills/test_skill_export_import.py` (fresh
  coverage — `test_skill_management.py` only covers create+execute+delete
  today, no export/import methods exist yet in `SkillFormPage` /
  `SkillDetailPage`).
- Page objects need **new methods**, not new classes — extend
  `SkillDetailPage` with `export_base_version_via_menu()` (mirrors the
  existing `pipeline_detail_page.py::export_pipeline_via_menu()` pattern —
  use `page.get_by_test_id("export-version-menuitem")`, wrap in
  `page.expect_download()`) and `delete_skill_via_menu()` already exists
  and was reused as-is for cleanup verification in this run. Add a new
  `SkillsListPage.import_skill(file_path)` method that clicks the Import
  button, handles the native file chooser (`page.expect_file_chooser()`),
  sets `file_path`, waits for the "Import parameters" dialog, and clicks
  its Import button.
- Two testids are missing for stable automation and should go through the
  `add-data-testid` skill before/alongside implementation:
  1. Skills-list **Import** button (currently only `getByRole('button',
     {name:'Import'})`, works but not the project's testid-only
     convention).
  2. Delete-confirmation dialog's name-entry textbox (currently only
     resolvable as the dialog's sole unlabelled textbox).
- Use the `skill_api` fixture (session-scoped `SkillAPI`) for teardown of
  both skill IDs, matching the existing `clean_skill` fixture pattern in
  `test_skill_management.py` — do not delete via UI in automated teardown
  (slower, more brittle); UI-delete was only used here for interactive
  verification.
- Read the downloaded file with Python's `pathlib` from Playwright's
  configured download directory (`page.expect_download()` gives a
  `Download` object; use `.path()` or `.save_as()` to a temp file, then
  parse YAML frontmatter with `yaml.safe_load` on the header block for the
  `name`/`description`/`tags` assertions, and the raw remainder for the
  instructions-body assertion).
- Wait strategy: after clicking Save in step 10, wait for the Save button
  to return to `disabled` state (dirty-flag cleared) rather than a fixed
  sleep — mirrors the existing `is_save_enabled()` / `wait_for_form_validation()`
  pattern in `SkillFormPage`.
