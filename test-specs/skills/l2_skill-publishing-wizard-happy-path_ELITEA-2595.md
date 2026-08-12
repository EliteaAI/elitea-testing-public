# Test Case: Skill Publishing Wizard — Happy Path

## Metadata
- **TMS ID**: ELITEA-2595
- **Linked Story**: none
- **Priority**: l2 (high, per case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost `auth_state`).
- A project exists and is accessible (`${ELITEA_PROJECT_ID}`, "Private" project used this run).
- User has the `skills.publish` permission and no platform policy blocks skill
  publishing for this project (`platformSettings.is_skill_publish_blocked` —
  confirmed unset/false this run; `usePublishSkill.hooks.js`).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: unique per run, e.g. `test-publish-skill-${uuid}` (case's literal
  `test-publish-skill` collides across repeat runs — generate uniquely)
- Skill description: ≥50 chars (live-confirmed threshold — see § Automation
  Hints; case's own "100+ characters" figure is generous but not the actual
  gate), containing at least one action verb (`helps`/`analyzes`/`generates`)
  to avoid the "lacks action verbs" WARNING (optional polish — WARNING alone
  doesn't block Publish, but a clean `PASS` is easy to reach and asserts more)
- Skill instructions: ≥100 chars (live-confirmed threshold)
- Version name: `v1.0` (must match `VERSION_NAME_REGEX` — letters/digits/dots/
  hyphens/underscores only)
- Category: any option from the live dropdown (`Business Analyst`, `Quality
  Assurance`, `Development`, `DevOps`, `Project Management`, `Knowledge &
  Documentation`, `Elitea`, `Epam`, `Other`) — this run used `Quality Assurance`
- **Custom icon** — NOT in the case's own Test Data table, but a REQUIRED
  prerequisite live (see § Known Defects / Coverage Map) — pick any existing
  entry from the project-scoped "Uploaded" gallery tab (fastest — no file
  upload needed) via `SkillFormPage.upload_skill_icon_edit_mode()`
  (ELITEA-2604), or upload `test-data/images/skill-fork-test-icon.png`
- **At least one tag** — also NOT in the case's Test Data table, also a
  REQUIRED prerequisite live — add via the skill form's Tags combobox
  (`skill-tags-input-field`, type + Enter)

## Test Steps
1. Navigate to `${BASE_URL}/skills/create`
   - **Verify**: create-skill form loads; fill Name, Description (≥50 chars),
     Instructions (≥100 chars); Save enabled once Name+Description non-empty
2. Click Save
   - **Verify**: navigates to `/skills/all/{skillId}`; skill created
     successfully
3. Add a tag and a custom icon to the skill (both required to avoid an
   outright FAIL at Validation — see Test Data)
   - **Verify**: tag chip renders in the Tags field; icon `<img>` renders
     with a non-empty `src` in place of the default placeholder; Save
     persists both
4. Open the skill's overflow ("Skill" ⋮) menu → VERSION group → "Publish"
   - **Verify**: Publish wizard modal opens on Step 1 "Preparation" — a
     3-step Stepper (Preparation/Validation/Publishing) is visible
5. Enter a valid Version name (`v1.0`) and select a Category from the dropdown
   - **Verify**: fields accept input; no validation errors shown; "Continue"
     stays disabled until the checkbox below is also checked
6. Check "I agree with the Publishing Terms."
   - **Verify**: checkbox is checked; "Continue" button becomes enabled
7. Click "Continue" to proceed to Step 2: Validation
   - **Verify**: `POST .../publish_skill_validate/prompt_lib/{project}/
     {skillId}/{versionId}` fires; Validation step renders the result
     (`SUMMARY:` header + status message + Critical/Warnings/Suggestions
     counter badges)
8. Verify validation does NOT return `FAIL`
   - **Verify**: response `status` is `WARN` or `PASS` (never `FAIL`) given
     the icon+tag+length prerequisites from step 3; "Publish" button (this
     step's confirm action) is ENABLED
9. Click "Publish" to complete the process
   - **Verify**: `POST .../publish_skill/prompt_lib/{project}/{skillId}/
     {versionId}` returns 200; wizard closes; a success toast appears
10. Re-select the newly published version by name from the VERSION dropdown
    (auto-navigation is unreliable — known defect #614, reproduces for
    skills too, see § Known Defects)
    - **Verify**: the new version (`v1.0`) is present in the dropdown list
11. Navigate to `${BASE_URL}/elitea-catalog?tab=skills`
    - **Verify**: the published skill appears under its selected Category
      group, with its custom icon and name
12. Verify the published skill's details
    - **Verify**: name, category match the input values (name shown on the
      catalog card is the skill's live Name field, not the version name)

## Expected Results
- The skill is created successfully with a custom icon and ≥1 tag in
  addition to the case's documented 100+-char description/instructions.
- The 3-step wizard completes: Preparation → Validation (`status` ≠ `FAIL`)
  → Publishing (200 response, success toast).
- The skill appears in the Catalog's Skills tab, grouped under its selected
  Category, after re-selecting the version by name (auto-navigation is
  unreliable, see Known Defects).
- No console errors beyond the pre-existing #611 Stepper-icon signature (see
  Known Defects) and the pre-existing #554 toolkits-404 race.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Skills, create skill with valid name/desc(100+)/instructions(100+) | skill created and saved | steps 1–2 | `step 2`: URL is `/skills/all/{id}` | asserted, *clarification: icon+tag also required, see Known Defects* |
| 2 Open skill, click "Publish" | wizard modal opens, Step 1 Preparation | step 4 | `step 4`: dialog visible (Version-name input rendered), Continue starts disabled | asserted, *clarification: trigger is a MENU ITEM inside the overflow menu, not a standalone "Publish" button; docs(afs) correction PR #1464 review — the AFS previously claimed "Stepper shows 3 steps" is asserted here, but the implementation never checks a step count (no testid exists on the Stepper's step nodes); the wording now matches what step 4's code actually verifies* |
| 3 Enter version name + category | fields accept, no errors | step 5 | `step 5`: field values reflect input | asserted |
| 4 Accept Publishing Terms checkbox | checked, Next enabled | step 6 | `step 6`: checkbox checked + Continue enabled | asserted |
| 5 Click Next → Step 2 Validation | validation runs automatically | step 7 | `step 7`: validate response captured | asserted |
| 6 Wait for validation to complete | passes, no FAIL (may show warnings) | step 8 | `step 8`: `status != "FAIL"` | asserted, *clarification: only true when icon+tag are present — see #1463* |
| 7 Click Next → Step 3 Publishing | publishing confirmation step shown | step 9 (Publish click) | `step 9`: publish request fires | asserted *(the live wizard collapses "Next"+"Publish" into a single "Publish" action on the Validation step once status≠FAIL — there's no separate intermediate confirmation click)* |
| 8 Click Publish | publishing completes, success shown | step 9 | `step 9`: 200 response + toast | asserted |
| 9 Navigate to Catalog | published skill appears with correct version | steps 10–11 | `step 12`: skill card visible under category (mislabeled `step 11` previously — step 11 only asserts the category heading visible; the category-scoped skill-card check is `get_skill_card(skill_name, category=CATEGORY_NAME)` in step 12's code) | asserted, *decomposed: version re-select (step 10) needed first due to #614* |
| 10 Verify published skill details | name/description/version/category match | step 12 | `step 12`: card fields match input | asserted |

**Axis 2 — Analyst additions.**
- `step 3` asserts the icon+tag are BOTH required to avoid FAIL — *added:
  discovered live that the case's documented prerequisites (name/desc/
  instructions/category/terms) are insufficient on their own; omitting this
  would leave the implementer stuck at a disabled Publish button with no
  explanation, exactly the #612 precedent.*
- `step 7` captures the validate response body (not just the visible status
  text) — *added: the `critical_issues`/`warnings` arrays and `source`
  field are the implementer's most reliable assertion surface, more stable
  than matching AI-generated prose.*
- Console-cleanliness check around the wizard, filtered for the pre-existing
  #611 (Stepper icon prop-forwarding) and #554 (toolkits 404 race)
  signatures — *added: same discipline already established in
  `test_agent_publish_unpublish_version.py` for the identical shared
  component; asserting blindly would either mask a real regression or
  false-fail on these two known, unrelated issues.*

## Cleanup
1. Delete the created skill via `SkillAPI.delete_skill(skill_id)` or the UI's
   "Delete skill" menu item (deletes all versions including the published
   one — confirmed acceptable for disposable test skills, no separate
   "unpublish" step required before delete based on this run's exploration
   scope).

## Concrete Handles (discovered during exploration)

Testid-only per `.agents/testing.md` § Locator policy — no role/text/CSS
handles. PROVENANCE verified via `cd ../EliteaUI && git fetch origin` +
`git grep` against `origin/main` and `origin/automation/testids` this run.

| Element | Testid | PROVENANCE |
|---|---|---|
| Skill Name input (create form) | `skill-name-input-field` | on-main ✓ |
| Skill Description input (create form) | `skill-description-input-field` | on-main ✓ |
| Skill Instructions editor | `skill-instructions-editor-content` | on-main ✓ |
| Skill Tags input | `skill-tags-input-field` | on-main ✓ |
| Create-form Save button | `skill-save-button` | on-main ✓ |
| Skill controls (⋮) overflow menu button | `skill-controls-menu-button` | on-main ✓ |
| "Publish" menu item | `publish-menuitem` | **dynamically constructed** — `DotMenu.jsx`: `` data-testid={testId ? `${testId}-menuitem` : undefined} ``, `testId = item.key`; `SkillControls.jsx` sets `key: 'publish'` at the call site. Not a literal grep hit on either ref — verify by reading `SkillControls.jsx`'s `key: 'publish'` line + `DotMenu.jsx`'s template, both on-main ✓ |
| Publish wizard — Version name input | `agent-publish-version-name-input` | on-`automation/testids` only (awaiting human promotion to main) — pre-existing, added for the agent Publish flow (ELITEA-1892), shared component |
| Publish wizard — Category select trigger | `agent-publish-category-select` (dynamic option: `select-option-{Category Label}`) — **implementer correction**: live source (`PreparationStep.jsx`) confirms no `-combobox` suffix, the AFS's original value was wrong | on-`automation/testids` only |
| Publish wizard — Publishing Terms checkbox | `agent-publish-agree-checkbox` | on-`automation/testids` only |
| Publish wizard — Continue button (Preparation step) | `agent-publish-continue-button` | on-`automation/testids` only |
| Publish wizard — Publish button (Validation step) | `agent-publish-confirm-button` | on-`automation/testids` only |
| Skill icon avatar (opens icon picker) | `skill-form-icon-button` | on-`automation/testids` only |
| Skill form icon `<img>` | `skill-form-icon-img` | on-main ✓ (pre-existing, ELITEA-2604) |
| Icon picker — Upload button | `icon_picker_upload_button` (page-object field name — see `skill_form_page.py`) | on-main ✓ (ELITEA-2604) |
| VERSION dropdown trigger | (existing `SkillDetailPage` field — see `switch_version()`/`open_version_selector()`) | on-main ✓ |
| VERSION option by name | dynamic `version-option-{name}` | on-main ✓ |
| Catalog — Skills tab | `catalog-skills-tab` | on-`automation/testids` only |
| Catalog — skill category section container (scopes the published skill's card as a DESCENDANT of its selected category, not merely present anywhere on the page) | `catalog-category-section-{slug}` (slugify: lowercase, `[^a-z0-9]+` → `-`) | **new — added this round**, EliteaAI/EliteaUI@c80de351, on-`automation/testids` only (awaiting human promotion to main) |

One new testid WAS added this round: `catalog-category-section-{slug}`
(EliteaAI/EliteaUI@c80de351) — superseding this AFS's original "no new
testids needed" claim, which held only for the initial implementation pass,
not after this fix round's addition. Every other handle this flow touches
remains pre-existing (shared with the agent Publish flow + prior skill AFS
work). The 5 pre-existing testids marked "on `automation/testids` only" are
from ELITEA-1892's agent-Publish rework, not new work for this case — they
will reach `main` via the same human cherry-pick already pending for that
case.

## Network Behavior
- `POST .../publish_skill_validate/prompt_lib/{project}/{skillId}/{versionId}`
  — fires on "Continue" click. `422` when the response body's `status` is
  `"FAIL"`; `200` when `"WARN"` or `"PASS"`. Body:
  `{status, critical_issues[], warnings[], recommendations[], counts,
  summary, ai_validation_available, validation_token}`.
- `POST .../publish_skill/prompt_lib/{project}/{skillId}/{versionId}` —
  fires on the Validation step's "Publish" click, only enabled once
  `status !== "FAIL"`. `200` on success; response may carry
  `{error: true, msg}` even on 200 (partial-success warning toast) — check
  for `data?.error` per `usePublishSkill.hooks.js`.
- Upload icon (edit mode): `POST .../upload_skill_icon/prompt_lib/{project}`
  (gallery upload) followed by `PUT .../upload_skill_icon/prompt_lib/
  {project}/{versionId}` (apply to this skill version) — TWO sequential
  requests, not one (mirrors `SkillFormPage.upload_skill_icon_edit_mode()`'s
  existing handling).

## Known Defects Found During Exploration
- **[MINOR/CLARIFICATION]** filed as
  https://github.com/EliteaAI/elitea-testing-public/issues/1463 — missing
  custom icon AND missing tags are `critical_issues`/`FAIL`-blocking, not
  documented anywhere in the case's Test Data as prerequisites. Not a
  product defect (deterministic, intentional backend rule) — case-text
  drift. Automation follows the live contract: icon+tag are required setup,
  not optional embellishment.
- **[MINOR, already tracked]** Known defect #614 (filed against ELITEA-1892,
  agent Publish) reproduces identically for skills: after a successful
  Publish, the VERSION dropdown does not auto-select the new version — it
  stays showing the previous active version until re-selected by name.
  Automation must call the skill-equivalent of `select_version_by_name()`
  after Publish rather than assume auto-navigation (same handling as
  `test_agent_publish_unpublish_version.py`).
- **[MINOR, already tracked, not independently re-verified this run]**
  Known defect #611 (agent Publish, same `PublishWizardModal.jsx` Stepper)
  likely reproduces for skills too — the console-cleanliness check should
  use the same `_is_known_defect_611`-style filter as the existing agent
  spec rather than assert blind console-cleanliness.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page objects: extend `SkillDetailPage` (`automation/pages/skill_detail_page.py`)
  with `open_publish_wizard()` / `fill_publish_preparation_step()` /
  `click_publish_continue()` / `confirm_publish()` methods MIRRORING
  `AgentDetailPage`'s existing implementations at
  `automation/pages/agent_detail_page.py:3714-3860` (same shared component,
  same testids, same network-wait pattern) — do not duplicate the
  `LocatorDescriptor` fields, add them to `SkillDetailPage` fresh since
  they don't yet exist there (only `AgentDetailPage` has them).
- Icon upload: reuse `SkillFormPage.upload_skill_icon_edit_mode()`
  (ELITEA-2604, `automation/pages/skill_form_page.py:457`) as-is — already
  handles the two-request edit-mode flow.
- Tag entry: reuse the existing `skill-tags-input-field` pattern from
  ELITEA-2433's spec (`test_add_save_remove_skill_tag.py` or similar) if a
  helper method already exists; otherwise a simple `.fill()` +
  `press('Enter')` on the testid suffices (confirmed live this run).
- Seed via `SkillAPI.create_skill(name, description, instructions)`
  (`automation/api/client.py:1427`) for description/instructions length —
  faster and more deterministic than typing 100+ chars via UI — then use
  the UI only for the icon/tag/publish flow the case actually tests. (The
  case's own step 1 says "Navigate to Skills section and create a new
  skill" — UI creation is also acceptable and was what this exploration
  run used; either is fine, API seeding is a speed optimization the
  implementer may take.)
- Wait strategy: `expect_response()` on `publish_skill_validate` /
  `publish_skill`, never a fixed sleep — mirrors
  `AgentDetailPage.click_publish_continue()` / `confirm_publish()` exactly.
