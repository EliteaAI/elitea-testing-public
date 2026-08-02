# Test Case: Create Pipeline — Full Details Persist After Save and Reload

## Metadata
- **TMS ID**: ELITEA-2021
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-02
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A toolkit exists in the project to attach (implementer: use the `github_toolkit` fixture —
  `automation/fixtures/data_fixtures.py:243` — which provisions credential + toolkit together;
  it `pytest.skip`s cleanly when `GIT_HUB_TOKEN` is unset, per `.agents/profile.md` § Roles &
  sample users. Do not hardcode a name from the shared dev project's ~30 leaked
  `AutoTest * Toolkit *` rows — they are unrelated leaked test data, not a fixture).

## Test Data

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — implicit via "Private" project context.

### generate-per-test (in test setup, cleaned up in its own teardown)
- Pipeline name: `autotest_pipeline_full_details_<unique>` (the `autotest_` prefix
  matches `cleanup_autotest_pipelines_at_end` — `automation/fixtures/cleanup_fixtures.py:43`
  — for defense-in-depth cleanup on deployed envs; on localhost that fixture no-ops, so the
  test's own teardown via `pipeline_api.delete_pipeline()` — the pattern in
  `test_create_pipeline_via_ui`, `automation/tests/ui/pipelines/test_pipeline_management.py:145`
  — is what actually cleans up).
- Description: `Pipeline with all fields populated`
- Tag: `automation`
- Welcome message: `Welcome to the pipeline`
- Chat starter: `Run analysis`
- Step limit: `50`
- Editor notes: `Test pipeline for automation`
- Toolkit: from the `github_toolkit` fixture (its generated display name).

## Test Steps

1. Navigate to `${BASE_URL}/pipelines/all?viewMode=owner` via the sidebar "Pipelines" link.
   - **Verify**: Pipelines dashboard loads (`pipelines-page-header` — reuse `PipelinesListPage`).
2. Click the sidebar "+ Pipeline" create button (`sidebar-create-button`).
   - **Verify**: navigates to `/pipelines/create?viewMode=owner`; the create form loads
     (`PipelineFormPage.wait_for_page_load`).
3. Fill Name: `autotest_pipeline_full_details_<unique>` (`agent-name-input`).
   - **Verify**: field shows the typed value.
4. Fill Description: `Pipeline with all fields populated` (`agent-description-input`).
   - **Verify**: field shows the typed value.
