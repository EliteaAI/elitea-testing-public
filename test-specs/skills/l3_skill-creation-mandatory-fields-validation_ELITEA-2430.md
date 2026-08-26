# Test Case: Skill creation — mandatory fields validation (Name and Description)

## Metadata
- **TMS ID**: ELITEA-2430
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost `auth_state`).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Unique skill name, e.g. `autotest-skill-mandatory-fields` (must satisfy the
  Name field's live client-side pattern — see § Concrete Handles — lowercase/
  digits/hyphens only, confirmed live via manual entry of a name containing
  only lowercase letters/digits/hyphens; a case-text-literal name is fine as
  long as it fits this shape)
- Description: any non-empty string
- Instructions: any non-empty string (kept filled/unchanged for all 5 Save-
  state checks — the case isolates Name/Description as the two fields under
  test, Instructions is control/constant throughout)

## Test Steps
1. Navigate to `${BASE_URL}/skills/create`
   - **Verify**: create-skill form loads (Name/Description/Instructions
     fields + Save/Cancel visible; Save initially disabled on the empty form)
2. Leave Name empty; fill Description and Instructions
   - **Verify**: fields accept and display the entered values
3. Verify Save button is disabled
4. Fill Name; clear Description; keep Instructions filled
   - **Verify**: Name field displays the entered value; Description field is
     empty
5. Verify Save button is disabled
6. Clear Name too (both Name and Description now empty; Instructions still
   filled)
7. Verify Save button is disabled
8. Fill both Name and Description (Instructions still filled)
   - **Verify**: both fields display the entered values
9. Verify Save button is enabled
10. Click Save
    - **Verify**: navigation to the new skill's detail page
      (`/skills/all/{id}`) succeeds; the skill then appears in the Skills
      list (`/skills/all`) by its Name

## Expected Results
- Save stays disabled for every combination of Name/Description where at
  least one of the two is empty — confirmed live for all three combinations
  the case exercises (Name empty; Description empty; both empty).
- Save becomes enabled only once both Name and Description are non-empty
  (with Instructions already satisfied throughout).
- Save succeeds, redirects to the new skill's detail page, and the skill is
  listed on `/skills/all` afterward.
- No console errors, no unexpected network failures.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Create Skill page | page loads | step 1 | `step 1`: form fields + disabled Save visible | asserted |
| 2 Leave Name empty, fill Description+Instructions | fields accept input | step 2 | `step 2`: field values reflect input | asserted |
| 3 Save disabled (Name empty) | Save inactive | step 3 | `step 3`: `is_save_enabled() is False` | asserted |
| 4 Fill Name, clear Description, keep Instructions | fields accept input | step 4 | `step 4`: field values reflect input | asserted |
| 5 Save disabled (Description empty) | Save inactive | step 5 | `step 5`: `is_save_enabled() is False` | asserted |
| 6 Leave both Name and Description empty | fields empty | step 6 | `step 6`: field values are empty | asserted |
| 7 Save disabled (both empty) | Save inactive | step 7 | `step 7`: `is_save_enabled() is False` | asserted |
| 8 Fill both Name and Description, keep Instructions | fields accept input | step 8 | `step 8`: field values reflect input | asserted |
| 9 Save enabled | Save active | step 9 | `step 9`: `is_save_enabled() is True` | asserted |
| 10 Click Save — skill created, appears in Skills list | navigation + list membership | step 10 | `step 10`: detail-page URL/testid + list membership by name | asserted |

**Axis 2 — Analyst additions.**
- None beyond the case. (Live exploration also surfaced per-field MUI helper
  text — "Name is required" / "Description is required" — but those
  `<p>` nodes carry no `data-testid` in `CreateSkillForm.jsx`, and the case
  only requires the Save-button disabled/enabled state, not the helper
  text's content — so no new testid was requested and no assertion was
  added on that text; the Save-button-state assertion is the case's actual
  and sufficient observable.)

## Cleanup
1. Delete the created skill via `SkillAPI.delete_skill(skill_id)` in a
   `try/finally` (mirrors `TestCreateSkill` in `test_skill_management.py`
   and the `clean_skill` fixture pattern) — get `skill_id` from the
   post-save redirect URL regex `/skills/all/(\d+)$`. Confirmed live in this
   run: UI delete flow works cleanly (overflow menu → type-to-confirm
   dialog → 204), no leftover skill after cleanup.

