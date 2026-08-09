# Test Case: Pipeline — State Panel Delete Custom Variable

## Metadata
- **TMS ID**: ELITEA-2044
- **Priority**: l2 (medium, as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-09
- **Status**: extend-existing

## Covering Spec (dedup / extension proof)

- **Covering spec**: `automation/tests/ui/pipelines/test_pipeline_state_panel_default_and_custom_variables.py`
  (TMS ELITEA-2042), merged to `origin/automation/base` (`2837fe92`).
- **Behavioural overlap**: ELITEA-2042's merged test already builds the exact precondition this
  case needs — a fresh pipeline, STATE panel opened, a custom variable `custom_output` added via
  the panel's `+` control (name input → Enter commit) — and already proves the default rows
  `input`/`messages` render NO delete control (its own step 4, source-verified structural
  guarantee on `StateVariableItemActions.jsx`'s `showToggle` branch).
- **The gap**: ELITEA-2042's own AFS explicitly scopes this OUT — *"Not asserted (deliberately out
  of this case's scope): clicking the custom row's own delete button ... Left unexercised rather
  than invented; a future case could cover add/remove-custom-variable lifecycle ... as its own
  scenario."* ELITEA-2044 is exactly that future case: click the custom row's delete (trash)
  button, verify the row disappears, verify the default rows still have no delete control (a
  repeat check, cheap given step 4 already establishes it structurally), save, and verify the
  YAML `state:` section no longer contains the deleted variable.
- **Extension shape**: add a **new test function** to the same file
  (`test_pipeline_state_panel_default_and_custom_variables.py`), reusing the `pipeline_id`
  fixture, `PipelineDetailPage.add_state_variable()` / `open_state_panel()` /
  `close_state_panel()` / `save_and_wait_for_update()` / `switch_to_yaml_view()` /
  `get_yaml_content()` — all already proven working by ELITEA-2042 — plus ONE new page-object
  method (`click_state_variable_delete`, additive) to click the delete button, since ELITEA-2042
  never needed to click it (only assert its absence on default rows). Does not modify ELITEA-2042's
  existing test body.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: Keycloak via `${TEST_USER}`).
- A pipeline is open in Flow view with a custom state variable added — satisfied in-test via the
  `pipeline_id` fixture (fresh empty pipeline) + `add_state_variable("custom_output")`, identical
  setup to ELITEA-2042's own steps 1–6.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- An empty pipeline via the `pipeline_id` fixture (`PipelineAPI`-backed create/delete).
- A custom variable `custom_output` (String, default type), added in-test via
  `add_state_variable()` — same value as the case's Test Data table and as ELITEA-2042's own.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`).

## Test Steps

1. Navigate to the pipeline (`pipeline_id` fixture + `navigate()`), open the STATE panel
   (`open_state_panel()`), and add a custom variable `custom_output` via `add_state_variable()`.
   **Verify**: `custom_output` row appears in the STATE panel (same assertion shape ELITEA-2042
   already uses) — confirmed live this session on a real pipeline (id 8652): the row renders name
   text, a "Select data type" button, an "Add default value (optional)" button, and a delete
   (trash) `IconButton` with no `aria-label`.
2. Locate the trash icon (delete) button next to `custom_output`.
   **Verify**: `[data-testid="pipeline-state-variable-delete-custom_output"]` is present —
   confirmed live this session; the testid already exists (added during ELITEA-2042's
   `add-data-testid` work, `EliteaAI/EliteaUI@d120871f`), so this case needs NO new testid.
3. Click the trash icon.
   **Verify**: `custom_output`'s row (its `pipeline-state-variable-name-custom_output` element)
   is removed from the panel — confirmed live this session: the click is a purely client-side
   state removal (zero network requests fired, zero console errors) with NO confirmation dialog —
   the row disappears instantly on click, unlike other delete flows in this app (pipeline/version
   delete) which show a type-to-confirm modal.
4. Verify the default variables `input` and `messages` still render NO delete/remove control.
   **Verify**: `[data-testid="pipeline-state-variable-delete-input"]` and
   `-delete-messages"]` both absent — confirmed live this session (repeat of ELITEA-2042 step 4's
   structural guarantee; cheap to re-check here since the row set just changed).
