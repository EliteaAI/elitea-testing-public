# Test Case: Skill Custom Icon Persistence on Save As Version

## Metadata
- **TMS ID**: ELITEA-2606
- **Linked Story**: none
- **Priority**: low (case frontmatter/body) — mapped to `l3`
- **Environment Explored**: local (`http://localhost:5173`, EliteaAI/EliteaUI
  `automation/testids` → DEV backend), project `Private` /
  `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login
  via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (agent), 2026-08-12
- **Status**: **ready-for-automation** — case executed end-to-end live: created
  a skill with a distinctive custom icon, used "Save As Version" to create
  `v2`, and confirmed the SAME uploaded-icon `src`/`meta.icon_meta` is present
  on both `v2` and the original `base` version, both immediately after
  creation and after a full page reload, and consistently when switching back
  and forth between the two versions. No functional/visual defect — the icon
  is byte-identical and correctly displayed/persisted on both versions. No
  testid gaps found: every locator this case touches already carries a
  `data-testid` (all pre-existing, several already exercised by sibling
  cases ELITEA-2437/ELITEA-2604/ELITEA-2605/ELITEA-2602/ELITEA-2603).
- **Not `extend-existing`/`already-covered` against any sibling icon or
  version case** — grepped `test-specs/skills/` for `icon` and `version`
  (§ neighbours below). The closest specs are:
  - ELITEA-2605 (`l2_skill-custom-icon-visibility-across-ui_ELITEA-2605.md`,
    merged to `origin/automation/base`) — proves the SAME uploaded icon
    renders correctly across 5 UI surfaces (list card, detail page,
    SkillMenu dropdown, agent SkillCard, chat mention), but **never touches
    versioning at all** — every observation is on a single-version skill.
  - ELITEA-2604 (`l2_skill-custom-icon-upload-and-validation_ELITEA-2604.md`,
    merged) — proves upload/replace/validate/delete mechanics for an icon on
    ONE version (create mode + edit mode of the SAME version), and documents
    the `PUT .../upload_skill_icon/prompt_lib/{project}/{versionId}`
    endpoint being version-scoped — but never creates a second version to
    check whether that version-scoping means a NEW version starts with no
    icon. That is exactly this case's open question, and it required its
    own live run to answer (verdict: no, the icon meta is copied into the
    new version at creation time — see Network Behavior).
  - ELITEA-2437 (`l3_skill-version-dropdown-set-default_ELITEA-2437.md`,
    merged) — creates a second version (`save_as_version()`) and drives the
    VERSION dropdown, but asserts default-version PATCH/toast/reorder, never
    icon content.
  - ELITEA-2602/ELITEA-2603 (Fork cases, merged) — prove icon is preserved
    **by reference** across a Fork (a different, cross-skill/cross-project
    copy mechanism, not "Save As Version" which creates a new version of
    the SAME skill). Useful precedent (same `meta.icon_meta` shape) but not
    the same code path — `save_as_version()`'s "create version" POST is a
    distinct endpoint from Fork's `skill_export_fork`.
  None of the above proves THIS case's specific observable (icon persists
  across a same-skill Save-As-Version + survives switching back to the
  ORIGINAL version), so this is fresh coverage, not a duplicate or a gap-only
  extension of any of them.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills section is accessible (`/skills/create`, `/skills/all/{id}`).
- A custom icon file is available under `test-data/images/` (this run reused
  the existing `skill-fork-test-icon.png` asset — a distinctive, already-small
  PNG already used by the sibling Fork cases; any of the existing
  `test-data/images/test-icon.*` assets work equally well).

## Test Data

### generate-per-test (created in test setup, cleaned up in teardown)
- Skill: `SkillAPI.create_skill(name="autotest-versionicon-skill-<ts>",
  description="...", instructions="...")` (`automation/api/client.py:1427`) —
  **however, the icon MUST be uploaded via the live UI form**
  (`SkillFormPage.upload_skill_icon()`), not via `create_skill()`'s payload —
  the create-skill API convenience method has no icon parameter, and this
  run confirmed icon upload is its own two-request flow
  (`open_icon_picker()` → file chooser → `POST
  /upload_skill_icon/prompt_lib/{project}` → apply to local form state →
  `Save`). Two viable setup shapes for the implementer:
  1. **Full-UI setup** (what this run exercised): navigate to
     `/skills/create`, fill required fields, `upload_skill_icon(path)`,
     `save_and_wait_for_navigation()`. Slower but exercises the exact case
     steps 1-3 as real assertions rather than pure fixture setup.
  2. **API-seed + UI icon-only setup**: `SkillAPI.create_skill()` for
     name/description/instructions, then navigate to the skill's edit page
     and `upload_skill_icon()` there (edit-mode upload — confirmed by
     ELITEA-2604 to fire the same POST + an immediate `PUT
     .../upload_skill_icon/prompt_lib/{project}/{versionId}`, no separate
     Save needed). Faster setup; case steps 1-3 become a precondition
     assertion instead of the literal case flow. **Recommended**, since
     this case's actual pass criterion (steps 4-13) is entirely about
     Save-As-Version + cross-version persistence, not upload mechanics
     (already covered by ELITEA-2604) — the implementer should choose
     whichever the team prefers for setup-vs-assertion balance; this run
     used shape 1 for full case-text fidelity during exploration.
- `SkillAPI.create_skill()` / `SkillAPI.delete_skill()`
  (`automation/api/client.py:1427,1478`) reused for setup/teardown.
- `SkillAPI.get_skill(skill_id)` (`automation/api/client.py:1460`) exists and
  returns `icon_meta`/`version_details.meta.icon_meta`, but **only for the
  version the bare (no-`versionId`) endpoint defaults to** — this run's live
  exploration always supplied an explicit `versionId` in the URL
  (`GET /skill/prompt_lib/{project}/{skillId}/{versionId}`) to pin down
  WHICH version's icon it was reading. `get_skill()` as currently written
  cannot express that distinction. See Automation Hints for the small
  extension needed if the implementer wants an API-level assertion in
  addition to the DOM-level one.
- New version name (`v2`) — confirmed live this run: the "Create version"
  dialog's Name field accepts a plain alphanumeric name with no additional
  constraints beyond what `save_as_version()` already handles (same as
  ELITEA-2437's `ver-1`/`ver_1` names).

## Test Steps

1. Create a skill with a distinctive custom icon (`SkillFormPage.
   upload_skill_icon(path)` on `/skills/create`)
   - **Verify**: skill is created with custom icon
   - **OBSERVED**: hover + click `skill-form-icon-button` → icon picker
     dialog (`icon_picker_dialog`) → Upload → file chooser → uploaded
     `skill-fork-test-icon.png`. `skill-form-icon-img`'s `src` updated to
     `https://dev.elitea.ai/app/skill_icon/399/<uuid>.png` immediately.
     Network: `POST /api/v2/elitea_core/upload_skill_icon/prompt_lib/399`
     → **200 OK** (single request — create mode, no `versionId` yet, same
     mechanism ELITEA-2604 documents).

