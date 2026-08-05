# Test Case: Create Skill from draft saves Skill and redirects to Skill details page

## Metadata
- **TMS ID**: ELITEA-1991
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/build_with_ai/ELITEA-1991_create-skill-from-draft-saves-and-redirects-to-skill-details.md`
- **Linked Story**: [EliteaAI/elitea-testing-public#139](https://github.com/EliteaAI/elitea-testing-public/issues/139)
- **Priority**: l2 (case priority: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV
  backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`). `.agents/profile.md`
  does not explicitly guarantee `${TEST_USER}` carries admin/editor role, but this run — same as the sibling
  ELITEA-1990 AFS — confirmed live that "Build with AI" renders and the full create flow completes without any
  permission gate under this credential on localhost. If a deployed-env run ever uses a lower-privilege account,
  re-verify this precondition there.
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: extend-existing
- **Case-gate note**: source case frontmatter carries `status: draft` / `execution_type: manual`.
  `.agents/testing.md` has no `TMS case-gate` section defining excluded statuses for this project (same
  recurring gap the ELITEA-1915/ELITEA-2001/ELITEA-1990 AFS lineage already flagged) — per the skill's default,
  this run proceeded and fetched/executed the case.

## Relationship to the existing suite (Rule-6 partial overlap → extend-existing)

`automation/tests/ui/skills/test_skill_build_with_ai.py::TestSkillBuildWithAIReviewFormEditableFields::
test_review_form_fields_are_editable_before_creation` (covering ELITEA-1990, spec
`test-specs/skills/l2_generated-skill-draft-fields-are-editable-before-creation_ELITEA-1990.md`) already
exercises almost the identical flow this case needs:

- opens the modal, fills the prompt, generates a (mocked) draft
- **asserts the review form is pre-populated with the generated Name/Description/Instructions** (its own
  Step 2 assertions, `modal.get_review_name() == GENERATED_DRAFT_PAYLOAD["name"]` etc.) — this is exactly
  ELITEA-1991's Step 2 ("review the generated values without modifying them ... all generated values are
  visible and correct")
- clicks "Create Skill" and asserts `201 Created`
- asserts redirect to `/skills/all/{id}` and that the detail page's Name/Description/Instructions match —
  **but only after the test has overwritten all three fields with edited values**. The existing test's whole
  point is proving the *edited* values win, not the *unmodified* ones.

**What's covered already:** modal-open → prompt → generate → review-form pre-population-matches-draft →
Create Skill → 201 → redirect → detail-page field assertions. All of that machinery (page object, mock
helper, redirect/URL-regex handling, `SkillAPI.delete_skill` cleanup) is proven and reusable.

**What's missing (the gap this AFS targets):**
1. A path where the review form fields are **never touched** before clicking "Create Skill" — i.e. an
   assertion that clicking Create Skill *without any edit* persists the **generated** values verbatim
   (case Steps 3-6). ELITEA-1990's test always edits first; no existing test exercises the through-line of
   generate → approve-unmodified → verify-generated-values-on-detail-page.
