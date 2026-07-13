# Test Case: Import Skill Non-Base Version

## Metadata
- **TMS ID**: ELITEA-1738
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills section is available with export and import capabilities.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Source skill name: kebab-case, e.g. `elitea-1738-export-skill` — **must be
  lowercase letters/digits/hyphens only, no leading/trailing hyphen** (same
  live client-side validation already documented for ELITEA-1737 — see that
  AFS's Known Defects / clarification #20; not re-filed here since it's the
  same product behavior, already tracked).
- Source skill description: any non-empty string, e.g. `"Automation test
  skill for non-base version export/import verification (ELITEA-1738)."`.
- Source skill tag: any string committed via Enter in the Tags combobox,
  e.g. `"regression"`.
- Source skill (base version) instructions: any non-empty string under the
  2500-char limit, e.g. `"You are a test skill created for ELITEA-1738
  base-version export/import verification. Always respond with the single
  word BASE."`.
- Additional version name: `ver_1` (per case Test Data — must not be
  `"base"`, the reserved `LATEST_VERSION_NAME`; the live "Create version"
  dialog rejects that value with a toast, see Concrete Handles).
- ver_1 instructions: base instructions + an appended sentence distinguishing
  it, e.g. `" This is version ver_1 with modified instructions - respond
  with VER1 instead."` — the distinguishing text is what step 5's field-parity
  assertion keys off.
- Downloaded export file: `${skill-name}.ver_1.md` (note: Playwright's
  download-suggested filename embeds the **exported version name**, unlike
  the base-version case where the file is just `${skill-name}.md` — see
  Concrete Handles), written to the Playwright download directory — read
  back and re-uploaded in the same test.

No `reuse-existing` or `generate-shared-with-cleanup` data applies — export/
import is inherently a fresh-state round trip (source skill + its ver_1
version + the exported file + the resulting imported skill), so everything
is generated per test and torn down in the same test's teardown.

## Test Steps
1. Navigate to `${BASE_URL}/skills/create`. Fill Name, Description, Tags
   (commit tag with Enter), Instructions (base-version content). Save.
   - **Verify**: form loads, Save enabled only after kebab-case name +
     required fields are valid; nav-blocker "unsaved changes" dialog
     appears — confirm it. URL settles on `/skills/all/{id}`; note the
     source skill ID (e.g. `101`) — this is the `base` version, Version ID
     equals the skill ID on first save (e.g. `101`/`101`).
