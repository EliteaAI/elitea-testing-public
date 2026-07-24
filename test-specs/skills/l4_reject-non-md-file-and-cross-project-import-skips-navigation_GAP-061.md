# Test Case: Skill import — non-.md file rejection and import into a different project

## Metadata
- **TMS ID**: GAP-061
- **Linked Story**: none (gap-analysis card; `coverage_target:
  src/[fsd]/features/skill/lib/hooks/useSkillImport.hooks.js`, ~6 uncovered
  branches)
- **Priority**: l4 (low, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end live
  (all 7 case steps), no blockers, no product defects. See § Classification
  note below for why this is fresh work rather than `extend-existing`
  against the merged `test_skill_export_import.py`.

## Classification note (declared reasoning, not a canon gap — routine
Rule-6 boundary call)

`automation/tests/ui/skills/test_skill_export_import.py` (merged to
`automation/base`, commits `9a30d01c`/`8cbd5633`/`79a5b077`) already covers
ELITEA-1737 (export+import base version, same project) and ELITEA-1738
(export+import a non-base version, same project) via
`SkillsListPage.import_skill()` / `.confirm_import()`. Per the
`extend-existing`-means-insert-into-same-test check (is the covering test's
missing assertions "just more cells of the same state machine, or a
genuinely separate scenario sharing only setup?"): GAP-061's two behaviors —
(a) wrong-extension rejection (no dialog ever opens) and (b) importing into
a **different** target project (asserting the app does **not** navigate,
the inverse of what both existing tests assert) — are not more states of
the existing round-trip tests. They reuse the same import UI *mechanism*
(`SkillsListPage`) but exercise a different precondition (a static fixture
file, not an exported one), a control the existing tests never touch (the
PROJECT selector), and an assertion that is the **opposite** of what the
existing tests check (no navigation vs. navigation). This is the "separate
scenario sharing only setup" case the reusable check reserves for a
sibling test, not an inserted state. Classified `ready-for-automation`, new
test added to the **same file** (shared page objects/fixtures), not
`extend-existing`.

## Preconditions
- User is logged in (localhost `auth_state`, `VITE_DEV_TOKEN`).
- At least two non-public projects accessible. Confirmed live: 5 projects
  in the selector — `Private` (399, **current/"Project A"**), `Bugs &
  Features` (406), `Elitea Development` (25), `Elitea Testing Team` (471),
  `UI Testing` (400, **used as "Project B"** — see Test Data below for why).
- Skills → Import feature available from the Skills list page toolbar
  (`skills-import-button`, already present — confirmed live).

## Test Data

### generate-per-test (written to a pytest `tmp_path` at test start, not
checked-in repo fixtures — mirrors the existing file's pattern of
generating the `.md` content programmatically rather than committing static
fixture files)
- Invalid fixture: a plain-text file with a non-`.md` extension, e.g.
  `notes.txt`, arbitrary non-empty content (content is irrelevant — the
  rejection is a pure filename-extension check, confirmed against source
  below).
- Valid fixture: a `.md` file with YAML frontmatter carrying `name` and
  `description` (both required — see Concrete Handles), e.g.:
  ```
  ---
  name: gap061-skill
  description: Automation fixture skill for GAP-061 cross-project import verification.
  tags:
    - regression
  ---
  You are a test skill created for GAP-061 cross-project import verification.
  Always respond with the single word CONFIRMED.
  ```
  Use a per-run unique `name` (e.g. `f"gap061-skill-{uuid.uuid4().hex[:8]}"`)
  to avoid any cross-run collision, consistent with the existing file's
  `uuid4().hex[:8]` suffix convention.