5. Add tag `automation` in the Tags combobox (`#tags` — **testid needed**, see § Concrete
   Handles) — type the text, then press Enter (placeholder literally reads "Type a tag
   and press comma/enter").
   - **Verify**: a chip labeled `automation` renders in the Tags field.
6. Fill Welcome message: `Welcome to the pipeline` (`agent-welcome-message-input`).
   - **Verify**: field shows the typed value. (Confirmed present on the **create** form,
     not gated behind an initial save — see Coverage Map note on step ordering.)
7. Click "+ Starter" (`agent-conversation-starter-add`), then fill the new starter input
   with `Run analysis` (`agent-conversation-starter-input`, first instance).
   - **Verify**: starter textarea shows `Run analysis`.
8. Expand "ADVANCED" (`agent-canvas-section-advanced` — already expanded by default,
   `aria-expanded="true"` on load) and set Step limit to `50` (numeric input, **testid
   needed**, see § Concrete Handles). Default value on a fresh pipeline is `25`.
   - **Verify**: field shows `50`.
9. Click Save (`agent-save-button`).
   - **Verify**: `POST` to the pipeline-create endpoint returns 2xx; page navigates to
     `/pipelines/all/{id}?destTab=configuration&name=...&viewMode=owner`
     (`PipelineDetailPage.wait_for_detail_page_load`). No console errors.
10. On the detail page's Configuration side panel (`pipeline-config-tab`), locate the
    "TOOLS" section (`agent-toolkits-section`) and click "+ Toolkit"
    (`agent-add-toolkit-button` — **exists in the DOM already; not yet a
    `LocatorDescriptor` field on `PipelineDetailPage`, see § Automation Hints**).
    In the opened popper, click the row for the fixture-provisioned toolkit
    (`toolkit-menu-item`, matched by its visible text — see § Concrete Handles for why
    exact-text `has_text` matching needs a render-settle wait, not why it's unreliable).
    - **Verify**: an `agent-toolkit-card` appears in the TOOLS section showing the
      toolkit's name.
11. Scroll to "EDITOR NOTES" in the same side panel and fill the Notes textarea with
    `Test pipeline for automation` (**testid needed on both the accordion header and the
    textarea**, see § Concrete Handles).
    - **Verify**: field shows the typed value.
12. Click Save again (`agent-save-button`) to persist the toolkit attach + editor notes
    added post-creation.
    - **Verify**: `POST`/`PUT` returns 2xx. No console errors.
13. Reload the page (`page.goto` the same `/pipelines/all/{id}?destTab=configuration&viewMode=owner`
    URL, or `page.reload()`) and re-read every field.
    - **Verify**: Name, Description, Tag chip `automation`, attached toolkit card,
      Welcome message, Chat starter `Run analysis`, Step limit `50`, and Editor Notes
      `Test pipeline for automation` are ALL present with their saved values.

## Expected Results
- All 13 steps complete without a UI error, a failed network request, or a console error.
- Every field the case names persists across the reload with its exact saved value —
  confirmed live in this session end-to-end (see Coverage Map / Known Defects — none found).

## Coverage Map

**Axis 1 — Case coverage.**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: existing toolkit available | toolkit selectable in step 6/10 | Test Data → `github_toolkit` fixture | fixture setup | asserted |
| 1 Navigate to Pipelines via sidebar | Pipelines section loads | step 1 | step 1: header visible | asserted |
| 2 Click "+" to create pipeline | New pipeline tab opens | step 2 | step 2: URL + form load | asserted |
| 3 Fill Name | Name populated | step 3 | step 3: field value | asserted |
| 4 Fill Description | Description populated | step 4 | step 4: field value | asserted |
| 5 Add tag "automation" | tag added | step 5 | step 5: chip visible | asserted |
| 6 Click "+ Toolkit", attach existing toolkit | Toolkit appears in Tools section | step 10 | step 10: `agent-toolkit-card` visible | asserted *(reordered — see note below)* |
| 7 Fill Welcome message | Welcome message populated | step 6 | step 6: field value | asserted *(reordered)* |
| 8 Add Chat starter "Run analysis" | Chat starter added | step 7 | step 7: field value | asserted *(reordered)* |
| 9 Set Step limit to "50" | Step limit shows "50" | step 8 | step 8: field value | asserted *(reordered)* |
| 10 Add Editor Notes | Editor notes populated | step 11 | step 11: field value | asserted *(reordered — see note)* |
| 11 Click Save | Pipeline saves without errors | steps 9, 12 | steps 9/12: 2xx + navigation, no console errors | asserted *(decomposed into two saves — see note)* |
| 12 Reload and verify all fields persist | all fields restored | step 13 | step 13: every field re-read | asserted |
| Expected Final State: all fields persist after save+reload | — | step 13 | step 13 | asserted |

**Reordering / decomposition note (case-text drift, live-product-driven — not a defect):**
the case lists the Tools-attach (step 6) and Editor Notes (step 10) actions interleaved
with fields that are available on the bare `/pipelines/create` form (name, description,
tag, welcome message, chat starter, step limit). Live exploration (this session) confirmed
the **Tools section and Editor Notes accordion do not render at all on `/pipelines/create`**
— they belong to `PipelineConfigurationForm.jsx`, which is only mounted on the **detail**
page (`/pipelines/all/{id}`) via `GeneralFormPanel`/`ConfigurationTab`. A pipeline must
already have an id (i.e. have been saved once) before a toolkit can be attached or notes
added — `ToolMenu.jsx`'s add-toolkit affordance is gated on `!isEntityUnsaved`. So the case
implicitly requires **two Save actions** (create, then attach+notes+save-again), which its
own step list doesn't spell out. This is the live product's actual, correct save/unlock
flow, not a bug — filed as a CLARIFICATION on the TMS case text (see § Known Defects) per
the reverse-masking guard. The AFS steps above reflect the real, verified order; nothing
in the case's *expected results* is contradicted — only the step *sequencing needed to
reach them*.

**Axis 2 — Analyst additions.**
- Step 9 asserts "no console errors" after the first save — *added: standard side-channel
  check per skill discipline, not explicitly requested by the case.*
- Step 12 asserts a 2xx response for the second save (toolkit attach + editor notes) —
  *added: the case only asserts the reload outcome; asserting the save call itself
  narrows a reload-only failure down to which of the two saves broke it.*
- Step 10 asserts the attached toolkit card shows the exact provisioned toolkit's name
  (not just "a card exists") — *added: makes step 13's persistence check meaningfully
  tied to step 10's action rather than any pre-existing card.*

## Cleanup
1. Delete the pipeline via API teardown: `pipeline_api.delete_pipeline(pipeline_id)`
   (pattern: `test_create_pipeline_via_ui`, `automation/tests/ui/pipelines/test_pipeline_management.py:145`).
2. `github_toolkit` fixture owns its own credential + toolkit teardown.

## Concrete Handles (discovered during exploration)

Live-verified via a scratch Playwright script against `http://localhost:5173`
(`.venv` python, no MCP browser available this session — see § Automation Hints).
Provenance checked fresh (`cd ../EliteaUI && git fetch origin`, 2026-08-02) for every
EXISTING testid below; all 14 are already on `main` (not just `automation/testids`).

| Element | Locator (testid) | Provenance | Notes |
|---|---|---|---|
| Pipeline name input | `agent-name-input` | on-main ✓ | Already a `LocatorDescriptor` field: `PipelineFormPage.name_input`. |
| Pipeline description input | `agent-description-input` | on-main ✓ | Already a field: `PipelineFormPage.description_input`. |
| **Tags input** | testid needed: `pipeline-tags-input` | needs-adding | MUI Autocomplete, `id="tags"`, placeholder `"Type a tag and press comma/enter"`. No `data-testid` on the Autocomplete root or the rendered `MuiChip` tag. Add the testid to the Autocomplete root (`ApplicationEditForm.jsx` or wherever `#tags` is defined) so both the input and the chip are reachable via `.locator()` scoped underneath it. |
| **Tag chip (rendered tag)** | testid needed: scope `[data-testid="pipeline-tags-input"] .MuiChip-root` or a dedicated chip testid | needs-adding | Verify text `automation` inside; no dynamic-per-value testid is required since the case only ever has one tag. |
| Welcome message textarea | `agent-welcome-message-input` | on-main ✓ | Exists in DOM (shared `AgentInput.WelcomeMessageInput` component) but **no `LocatorDescriptor` field yet on `PipelineFormPage`/`PipelineDetailPage`** — add one (mirrors `AgentFormPage.welcome_message_input`). |
| "+ Starter" button | `agent-conversation-starter-add` | on-main ✓ | Same as above: exists in DOM, add as a field on `PipelineDetailPage` (mirrors `AgentFormPage.conversation_starter_add_button`). |
| Chat starter textarea | `agent-conversation-starter-input` | on-main ✓ | Same: add field (mirrors `AgentFormPage.conversation_starter_inputs`). Multiple starters render one each; index `[0]` for this case. |
| ADVANCED accordion header | `agent-canvas-section-advanced` | on-main ✓ | Already expanded by default (`aria-expanded="true"`); do not click it going in — only click to toggle if a prior step collapsed it. |
| **Step limit input** | testid needed: `pipeline-step-limit-input` | needs-adding | `ApplicationAdvanceSettings.jsx`. Current DOM id is React-generated (`:r1t:`-style) — unstable across renders/entities. `input[inputmode="numeric"][max="999"]` is a usable scoped fallback ONLY until the testid lands (min=0, max=999, default value `"25"`). |
| Save button | `agent-save-button` | on-main ✓ | Already a field: `PipelineFormPage.save_button`. Used for BOTH the initial create-save and the later attach+notes save. |
| Pipeline detail config panel | `pipeline-config-tab` | on-main ✓ | Container `ContentContainer` in `GeneralFormPanel.jsx`. Already used implicitly via `PipelineDetailPage`; no field currently named for it — add one if the implementer wants to scope queries inside it. |
| TOOLS section container | `agent-toolkits-section` | on-main ✓ | Already a field: `PipelineDetailPage.toolkits_section`. |
| **"+ Toolkit" button** | testid needed as a page-object field: `agent-add-toolkit-button` | on-main ✓ (DOM), needs-adding (page object) | Testid EXISTS in the DOM (`ToolMenu.jsx:576`) and is on `main` already — only the `LocatorDescriptor` field is missing from `PipelineDetailPage` (which currently only has `add_mcp_button` for the sibling "+ MCP" button). Add `add_toolkit_button = LocatorDescriptor(testid="agent-add-toolkit-button", ...)`. |
| Toolkit search input (inside popper) | `toolkit-search-input` | on-main ✓ | Already a class constant: `PipelineDetailPage.TOOLKIT_SEARCH_INPUT_SELECTOR`. **Caveat**: typing into it did NOT visibly filter the listbox in this session's live probe (14 items before and after typing a full toolkit name) — see § Known Defects for the CLARIFICATION filed. Automation should NOT rely on search narrowing the list; select by exact visible text among the (unfiltered) rendered rows instead. |
| Toolkit listbox row | `toolkit-menu-item` | on-main ✓ | Already a class constant: `PipelineDetailPage.TOOLKIT_MENU_ITEM_SELECTOR`. Select via `page.locator(TOOLKIT_MENU_ITEM_SELECTOR, has_text=toolkit_name).first.click()` — `has_text` filtering worked reliably at click time in this session even when `.count()` immediately after opening the popper under-reported (render-settle race; add a short `wait_for` on the popper's item count stabilizing, not a hardcoded sleep). |
| Attached toolkit card | `agent-toolkit-card` | on-main ✓ | Already a field: `PipelineDetailPage.toolkit_card`. Verified: shows the toolkit's display name; a pre-existing `has_toolkit_warning_message()` method on the page object already covers the "Your configuration does not match..." warning banner that can appear on some toolkit cards (observed on this session's GitHub toolkit, unrelated to this case — a known/expected state, not a new defect). |
| **EDITOR NOTES accordion header** | testid needed: `pipeline-editor-notes-section` | needs-adding | `ApplicationEditorNotes.jsx` — the `BasicAccordion` `items` array doesn't pass a `testId` for this item (unlike `ApplicationTools.jsx`, which does). Add `testId: 'pipeline-editor-notes-section'` to the accordion item object. |
| **Editor Notes textarea** | testid needed: `pipeline-editor-notes-input` | needs-adding | `Input.StyledInputEnhancer` inside `ApplicationEditorNotes.jsx` — no `data-testid` prop is forwarded to the underlying textarea. Add one (the component already accepts a `fieldName` prop used only for the fullscreen-dialog title; a separate `data-testid` needs wiring). Current fallback scope: label text `"Notes"` → nearest ancestor `.MuiFormControl-root` → `textarea` (brittle; only until the testid lands). |

## Network Behavior
- `POST` to the pipeline/application create endpoint (`/api/v2/elitea_core/application/prompt_lib/{project_id}` family — confirm exact path via `elitea-platform` skill or by observing the request in this test) fires on the FIRST Save (step 9) — expect 2xx, capture the returned id for navigation/cleanup.
- A second `POST`/`PUT` fires on the SECOND Save (step 12, after toolkit attach + editor notes) — expect 2xx. In this session's probe it hit `POST /api/v2/elitea_core/applications/prompt_lib/399` → `201`.
- No WebSocket traffic is relevant to this case (no chat interaction is asserted).

## Known Defects Found During Exploration
- None found. Full flow (create → attach toolkit → fill editor notes → save → reload)
  executed cleanly end-to-end in this session with every field verified restored after
  reload (`FullDetailsPipe_probe2`, pipeline id `6754`, see session artifacts).
- **CLARIFICATION (case-text drift, not a product defect)** — the case's step ordering
  (Toolkit attach at step 6, before Welcome message/Chat starter/Step limit at steps
  7–9) does not match the live product: Tools-section attach and Editor Notes are ONLY
  available on the pipeline **detail** page (after an initial Save creates the entity),
  never on the `/pipelines/create` form. The case also never mentions the implied SECOND
  Save this requires. Recommend the TMS case text be updated to reflect the two-phase
  save; not filed as a tracker issue per `.agents/profile.md` § Bug filing (this is a
  case-text note, not a defect) — flagged here for the case author, per the
  reverse-masking guard in `test-case-analysis` SKILL.md § Classify findings.
- **Observation, not filed**: typing into the toolkit-picker's search input
  (`toolkit-search-input`) did not visibly narrow the 14-row listbox in this session's
  probe (same items before/after typing a full, unique toolkit name). Not escalated to
  a defect because (a) it doesn't block this case — exact-text selection among the
  unfiltered rows works reliably — and (b) it wasn't isolated to a pristine repro per
  the interaction-discovery ladder in `.agents/role-overrides.md` (only tried once,
  headless, no manual UI cross-check). Recorded here so a future MCP-node or
  toolkit-search-focused case picks it up as a starting hypothesis rather than
  re-discovering it from zero.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, confirmed (`.agents/testing.md`).
- Page objects: extend `PipelineFormPage` (`automation/pages/pipeline_form_page.py`) with
  a `tags_input` field, and `PipelineDetailPage` (`automation/pages/pipeline_detail_page.py`,
  which subclasses `PipelineFormPage`) with `welcome_message_input`,
  `conversation_starter_add_button`, `conversation_starter_inputs`, `step_limit_input`,
  `add_toolkit_button`, `editor_notes_section`, `editor_notes_input` — do not duplicate
  `AgentFormPage`'s fields; add pipeline-specific ones directly since `PipelineDetailPage`
  does not inherit from `AgentFormPage` (they're siblings sharing a UI component, not a
  class hierarchy — same testid values, separate `LocatorDescriptor` fields per project
  convention observed in the existing file, e.g. `PipelineFormPage.name_input` duplicating
  `AgentFormPage.name_input`'s testid rather than importing it).
- No Playwright MCP server was reachable in this analysis session (deferred-tool search
  returned no `browser_*`/playwright tools); exploration used a standalone `.venv`
  Playwright script driving `http://localhost:5173` directly (headless chromium, plain
  `sync_playwright()`, no `auth_state` fixture needed since `config.py`'s existing
  localhost bypass applies to a bare context too — confirmed, no login screen appeared).
  The implementer's actual test should still go through the standard `page`/`context`
  pytest fixtures — this was exploration-only, not a fixture substitute.
- Wait strategy: after the FIRST Save, wait for `page.wait_for_load_state("networkidle")`
  before touching the Tools/Editor-Notes sections — they aren't mounted until the detail
  page's `PipelineConfigurationForm` finishes loading (confirmed: absent from the DOM
  immediately post-navigate, present ~1s later in this session's probe).
- The exploration's throwaway pipelines (`FullDetailsPipe_probe`, id 6753 — has a
  duplicate-toolkit artifact from a mid-probe double-click, and `FullDetailsPipe_probe2`,
  id 6754 — clean) were left in the shared local dev DB; this session's cleanup fixture
  (`cleanup_autotest_pipelines_at_end`) does not match their names (no `autotest_` prefix)
  and is also localhost-skipped. Harmless to other suites (name-pattern searches won't
  match "FullDetailsPipe_probe*"), but the implementer's own fixture should use the
  `autotest_` prefix + `pipeline_api.delete_pipeline()` teardown per this AFS's Cleanup
  section, not leave anything behind.