2. On the skill detail page, edit the Instructions field (append
   distinguishing text), then click **"Save As Version"** (in the
   version tab bar, next to "Save"/"Discard" — NOT the overflow menu).
   A **"Create version"** dialog opens with a single "Name" textbox and a
   disabled "Save" until non-empty.
   - **Verify**: enter `ver_1`, click the dialog's Save. Toast `Version
     "ver_1" created` appears; URL becomes `/skills/all/{skillId}/{newVersionId}`
     (e.g. `/skills/all/101/102`); the VERSION selector (`id="skill-version-select"`)
     now shows `ver_1`; Skill ID stays `101`, Version ID becomes the new
     value (`102`). Both `base` and `ver_1` versions now exist on the skill.
3. With `ver_1` selected, open the overflow/controls menu
   (`skill-controls-menu-button`) and click the VERSION-scoped **Export**
   item (`export-version-menuitem`).
   - **Verify**: a `.md` file downloads. **The downloaded filename embeds
     the exported version name** — observed as
     `elitea-1738-export-skill.ver_1.md` (pattern:
     `${skill-name}.${version-name}.md`), NOT a bare `${skill-name}.md` as
     seen for base-version exports in ELITEA-1737. Implementer should
     assert the download's `suggested_filename()` contains both the skill
     name and `ver_1`, not do an exact-match on `${skill-name}.md`.
4. Read the downloaded `.md` file.
   - **Verify**: YAML frontmatter contains `name`, `description`,
     `elitea_version: ver_1`, `tags` (list); the markdown body (after the
     closing `---`) is the ver_1 instructions text (base text + the
     appended distinguishing sentence). **Note**: unlike the base-version
     export explored in ELITEA-1737 (whose frontmatter has no `version`-ish
     key at all), a **non-base** version export DOES carry an explicit
     `elitea_version: <version-name>` frontmatter key — confirmed live in
     this run. This is an additional discovered fact, not a case
     requirement to assert against (the case's own Test Data table doesn't
     list a frontmatter field for ELITEA-1738), but it's a useful assertion
     opportunity for the implementer (Axis 2 addition, see Coverage Map).
5. Navigate to `${BASE_URL}/skills/all`. Click the **"Import"** button
   (top-right toolbar). Upload the ver_1-exported `.md` file.
   - **Verify**: an "Import parameters" dialog opens showing PROJECT, the
     entity name, and **`Type: Skill | Version: base`** — confirmed live:
     even though the uploaded file was exported from `ver_1`, the dialog
     unconditionally displays `Version: base` (this is a hardcoded string
     in `SkillImportModal.jsx` — `Type: Skill | Version: ${LATEST_VERSION_NAME}`
     — not derived from the file's `elitea_version` field). Expand "Show
     details" and verify the Description and Instructions preview fields
     match the source skill's **ver_1** content exactly (confirmed live —
     the modified/appended instructions text is what's previewed, proving
     the exported ver_1 content — not base — is what's carried into the
     import).
6. Click the dialog's **"Import"** button.
   - **Verify**: navigation to `/skills/all/{new-id}` (e.g. `/skills/all/102`,
     unique vs. source skill id `101`); a success toast appears (implicit —
     new skill visible immediately after redirect); `POST
     /elitea_core/skill_import/prompt_lib/{project}/` returns `201`.
7. On the imported skill's detail page, verify:
   - VERSION selector shows **`base`** (confirmed live — regardless that
     the exported source was `ver_1`, this is the case's central
     assertion and it holds).
   - Name, Description, Tags match the source skill's **ver_1** content
     (i.e. the exported version's content, not the skill's original base
     version) exactly.
   - Instructions textbox content matches the ver_1 instructions
     (base text + appended distinguishing sentence) exactly — this is
     the strongest signal that the exported *version's* content (not a
     stale/default base) made it through the round trip.
   - Skill ID (Information section) is unique vs. the source skill ID.
8. Edit a field on the imported skill (e.g. append text to Description)
   to enable Save, then click Save.
   - **Verify**: Save completes with no validation error text, no failed
     network response (`PUT /elitea_core/skill/prompt_lib/{project}/{id}`
     and `PUT .../{id}/{versionId}` both `200`), and no new console
     errors; Save/Discard buttons return to disabled state (dirty flag
     cleared) confirming a clean save.

## Expected Results
- A new Skill entity is created from the exported (non-base, `ver_1`) `.md`
  file with a unique ID different from the source skill.
- The imported Skill's version is **`base`** — regardless of the fact that
  `ver_1` was the exported version — and its name/description/tags/
  instructions match the **exported ver_1 content** exactly (not the
  source skill's original base-version content).
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
| Test Data: Initial skill version = `base` | skill created with `base` version | step 1 | step 1: URL settles on `/skills/all/{id}`, Version ID = Skill ID | asserted |
| Test Data: Additional version name = `ver_1` | version created and named `ver_1` | step 2 | step 2: "Create version" dialog, toast `Version "ver_1" created`, VERSION selector shows `ver_1` | asserted |
| Test Data: Version to export = `ver_1` | export operates on the `ver_1` version, not base | step 3 | step 3: export triggered while VERSION selector shows `ver_1`; filename embeds `ver_1` | asserted |
| 1 Create a Skill with base version, modify instructions, save as new version `ver_1` | Skill has both `base` and `ver_1` versions saved | steps 1–2 | step 2: VERSION selector toggled to `ver_1`, both versions exist (verified by VERSION dropdown containing both) | asserted |
| 2 Switch to `ver_1` version and export | `.md` file downloaded representing `ver_1` | step 3 | step 3: download event; filename contains `ver_1` | asserted |
| 3 Import the exported `.md` file | import completes without errors, new Skill entry appears | steps 5–6 | step 6: navigation to new skill id + `201` on import POST | asserted |
| 4 Open imported Skill and verify `base` version created | imported Skill shows `base` version (not `ver_1`) | step 7 | step 7: VERSION selector reads `base` | asserted |
| 5 Verify all fields (name, description, instructions, tags) populated correctly | fields match the exported `ver_1` version's content | step 7 | step 7: Name/Description/Tags/Instructions compared to source's ver_1 content | asserted |
| 6 Edit a field and save | Skill saves without errors, changes persisted | step 8 | step 8: no validation error, `PUT` both `200`, dirty flag clears | asserted |

### Axis 2 — Analyst additions

- step 4 asserts the exported `.md`'s frontmatter carries an explicit
  `elitea_version: ver_1` key — *added: not required by the case's own Test
  Data table, but a directly observable, stable fact discovered live in
  this run and a strong assertion opportunity (distinguishes this AFS's
  non-base export from ELITEA-1737's base export, which has no such key at
  all — see that AFS's clarification #21). Not filed as a defect/clarification:
  both behaviors (present for non-base, absent for base) are internally
  consistent product behavior, not case-text drift.*
- step 3 documents that the downloaded filename pattern is
  `${skill-name}.${version-name}.md` for non-base exports (vs. bare
  `${skill-name}.md` for base, per ELITEA-1737) — *added: a required
  implementer handle not explicit in the case text; asserting an exact
  filename match without this would be a hard-coded assumption bug in the
  automated test.*
- step 5 asserts the Import-parameters dialog's "Show details" preview
  shows the **ver_1** description/instructions (not base) — *added:
  decomposes case step 3 ("Import completes without errors") into an
  intermediate verification point proving the exported version's content
  (not a stale default) is what's staged for import, before the final
  Import click. Confirmed live against `SkillImportModal.jsx`.*
- step 5 also documents the live source-code confirmation
  (`SkillImportModal.jsx`: `subtitle={\`Type: Skill | Version:
  ${LATEST_VERSION_NAME}\`}`) that the dialog's "Version: base" label is
  **hardcoded**, not derived from the uploaded file's `elitea_version`
  field — *added: this is the mechanism behind the case's central
  assertion (imported skill always lands on `base`) and is useful context
  for the implementer to understand why the assertion holds regardless of
  which version was exported, rather than treating it as coincidental.*