2. Fill in all required fields and save
   - **Verify**: skill is saved successfully
   - **OBSERVED**: `SkillFormPage.fill_form(name, instructions, description)`
     (pre-existing) + `skill-save-button` click. URL settles on
     `/skills/all/{id}` (this run: skill id **1510**, base version id
     **1570** — visible in the Information panel's "Version ID" field once
     on the detail page). Network: `POST /api/v2/elitea_core/skills/
     prompt_lib/399` → **201 Created**.

3. Verify the custom icon is displayed
   - **Verify**: custom icon is visible on skill
   - **OBSERVED**: on `/skills/all/1510` (base version, no explicit version
     segment yet), `skill-form-icon-img`'s `src` is unchanged from step 1's
     value — confirmed via `page.evaluate` reading the `<img>`'s `src`
     attribute directly (`document.querySelector('[data-testid=
     "skill-form-icon-img"]').src`).

4. Click "Save As Version" or equivalent versioning action
   - **Verify**: version creation dialog/form appears
   - **OBSERVED**: `skill-save-as-version-button` (`SkillDetailPage.
     save_as_version_button`, pre-existing) click opens the "Create version"
     dialog (`skill-create-version-dialog`), confirmed live via
     `heading "Create version"`.

5. Enter a new version name (`v2`)
   - **Verify**: version name is entered
   - **OBSERVED**: `skill-create-version-name-input-field` (pre-existing,
     `SkillDetailPage.create_version_name_input_field`) accepts `v2`; the
     dialog's `skill-create-version-save-button` (initially `[disabled]`)
     becomes enabled once the field is non-empty.

