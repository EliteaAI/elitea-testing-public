# Test Case: Multiple tags can be saved on a Skill upon and after creation

## Metadata
- **TMS ID**: ELITEA-2434
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`).
- A project is selected/accessible (`Private`, id `399` in this run).

## Test Data

### generate-per-test (created live via the UI create form in this test, not the API — the case explicitly exercises the pre-save Tags field; cleaned up in its own teardown)
- Skill name: `autotest-multi-tag-{timestamp}` (kebab-case, ≤32 chars).
- Skill description: `"Autotest skill for ELITEA-2434 multi-tag verification."`
- Skill instructions: `"You are a test skill used for multi-tag automation. Reply 'ok'."`
- Tags added BEFORE first save: `tag1`, `tag2` (plain alphanumeric — no
  hyphen, so no case-text-drift issue here, unlike ELITEA-2433's
  `"regression-v1"`).
- Tags added AFTER save (edit mode): `tag3`, `tag4`.

## Test Steps
1. Navigate to `${BASE_URL}/skills/create`. Fill Name, Description,
   Instructions (`SkillFormPage.fill_form()`). Click into the Tags
   combobox (`skill-tags-input-field`), type `tag1`, press Enter; type
   `tag2`, press Enter — both committed BEFORE the first Save.
   - **Verify**: two tag chips (`tag1`, `tag2`) render in the create form
     (`get_tags() == ["tag1", "tag2"]`); confirmed live — the Tags field is
     fully available and committable pre-save on `/skills/create`.
2. Click Save (`SkillFormPage.save_and_wait_for_navigation()`).
   - **Verify**: `POST /api/v2/elitea_core/skills/prompt_lib/{project_id}`
     fires and returns `201`; the payload's `tags` includes `tag1`/`tag2`;
     the browser navigates from `/skills/create` to
     `/skills/all/{new_skill_id}` (create-flow behavior, distinct from the
     edit-flow's no-navigation save).
3. Re-open the Skill — navigate away (`${BASE_URL}/skills/all`) then back
   into `${BASE_URL}/skills/all/{skill_id}` (a fresh page load, not just
   the post-create render, to prove backend persistence).
   - **Verify**: `get_tags() == ["tag1", "tag2"]` on the freshly-loaded
     detail page — confirmed live, both tags survive the create → reload
     round trip.
4. Add new tags `tag3`, `tag4` to the saved (existing) Skill — same
   Tags-combobox interaction as step 1, now in edit mode.
   - **Verify**: `get_tags() == ["tag1", "tag2", "tag3", "tag4"]` in the
     form (all four present, original order preserved); `skill-save-button`
     enabled. Click Save (`SkillDetailPage.save_edits()`).
   - **Verify**: `PUT .../skill/prompt_lib/{project_id}/{skill_id}` fires
     and returns `200`; toast `"Skill saved"`; no navigation (edit-flow
     save contract, confirmed live).
5. Verify all four tags are persisted — navigate away and back into the
   detail page (fresh reload, same discipline as step 3).
   - **Verify**: `get_tags() == ["tag1", "tag2", "tag3", "tag4"]` on the
     freshly-loaded page — confirmed live, all four tags (2 from creation
     + 2 from the later edit) persist together through a full backend
     round trip. Also verify the skill's card in `/skills/all` — **amended
     during implementation** (case-text drift, see Known Defects
     Clarification #1 below): `CardTagSection.jsx` caps a card at
     `MAX_NUMBER_TAGS_SHOWN = 2` individually-rendered tag chips regardless
     of how many tags the skill actually has, so a 4-tag skill's card never
     renders 4 chips. The live-accurate check is:
     `SkillsListPage.get_card_tags(skill_name)` returns exactly the 2
     rendered chips, both members of the 4-tag set, **and**
     `SkillsListPage.get_card_tag_overflow_text(skill_name) == "+2"`
     (new page-object method, ELITEA-2434) proving the other 2 aren't
     silently dropped, just collapsed into the overflow badge.

## Expected Results
- Tags committed before the first Save (create flow) are included in the
  `POST` payload and persist through the create → detail-page redirect and
  a subsequent fresh reload.
- Tags added later (edit flow) merge with the pre-existing tags rather than
  replacing them — the full set of 4 persists together through a fresh
  reload and renders on both the detail-page form and the list-view card.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create new Skill with tags "tag1","tag2" added before first save | operation completes, state updates | step 1 | `step 1`: `get_tags() == ["tag1","tag2"]` pre-save | asserted |
| 2 Save the Skill | operation completes, state updates | step 2 | `step 2`: POST 201, tags in payload, redirect to detail page | asserted |
| 3 Re-open the Skill | action completes, expected UI state | step 3 | `step 3`: fresh reload, `get_tags() == ["tag1","tag2"]` | asserted |
| 4 Add new "tag3","tag4" tags to the saved skill | operation completes, state updates | step 4 | `step 4`: PUT 200, toast, all 4 in form | asserted |
| 5 Verify all four tags are persisted | condition holds | step 5 | `step 5`: fresh reload, `get_tags() == [4 tags]`, card shows all 4 | asserted |

### Axis 2 — Analyst additions
- `step 2` asserts the `POST` payload's `tags` field explicitly (not just
  the redirect) — the case only checks "operation completes"; added so a
  regression that drops pre-save tags from the create payload (but still
  redirects successfully) would be caught.
- `step 3` and `step 5` both use a **fresh page navigation** rather than
  reading the post-action render — proves backend persistence at both
  checkpoints (post-create and post-edit), not just client-side state
  surviving in memory.
- `step 4` asserts tag ORDER is preserved in the form
  (`["tag1","tag2","tag3","tag4"]`, not merely "all 4 present") — added
  because the case's step 5 wording ("all four tags are persisted") could
  be satisfied by a set-membership check alone; order preservation is a
  stronger, still-cheap assertion confirmed live.
- `step 5` also checks the list-view card renders all four tags — the
  case's pass criterion only mentions the detail page implicitly; added
  for parity with ELITEA-2433's card-level check and because
  `get_card_tags()` already exists.

## Cleanup
1. Delete the skill via `skill_api.delete_skill(skill_id)` in a
   `try/finally` (the skill's ID is captured from the create-flow's
   post-save redirect URL, `/skills/all/(\d+)$`, same pattern documented
   for the Build-with-AI tests).

## Concrete Handles (discovered during exploration)

No testid gaps for this case — every element is already wired.

| Element | Recommended Locator | Fallback |
|---|---|---|
| Name / Description / Instructions inputs | `SkillFormPage.name_input` / `description_input` / `instructions_editor` (existing, `fill_form()`) | none needed |
| Tags combobox / input | `LocatorDescriptor(testid="skill-tags-input")` / `skill-tags-input-field` (existing, `add_tag()`) | none needed |
| Committed tag chip | `LocatorDescriptor(testid="skill-tag-chip")` (existing, `get_tags()`) | none needed |
| Save button (create flow) | `LocatorDescriptor(testid="skill-save-button")`; `SkillFormPage.save_and_wait_for_navigation()` (existing — handles the nav-blocker dialog) | none needed |
| Save button (edit flow) | Same testid; `SkillDetailPage.save_edits()` (existing — PUT-wait + toast-assert + no-navigation-assert) | none needed |
| Skill card's tag chips (list view) | `SkillsListPage.get_card_tags(skill_name)` / `CARD_TAG_CHIP` (existing, ELITEA-1740 rework) | none needed |

## Network Behavior
- `POST /api/v2/elitea_core/skills/prompt_lib/{project_id}` — create-flow
  save; payload `{name, description, versions: [...], tags: [...]}`
  (pre-save tags ride this payload); returns `201`.
- `PUT /api/v2/elitea_core/skill/prompt_lib/{project_id}/{skill_id}` —
  edit-flow save (adding tag3/tag4); returns `200`.
- `GET /api/v2/elitea_core/skill/prompt_lib/{project_id}/{skill_id}` —
  fires on each fresh detail-page load (steps 3 and 5); confirms the
  persisted tag list without relying on client-side state.

## Known Defects Found During Exploration
- **[CLARIFICATION]** (added during implementation) Step 5's original
  wording assumed a Skill card in `/skills/all` renders every one of its
  tags as an individual chip. Confirmed live/source-side
  (`EliteaUI/src/components/CardTagSection.jsx`,
  `MAX_NUMBER_TAGS_SHOWN = 2`): a card renders **at most 2** tag chips
  regardless of the skill's actual tag count, with a "+N" overflow badge
  (`entity-card-tag-overflow` testid) covering the rest. This is intentional
  UI design (a card is a compact summary), not a persistence defect — the
  detail-page form (step 5's `get_tags()` check) still proves all 4 tags
  are correctly persisted server-side. Case-text drift, not a product
  defect; the reverse-masking-safe assertion is: 2 chips rendered (both
  real members of the 4-tag set) + overflow badge reads `"+2"`. Not filed
  as a tracker issue (cosmetic/UI-design fact, not a behavior bug) — noted
  here so a future analyst/implementer on a card-tag assertion doesn't
  re-derive this.
- No other defects found. (Unlike ELITEA-2433, this case's own test data —
  `tag1` through `tag4` — contains no hyphens, so the Tags-field
  hyphen-rejection behavior documented in
  `EliteaAI/elitea-testing-public#1445` does not affect this case.)

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page objects: `SkillFormPage` (create-flow) and `SkillDetailPage`
  (extends `SkillFormPage`, edit-flow) — both exist, pure reuse, no new
  page-object work needed for this case.
- Fixture: `skill_api` (`SkillAPI`) for teardown-only cleanup (setup is via
  the live UI create form itself, per this case's own scope — unlike
  ELITEA-2433 where setup-via-API is safe because the case doesn't care
  about the create form).
- Rides the same branch/file area as ELITEA-2433 (both skills/tags cases,
  analysed together) but is its own test method — the two cases differ in
  STEPS (create-with-pre-save-tags-then-extend vs
  open-existing-then-add-then-remove), not just data, so they are NOT a
  parameterized family per `test-case-analysis` § Execute.