- step 8 asserts zero new console errors during the final Save — *added:
  standard side-channel check per skill discipline, mirrors ELITEA-1737.*
- step 2 documents that `"base"` (case-insensitive, `LATEST_VERSION_NAME`)
  is a **reserved name** rejected by the "Create version" dialog with a
  toast error (`"base" is reserved. Please pick a different version
  name.`) — *added: confirmed by reading `SaveSkillVersionButton.jsx`
  (not independently exercised live in this run — see Blocked Steps note);
  relevant defensive-negative-case context for the implementer, not part
  of this case's own steps.*
- step 3 documents the overflow menu's VERSION group gained a **"Set as a
  default"** item (disabled while viewing a version that already IS the
  default) not present in the ELITEA-1737 AFS's menu inventory — *added:
  menu composition differs slightly by context (viewing `base` vs.
  viewing `ver_1`); when viewing `ver_1`, "Set as a default" is enabled
  and "Delete" (version) is enabled — confirmed live; when viewing `base`,
  both are disabled since base is the implicit default and can't be
  deleted. Useful for the implementer's menu-item assertions if the test
  also exercises the `ver_1`-viewing state.*

## Cleanup
1. Delete the imported skill via the overflow menu → "Delete skill" →
   type the skill name to confirm → click Delete. (Verified in this run:
   deletes cleanly, redirects to `/skills/all`.)
2. Delete the source skill the same way (deleting the skill removes both
   its `base` and `ver_1` versions — no separate version-delete step
   needed).
3. Alternatively/preferably for automated cleanup, use the existing
   `skill_api` fixture (`automation/fixtures/api_fixtures.py`,
   `SkillAPI.delete_skill(skill_id)` in `automation/api/client.py:1182`)
   in test teardown for both the source and imported skill IDs — mirrors
   the `clean_skill` fixture pattern already used in
   `test_skill_management.py` and the pattern recommended in the
   ELITEA-1737 AFS. Track both IDs (source from step 1, imported from
   step 6/7) and delete both, tolerating "already gone" errors.

## Concrete Handles (discovered during exploration)