### reuse-existing (target project for cross-project import)
- **Target project: `UI Testing` (id `400`)`.** Confirmed live this run
  (skill create + skill delete both succeeded cleanly, `204`-equivalent UI
  outcome, no permission toast) — safe for both the import destination and
  its own cleanup. Do **not** use `Elitea Testing Team` (471): per prior
  sessions (ELITEA-1893 AFS, `fork_agent_flow_and_localhost_dev_token_
  permission_scoping.md` memory) the fixed localhost `VITE_DEV_TOKEN`
  identity lacks delete permission there for *agents*; not independently
  re-verified for skills in this session, so avoid it as an unnecessary
  risk when 400 is already confirmed-good for skills specifically.
- Source/current project: `Private` (399) — the default project this
  identity lands on; used as "Project A" throughout, matching the
  live-confirmed page title `"Skills: all - Private"`.

### Important environment caveat — cleanup needs a project-400-scoped
`SkillAPI`, not the shared `skill_api` fixture
The session-scoped `skill_api` fixture (`automation/fixtures/api_fixtures.py`)
constructs `SkillAPI(browser_cookies=_browser_cookies)` with **no
`project_id` override**, so it defaults to `settings.elitea_project_id`
(399/`Private`). The skill this case creates lives in **400**
(`UI Testing`), so deleting it via the shared fixture will silently 404 (or
worse, target the wrong skill id if IDs collide across projects — they
don't, but don't rely on that). Construct a **second, project-scoped**
client directly in the test:
```python
from api.client import SkillAPI
project_b_skill_api = SkillAPI(browser_cookies=_browser_cookies, project_id="400")
```
(`_browser_cookies` is the existing session-scoped fixture already used by
every other `*_api` fixture in `api_fixtures.py` — request it directly,
don't re-derive cookies.) Use this instance for both the case's own step 7
presence check (`list_skills()` or a direct `GET .../skill/prompt_lib/400/{id}`)
and its cleanup delete — faster and more reliable than a second in-test UI
project-switch, and the case's "confirm the imported skill is present" is
satisfied by the API read just as validly as a UI list-grep.

## Test Steps

1. With `Private` (399, "Project A") selected, navigate to the Skills list
   (`skills-import-button` visible), click Import, and — via the native
   file-chooser (`page.expect_file_chooser()`) — select a non-`.md` file
   (e.g. `notes.txt`).
   - **Verify**: a toast reading exactly `"Only .md files can be
     imported."` appears (`toast-message` testid, reused from the existing
     `import_success_toast_message` field's testid — same generic
     app-wide Toast container, error severity this time). **Verify**: the
     preview dialog (`skill-import-preview-dialog`) never renders —
     confirmed live via `document.querySelector(...)` returning null and
     `[role="dialog"]` count `0` after the toast fires.
2. Click `skills-import-button` again (same session — confirmed live this
   works correctly back-to-back with step 1, no stale-input contamination)
   and select the valid `.md` fixture via the native file chooser.
   - **Verify**: `skill-import-preview-dialog` opens.
3. Read the preview main-entity card.
   - **Verify**: `skill-import-preview-name` text content equals the
     fixture's `name`. **Verify**: `skill-import-preview-type-version`
     text content is exactly `"Type: Skill | Version: base"` — confirmed
     live this is a **hardcoded** label (`LATEST_VERSION_NAME` constant in
     `SkillImportModal.jsx`), not derived from the file, so it reads
     `base` unconditionally regardless of fixture content.
4. In the dialog, open the PROJECT selector (currently shows `Private`,
   no testid yet — see Handles Reference) and select **`UI Testing`**
   (400) from the dropdown.
   - **Verify**: the selector's displayed value becomes `UI Testing`.
     Confirmed live via `select-option-400` (existing, already-present
     testid on the option — see Handles Reference) — the same shared
     `SingleSelectMenuItem`/`select-option-{value}` family already used by
     the Fork wizard's project picker (ELITEA-1893).
5. Click the dialog's Import (confirm) button (currently no testid — see
   Handles Reference).
   - **Verify**: the dialog closes (`skill-import-preview-dialog` no
     longer present). Confirmed live: URL and page `<title>` are
     **unchanged** (`http://localhost:5173/skills/all`, `"Skills: all -
     Private"`) — the app never navigates, because
     `confirmImport()`'s `importProjectId !== projectId` branch skips
     `goToSkill()` (source-confirmed, `useSkillImport.hooks.js`).
6. Observe the app immediately after import (same page, same session — no
   navigation to assert *away from*, since none occurs).
   - **Verify**: current project selector (top toolbar,
     `project-selector-trigger-combobox`) still shows `Private`; the
     Skills list still shows Project A's skills, not a lone new one —
     i.e. the app stayed exactly where it was.
7. Switch to Project B (`UI Testing`/400) — via UI project switcher or,
   preferably, a project-scoped `SkillAPI` (see Test Data caveat above) —
   and confirm the imported skill is present (name matches the fixture),
   then delete it.
   - **Verify** (confirmed live): the imported skill (`gap061-skill`,
     confirmed with a full field readback — name, description, tag,
     instructions, version=`base` — all matching the source fixture
     exactly) exists in project 400's list. **Verify**: deleting it (via
     UI overflow menu → Delete skill → type-to-confirm → Delete, OR via
     the project-scoped `SkillAPI.delete_skill()`) succeeds — confirmed
     live via UI: redirect to `/skills/all`, skill absent from a
     subsequent list re-fetch, **zero console errors** throughout.

