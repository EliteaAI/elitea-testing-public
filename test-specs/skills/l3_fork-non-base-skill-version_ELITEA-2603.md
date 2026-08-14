# Test Case: Fork Non-Base Skill Version

## Metadata
- **TMS ID**: ELITEA-2603
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend)
- **User set**: `${TEST_USER}` (dev-token identity on localhost)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`).
- Source project `Private` (id `399`) and target project `UI Testing` (id
  `400`) are both accessible (same known-good pair confirmed in the
  ELITEA-2602 session — `.agents/memory/qa-engineer/fork_agent_flow_and_localhost_dev_token_permission_scoping.md`).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: kebab-case, e.g. `el-2603-versioned-skill-${suffix}`.
- Base version instructions: any non-empty string, e.g. "Comprehensive
  instructions for the skill behavior used to verify the fork end-to-end
  flow" (this run reused ELITEA-2602's source skill and its base version as
  the starting point — a fresh skill works identically).
- Version 2 name: `v2-enhanced` — **hyphen IS accepted here** (Create
  Version dialog's Name field has a different/looser validation than the
  Tags field — confirmed live, no rejection).
- Version 2 instructions: different from base, e.g. "Enhanced instructions
  with additional capabilities for the v2-enhanced version — ELITEA-2603."
- **Version 2 Tags — MUST use underscores, NOT the case's literal
  `v2-tag`.** Same silent-hyphen-rejection root cause as ELITEA-2602 (issue
  #1445). Use `v2_tag` and `enhanced` (the latter has no hyphen, works as
  literally specified).

No `reuse-existing` or `generate-shared-with-cleanup` data applies.

## Test Steps
1. Create a skill in `Private`/399 with base-version instructions (via UI
   form, or reuse an existing skill — this session added a version directly
   to the ELITEA-2602 source skill after that case's own steps completed).
   - **Verify**: skill created, `version_details.name` = `"base"`.
2. On the skill's detail page, edit the instructions field to the "Version 2
   Instructions" test data, and edit the Tags to `v2_tag` + `enhanced`
   (remove any pre-existing tags first via each chip's delete icon — click
   the icon child, NOT the chip body, per
   `.agents/memory/qa-engineer/skill_tags_field_hyphen_rejected_and_chip_delete_icon_only.md`).
   **This edit MUST happen BEFORE clicking "Save As Version"** —
   `save_as_version()` snapshots whatever is CURRENTLY in the editor, not
   the previously-active version's stored content
   (`.agents/memory/qa-engineer/skill_save_as_version_captures_current_editor_content.md`).
   Reversing the order silently creates a v2 identical to base.
3. Click "Save As Version" (`skill-save-as-version-button`); in the
   resulting "Create version" dialog, type the version name (`v2-enhanced`)
   into the Name field and click Save (`skill-create-version-save-button`).
   - **Verify**: `POST` succeeds; URL gains a second digit segment
     (`/skills/all/{skillId}/{newVersionId}`); the VERSION selector now
     shows `"v2-enhanced"` as the active version (auto-navigates there — a
     follow-up explicit "switch to v2-enhanced" step, if scripted, is a
     confirmed no-op).
4. Verify the VERSION dropdown lists both versions.
   - **Verify**: opening `skill-version-select` shows both `base` and
     `v2-enhanced` as options (`[data-testid="version-option-{name}"]`
     dynamic template).
5. (v2-enhanced is already the active/selected version per step 3's
   auto-navigation — case step 5 is satisfied structurally, no separate
   action needed.)
6. Open the skill's overflow menu (`skill-controls-menu-button`) and click
   "Fork" (`fork-menuitem`).
   - **Verify**: Fork wizard dialog opens (`agent-import-preview-dialog`).
7. Expand the Main-entity card (`agent-import-preview-card-toggle`).
   - **Verify**: `agent-import-preview-instructions`-equivalent text (the
     dialog's "Instructions:" paragraph) shows the **v2-enhanced version's**
     instructions ("Enhanced instructions with additional capabilities...")
     — confirmed live, NOT the base version's original text. The
     Description field shown is the SKILL-level description (shared across
     versions, unchanged) — this is expected, description is not
     version-scoped.
8. Select target project `UI Testing` (400) via
   `agent-import-wizard-project-select-combobox` → `select-option-400`.
9. Click "Fork" (`agent-fork-confirm-button`).
   - **Verify**: `POST /api/v2/elitea_core/fork/prompt_lib/400` → 201
     Created; response's `result.skills[0].id` is the new forked skill ID
     (e.g. `9` this session). Same pre-existing #570 console warning fires
     (see ELITEA-2602's AFS, § Known Defects — not re-documented here,
     same handling).
10. Click "Got it" (`agent-import-complete-got-it-button`).
    - **Verify**: navigates to the forked skill's detail page in the target
      project.
11. Verify via `GET /api/v2/elitea_core/skill/prompt_lib/400/{forkedSkillId}`:
    - `versions` array has exactly ONE entry, `name: "base"` — **the
      forked skill's version name is normalized to "base" in the target
      project**, regardless of which version was forked (case's central
      assertion).
    - `version_details.instructions` = the v2-enhanced version's
      instructions text — NOT the original base version's text (confirmed
      this run: source skill's base instructions were "Comprehensive
      instructions...", forked copy shows "Enhanced instructions...").
    - `version_details.tags` = `[v2_tag, enhanced]` — the v2-enhanced
      version's tags, not the base version's original tags (confirmed this
      run: base had `test_tag`/`fork_demo` at the time of forking,
      forked copy correctly shows the v2-enhanced set instead).
    - `version_details.meta.parent_version_id` = the SOURCE's v2-enhanced
      version ID (NOT its base version ID) — confirms the fork correctly
      points its lineage at the specific version that was active when
      Fork was clicked, not always at base.

## Expected Results
- Forking a non-base version copies that version's specific configuration
  (instructions + tags), not base's.
- The forked skill's version name is normalized to `"base"` in the target
  project.
- `parent_version_id` lineage correctly identifies the SOURCE version that
  was forked (v2-enhanced's id), proving the backend captured the
  version-specific export, not a generic skill-level export.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create skill w/ base instructions | skill created with "base" version | step 1 | step 1 | asserted |
| 2 Save the skill | saved successfully | step 1 | step 1 | asserted |
| 3 Create v2-enhanced version, different instructions/tags | new version created | steps 2–3 | step 3 | asserted |
| 4 Verify multiple versions exist | dropdown shows both | step 4 | step 4 | asserted |
| 5 Select v2-enhanced as active | v2-enhanced selected | step 3 (auto) | step 3 | asserted *(decomposed — save-as-version auto-navigates, no separate select action needed; documented as a confirmed no-op if scripted anyway)* |
| 6 Open menu, click Fork | wizard opens | step 6 | step 6 | asserted |
| 7 Verify modal shows v2-enhanced details (not base) | version-specific instructions/tags shown | step 7 | step 7 | asserted *(tags not shown in preview at all — see ELITEA-2602's clarification #1455, same root cause, not re-filed; instructions ARE confirmed version-specific)* |
| 8 Select Project B | Project B selected | step 8 | step 8 | asserted |
| 9 Complete fork operation | fork completes | step 9 | step 9 | asserted |
| 10 Navigate to Project B Skills | list loads | step 10 | step 10 | asserted *(decomposed — Got-it navigates directly onto the forked skill's own page)* |
| 11 Open forked skill | forked skill opens | step 10 | step 10 | asserted |
| 12 Verify version name is "base" | dropdown shows "base" | step 11 | step 11 | asserted |
| 13 Verify instructions match v2-enhanced | enhanced content present | step 11 | step 11 | asserted |
| 14 Verify v2-enhanced tags present | v2-tag, enhanced tags present | step 11 | step 11 | asserted *(as `v2_tag`, `enhanced` — hyphenated `v2-tag` silently rejected by the live product, same #1445 root cause)* |
| 15 Verify forked skill does NOT have original base content | content differs from Project A's base | step 11 | step 11 | asserted |

### Axis 2 — Analyst additions

- step 11 asserts `parent_version_id` specifically equals the SOURCE's
  v2-enhanced version id (not its base version id) — *added: this is the
  strongest possible proof that the backend captured the version-specific
  export rather than defaulting to base internally and only faking the
  preview; the case's own steps stop at content-comparison, this closes the
  gap with a structural guarantee.*
- step 3 documents the "edit before save-as, not after" ordering requirement
  explicitly as a numbered step precondition — *added: silently produces a
  false-positive-shaped test if reversed (confirmed in prior-session
  memory), too easy to get backwards without this being called out inline
  rather than only in a memory file the implementer might not read.*

## Cleanup
1. Delete the forked skill in `UI Testing`/400 (same UI delete flow as
   ELITEA-2602).
2. Delete the source skill (with both its versions) in `Private`/399 —
   deleting the skill removes both versions together, no separate
   per-version cleanup needed (confirmed live: `skill-delete-menu-item`'s
   confirmation targets the whole skill entity, not the currently-active
   version).

## Concrete Handles (discovered during exploration)

All Fork-wizard and project-switch handles are IDENTICAL to ELITEA-2602's
AFS (`test-specs/skills/l2_fork-skill-end-to-end_ELITEA-2602.md` § Concrete
Handles) — not re-listed here except for the version-management additions
specific to this case:

| Element | Recommended Locator | Fallback |
|---|---|---|
| Save As Version button | `getByTestId('skill-save-as-version-button')` | none needed |
| Create Version dialog | `getByTestId('skill-create-version-dialog')` | none needed |
| Create Version name input (real `<input>`) | `getByTestId('skill-create-version-name-input-field')` | none needed |
| Create Version save button | `getByTestId('skill-create-version-save-button')` | none needed |
| Version selector (trigger) | `getByTestId('skill-version-select')` | none needed |
| Version option (dynamic, by name) | `[data-testid="version-option-{versionName}"]` (class constant template, e.g. `version-option-v2-enhanced`) | none needed |
| Tag chip delete icon (per-tag) | `[data-testid="skill-tag-chip-delete-{tagName}"]` — click the icon CHILD, not the chip button itself (clicking the label/body is a confirmed no-op) | none needed |

## Network Behavior
- `POST .../skills/prompt_lib/{projectId}` — version creation (Save As
  Version), 200/201.
- `GET .../skill_export_fork/prompt_lib/{sourceProjectId}/{skillId}/{versionId}`
  — fires with the CURRENTLY-ACTIVE version's ID when the Fork wizard opens
  (confirms the version-specific export, not always base's).
- `POST .../fork/prompt_lib/{targetProjectId}` — 201, same shape as
  ELITEA-2602.
- `GET .../skill/prompt_lib/{targetProjectId}/{forkedSkillId}` — source of
  truth for the version-name-normalized-to-base + version-specific-content
  assertions.

## Known Defects Found During Exploration
- **[Case-text drift, not a bug]** Test Data's `v2-tag` value contains a
  hyphen, silently rejected by the Tags field. Same root cause as
  ELITEA-2602/#1445 — commented on the existing issue, not re-filed. Use
  `v2_tag` in automation.
- Same Main-entity-card-omits-tags observation as ELITEA-2602 applies here
  too (already filed as #1455) — not re-filed.
- Same pre-existing #570 console warning fires on Fork Complete — not a new
  finding.
- No NEW defects beyond what ELITEA-2602's session already surfaced.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest.
- This case's Fork-wizard/project-switch/cleanup mechanics are 100% shared
  with ELITEA-2602 — the implementer should factor the common Fork-flow
  page-object methods once (on `SkillDetailPage`) and have BOTH tests call
  them, rather than duplicating. The two cases remain separate test
  functions/specs (different setup: version creation vs plain create: and
  different core assertions: version-name-normalization vs
  field-preservation/independence) but share the underlying Fork
  interaction methods.
- `save_as_version(name)` on `SkillDetailPage` (once added, mirroring the
  ELITEA-1738/2440 precedent already in the page object per
  `.agents/memory/qa-engineer/skill_save_as_version_captures_current_editor_content.md`)
  snapshots CURRENT editor content — the test must edit instructions/tags
  BEFORE calling it, never after.
- Reuse `SkillDetailPage.VERSION_OPTION`/`VERSION_OPTION_ANY` (pre-existing,
  from the ELITEA-1738 rework) for the version-dropdown assertions in step
  4 — do not add new testids for this, they already exist.
