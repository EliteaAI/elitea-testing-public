# Test Case: Edit Skill name, description, and instructions

## Metadata
- **TMS ID**: ELITEA-2431
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost `auth_state`).
- A skill must already exist to edit — Rule 10 (read-only-by-default)
  evaluated NO: editing/persisting requires the ability to mutate the
  entity, so an existing stable skill cannot serve; seed a fresh skill
  via `SkillAPI.create_skill()` and clean it up afterward.

## Test Data
### generate-per-test (seeded via API, deleted in teardown)
- Original name: `autotest-skill-edit-original`
- New name: `autotest-skill-edit-updated` (both must satisfy the live
  client-side Name pattern shared by create/edit —
  `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/`, confirmed against
  `skillValidationSchema.validation.js`)
- Original description: `"Original description before edit"`
- New description: `"Updated description after edit"`
- Original instructions: `"Always say ORIGINAL"`
- New instructions: `"Always say UPDATED"`

## Test Steps
1. Open an existing Skill (`/skills/all/{id}`)
   - **Verify**: skill detail/edit page loads with the seeded Name,
     Description, Instructions values displayed
2. Change the Name, Description, and Instructions fields to new values
   - **Verify**: each field displays the newly entered value; Save becomes
     enabled once all three hold valid values
3. Click Save
   - **Verify**: the update persists (`PUT` request → `200 OK`) and a
     "Skill saved" confirmation toast appears; the page stays on the same
     detail URL (no navigation, unlike the create-flow Save)
4. Navigate back to the Skills list and re-open the Skill
   - **Verify**: the skill is listed under its NEW name; clicking it opens
     its detail page
5. Verify all three updated values are persisted correctly
   - **Verify**: Name/Description/Instructions fields all show the values
     entered in step 2, not the originals