6. Optionally modify the instructions
   - **Verify**: instructions are updated
   - **OBSERVED — SCOPE NOTE**: this run did NOT modify instructions before
     Save As Version (the case marks this step "Optionally"; the version was
     created with the base version's instructions carried forward
     unmodified, which is itself the `save_as_version()` page-object
     method's existing, already-tested behavior — see ELITEA-2437). Icon
     persistence is independent of whether instructions changed, so this
     step is a genuine no-op for THIS case's pass criterion; automating it
     as a literal instructions-edit adds no signal specific to icon
     persistence and duplicates ELITEA-2431's instructions-edit coverage.
     Recommend the implementer skip an explicit instructions-edit action
     here (Coverage Map disposition: **out-of-scope**, not dropped).

7. Save the new version
   - **Verify**: new version is created successfully
   - **OBSERVED**: `skill-create-version-save-button` click →
     `version_toast_message` (`toast-message` testid) shows exact text
     `Version "v2" created` (pre-existing `save_as_version()` assertion).
     URL transitions to `/skills/all/1510/1571` (new version id **1571**).
     Network (the case-critical evidence): `POST /api/v2/elitea_core/skill/
     prompt_lib/399/1510` → **201 Created**, response body:
     ```json
     {"id": 1571, "name": "v2", "instructions": "...", "status": "draft",
      ...,
      "meta": {"icon_meta": {
        "url": "https://dev.elitea.ai/app/skill_icon/399/d2a947dc-....png",
        "name": "d2a947dc-....png", "size": "32x32",
        "initial_file_size": "1.8KiB", "resulting_file_size": "102.0B"
      }}}
     ```
     — **this is the authoritative, server-side proof that the backend
     copies the base version's `icon_meta` into the newly-created version
     at creation time**, byte-identical URL to the base version's icon. Not
     a client-side carryover artifact.

8. Verify the new version is now active/selected
   - **Verify**: version dropdown shows `v2` as current
   - **OBSERVED**: `skill-version-select` (`SkillDetailPage.
     version_selector`) displays `v2`; URL path segment is `1571`
     (confirmed via `get_version_selector_value()` returning `"v2"` and the
     URL's trailing digit segment).

9. Verify the custom icon is displayed on the new version
   - **Verify**: custom icon is preserved (not reverted to default)
   - **OBSERVED**: `skill-form-icon-img`'s `src` on `/skills/all/1510/1571`
     is **byte-identical** to step 1/3's value (same UUID filename).
     Confirmed both immediately after version creation (client state) AND
     after a full hard navigation/reload to `/skills/all/1510/1571`
     (server-fetched state) — ruling out "client-side carryover only,
     doesn't actually persist" as a false-positive.

10. Switch back to the base version
    - **Verify**: base version is selected
    - **OBSERVED**: open `skill-version-select-combobox` → click the
      dynamic `version-option-base` option (existing `VERSION_OPTION`
      template, `.format("base")`) → URL transitions to
      `/skills/all/1510/1570`; `switch_version("base")` (pre-existing
      method) is the direct automation hook for this step.

11. Verify the custom icon is still present on base version
    - **Verify**: custom icon is displayed
    - **OBSERVED**: `skill-form-icon-img`'s `src` on `/skills/all/1510/1570`
      remains byte-identical to the original upload — base version was
      never touched by the version-creation flow, so this is the expected
      "unaffected" baseline, confirmed live rather than assumed.

12. Switch to v2 again
    - **Verify**: v2 is selected
    - **OBSERVED**: `switch_version("v2")` → URL back to
      `/skills/all/1510/1571`; `skill-version-select` displays `v2`.

13. Verify both versions share the same custom icon
    - **Verify**: custom icon is consistent across versions
    - **OBSERVED**: re-confirmed `skill-form-icon-img`'s `src` on v2 matches
      steps 3/9/11's value exactly — same string, three-way match across
      base (twice) and v2 (twice), byte-identical throughout the whole
      switch-base→switch-v2 round trip.

**Side-channel check:** zero console errors observed across the full
create→upload→save→Save-As-Version→switch-base→switch-v2 flow (confirmed via
`browser_console_messages`, filtered to errors, checked at multiple points
during the run). The only console error seen in this session fired AFTER the
case's own steps, during teardown (skill deletion) — a single stale-refetch
404 (`GET .../skill/prompt_lib/399/1510/1571` after the skill's own `DELETE`
had already returned `204`), the same documented artifact pattern already
noted in ELITEA-2604/ELITEA-2605's Expected Results (a page-still-mounted
refetch racing the just-completed delete+redirect, not a defect this case's
flow causes).

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end: "Save As
Version" creates a new version successfully, the custom icon is preserved on
the new version (confirmed via DOM `src` AND the create-version response
body's `meta.icon_meta`), the custom icon remains on the original `base`
version, and the icon is consistent when switching between versions in both
directions. No functional or visual product defect found. No testid gaps —
every element this case's flow touches already carries a `data-testid`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture | asserted |
| Precondition: project accessible | — | AFS Preconditions | project 399 | asserted |
| Precondition: custom icon file available | — | AFS Preconditions + Test Data | `test-data/images/skill-fork-test-icon.png` | asserted |
| 1 Create a skill with a distinctive custom icon | skill created with custom icon | step 1 | `skill-form-icon-img` src set; `POST upload_skill_icon` 200 | asserted |
| 2 Fill required fields and save | skill saved successfully | step 2 | `skill-save-button`; `POST skills` 201; URL `/skills/all/{id}` | asserted |
| 3 Verify custom icon displayed | custom icon visible | step 3 | `skill-form-icon-img` src unchanged | asserted |
| 4 Click "Save As Version" | version dialog appears | step 4 | `skill-create-version-dialog` heading | asserted |
| 5 Enter new version name | name entered | step 5 | `skill-create-version-name-input-field` value `v2`; Save button enabled | asserted |
| 6 Optionally modify instructions | instructions updated | step 6 | N/A — case marks this "Optionally"; not exercised, no icon-persistence signal | **out-of-scope** (see step 6 note) |
| 7 Save the new version | version created successfully | step 7 | `Version "v2" created` toast; `POST skill/.../1510` 201; URL `.../1571` | asserted |
| 8 Verify new version active/selected | dropdown shows v2 | step 8 | `skill-version-select` text `v2`; URL segment `1571` | asserted |
| 9 Verify icon on new version | icon preserved, not reverted | step 9 | `skill-form-icon-img` src match, pre- and post-reload | asserted |
| 10 Switch back to base version | base version selected | step 10 | `switch_version("base")`; URL `.../1570` | asserted |
| 11 Verify icon still on base version | icon displayed | step 11 | `skill-form-icon-img` src match | asserted |
| 12 Switch to v2 again | v2 selected | step 12 | `switch_version("v2")`; URL `.../1571` | asserted |
| 13 Verify both versions share same icon | icon consistent across versions | step 13 | `skill-form-icon-img` src match, third confirmation | asserted |
| Expected Final State: custom icon preserved on both versions | — | steps 9/11/13 | three-way src match | asserted |

### Axis 2 — Analyst additions

- step 1/step 7 both capture the underlying network evidence (`POST
  upload_skill_icon` 200; `POST skill/.../{skillId}` 201 with
  `meta.icon_meta` in the response body) — *added: gives the implementer an
  authoritative server-side assertion point instead of relying solely on
  DOM `src` reads, and a `page.wait_for_response` hook instead of a fixed
  sleep, mirroring `save_as_version()`'s existing wait pattern.*
- step 9 explicitly re-checks the icon AFTER a full page reload, not just
  immediately post-creation — *added: rules out "looks preserved because
  client state carried over, but a fresh load would reveal it wasn't
  actually saved server-side" as a false pass, the same discipline
  ELITEA-2604's Part A step 7 applied to a plain icon upload.*
- Metadata note distinguishing this case from ELITEA-2602/ELITEA-2603 (Fork)
  — *added: both prove "icon preserved by reference" via the SAME
  `meta.icon_meta` shape, but through different endpoints
  (`skill_export_fork` vs the plain "create version" POST) — worth citing
  as corroborating precedent, not treating as the same code path.*
- "zero console errors across the case's own flow" + explicit note that the
  ONE console error seen fired during teardown, not the case — *added:
  side-channel discipline per this skill's standard, with the false-alarm
  ruled out explicitly so a future reader doesn't mistake it for a defect
  this case introduced.*

## Cleanup
- **Skill created during this pass (id 1510, name
  `elitea-2606-version-icon-skill`, versions `base`=1570 + `v2`=1571)** was
  deleted via the UI's type-to-confirm delete flow (detail page → overflow
  "⋮" menu → SKILL-scoped "Delete skill" → typed exact name → Delete).
  Verified via network: `DELETE /api/v2/elitea_core/skill/prompt_lib/
  399/1510` → **204 No Content**, redirect to `/skills/all`. Deleting the
  skill removes both versions in one call — no separate per-version cleanup
  needed.
- Nothing left behind from this analysis run.

## Concrete Handles (discovered/confirmed during exploration)

All testids below are **pre-existing** — no gaps found, no `add-data-testid`
work required for this case.

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skill icon button (opens picker, two-click quirk — see `_surface.md` § Fork wizard note 3) | `page.get_by_test_id("skill-form-icon-button")` — **confirmed live, existing testid**, already `SkillFormPage.skill_icon_button` | n/a |
| Skill icon `<img>` (the persistence-check element) | `page.get_by_test_id("skill-form-icon-img")` — **confirmed live, existing testid**, already `SkillFormPage.skill_icon_img` / `get_form_icon_src()` | n/a |
| Icon picker Upload button | `page.get_by_test_id("agent-icon-picker-upload-button")` — **confirmed live, existing testid** (entity-agnostic shared dialog, note the `agent-` prefix despite being used on the Skill form) | n/a |
| "Save As Version" button | `page.get_by_test_id("skill-save-as-version-button")` — **confirmed live, existing testid**, already `SkillDetailPage.save_as_version_button` | n/a |
| "Create version" dialog | `page.get_by_test_id("skill-create-version-dialog")` — **confirmed live, existing testid** | n/a |
| Create-version Name field | `page.get_by_test_id("skill-create-version-name-input-field")` — **confirmed live, existing testid**, already `SkillDetailPage.create_version_name_input_field` | n/a |
| Create-version Save button | `page.get_by_test_id("skill-create-version-save-button")` — **confirmed live, existing testid**, already `SkillDetailPage.create_version_save_button` | n/a |
| VERSION dropdown trigger | `page.get_by_test_id("skill-version-select")` / clickable inner combobox `[data-testid="skill-version-select-combobox"]` — **confirmed live, existing testid**, already `SkillDetailPage.version_selector` | n/a |
| Version option row, keyed by name | `page.locator('[data-testid="version-option-{}"]'.format(name))` — **confirmed live, existing dynamic testid**, already `SkillDetailPage.VERSION_OPTION` | n/a |
| Version creation/save toast | `page.get_by_test_id("toast-message")` — **confirmed live, existing testid**, already `SkillDetailPage.version_toast_message` | n/a |

**No `add-data-testid` work needed for this case** — every element on its
executed code path already carries a `data-testid`, reused from
ELITEA-1738/ELITEA-2437/ELITEA-2604/ELITEA-2605's prior rework.

## Network Behavior
- `POST /api/v2/elitea_core/upload_skill_icon/prompt_lib/{project_id}` —
  fires on icon upload in create mode, `200 OK`. Not independently
  re-verified beyond status this run (already exhaustively documented by
  ELITEA-2604).
- `POST /api/v2/elitea_core/skills/prompt_lib/{project_id}` — fires on
  initial skill Save, `201 Created`.
- **`POST /api/v2/elitea_core/skill/prompt_lib/{project_id}/{skill_id}`
  (singular `skill`, the "create version" endpoint fired by "Save As
  Version") — the case-critical call.** `201 Created`, response body
  includes `{"id": <newVersionId>, "name": <versionName>, ...,
  "meta": {"icon_meta": {"url": ..., "name": ..., "size": ...,
  "initial_file_size": ..., "resulting_file_size": ...}}}` —
  the `icon_meta.url` is byte-identical to the base version's, proving
  server-side copy-forward, not a client artifact.
- `GET /api/v2/elitea_core/skill/prompt_lib/{project_id}/{skill_id}/
  {version_id}` — fires on version switch / page load with an explicit
  version segment; response body's `version_details.meta.icon_meta`
  matches whichever version's id was requested. Used this run (via direct
  `browser_network_request` inspection) to independently confirm BOTH
  `1570` (base) and `1571` (v2) carry the identical `icon_meta.url` after a
  full reload — the authoritative per-version assertion point if the
  implementer wants an API-level check in addition to the DOM `src` read.
- `DELETE /api/v2/elitea_core/skill/prompt_lib/{project_id}/{skill_id}` —
  cleanup, `204 No Content`.

## Known Defects / Observations Found During Exploration
No functional or visual product defect was found. The custom icon is
correctly and server-side-persistently carried forward from the base
version into a newly-created version via "Save As Version", and the base
version's own icon is unaffected by the operation. Consistent with the
"icon preserved by reference" pattern the Fork cases (ELITEA-2602/ELITEA-2603)
already documented for a different code path — this case establishes the
same guarantee holds for same-skill version creation too.

## Blocked Steps
None. All 13 case steps were executed end-to-end live against the real DEV
backend, including creating the skill with a custom icon, saving it,
creating a second version via "Save As Version", verifying the icon on the
new version (both immediately and after a full reload), switching back to
base and re-verifying, and switching to v2 again for a third confirmation —
followed by full cleanup.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/skills/test_skill_icon_persists_on_save_as_version.py`
  (new file — grep of `automation/tests/ui/skills/` found no existing test
  combining icon upload with version creation; the nearest neighbors,
  `test_skill_custom_icon_*` (ELITEA-2604/2605, if/when implemented) and
  any `test_skill_version_*` file (ELITEA-2437), each cover one half of
  this case but not their intersection).
- `SkillFormPage.upload_skill_icon(file_path)` (pre-existing) for step 1/
  setup; `SkillFormPage.get_form_icon_src()` (pre-existing) for every
  "verify icon" step (3/9/11/13) — returns `""` for an absent `<img>`
  (default state), never times out, safe to call repeatedly across version
  switches.
- `SkillDetailPage.save_as_version(version_name)` (pre-existing,
  `automation/pages/skill_detail_page.py:1015`) is the direct hook for
  steps 4-7 — already waits on the `Version "{name}" created` toast and the
  URL's version-id segment changing; no new page-object method needed for
  version creation itself.
- `SkillDetailPage.switch_version(version_name)` (pre-existing,
  `automation/pages/skill_detail_page.py:1072`) is the direct hook for
  steps 10/12 — already polls the selector's displayed text to avoid the
  documented MUI re-render race (ELITEA-2440's lesson, noted in its own
  docstring).
- **Optional API-level assertion**: `SkillAPI.get_skill(skill_id)`
  (`automation/api/client.py:1460`) exists but currently has NO way to
  target a SPECIFIC version's `icon_meta` — it always hits the bare
  `/skill/prompt_lib/{project}/{skill_id}` endpoint (no `versionId`
  segment), so it cannot independently distinguish base's vs v2's icon at
  the API layer. If the implementer wants an API-level assertion alongside
  the DOM-level one (recommended, since it's the more authoritative
  signal — see Network Behavior), extend `get_skill()` with an optional
  `version_id: int | None = None` parameter that appends `/{version_id}` to
  the URL when provided; this is a small, additive change with no impact
  on existing callers (ELITEA-2602/ELITEA-2603 already use the bare form
  and would be unaffected). Not a testid gap — a Python API-client
  extension, so it is implementer work, not `add-data-testid` work.
- Wait strategy: wait on the `POST skill/prompt_lib/{project}/{skill_id}`
  network response (`page.wait_for_response`) for step 7's version-creation
  assertion rather than a fixed sleep — `save_as_version()` already does
  this internally via its toast-wait + URL-change-wait combination.
- Consider parametrizing the DOM-level icon-src assertion into a small
  helper (`assert_icon_persisted(expected_src)`) reused across steps 3/9/11/
  13, since it's the same three-way comparison repeated at four points in
  the flow — reduces duplication without weakening the assertion (each call
  site still independently confirms the DOM state at that point in the
  flow, it's just not four near-identical inline blocks).
