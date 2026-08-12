# Test Case: Create Pipeline — Minimal

## Metadata
- **TMS ID**: ELITEA-2020
- **Linked Story**: none
- **Priority**: high (case) / l2 (AFS prefix)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst/Implementer**: test-automation-engineer (Axel), combined slot, batch `elitea-2020-create-pipeline-minimal`
- **Status**: extend-existing

## Extension target

**Covering spec**: `automation/tests/ui/pipelines/test_pipeline_management.py`,
class `TestCreatePipeline` (lines 108–173), merged to `origin/automation/base`
(commit `23c8035a`).

**Behavioural overlap (what's already proven).** `test_create_pipeline_via_ui`
(lines 114–153) already covers:
- Navigate to the create form via `PipelineFormPage.navigate_to_create()`
  (direct URL nav, NOT the sidebar "+" control).
- Fill Name + Description, verify Save enabled, click Save.
- Verify URL becomes `/pipelines/all/{id}` (numeric id present) and detail
  page shows the correct Name.
- Cleanup via API.

**Gap ELITEA-2020 actually asks for (3 elements the covering test does not
assert)**:
1. **Navigation via the sidebar "+" control**, not a direct URL nav (case
   Step 2: "Click the '+' button next to 'Pipeline' label in the sidebar
   header area").
2. **"Pipeline ID:" in the Information section** — the covering test only
   checks the URL and the Name field; it never opens/reads the Information
   accordion (case Step 8).
3. **VERSION dropdown defaults to "base"** — not asserted anywhere in the
   covering spec (case Step 9).

None of these three exist as assertions anywhere else in
`test_pipeline_management.py` (confirmed by reading the full file,
`TestCreatePipeline`/`TestEditPipeline`/`TestPipelineIsolation` classes).

## Preconditions
- User is logged in (`auth_state` on localhost).
- Project `Private` (id `${ELITEA_PROJECT_ID}`) has Pipelines feature access
  (satisfied — pre-existing pipelines visible in the dashboard).

## Test Data

### generate-per-test (created live by the test, cleaned up via API)
- Pipeline name: `autotest_create_pipeline_minimal_<short-suffix>` (case's
  literal `AutoTest_Pipeline` is not reused verbatim — the suite convention,
  confirmed across every sibling `TestCreatePipeline`/`TestSearchPipeline`
  test, is an `autotest_`-prefixed unique name per run so parallel/repeat
  runs don't collide; the case's literal name is not itself an observable
  the case asserts).
- Description: `Automated test pipeline` (verbatim from case Test Data — used
  as-is, not itself asserted beyond "field accepts and displays it", which
  the covering test already proves via `get_description()`-equivalent
  behavior; this AFS does not re-assert description content, only that
  filling it is a precondition for Save to enable, per live-confirmed
  behavior below).

## Test Steps

1. Navigate to `/pipelines/all` (`PipelinesListPage.navigate()`).
   - **Verify**: dashboard loads (`page_header` visible) — precondition, not
     a case step of its own (case Step 1 folds into this).
2. Click the sidebar "+" control (`sidebar-create-button`, confirmed live to
   render as a "Pipeline"-labeled button while the current route is the
   Pipelines dashboard — see Concrete Handles).
   - **Verify**: URL becomes `/pipelines/create?viewMode=owner`, an empty
     "New Pipeline" form tab is shown (case Step 2).
3. Fill Name field with the generated pipeline name.
   - **Verify**: Name field holds the typed value (case Step 3).
4. Fill Description field with `Automated test pipeline`.
   - **Verify**: Description field holds the typed value (case Step 4).
5. Verify Save button is enabled once both Name and Description are filled
   (case Step 5 — case text says "after Name is filled", but by the time
   Step 5 runs in the case's own sequence, Step 4/Description has already
   run too; live-confirmed the button stays DISABLED with Name alone and
   only enables once Description is also present — see Known Defects /
   case-text note below).
6. Click Save.
   - **Verify**: no error; save request completes (case Step 6).
7. Verify the URL changes to `/pipelines/all/{numeric-id}...` (case Step 7).
8. Open/read the Information section and verify "Pipeline ID:" is present
   with a numeric value equal to the id parsed from the URL (case Step 8).
9. Verify the VERSION selector's displayed text is exactly `base` (case
   Step 9).

## Expected Results
- Sidebar "+" navigates directly to the minimal create form
  (`/pipelines/create?viewMode=owner`), confirmed live to be
  `sidebar-create-button`'s target when the user is on the Pipelines
  dashboard (`CreateEntityButton.jsx`'s `currentLabel`/`isSimpleCreateRoute`
  logic resolves the current route to the "Pipeline" label and renders a
  direct-navigate button, not a dropdown).
- Save requires BOTH Name and Description non-empty (see Known Defects/
  case-text note) — matches `test_create_pipeline_required_fields_validation`
  in the covering spec (Save stays disabled with Name-only).
- After Save: URL is `/pipelines/all/{id}?destTab=configuration&name=...`
  with a numeric `{id}` (confirmed live: id `8056` for the probe run).
- Information section (`agent-information-section`, pre-existing shared
  testid, already confirmed on-main per `_surface.md`) shows "Pipeline ID:"
  next to the `copy-id` button, whose text content IS the numeric id
  (confirmed live, matches `PipelineDetailPage.get_pipeline_id()`, already
  implemented and unmodified).
- VERSION selector shows the visible text `base` for a freshly created
  pipeline (confirmed live via the `agent-version-selector-trigger` testid's
  `textContent` — **corrected 2026-08-07, review fix round 1, then
  round 1's "fabricated" verdict itself corrected 2026-08-07, review fix
  round 2**: the originally-recorded `agent-version-selector-trigger-combobox`
  testid is REAL (`SingleSelect.jsx:661`'s `SelectDisplayProps` template
  literal), just not yet promoted to `main` (present on
  `automation/testids` only) and unreachable by a literal-string grep
  because it's template-constructed at render time. The page-object choice
  of the no-suffix testid is correct regardless — see Concrete Handles table
  below for the full trace).
- No console errors observed across the whole create→save→verify flow.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Pipelines via sidebar "Pipelines" button | Pipelines section loads | step 1 | step 1: dashboard header visible | asserted |
| 2 Click "+" next to "Pipeline" label in sidebar header | New pipeline tab opens, empty form | step 2 | step 2: URL == `/pipelines/create?viewMode=owner`, form tab visible | asserted |
| 3 Fill Name = "AutoTest_Pipeline" | Name field populated | step 3 | step 3: `get_name()` equals filled value | asserted |
| 4 Fill Description = "Automated test pipeline" | Description field populated | step 4 | step 4: `get_description()` equals filled value | asserted |
| 5 Verify Save enabled after Name filled | Save active/enabled | step 5 | step 5: `is_save_enabled()` True (both fields present, live-confirmed precondition — see case-text note) | asserted |
| 6 Click Save | Save request submitted | step 6 | step 6: no exception, network settles | asserted |
| 7 Verify URL includes numeric pipeline ID | URL updates | step 7 | step 7: URL path matches `/pipelines/all/<digits>` | asserted |
| 8 Verify "Pipeline ID:" in Information section, numeric | Pipeline ID displayed | step 8 | step 8: `get_pipeline_id()` is a non-empty digit string, equals the URL id | asserted |
| 9 Verify VERSION dropdown shows "base" | VERSION defaults to "base" | step 9 | step 9: version selector text == "base" | asserted |

**Axis 2 — Analyst/implementer additions**

- Cross-check the Information-section Pipeline ID against the URL id (not
  just "is numeric") — *added: a numeric-but-wrong id would pass a weaker
  "is digit" check; comparing to the URL's own id closes that gap for free
  since both are already being read.*
- Cleanup via API (`pipeline_api.delete_pipeline`) — *added: matches every
  sibling test in this file; the case text has no explicit cleanup step but
  the suite convention leaves no test data behind.*

## Cleanup
1. `pipeline_api.delete_pipeline(int(pipeline_id))` in a `finally` block,
   matching `test_create_pipeline_via_ui`'s existing pattern (lines 147–153
   of the covering file).