2. **Skills list appearance** (case Step 7: "Navigate to the Skills list and verify the new Skill appears
   there"). No existing skill Build-with-AI test asserts the created skill is visible/listed on
   `/skills/all` after creation — ELITEA-1990's test redirects to the detail page and stops there, then
   cleans up via API without ever revisiting the list.

Because the overlap is large (same modal, same generate call, same create-and-redirect flow) but the two
gaps above are cleanly identifiable and additive, this is **`extend-existing`**, not a fresh
`ready-for-automation` spec — a near-duplicate `.spec.ts` reproducing the whole flow again would defeat
Rule-6 dedup. The implementer should add ONE new test method to
`TestSkillBuildWithAIReviewFormEditableFields` (or a peer class in the same file) that: generates a draft,
**skips the edit steps entirely**, clicks Create Skill directly, asserts the detail page holds the
generated (not edited) values, then navigates to `/skills/all` and asserts the new skill's name is present
in the list.

## Preconditions
- User is logged in to Elitea (localhost `auth_state`/`VITE_DEV_TOKEN`) with a role sufficient to create
  skills — confirmed live in this run (see Metadata note).
- A project is selected/accessible (`Private`, id `399` in this run).
- (Per the same case-text-drift pattern already documented for ELITEA-1990/ELITEA-2001: "a skill draft has
  been generated" is stated as a precondition in the case, but is actually produced by this AFS's own Steps
  1-2 — not an independent setup requirement. See Coverage Map disposition.)

## Test Data

### reuse-existing
None — no dependency on any pre-existing environment fixture beyond project selection (`Private`, id 399),
already covered under § Preconditions.

### generate-per-test
All created live by this run and deleted in Cleanup — nothing shared or left behind:
- Natural-language prompt used to generate the draft (this run):
  `"Create a skill that reviews changelog entries and rewrites them in a consistent, user-facing tone."`
  — any valid non-empty prompt satisfies the case.
- Live-generated draft (real DEV backend, unmocked — confirmed live in this exploration):
  - Name: `changelog-editor`
  - Description: `Reviews and rewrites changelog entries in a consistent, user-facing tone. Transforms
    technical commits and internal notes into clear, benefit-focused updates that help users understand
    what changed and why it matters.`
  - Instructions: full markdown-formatted instructions text (opens with `# Changelog Editor`), ~1650
    characters (`846 characters left` of the 2500-char instructions budget on the detail page after
    creation) — content itself isn't asserted by the case, only that it's non-empty and matches between
    draft and created skill.
- The resulting created Skill (id `674`, version id `696` in this run) is generate-per-test data, deleted
  via the UI delete-menu flow as part of Cleanup.

### generate-shared-with-cleanup
None.

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. In the "General" accordion section, click **"Build with AI"**
   (`generate-skill-open-button`) to open `GenerateSkillModal`. Fill the prompt textarea
   (`generate-skill-prompt-input`) with the test-data prompt.
   - **Verify**: Generate button (`generate-skill-submit-button`) is disabled while the prompt textarea is
     empty, becomes enabled once filled — confirmed live via snapshot before/after fill.

2. Click **Generate** and wait for the real (unmocked) DEV backend to return a draft (network: `POST
   /api/v2/elitea_core/generate_skill_draft/prompt_lib/399 => [200]`, confirmed live in this run,
   ~30s generation time observed).
   - **Verify**: the modal transitions to the review-form step, showing non-empty generated
     Name/Description/Instructions and the **"Back to prompt"** / **"Create Skill"** action buttons
     (`generate-skill-back-button` / `generate-skill-approve-button`) — matches the case's Step 1 expected
     result exactly.

3. Review the generated Name, Description, and Instructions **without modifying any of them**.
   - **Verify**: all three fields display the exact draft values from Step 2, unchanged — confirmed live
     via accessibility snapshot immediately after generation, before any interaction with the form fields.
     (This is the gap ELITEA-1990's existing test does not cover — its equivalent snapshot is taken, then
     the fields are immediately overwritten.)

4. Click **"Create Skill"** (`generate-skill-approve-button`) with no edits made.
   - **Verify**: network shows `POST /api/v2/elitea_core/skills/prompt_lib/399 => [201] Created` (confirmed
     live) with zero console errors/warnings during the create call (confirmed via
     `browser_console_messages`, level=warning, 0 results).

5. Observe the resulting navigation.
   - **Verify**: the browser is redirected to `/skills/all/{new_skill_id}` (confirmed live:
     `/skills/all/674`) — the Skill details page, satisfying the case's Step 5.

6. Verify the Skill details page shows the correct Name, Description, and Instructions.
   - **Verify**: the detail page's General section shows **Name** = `changelog-editor`, **Description** =
     the generated description verbatim, and the **Instructions** editor content opening with `# Changelog
     Editor` matching the generated draft's instructions verbatim (confirmed live via full accessibility
     snapshot of the detail page's `Name *`, `Description *`, and Instructions editor immediately after
     redirect) — satisfying the case's Step 6, and directly proving the "unmodified" through-line (contrast
     with ELITEA-1990, which proves the opposite: edited values win). Skill ID `674` / Version ID `696`
     also visible in the page's "Information" section, matching the redirect URL.

7. Navigate to the Skills list (`Skills` nav item → `/skills/all`) and verify the new Skill appears there.
   - **Verify**: `changelog-editor` is present in the Skills card-list view (confirmed live —
     newest-created skill sorts first in the list) — satisfying the case's Step 7. This is the second gap
     ELITEA-1990's existing test does not cover (that test never revisits the list after creation).

## Expected Results

