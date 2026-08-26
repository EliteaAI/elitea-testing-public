# Test Case: Add, save, and remove a tag on a Skill

## Metadata
- **TMS ID**: ELITEA-2433
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

### generate-per-test (in test setup via `skill_api` fixture, cleaned up in its own teardown)
- Skill name: `autotest-tag-add-remove-{timestamp}` (kebab-case, ≤32 chars —
  the live Skill `Name *` field enforces lowercase-kebab-case-only, same
  constraint tracked for ELITEA-1737/1739/1740).
- Skill description: `"Autotest skill for ELITEA-2433 tag add/remove flow."`
- Skill instructions: `"You are a test skill used for tag add/remove automation. Reply 'ok'."`
- Created via `SkillAPI.create_skill()` with no `tags` field in the payload
  — satisfies the case's "existing Skill with no tags" precondition without
  depending on a specific pre-existing project skill (safer for repeat
  runs / parallel suites than reusing a shared fixture skill).
- **Tag text: `regression_v1`** — **NOT** `"regression-v1"` as literally
  written in the case's step 2. The live Tags field rejects hyphens
  client-side (see Known Defects/Clarification #1 below); this is
  case-text drift, not a product defect. `regression_v1` (underscore)
  is functionally equivalent for the purposes of this case (add → save →
  verify → remove → save → verify) and commits/persists normally.

## Test Steps
1. Setup: create the skill via `skill_api.create_skill()` (no tags). Navigate
   to `${BASE_URL}/skills/all/{skill_id}`.
   - **Verify**: Skill detail page loads (`skill-information-section`
     visible); `SkillFormPage.get_tags()` returns `[]` (confirms the
     "no tags" precondition on the live skill, not just an assumption).
2. Click into the Tags combobox (`skill-tags-input-field`), type
   `regression_v1`, press Enter.
   - **Verify**: a tag chip labelled `regression_v1` appears in the form
     (`skill-tag-chip` testid, text content `regression_v1`); the
     `skill-save-button` becomes enabled (was disabled pre-edit).
3. Click Save (`SkillDetailPage.save_edits()`).
   - **Verify**: `PUT .../skill/prompt_lib/{project}/{skill_id}` fires and
     returns `200`; toast text is exactly `"Skill saved"`; the browser URL
     does NOT change (edit-flow save, no navigation — confirmed live,
     matches `save_edits()`'s documented contract). Then navigate to
     `${BASE_URL}/skills/all` (list) and verify the skill's card renders a
     `regression_v1` tag chip (`SkillsListPage.get_card_tags(skill_name)`
     includes `"regression_v1"`) — confirmed live.
4. Re-open the skill (navigate to `${BASE_URL}/skills/all/{skill_id}` —
   a fresh page load, not just the post-save render, to prove backend
   persistence rather than lingering client state). Click the
   `regression_v1` chip's delete icon (the icon `<img>`/SVG child inside
   the `skill-tag-chip` node — clicking the chip's label/body does NOT
   remove it, confirmed live; see Concrete Handles for the exact locator).
   - **Verify**: the chip disappears from the form; `get_tags()` returns
     `[]`; `skill-save-button` becomes enabled again.
5. Click Save (`SkillDetailPage.save_edits()`).
   - **Verify**: `PUT .../skill/prompt_lib/{project}/{skill_id}` fires and
     returns `200`; toast `"Skill saved"`. Navigate to
     `${BASE_URL}/skills/all` (list) and verify the skill's card no longer
     renders any tag chip (`get_card_tags(skill_name) == []`) — confirmed
     live.

## Expected Results
- Adding a tag, saving, and reloading correctly persists the tag on both
  the detail-page form and the list-view card.
- Removing the tag (via its chip's delete icon), saving, and reloading
  correctly removes it from both the form and the card — no orphan tag
  remains anywhere (form, card, or the page-header Tags filter panel).
- Both saves use the edit-flow `PUT` (not `POST`), fire the `"Skill saved"`
  toast, and do not navigate away from the detail page.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open an existing Skill with no tags | page/section loads | step 1 | `step 1`: detail page loads, `get_tags() == []` | asserted |
| 2 Add tag "regression-v1" | operation completes, state updates | step 2 | `step 2`: chip appears, Save enabled | asserted *(tag text changed to `regression_v1` — case-text drift, see Clarification #1)* |
| 3 Save — verify tag appears on Skill card in list | operation completes, state updates | step 3 | `step 3`: PUT 200, toast, card shows chip | asserted |
| 4 Re-open the Skill and remove "regression_v1" | action completes, expected UI state | step 4 | `step 4`: chip removed, Save enabled | asserted |
| 5 Save — verify tag no longer appears on card | operation completes, state updates | step 5 | `step 5`: PUT 200, toast, card has no chip | asserted |

### Axis 2 — Analyst additions
- `step 1` asserts `get_tags() == []` on the live skill before touching it
  — the case says "with no tags" but never explicitly verifies it; added
  so a future regression that pre-populates a tag on skill creation would
  fail loudly here instead of silently passing step 2.
- `step 4` re-opens via a **fresh page navigation** (not just reading the
  post-save render) — proves backend persistence of the add (step 3) and
  of the eventual removal (step 5), not just client-side state.
- `step 5` also asserts the page-header Tags filter panel drops back to
  "No tags to display" (confirmed live) as a second, independent signal
  that the tag is gone project-wide, not just off one card.

## Cleanup
1. Delete the skill via `skill_api.delete_skill(skill_id)` in a
   `try/finally` (mirrors `test_skill_pin_unpin.py`'s pattern).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Tags combobox wrapper | `LocatorDescriptor(testid="skill-tags-input")` (existing, `SkillFormPage.tags_input`) | none needed — testid resolves directly |
| Tags input (real `<input>`) | `LocatorDescriptor(testid="skill-tags-input-field")` (existing, `SkillFormPage.tags_input_field`, used by `add_tag()`) | none needed |
| Committed tag chip | `LocatorDescriptor(testid="skill-tag-chip")` (existing, `SkillFormPage.tag_chip`, shared/collection locator; `get_tags()` reads text) | none needed |
| Tag chip's delete icon | **testid needed**: `skill-tag-chip-delete-{tag_name}` (dynamic, name-keyed — `chipDeleteTestId` prop on `AutoCompleteDropDown`/`TagEditor`, wired at `CreateSkillForm.jsx`'s `<TagEditor>` call site, mirrors the existing `getOptionTestId` pattern). **Interim (pre-fix) locator**: `page.get_by_test_id("skill-tag-chip").filter(has_text=tag_name).locator("img, svg")` — scoped to the specific chip by its text, then its only child node (the delete icon); clicking the chip's label/body does NOT trigger removal (confirmed live). |
| Save button (edit flow) | `LocatorDescriptor(testid="skill-save-button")` (existing, `SkillFormPage.save_button`; `SkillDetailPage.save_edits()` already wraps click + PUT-wait + toast-assert + no-navigation-assert) | none needed |
| Skill card's tag chip (list view) | `LocatorDescriptor` via `SkillsListPage.CARD_TAG_CHIP` template + `get_card_tags(skill_name)` (existing, ELITEA-1740 rework) | none needed |
| Skill detail page load anchor | `LocatorDescriptor(testid="skill-information-section")` (existing, `wait_for_page_load()`) | none needed |

## Network Behavior
- `PUT /api/v2/elitea_core/skill/prompt_lib/{project_id}/{skill_id}` — fires
  on both saves (add-tag save and remove-tag save); returns `200`. Same
  endpoint/mechanism as any other field edit — no new endpoint for tags.
- `GET /api/v2/elitea_core/skills/prompt_lib/{project_id}?...` — the
  list-fetching endpoint; re-fires on navigating to `/skills/all` and
  reflects the current tag state in each skill's payload.
- Typing an invalid (hyphenated) tag value fires **zero** network
  calls — validation and silent-filtering are 100% client-side
  (`AutoCompleteDropDown.jsx`'s `onChangeMulti`).

## Known Defects Found During Exploration
- **[CLARIFICATION]** Case step 2's literal test data `"regression-v1"`
  can never be entered as a tag — the live Tags field rejects hyphens
  (`NormalTagNameInputRegExp` / `NormalSingleTagNameInputRegExp`, both
  `\w`-only + comma/whitespace). Confirmed live: typing it and pressing
  Enter silently drops the value (no chip, no network call). Filed as
  `EliteaAI/elitea-testing-public#1445`. Case-text drift, not a product
  defect — automation uses `regression_v1` instead (see Test Data).
- No other defects found.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page objects: `SkillDetailPage` (extends `SkillFormPage`) for the
  edit-flow interactions; `SkillsListPage` for the card-level tag
  verification. Both already exist — this case is pure reuse plus the one
  new page-object method (tag-chip delete) once the testid lands.
- Fixture: `skill_api` (session-scoped `SkillAPI` client) for setup/teardown
  — see `test_skill_pin_unpin.py` for the exact `try/finally` shape.
- The tag-chip delete-icon testid gap (`skill-tag-chip-delete-{name}`) is
  genuinely addable via `add-data-testid` (100% app-owned JSX) — not a
  `#579` stop+flag exception. Implementer should add it rather than ship
  the interim positional-child workaround, per
  `.agents/testing.md` § Locator policy ("missing testid is work to do").