## Concrete Handles (discovered during exploration, all confirmed live)

Locator policy for this project is **testid-only** — see
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy.

| Element | Testid | LocatorDescriptor | Provenance |
|---|---|---|---|
| Sidebar "+" create control | `sidebar-create-button` | **not yet a field on `PipelinesListPage`** — implementer adds `sidebar_create_button = LocatorDescriptor(testid="sidebar-create-button")`, mirrors the identical field already on `AgentsListPage`/`ToolkitsListPage`/`CredentialsListPage`/`ChatPage` | on-main ✓ (`CreateEntityButton.jsx`, confirmed live: clicking it while on `/pipelines/all` navigates to `/pipelines/create?viewMode=owner`) |
| Name input | `agent-name-input` | `PipelineFormPage.name_input` (existing) | on-main ✓ (pre-existing, `_surface.md` § Confirmed testids) |
| Description input | `agent-description-input` | `PipelineFormPage.description_input` (existing) | on-main ✓ |
| Save button | `agent-save-button` | `PipelineFormPage.save_button` (existing) | on-main ✓ |
| Information section (accordion root) | `agent-information-section` | **not yet a field on `PipelineDetailPage`** — implementer adds `information_section = LocatorDescriptor(testid="agent-information-section")` | on-main ✓ (`_surface.md` § Confirmed testids; confirmed live this session via DOM query) |
| Pipeline ID (copy button, text content = the id) | `copy-id` | `PipelineDetailPage.copy_id_button` + `get_pipeline_id()` (existing, unmodified) | on-main ✓ |
| VERSION selector (shows "base") | `agent-version-selector-trigger` | **not yet a field on `PipelineDetailPage`** — implementer adds `version_selector = LocatorDescriptor(testid="agent-version-selector-trigger")` + a `get_version_display() -> str` getter | on-main ✓ (`ApplicationVersionSelect.jsx:228`, `testId="agent-version-selector-trigger"` prop → `VersionSelect.jsx:176`/`SingleSelect.jsx` applies `data-testid={dataTestId}` on the `SingleSelect` root AND, via `SelectDisplayProps`, a second `data-testid="agent-version-selector-trigger-combobox"` on the nested MUI-internal `role="combobox"` display div — same shared entity-tab-bar component `AgentDetailPage.version_selector_trigger` also reads. **Corrected 2026-08-07, review fix round 1, then re-corrected round 2**: round 1 called the `-combobox` variant "does not exist" from a zero-hit literal-string grep; that grep can't find a template-constructed string (`` `${dataTestId}-combobox` ``, `SingleSelect.jsx:661`) and the variant IS real — but ref-specific: **`needs-adding to main` / on `automation/testids` only** (0 hits on `main`, 1 hit on `automation/testids` for `git grep -- "-combobox" -- src/`, re-verified with a fresh `git fetch origin` on both). The page object still correctly uses the no-suffix `agent-version-selector-trigger`, on-main ✓ on both refs, unrelated to the `-combobox` variant's existence.) |