Matches the case's stated Pass criteria exactly, live-verified end-to-end in this run: reviewing the
generated draft without modification, clicking "Create Skill" creates the skill with the **generated**
values (not edited — this case's defining contrast with ELITEA-1990), the user is redirected to the new
skill's details page showing those values correctly, and the new skill appears in the Skills list. No step
produced an unexpected result; zero console errors/warnings across the whole flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "A skill draft has been generated via the Build with AI modal" | draft exists | steps 1-2 | step 2: review form populated after a real (unmocked) generate call | clarification *(case-text drift — the case states this as setup, live it's the outcome of Steps 1-2; same pattern already documented in the ELITEA-1990/ELITEA-2001 AFS lineage, not filed separately — see Known Defects)* |
| 1 Generate a skill draft via Build with AI modal | review/edit form displayed with generated values | steps 1-2 | step 2: review form step reached, all three fields non-empty | asserted |
| 2 Review generated Name/Description/Instructions without modifying | all generated values visible and correct | step 3 | step 3: snapshot shows unmodified draft values immediately after generation | asserted |
| 3 Click "Create Skill" | skill creation initiated | step 4 | step 4: `POST .../skills/prompt_lib/399 => 201` | asserted |
| 4 Verify the Skill is created in the current project | Skill saved to current project | step 4 | step 4: 201 response scoped to project 399's endpoint; skill later found in that project's Skills list (step 7) | asserted |
| 5 Verify redirect to the Skill details page | Skill details page of new Skill displayed | step 5 | step 5: URL `/skills/all/674` confirmed | asserted |
| 6 Verify Skill details page shows correct Name/Description/Instructions from the draft | values match generated draft | step 6 | step 6: detail-page snapshot values compared against Step 2's generated draft values | asserted |
| 7 Navigate to Skills list, verify new Skill appears | new Skill listed on Skills list page | step 7 | step 7: `changelog-editor` present in `/skills/all` card list | asserted |

### Axis 2 — Analyst additions

- step 4 documents zero console errors/warnings during the create call as an explicit guard — *added:
  silent errors are the worst bugs; the case doesn't mention console health but it's free to check and
  worth guarding.*
- step 6 explicitly contrasts this case's "generated values persist unmodified" assertion against
  ELITEA-1990's "edited values override generated ones" assertion — *added: makes the two specs'
  non-overlapping purpose explicit for future readers, since both touch the same modal and same detail
  page.*
- Metadata/Relationship section documents the exact Rule-6 partial-overlap reasoning (which steps are
  already proven vs. which two are the gap) — *added: this is the AFS's core deliverable for an
  `extend-existing` classification, not itself a case requirement, but required by the skill's own
  contract for this status.*

## Cleanup
1. The skill created during this exploration (id `674`, "changelog-editor") was deleted live via the UI
   overflow-menu delete flow (`skill-controls-menu-button` → `skill-delete-menu-item` → type-to-confirm
   dialog with the skill's name → `Delete`), confirmed by redirect back to `/skills/all` and the Skills
   count decrementing from 16 to 15 in the "Test Bot" tag summary.
2. For automated runs: use the existing `SkillAPI.delete_skill(skill_id)` helper (`automation/api/
   client.py:1350`, cookie-based auth) in a fixture/teardown — same pattern already used by
   `test_review_form_fields_are_editable_before_creation` in the covering test file. Do not use a raw
   `fetch()` from page JS context (documented as CORS-failing in the ELITEA-1990 AFS's Known Defects).

## Concrete Handles (discovered during exploration)

All handles below are pre-existing (confirmed live, no new testids required by this case — unlike
ELITEA-1990, which added the three `generate-skill-review-*-input` fields):

| Element | Recommended Locator | Fallback |
|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` (pre-existing, confirmed live) | n/a — testid-only policy |
| Prompt textarea | `generate-skill-prompt-input` (pre-existing) | n/a |
| Generate button | `generate-skill-submit-button` (pre-existing) | n/a |
| Review-form Name/Description/Instructions fields | `generate-skill-review-name-input` /
  `generate-skill-review-description-input` / `generate-skill-review-instructions-input` (added by
  ELITEA-1990, already on `GenerateSkillModalPage` — reuse `modal.get_review_name()` /
  `get_review_description()` / `get_review_instructions()`, this case never calls the corresponding
  `set_review_*` setters) | n/a |
| "Create Skill" button | `generate-skill-approve-button` (pre-existing) | n/a |
| Skill detail page Name field | `skill-name-input-field` (pre-existing, per `skill_detail_page.py`) —
  confirmed live post-redirect shows the generated (unmodified) value | n/a |
| Skill detail page Description field | `skill-description-input-field` (pre-existing) — confirmed live | n/a |
| Skill detail page Instructions editor | `skill-instructions-editor-content` (pre-existing) — confirmed live | n/a |
| Skills list card item (for Step 7's "appears in list" assertion) | `SkillsListPage` — existing page
  object; this run confirmed the created skill's name text (`changelog-editor`) renders as a card-list
  item title in `/skills/all` — recommend the implementer add a `find_skill_by_name(name) -> Locator` /
  `is_skill_listed(name) -> bool` helper on `SkillsListPage` if one doesn't already exist, since no
  existing test in this suite currently asserts list-membership by name (see Automation Hints) | n/a |
| Skill delete flow (cleanup) | `skill-controls-menu-button` → `skill-delete-menu-item` →
  `Dialog.type_to_confirm` + `Delete` (all pre-existing, per `skill_detail_page.py:delete_skill_via_menu`) | n/a |

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/399` — draft generation, `200`, real backend
  (unmocked), ~30s.
- `POST /api/v2/elitea_core/skills/prompt_lib/399` — skill creation on approval, `201 Created`, confirmed
  live. Payload (from `GenerateSkillModal.jsx handleApprove`): `{name, description, versions: [{name:
  "base", instructions}]}` — same shape documented in the ELITEA-1990 AFS, no `temperature`/
  `reasoning_effort` fields (bug #524 does not apply here, same non-relationship already established for
  ELITEA-1990).
- `GET /api/v2/elitea_core/skill/prompt_lib/399/{id}` — detail-page load after redirect, `200`.
- No console errors or warnings observed at any point during the case's own steps (1-7). One 404 was
  observed AFTER deletion (cleanup, not a case step) — see Known Defects #2.

## Known Defects Found During Exploration

1. **Case-text drift (CLARIFICATION, not a product defect).** Same pattern already documented for
   ELITEA-1990/ELITEA-2001/ELITEA-1915: the case's Preconditions line ("A skill draft has been generated
   via the Build with AI modal") describes the outcome of this AFS's own Steps 1-2, not an independent
   setup requirement. Not filed as a GitHub issue — a case-authoring precision gap, not a live product
   defect.

2. **[Non-blocking, informational — not filed] Stale-component refetch 404 after skill deletion.** After
   deleting skill 674 via the UI delete flow (redirect back to `/skills/all` succeeded correctly), one
   console error appeared: `GET /api/v2/elitea_core/skill/prompt_lib/399/674 => 404` — some
   already-unmounting/stale component appears to fire one more fetch for the just-deleted skill id during
   the redirect. This occurs entirely **after** the case's own Step 7 assertion has already passed and is
   **outside the case's step scope** (cleanup-only artifact, not part of ELITEA-1991's Pass/Fail criteria).
   Not filed — low severity, does not affect the create/redirect/list-appearance flow the case actually
   tests, and matches the general shape of transient stale-fetch races already noted informally elsewhere
   in this suite's memory. Flagged here for visibility only; the implementer should not assert on this
   404 either way (soft-ignore, not `# Known defect:` since no ticket exists).

No functional product defect was found. The live product's behavior across all 7 case steps matches the
case's Pass criteria exactly, in this live run.

## Blocked Steps
None. All 7 case steps were executed end-to-end live in this run, unmocked against the real DEV backend,
producing a fully successful outcome (skill 674, "changelog-editor", created with generated values intact,
redirected correctly, and visible in the Skills list before cleanup).

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home:
  `automation/tests/ui/skills/test_skill_build_with_ai.py` (existing file — **extend**
  `TestSkillBuildWithAIReviewFormEditableFields`, or add a sibling test method in the same class, rather
  than a new file/class — the modal-open/generate/redirect scaffolding is identical to
  `test_review_form_fields_are_editable_before_creation`; only skip that test's edit steps (3-5) and add
  the list-appearance check after its Step 7).
- Reuse `GenerateSkillModalPage.mock_generate_success(...)` to mock the draft response for determinism
  (this AFS's live exploration used a real, unmocked call to validate the full happy path once — same
  dual-run rationale already established in the ELITEA-1990 AFS). Reuse `modal.get_review_name()` /
  `get_review_description()` / `get_review_instructions()` to capture the pre-edit values for the
  "unmodified through creation" assertion — do **not** call the `set_review_*` setters at all in this test.
- New page-object surface needed: a `SkillsListPage` helper to assert list-membership by name (e.g.
  `is_skill_listed(name: str) -> bool` or `find_skill_card(name: str)`), since no existing test in this
  suite currently exercises this assertion — check `automation/pages/skills_list_page.py` first in case a
  suitable method already exists under a different name before adding one.
- Cleanup: use `SkillAPI.delete_skill(skill_id)` (cookie-auth, existing helper, `automation/api/
  client.py:1350`) in a `try/finally` or pytest fixture teardown, same pattern as the covering test —
  get `skill_id` from the URL after redirect (`page.url` regex `/skills/all/(\d+)$`).
- Assertion for Step 6 (generated values persist unmodified) should compare against the actual generated
  draft values captured earlier in the same test (via the review-form fields' values immediately after
  generation, before any interaction), not hardcoded constants — robust to LLM output variance if an
  un-mocked variant is kept, trivial if the draft is mocked.