Reused as-is from the ELITEA-1737 AFS (`test-specs/skills/l3_import_skill_base_version_ELITEA-1737.md`)
where unchanged — not re-verified in isolation in this run except where noted:

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skill create form / detail form fields | Existing `SkillFormPage` (`automation/pages/skill_form_page.py`) — `name_input`, `description_input`, `instructions_editor` / `instructions_editor_content`, `save_button` | n/a — reuse existing page object |
| Skill detail page (ID, controls menu, export) | Existing `SkillDetailPage` (`automation/pages/skill_detail_page.py`) — `controls_menu_button`, `get_skill_id()`, `export_base_version_via_menu()` | n/a — reuse existing page object; **new** method needed for exporting a *non-default* version, see Automation Hints |
| Overflow-menu **Export** item (version-scoped) | `page.get_by_test_id("export-version-menuitem")` — confirmed present and correctly exports the *currently selected* version (not always base) in this run | `page.get_by_role("menuitem", name="Export")` scoped to VERSION group |
| **VERSION selector** (base ⇄ ver_1 switcher on the edit/detail page — distinct from `SkillDetailPage`'s read-only "Version" display) | `page.locator("#skill-version-select")` — confirmed present live (`SkillTabBar.jsx`, `id="skill-version-select"`); **no `data-testid` yet** | `page.get_by_role("combobox", name=<current version name>)` — works but name changes with selection, not stable across steps |
| **"Save As Version" button** (creates a new named version from current edits) | `page.get_by_role("button", name="Save As Version")` — confirmed live; **no `data-testid` yet** | none robust — accessible name is stable text, low risk |
| **"Create version" dialog** — Name textbox | `page.get_by_role("dialog").get_by_role("textbox", name="Name")` — confirmed live, single unlabelled-by-testid field | none needed, dialog scoping is sufficient |
| **"Create version" dialog** — Save (confirm) button | `page.get_by_role("dialog").get_by_role("button", name="Save")` — disabled until Name is non-empty | none needed |
| Skills list **Import** button | `page.get_by_test_id("skills-import-button")` — **now has a testid** (confirmed live this run); ELITEA-1737's AFS flagged this as missing at the time — **resolved since**, no action needed | `page.get_by_role("button", name="Import")` |
| Import-parameters dialog **Import** (confirm) button | `page.get_by_role("dialog").get_by_role("button", name="Import")` — scoping to the dialog required, toolbar button shares the same accessible name | none needed if scoped correctly |
| Import-parameters dialog **Show details** toggle | `page.get_by_role("button", name="Show details")` — confirmed live | none needed |
| Delete-skill menu item | `page.get_by_test_id("skill-delete-menu-item")` | `page.get_by_role("menuitem", name="Delete skill")` |
| Delete-confirmation name field | `page.get_by_test_id("delete-confirm-name-input")` — **now has a testid** (confirmed live this run; internally has an `#name` child input — `page.get_by_test_id("delete-confirm-name-input").locator("#name")`); ELITEA-1737's AFS flagged this as missing at the time — **resolved since** | `page.get_by_role("dialog").get_by_role("textbox")` |
| Delete-confirmation confirm button | `page.get_by_role("dialog").get_by_role("button", name="Delete")` | none needed |
| Skill Information section — Skill ID / Version ID | Existing `SkillDetailPage.get_skill_id()`; Version ID currently only readable via the "Copy version ID" button's text or the URL's second path segment (`/skills/all/{skillId}/{versionId}`) — **no dedicated method yet**, see Automation Hints | n/a |

## Network Behavior
- `POST /elitea_core/skill_import/prompt_lib/{project_id}` — fires on
  clicking Import in the import-parameters dialog; returned `201 Created`
  in this run.
- `GET /elitea_core/skills/prompt_lib/{project_id}?...` — list refetch
  after import.
- `GET /elitea_core/skill/prompt_lib/{project_id}/{id}` — detail fetch
  when landing on the imported skill's page.
- `PUT /elitea_core/skill/prompt_lib/{project_id}/{id}` and
  `PUT /elitea_core/skill/prompt_lib/{project_id}/{id}/{versionId}` — both
  fire on the final Save (step 8); both returned `200` in this run.
- The **"Save As Version"** action (step 2) was not isolated in the
  network log in this run (no explicit capture between the dialog Save
  click and the toast) — by analogy with the version-switch pattern in
  `SkillVersionSelector.jsx` (attach/detach) this is likely a dedicated
  version-create endpoint, distinct from the base skill's own PUT/POST —
  **unconfirmed, re-verify with a fresh network capture before hard-coding**
  if the implementer wants to assert on it directly (not required — the
  UI-level toast + URL-change + VERSION-selector assertions are sufficient
  and were what this run actually verified).
- The **Export** request itself was not captured in this run's network log,
  same caveat as ELITEA-1737 — it triggers a file **download**, not a
  plain XHR; assert on the Playwright `download` event (filename pattern
  `${skill-name}.${version-name}.md`) rather than hunting for the
  underlying request.

## Known Defects Found During Exploration
None. No functional defects and no case-text drift found in this run — the
case's Test Data and Steps matched live behavior exactly, including the
central non-obvious assertion (imported skill always lands on `base`
regardless of exported version) which was independently confirmed both at
the UI level and by reading `SkillImportModal.jsx`'s hardcoded
`Version: ${LATEST_VERSION_NAME}` label.

Reused from ELITEA-1737 (not re-filed, same underlying product behavior,
already tracked there):
- [#20](https://github.com/EliteaAI/elitea-testing-public/issues/20) —
  skill names must be kebab-case; applies identically to this case's
  skill-creation step.

## Blocked Steps
None — all case steps executed end-to-end successfully in this run (source
skill id `101` with `base`/`ver_1` versions `101`/`102`, imported skill id
`102` with `base` version `103`, all created and cleaned up during this
analysis). One Axis-2 addition (the "base" reserved-name rejection in the
Create-version dialog) was documented from source-code reading rather than
independently exercised live — flagged inline, not a blocker for this
case's own steps.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. New file:
  `automation/tests/ui/skills/test_skill_export_import.py` — the same file
  ELITEA-1737's automation would add (if that PR is already merged, extend
  it with a new `test_import_skill_non_base_version` test rather than
  duplicating the file; if not yet merged, coordinate file ownership with
  that implementation).
- `SkillDetailPage` needs **new methods** beyond what ELITEA-1737 needed:
  - `save_as_version(version_name: str)` — clicks "Save As Version",
    fills the "Create version" dialog's Name field, clicks Save, waits for
    the `Version "{version_name}" created` toast and for the URL to
    contain `/{skillId}/{newVersionId}`.
  - `switch_version(version_name: str)` — clicks the `#skill-version-select`
    combobox and selects the named version from its menu (not needed by
    this case since `save_as_version` already lands on the new version,
    but a natural companion method worth adding for future version-related
    cases).
  - `get_version_id()` — parses the current version id from the URL's
    second path segment (mirrors the existing `get_skill_id()` pattern in
    the same file), needed to assert Version ID changes across steps 1→2→7.
  - `export_version_via_menu()` — generalize the existing
    `export_base_version_via_menu()` to export whatever version is
    currently selected (same `export-version-menuitem` testid, the method
    just shouldn't assume "base" in its name/docstring since it now
    exports ver_1 too); rename or add a thin wrapper, implementer's call.
- Two testids flagged as missing in ELITEA-1737's AFS are now confirmed
  present (`skills-import-button`, `delete-confirm-name-input`) — no
  `add-data-testid` work needed for those. Two *new* elements in this
  case still lack testids and are lower priority (their accessible-role
  locators are stable and unique in this run): the `#skill-version-select`
  combobox and the "Save As Version" button. Flag via `add-data-testid`
  only if they prove flaky in CI — not blocking for initial implementation.
- Read the downloaded file's frontmatter with `yaml.safe_load`, same
  approach as ELITEA-1737: assert `name`, `description`, `tags`, and (new
  for this case) `elitea_version == "ver_1"`; the body (after the closing
  `---`) is the ver_1 instructions text.
- Use the `skill_api` fixture (session-scoped `SkillAPI`) for teardown of
  both skill IDs — do not delete via UI in automated teardown (slower,
  more brittle); UI-delete was only used here for interactive
  verification, mirrors ELITEA-1737's guidance exactly.
- Wait strategy: after clicking "Save As Version" dialog's Save, wait for
  the toast text `Version "ver_1" created` (or the URL to contain the new
  version id) rather than a fixed sleep. After the final Save in step 8,
  wait for the Save button to return to `disabled` state, mirroring
  ELITEA-1737's `wait_for_form_validation()` guidance.