## Expected Results
- Editing an existing skill's Name/Description/Instructions and clicking
  Save persists the change server-side (confirmed via a `PUT
  .../skill/prompt_lib/{project}/{skillId}` → `200 OK` and the "Skill
  saved" toast) without navigating away from the detail page.
- Re-opening the skill (list → card click) after the edit shows all three
  updated values, not the originals — full round-trip persistence.
- No console errors, no unexpected network failures.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open an existing Skill | detail page loads | step 1 | `step 1`: `get_name()`/`get_description()`/`get_instructions()` == seeded values | asserted |
| 2 Change Name, Description, Instructions to new values | action completes without error, fields reflect new values | step 2 | `step 2`: field getters == new values + Save enabled | asserted |
| 3 Click Save | control responds, expected next state shown | step 3 | `step 3`: PUT response status 200 + "Skill saved" toast text (inside `save_edits()`) | asserted |
| 4 Navigate back to list, re-open the Skill | detail page loads | step 4 | `step 4`: `skill_exists_in_list(new_name)` + navigation via `click_skill_card()` + `wait_for_page_load()` | asserted |
| 5 Verify all three values persisted | fields show updated values | step 5 | `step 5`: `get_name()`/`get_description()`/`get_instructions()` == new values | asserted |

**Axis 2 — Analyst additions.**
- None beyond the case. Source-level confirmation (not asserted directly,
  informational): the edit-flow Save button reuses the exact same
  `skill-save-button` testid as the create-flow Save, but drives a
  different hook (`useSaveSkill.hooks.js`, `PUT` + `resetForm()` +
  `toastSuccess('Skill saved')`) with no navigation — distinct from the
  create-flow's `useSkillCreate`/navigate-to-detail-page behavior already
  covered by `TestCreateSkill`.

## Cleanup
1. Delete the seeded skill via `SkillAPI.delete_skill(skill_id)` in a
   `try/finally` (same pattern as `TestCreateSkill`/`clean_skill`).
   Confirmed live in this run: no leftover skill after cleanup.

## Concrete Handles (discovered during exploration)

All testid-only. Every field/read handle was already wired on
`SkillFormPage`/`SkillDetailPage`; one new page-object METHOD (no new
testid) was added for the edit-Save mechanics:

| Element | Testid | Page-object field/method |
|---|---|---|
| Name field (real `<input>`) | `skill-name-input-field` | `SkillFormPage.name_input_field` / `set_name()` / `get_name()` |
| Description field (real `<textarea>`) | `skill-description-input-field` | `SkillFormPage.description_input_field` / `set_description()` / `get_description()` |
| Instructions editor content | `skill-instructions-editor-content` | `SkillFormPage.instructions_editor_content` / `fill_instructions()` / `get_instructions()` |
| Save button | `skill-save-button` | `SkillFormPage.save_button` (`is_save_enabled()`); edit-flow save via new `SkillDetailPage.save_edits()` |
| Confirmation toast | `toast-message` | `SkillDetailPage.version_toast_message` (reused — generic app-wide toast, already wired for the Save-As-Version flow) |
| Skill list card (re-open by new name) | `entity-card-name` (card), skill card container | `SkillsListPage.click_skill_card()` / `skill_exists_in_list()` |

No handle gaps. `SkillDetailPage.save_edits()` is a genuinely new METHOD
(not a testid gap) needed because the existing
`save_and_wait_for_navigation()` is create-flow-specific — its
"already navigated" completion check (`"/skills/all/" in url and
"/create" not in url`) is already true *before* the click when already on
a detail page, so reusing it for an edit-save would return immediately
without ever waiting for the PUT to complete (a false pass, not a real
wait). `save_edits()` instead waits on the `PUT
.../skill/prompt_lib/{project}/{skillId}` response (matched by
URL-ends-with-skillId + method PUT, same pattern as
`click_pin_toggle_menu_item()`) and the "Skill saved" toast.

## Network Behavior
- Field edits (Name/Description/Instructions) are 100% client-side,
  synchronous Formik/yup validation (same `skillValidationSchema.
  validation.js` used by the create form) — confirmed live, no network
  calls fire while typing.
- `PUT /api/v2/elitea_core/skill/prompt_lib/{project}/{skillId}` fires on
  Save (step 3) → `200 OK`, confirmed live. No `versionId` path segment —
  this call updates BOTH the skill's name/description AND the currently
  selected version's instructions in one request (confirmed source-side,
  `useSaveSkill.hooks.js`'s `onSave()`).
- `GET /api/v2/elitea_core/skills/prompt_lib/{project}/...` re-fires on
  navigating back to the Skills list (step 4), returning the skill under
  its new name.
- `DELETE /api/v2/elitea_core/skill/prompt_lib/{project}/{skillId}` on
  cleanup → `204 No Content`.

## Known Defects Found During Exploration
None. The edit → Save → re-open → verify round trip behaved exactly per
the case's expected results on the first live run.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, confirmed from `.agents/testing.md`.
- Page objects: `SkillDetailPage` (`automation/pages/skill_detail_page.py`,
  extends `SkillFormPage`) — already had every field getter/setter this
  case needs (`get_name`/`set_name`/`get_description`/`set_description`/
  `get_instructions`/`fill_instructions`, all pre-existing from ELITEA-2430
  and earlier work). Only new addition: `SkillDetailPage.save_edits()`
  (additive-only, new method, no existing method body touched) — see
  § Concrete Handles for why the create-flow save helper isn't reusable.
- Seed via `SkillAPI.create_skill(name, description, instructions)` →
  returns `{"id": ..., ...}`; `skill_id = created["id"]`.
- Re-open by NEW name: `SkillsListPage.click_skill_card(new_name)`
  (pre-existing, added for ELITEA-2435) followed by
  `SkillDetailPage.wait_for_page_load()` — mirrors the existing
  list→detail navigation pattern used elsewhere in this suite.
- Test location: `automation/tests/ui/skills/test_skill_management.py`,
  new class `TestEditSkill` — same file as `TestCreateSkill`/
  `TestSkillMandatoryFieldsValidation` (all three exercise the same
  Name/Description/Instructions form, just different lifecycle stages:
  create, create-validation, edit-persistence).