No `add-data-testid` work needed — every handle this AFS touches already
exists on `main`. This case is a pure page-object wiring + new-test gap, not
a testid gap.

## Network Behavior
- Save on create: `POST .../applications/prompt_lib/{project_id}` → 2xx
  (existing `save_and_wait_for_creation()` helper already encodes this same
  endpoint for the create path; not re-derived here).
- No network call specific to reading the Information section or VERSION
  selector — both are already-present DOM state from the create response,
  no extra XHR to wait on beyond the Save response itself.

## Known Defects Found During Exploration
- **None.** Flow behaves exactly as observed live: sidebar "+" → minimal
  form → Save → detail page with correct URL, Information section, and
  VERSION.
- **Case-text looseness (not a defect, not filed)**: the case Objective says
  "created with only the required Name field", but Test Data + Steps 3–4
  fill both Name AND Description, and live-confirmed behavior is that Save
  stays disabled with Name alone (matches the covering spec's own
  `test_create_pipeline_required_fields_validation`, which already asserts
  this). Step 5 is compatible with this reality only because Step 4 (fill
  Description) has already run by the time Step 5 checks Save — so the case
  is internally consistent in practice despite the misleading Objective
  wording. Not worth a separate clarification ticket: the steps themselves
  are unambiguous and this AFS's step 5 asserts exactly what the live
  product does.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, matches covering spec).
- Extend `TestCreatePipeline` in
  `automation/tests/ui/pipelines/test_pipeline_management.py` with a new test
  method, e.g. `test_create_pipeline_minimal_via_sidebar_button` — additive
  only, existing `test_create_pipeline_via_ui` /
  `test_create_pipeline_required_fields_validation` bodies stay untouched.
- Add `PipelinesListPage.sidebar_create_button` + a
  `click_create_pipeline()` method mirroring
  `ToolkitsListPage.click_create_toolkit()` (same shared
  `sidebar-create-button` testid, same click→`wait_for_url()` pattern).
- Add `PipelineDetailPage.information_section` + `version_selector` +
  `get_version_display()`.
- Reuse `PipelineDetailPage.get_pipeline_id()` unmodified for step 8.
- Tag with `@allure.issue(...ELITEA-2020...)` per the file's existing
  convention (see the other tests in this class); keep `@pytest.mark.p0`
  since this is the base creation flow's minimal-fields path (parallel
  priority to `test_create_pipeline_via_ui`, which is also `p0`+`smoke`).