## Concrete Handles (discovered during exploration)

All testid-only, all pre-existing (`automation/pages/skill_form_page.py`
already wires every one of these — no `add-data-testid` work needed for
this case):

| Element | Testid | Page-object field |
|---|---|---|
| Name field (real `<input>`) | `skill-name-input-field` | `SkillFormPage.name_input_field` |
| Description field (real `<textarea>`) | `skill-description-input-field` | `SkillFormPage.description_input_field` |
| Instructions editor content | `skill-instructions-editor-content` | `SkillFormPage.instructions_editor_content` |
| Save button | `skill-save-button` | `SkillFormPage.save_button` (`is_save_enabled()` already implemented) |
| Skill detail confirmation anchor | `skill-information-section` | used internally by `save_and_wait_for_navigation()` |
| Skill list card name (for step-10 list-membership check) | `entity-card-name` | `SkillsListPage.skill_card_name` / `skill_exists_in_list()` |

No handle gaps — every element the case touches already has a stable
`data-testid` bound through the existing `SkillFormPage`/`SkillsListPage`
page objects.

## Network Behavior
- Save-state transitions (steps 3/5/7/9) are 100% client-side, synchronous
  Formik/yup validation (`skillValidationSchema.validation.js`) — confirmed
  live, no network calls fire on field edit.
- `POST /api/v2/elitea_core/skills/prompt_lib/{projectId}` fires on Save
  (step 10) → `201 Created`, confirmed live (skill id `1428` created,
  navigated to `/skills/all/1428`).
- `DELETE /api/v2/elitea_core/skill/prompt_lib/{project}/{skillId}` on
  cleanup → `204 No Content`.

## Known Defects Found During Exploration
None found. All 5 Save-state checks (steps 3, 5, 7, 9, and the final
Save-succeeds-and-lists at step 10) behaved exactly per the case's expected
results.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, confirmed from `.agents/testing.md`.
- Page objects: `SkillFormPage` (`automation/pages/skill_form_page.py`) and
  `SkillsListPage` (`automation/pages/skills_list_page.py`) — both already
  cover every handle this case needs. `SkillFormPage.set_description()`
  already exists (click + `select_text()` + Backspace + type — the reliable
  clear-then-fill pattern, confirmed live it correctly clears a populated
  field). **Gap: no symmetric `set_name()` method exists yet** —
  `fill_form()`'s internal `_fill_text_input()` (Ctrl+A + type) does NOT
  reliably clear a populated field back to empty (typing an empty string
  after Ctrl+A leaves the selection unresolved, field stays populated) —
  confirmed by inspecting `_fill_text_input`'s implementation against
  `set_description`'s docstring rationale, same MUI-input class of
  component in both cases. The implementer should add
  `SkillFormPage.set_name(name: str)` mirroring `set_description()`
  exactly (additive-only, new method, no existing method body touched) —
  needed for step 6's "clear Name too" transition (step 4 already fills an
  *empty* Name field, where `_fill_text_input`/`fill_form`'s existing
  behavior is fine; only step 6's clear-a-populated-field needs the new
  method).
- Wait strategy: after every field edit, call
  `SkillFormPage.wait_for_form_validation()` (already exists — waits network
  + a fixed debounce) before reading `is_save_enabled()`. Confirmed live
  the Save `disabled` attribute flips synchronously on validation, no
  extra wait needed beyond the existing helper.
- Cleanup: reuse the `clean_skill`-fixture pattern from
  `test_skill_management.py` (delete-if-exists before + after, via
  `skill_api` fixture) rather than inventing a new cleanup helper.
- Suggested test location: `automation/tests/ui/skills/test_skill_management.py`
  (same file as `TestCreateSkill`, since it exercises the same create form)
  — new class `TestSkillMandatoryFieldsValidation`, OR a small dedicated
  file `test_skill_creation_validation.py` if the reviewer prefers isolating
  the 5-assertion validation flow from the create+run+delete happy-path
  test. Either is consistent with the project's per-feature file grouping;
  implementer's call.