5. Save the pipeline (`agent-save-button` / `save_and_wait_for_update()`).
   **Verify**: saves without errors — confirmed live this session: `PUT
   .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` → **201 Created**, zero console
   errors.
6. Switch to Yaml view and verify the `state:` section no longer includes `custom_output`.
   **Verify — confirmed live, exact match to the case**: post-delete-and-save YAML is
   ```yaml
   state:
     input:
       type: str
     messages:
       type: list
   ```
   (read via `get_yaml_content()`; no `custom_output` key present at all — assert by key
   ABSENCE, i.e. `"custom_output" not in state_section`, not by counting keys, since other
   MODULES-driven state vars like `input_attachments` (ELITEA-2043) are orthogonal and must not
   make this assertion brittle).

## Expected Results
- Clicking the trash icon next to a custom state variable removes it from the STATE panel
  immediately, with no confirmation dialog and no network call (the removal is purely local
  editor state until Save).
- Default variables `input`/`messages` continue to render no delete control after a custom
  variable is added and removed alongside them.
- Saving persists the removal — the YAML `state:` section omits the deleted variable entirely
  after Save.
- Zero console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline with a custom state variable ("custom_output") | Pipeline open with "custom_output" in state | step 1 | step 1: row present after `add_state_variable()` | asserted |
| 2 Click "State" button | STATE panel opens | step 1 | step 1: `open_state_panel()` + add-variable button visible | asserted |
| 3 Locate the trash icon (delete) button next to "custom_output" | Trash icon visible | step 2 | step 2: `pipeline-state-variable-delete-custom_output` present | asserted |
| 4 Click trash icon — verify variable is removed from panel | "custom_output" removed from panel | step 3 | step 3: name testid absent post-click | asserted |
| 5 Verify default "input"/"messages" do NOT have delete buttons | no trash/delete buttons on defaults | step 4 | step 4: both delete testids absent | asserted |
| 6 Save pipeline — verify removal persists in YAML | YAML state section excludes "custom_output" after save | steps 5–6 | step 5: 201 + zero console errors; step 6: YAML key absent | asserted |
| Expected Final State: "custom_output" permanently deleted from panel + YAML; defaults remain with no delete option | — | steps 3,4,6 | steps 3,4,6 | asserted |
| Pass/Fail: all steps complete without errors; custom var deleted from panel/YAML; defaults show no delete buttons | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 1 additionally documents the row's full control set (name, type-select, add-default-value,
  delete) confirmed live — *added: gives the implementer the complete precondition shape rather
  than just "a row exists", consistent with ELITEA-2042's own step-6 documentation.*
- Step 3 additionally documents that the delete is a **client-side-only, no-confirm-dialog**
  action (zero network requests, zero console errors) — *added: this differs from every other
  delete flow in the pipelines feature area (pipeline delete, version delete both show a
  type-to-confirm `DeleteEntityModal`), which is a trap for an implementer who might otherwise
  wait for a confirm dialog that never appears.*