## Expected Results
- A non-`.md` file is rejected: exact toast text, no dialog, no skill
  created.
- A valid `.md` opens the preview dialog with the correct name and the
  hardcoded `Type: Skill | Version: base` subtitle.
- Changing the PROJECT selector to a different, valid project and
  confirming import succeeds (new skill created in the **target** project,
  fields matching the fixture) **and** leaves the user on the current
  project's Skills list — no navigation into the imported skill.
- Cleanup (deleting the cross-project skill) succeeds without error.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: non-.md file rejected | Toast `"Only .md files can be imported."`, no preview dialog | AFS step 1 | live: toast text exact match, `roleDialogs: 0` | asserted |
| Step 2: valid .md opens preview | `skill-import-preview-dialog` opens | AFS step 2 | live: `dialogPresent: true` | asserted |
| Step 3: preview shows name + Type/Version | `skill-import-preview-name` = fixture name; `skill-import-preview-type-version` = `"Type: Skill \| Version: base"` | AFS step 3 | live: both text-content reads exact-matched | asserted |
| Step 4: change PROJECT selector to Project B | Selector shows target project | AFS step 4 | live: combobox text became `"UI Testing"` after `select-option-400` click | asserted |
| Step 5: click Import | Success toast / dialog closes | AFS step 5 | live: `dialogPresent: false` after confirm click (toast text not independently re-captured in the final combined run — see Blocked Steps note; captured cleanly in an earlier isolated run of the identical action) | asserted (see note) |
| Step 6: no navigation into imported skill | App stays on current Skills list, URL/title unchanged | AFS step 5–6 | live: URL stayed `.../skills/all`, title stayed `"Skills: all - Private"` immediately after confirm | asserted |
| Step 7: switch to Project B, confirm present, delete | Skill exists in 400; delete succeeds | AFS step 7 | live: full field readback (name/description/tag/instructions/version) matched fixture in project 400; delete redirected to list, skill absent afterward, 0 console errors | asserted |

### Axis 2 — Analyst additions

- Confirmed live that steps 1→2 (reject, then immediately retry with a
  valid file) work correctly **within the same page session** — no stale
  detached `<input>` element or app-side state leaks between the two
  `openFileDialog()` invocations. De-risks the implementer writing this as
  ONE continuous test rather than two isolated ones. *(Not a case-text
  element — an analyst verification that the case's own step ordering is
  safe to implement literally.)*