- Step 6 additionally specifies asserting by **key absence**, not by counting `state:` keys —
  *added: `input_attachments` (ELITEA-2043's MODULES-driven state var) is an orthogonal source of
  extra `state:` keys; a count-based assertion would be brittle against unrelated MODULES state,
  while a presence/absence check on `custom_output` specifically is not.*
- **Not asserted (deliberately out of this case's scope, consistent with ELITEA-2042's own
  Axis-2 scoping):** the "Add default value (optional)" affordance, and the effect of deleting a
  custom variable that is currently SELECTED as a node's Input/Output (a downstream-usage
  interaction the case's own steps never set up or exercise). Left unexercised rather than
  invented; a future case could cover that interaction as its own scenario.

## Cleanup
1. This session reused the pre-existing `ELITEA-2043_attachments_state` pipeline (id `8652`,
   left over from a prior analyst session, flagged in that session's AFS as safe-to-delete-later)
   for live exploration — added `custom_output`, deleted it, saved. Net effect: the pipeline's
   persisted state is unchanged from before this session (still just `input`/`messages`) — no new
   residue left behind.
2. Implementer teardown: use the existing `pipeline_id` fixture
   (`automation/fixtures/data_fixtures.py`) — creates-and-deletes an empty pipeline per test via
   `PipelineAPI`; the custom variable lives inside the pipeline's own JSON, no separate cleanup.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| STATE panel toggle / add-variable button / name input / close | `pipeline-state-drawer-toggle-button` / `pipeline-state-add-variable-button` / `pipeline-state-add-variable-name-input` / `pipeline-state-drawer-close-button` | pre-existing, confirmed live this session; already wired via `open_state_panel()` / `add_state_variable()` / `close_state_panel()` | none needed |
| Custom-variable row's delete (trash) button | `[data-testid="pipeline-state-variable-delete-{name}"]` (dynamic template, e.g. `pipeline-state-variable-delete-custom_output`) | **already exists** — added during ELITEA-2042's `add-data-testid` work (`EliteaAI/EliteaUI@d120871f`); page object already has the template constant `STATE_VARIABLE_DELETE` and the absence-checking method `is_state_variable_delete_button_present`. Confirmed live this session: present on the `custom_output` row, absent on `input`/`messages`. **No new testid needed** — only a new page-object CLICK method (`click_state_variable_delete`) is needed, since the existing method only checks presence/absence. | none needed |
| Custom-variable row's name label (for absence-after-delete check) | `[data-testid="pipeline-state-variable-name-{name}"]` | pre-existing (ELITEA-2042); already wired as `is_state_variable_present()` (absence-assertion method, added for ELITEA-2043) and `get_state_variable_name_text()` | none needed |
| Default-row delete-button absence check | `[data-testid="pipeline-state-variable-delete-{name}"]` on `input`/`messages` | pre-existing; already wired as `is_state_variable_delete_button_present()` | none needed |
| Flow/Yaml view toggle + editor | `pipeline-yaml-view` / `pipeline-yaml-editor` | pre-existing, confirmed live; already wired as `switch_to_yaml_view()` / `get_yaml_content()` | none needed |
| Pipeline Save button | `agent-save-button` | pre-existing; already wired as `save_and_wait_for_update()`. Confirmed live this session firing `PUT .../application/prompt_lib/{project}/{pipeline_id}` → 201. | none needed |

No new testids are needed for this extension — every element it touches already carries one from
ELITEA-2042's prior `add-data-testid` work.

## Network Behavior
- Clicking the delete (trash) button on a custom variable row fires **zero** network requests —
  confirmed live this session: the removal is purely client-side editor state until Save.
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on Save click
  (step 5); persists the updated `state:` YAML with the deleted variable omitted. Confirmed live:
  returns **201 Created**, zero console errors.

## Known Defects Found During Exploration

No product defects found. This session executed all 6 case steps to completion against the live
local environment (pipeline id 8652), with zero console errors at every checkpoint, including a
real delete-click → Save → 201 → YAML round-trip confirming the variable's persistent removal.

No case-text drift identified — the case's wording matches live behavior exactly (trash icon
present, click removes it, defaults have no delete buttons, YAML omits the deleted variable after
save).

## Blocked Steps

None. All 6 steps were executed to completion against the live local environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **No new testids needed** — this case's only gap vs. the existing page object is a CLICK method
  for the delete button (`STATE_VARIABLE_DELETE` template already exists, used so far only for
  presence/absence checks via `is_state_variable_delete_button_present`). Add
  `click_state_variable_delete(name, timeout)` to `PipelineDetailPage`, reusing the existing
  `STATE_VARIABLE_DELETE` class constant — do not add a second constant for the same testid
  pattern.
- **No confirmation dialog** — unlike pipeline/version delete (which show a `DeleteEntityModal`
  type-to-confirm dialog), the STATE panel row's delete button removes the row immediately on
  click. Don't wait for a dialog that never appears.
- **Assert YAML by key absence**, not by counting `state:` keys — other MODULES-driven state vars
  (e.g. `input_attachments`, ELITEA-2043) are an orthogonal source of extra keys.
- `_surface.md` updated this session with a short note under the existing STATE-panel section
  confirming the delete-button testid's pre-existence and the no-confirm-dialog behavior.