- Confirmed the dialog's PROJECT selector is **local component state**
  (`useState` in `SkillImportModal.jsx`, `forLocalUsage` mode), not the
  global Redux `project` — selecting Project B in the dialog does **not**
  change the app's active project or navbar selector mid-dialog. This is
  why step 6's "stays on Project A's list" is guaranteed by design, not
  timing-dependent. *(Added: explains *why* step 6 holds, useful context
  the case text doesn't spell out.)*
- Confirmed the dialog's "Type: Skill | Version: base" subtitle is a
  **hardcoded literal** (`LATEST_VERSION_NAME`), unconditional on the
  uploaded file's own content — same finding ELITEA-1738's AFS made for
  the same-project import path; holds identically for a fresh/static
  fixture file, not just an exported one. *(Added: confirms the case's
  Test Data "Preview subtitle" row is a hardcoded constant, not something
  that could vary and needs no per-fixture branching in the test.)*

## Handles Reference

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Skills list Import button | `skills-import-button` | on-`automation/testids` ✓ (confirmed live via `document.querySelector`) | already wired as `SkillsListPage.import_button` |
| Import preview dialog | `skill-import-preview-dialog` | on-`automation/testids` ✓ | already wired |
| Import preview name | `skill-import-preview-name` | on-`automation/testids` ✓ | already wired |
| Import preview Type/Version | `skill-import-preview-type-version` | on-`automation/testids` ✓ | already wired |
| Error toast (wrong extension) | `toast-message` | on-`automation/testids` ✓ | same generic app-wide Toast container already used by `SkillsListPage.import_success_toast_message` — this case's own field should be separately named, e.g. `import_error_toast_message`, per the established "own named field per page object" convention (see `elitea_1934_...` memory) |
| **PROJECT selector (dialog)** | **none — `testid needed: skill-import-project-select`** | needs-adding | `<ProjectSelect name="skillImportProject" .../>` in `SkillImportModal.jsx` (~line 46) renders no `data-testid` on its trigger. Confirmed live: `dlg.querySelector('[role="combobox"]')` → `data-testid: null`. **Fix**: add `data-testid="skill-import-project-select"` directly to the `<ProjectSelect>` JSX element in `SkillImportModal.jsx` — it flows through `ProjectSelect`'s `...last` spread into `Select.SingleSelect`'s `data-testid` prop (confirmed by reading `ProjectSelect.jsx`/`SingleSelect.jsx` source: `SingleSelect` wires `data-testid={dataTestId}` on the underlying MUI `<Select>` AND `SelectDisplayProps={{'data-testid': \`${dataTestId}-combobox\`}}` on its display div) — no component code change needed beyond the JSX prop, this is a one-line addition. |
| PROJECT dropdown option | `select-option-{projectId}` | on-`automation/testids` ✓ (confirmed live: `select-option-399/406/25/471/400`) | Existing shared `SingleSelectMenuItem` family (same pattern as ELITEA-1893's Fork wizard) — **no new testid needed**, this one already fires correctly for the Skill import dialog's options (confirmed live, not just by analogy). Implementer should add a class-level template constant to `SkillsListPage` (mirrors `ChatPage.SELECT_OPTION` / `PipelineDetailPage.SELECT_OPTION`): `IMPORT_PROJECT_OPTION = '[data-testid="select-option-{}"]'`. |
| **Dialog Import (confirm) button** | **none — `testid needed: skill-import-confirm-button`** | needs-adding | Bare `Button.BaseBtn` in `SkillImportModal.jsx`'s `actions` (~line 103), no `data-testid` prop. Confirmed live: `[...dlg.querySelectorAll('button')].find(b=>b.textContent==='Import')` had `testid: null`. One-line fix: add `data-testid="skill-import-confirm-button"` to that `Button.BaseBtn`. This is the ONLY new confirm-side testid this case's test touches — do **not** also add a Cancel-button testid (`skill-import-cancel-button`, listed in the source card's Automation Notes) since this case's steps never click Cancel; per `.agents/role-overrides.md` § scope-is-load-bearing, that would be an untouched-element addition and out of scope for this test. Leave `skill-import-cancel-button` for whichever future case actually exercises Cancel. |
| App project switcher (navbar, NOT the dialog) | `project-selector-trigger` / `project-selector-trigger-combobox` | on-`automation/testids` ✓ (pre-existing, confirmed live) | Used only to assert step 6 ("still shows Private") and, if the implementer chooses UI-based verification over API, to switch to Project B for step 7. Distinct component from the in-dialog `ProjectSelect` above — same shared `select-option-{value}` option family, different trigger. |
| Skill detail testids (name/description/tags/instructions/version, for the step-7 field readback if done via UI) | `skill-name-input-field`, `skill-description-input-field`, `skill-tag-chip`, `skill-instructions-editor-content`, `skill-version-select-combobox` | on-`automation/testids` ✓ (all pre-existing, confirmed live) | Already wired via `SkillDetailPage`/`SkillFormPage` — reuse as-is; no new testids. Only needed if the implementer verifies step 7 via UI instead of the recommended project-scoped API read. |
| Delete-skill flow (cleanup, if done via UI) | `skill-controls-menu-button`, `skill-delete-menu-item` | on-`automation/testids` ✓ (pre-existing) | Confirmed live end-to-end in project 400: menu → Delete skill → type-to-confirm (unlabelled `#name` input inside `[role="dialog"]`, no testid — pre-existing gap, not newly introduced by this case) → Delete button (role/text-matched, no testid) → redirect to `/skills/all`. |

## Network Behavior
- `POST /elitea_core/skill_import/prompt_lib/{targetProjectId}` — fires on
  clicking the dialog's Import button; `targetProjectId` is **400** here
  (not the current project 399) — this is the concrete assertion point
  distinguishing this case from ELITEA-1737/1738, which always import into
  the *current* project. Not independently re-captured via network trace
  in the final combined session (the `browser-verify`/CDP harness used for
  this analysis reconnects per-command and can miss requests that fire
  between connections — see Blocked Steps); the same endpoint + a
  `{project}` path segment behavior is already documented and trustworthy
  from ELITEA-1737's AFS. Implementer should assert on
  `page.expect_response(...)` matching this URL pattern with the target
  project id, mirroring the existing tests' pattern.
- No request fires at all for the wrong-extension rejection (step 1) — the
  `!file.name.endsWith('.md')` check happens entirely client-side before
  any network call (confirmed by source reading `useSkillImport.hooks.js`
  `stageFile()`).

## Known Defects Found During Exploration
None. Case text matches live behavior exactly on every asserted point —
no case-text drift, no CLARIFICATION needed.

## Blocked Steps
None blocking. Two minor **analysis-tooling** notes, not case blockers:
- The CDP-based harness used for live exploration (isolated Chrome
  instance, since the shared Playwright MCP browser — lane 0 — was
  occupied by a concurrent session) required a `document.createElement`
  patch to reliably assign files to the app's dynamically-created,
  initially-detached `<input type=file>` element. That patch, left active,
  once interfered with an unrelated MUI text field (the delete-confirmation
  name input) in the SAME page session — a **self-inflicted, tooling-side**
  contamination, not a product defect (see
  `browser_verify_cdp_clear_backspace_does_not_clear_mui_textarea.md`-style
  entry to be logged in memory). Resolved by a fresh navigation before the
  affected step. Playwright's own `page.expect_file_chooser()` (what the
  actual automated test uses) does not have this limitation — it is a
  purpose-built API, not a hand-rolled CDP workaround — so this does not
  carry forward to the implementer.
- Because of the same per-command-reconnect harness limitation, the
  `skill_import` POST request/response for the final (Project B) import
  wasn't independently captured on its own in the very last consolidated
  run (it *was* captured correctly, with matching UI outcomes, in an
  earlier isolated single-scenario run of the identical action, and the
  resulting skill's presence in project 400 with all fields correct was
  independently confirmed by a full field readback, which is a strictly
  stronger check than a bare status code). Implementer's own
  `page.expect_response()` in Playwright will capture this natively with
  no such gap.

## Automation Hints
- **File**: add to the existing
  `automation/tests/ui/skills/test_skill_export_import.py` (shared page
  objects, shared `cleanup_skill_ids`-style teardown idiom) rather than a
  new file — same feature, same import mechanism.
- **New page-object methods needed on `SkillsListPage`:**
  1. `attempt_import_invalid_file(file_path, timeout=10000)` — clicks
     `import_button`, sets the file via `page.expect_file_chooser()`, then
     waits for the error toast (`toast-message` / a new
     `import_error_toast_message` field) to become visible **instead of**
     waiting for the preview dialog (the existing `import_skill()` method
     always waits for `"Import parameters"` text and would time out
     uselessly on a rejected file — do not reuse it for this path
     as-is).
  2. `select_import_target_project(project_id)` — clicks the new
     `skill-import-project-select` testid (once added), then clicks
     `IMPORT_PROJECT_OPTION.format(project_id)` (new class constant,
     `'[data-testid="select-option-{}"]'`, mirroring
     `ChatPage.SELECT_OPTION` / `PipelineDetailPage.SELECT_OPTION`).
  3. `confirm_import()` already exists but is scoped correctly
     (`dialog.get_by_role("button", name="Import")`) — once the new
     `skill-import-confirm-button` testid is added, switch this method's
     locator from the role-based lookup to the testid (a compliance
     improvement, not new behavior — the existing method's role-based
     locator was a legacy `needs-adding` gap already flagged in
     ELITEA-1737's AFS Concrete Handles, never closed).
     **Important behavioral difference for THIS case**: the existing
     `confirm_import()` waits for
     `page.wait_for_url("**/skills/all/**", timeout=timeout)` after
     clicking — that wait will **time out** for a cross-project import
     (no navigation occurs). Add a `confirm_cross_project_import()`
     variant (or a parameter) that instead waits for the dialog to close
     (`dialog.wait_for(state="hidden")`) and the success toast to appear,
     WITHOUT waiting for a URL change.
- **Testids to add** (via `add-data-testid`, on `automation/testids`):
  `skill-import-project-select` (on the dialog's `<ProjectSelect>` element)
  and `skill-import-confirm-button` (on the dialog's Import `Button.BaseBtn`).
  Exact JSX locations and the one-line fix for each are in § Handles
  Reference above. Do **not** add a Cancel-button testid — out of this
  case's touched-elements scope (see Handles Reference note).
- **Cleanup**: construct a project-400-scoped `SkillAPI` directly
  (`SkillAPI(browser_cookies=_browser_cookies, project_id="400")`) for
  both the step-7 presence check and the delete — see Test Data § caveat.
  Do not rely on the shared session-scoped `skill_api` fixture (pinned to
  project 399) for this skill.
- **Wait strategy**: after the rejection toast, assert
  `page.locator('[data-testid="skill-import-preview-dialog"]').count() == 0`
  (or `not_to_be_visible()`) rather than a fixed sleep — the toast
  appearing IS the completion signal for the client-side-only rejection
  path (no network round-trip to wait on, confirmed above).
- Reuse `capture_console_errors()` (already on `SkillDetailPage`, used by
  both existing tests in this file) around the cross-project import +
  delete flow, matching the existing tests' zero-console-errors discipline.
