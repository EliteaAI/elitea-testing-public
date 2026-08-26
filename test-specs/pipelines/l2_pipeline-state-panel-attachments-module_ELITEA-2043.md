# Test Case: Pipeline — State Panel with Attachments Module

## Metadata
- **TMS ID**: ELITEA-2043
- **Linked Story**: none
- **Priority**: l2 (medium — as authored in the source TMS case; implementer
  should use `@pytest.mark.p2`, matching the case's authored priority)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-09
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed
  envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline is open in Flow view — satisfied via the `pipeline_id` fixture
  (fresh empty pipeline, `automation/fixtures/data_fixtures.py`) +
  `PipelineDetailPage.navigate(pipeline_id)`, which lands on Flow view by
  default (matches this session's live exploration: created pipeline id
  `8652` via the create form, landed on
  `/pipelines/all/8652?viewMode=owner` in Flow view with no extra
  navigation).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- An empty pipeline via the `pipeline_id` fixture
  (`automation/fixtures/data_fixtures.py`, `PipelineAPI`-backed create/delete).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project
  was "Private" (id 399), matching `.env.test`.

## Test Steps

1. Open a pipeline in Flow view and enable the "Attachments" toggle in the
   MODULES section of the TOOLS accordion (left panel).
   **Expected**: toggle flips to checked (`agent-canvas-tools-toggle-attachments`)
   — confirmed live, purely client-side/formik state, zero network requests,
   same mechanism ELITEA-2059 already documented for this switch (already
   wired as `PipelineDetailPage.toggle_attachments_module()` /
   `is_tools_module_toggle_checked("attachments")`). The TOOLS accordion
   renders already-expanded by default (same pattern as Welcome
   message/Advanced, ELITEA-2052/2021's note) — no extra click needed to
   reach the toggle.
2. Click the "State" button on the canvas (`pipeline-state-drawer-toggle-button`).
   **Expected**: STATE panel opens (confirmed live, already wired as
   `PipelineDetailPage.open_state_panel()`).
3. Verify the STATE panel shows three immutable variables: `input`,
   `messages`, `input_attachments`.
   **Expected — CONFIRMED live, with the SAME case-text CLARIFICATION
   already filed for this panel** (`EliteaAI/elitea-testing-public#1154`,
   from ELITEA-2042's analysis): the case's step wording ("input (str)",
   "messages (list)", `input_attachments` implied `(list)`) implies the
   panel's row visibly shows each variable's TYPE — live UI renders ONLY
   name + toggle on every row (`StateVariableItem.jsx`), no type badge at
   all. All three rows ARE present with a checked toggle immediately after
   the Attachments toggle flips (confirmed live: `input_attachments` row
   appears the instant the MODULES switch is clicked — no Save, no reload).
   Type is asserted via the YAML step (step 7) instead, where the type
   (`list`) genuinely is observable. This is the SAME already-filed
   clarification, not a new ticket — no new filing needed.
4. Verify `input_attachments` has no delete button (immutable).
   **Expected — CONFIRMED live**: `pipeline-state-variable-delete-input_attachments`
   has zero DOM matches (same structural guarantee ELITEA-2042 documented
   for `input`/`messages` — `StateVariableItemActions.jsx`'s `showToggle`
   branch is mutually exclusive with the delete-`IconButton` branch;
   `input_attachments` is rendered through the SAME auto-added/immutable
   code path, not the user-added-custom-variable path, so it gets the same
   toggle-only treatment). Already testable via
   `PipelineDetailPage.is_state_variable_delete_button_present("input_attachments")`
   (existing dynamic-testid method, no new page-object work needed).
5. Disable the "Attachments" toggle in MODULES.
   **Expected**: toggle flips to unchecked — confirmed live, same
   instant/client-side mechanism as step 1 (toggle back), zero network
   requests.
6. Verify `input_attachments` is removed from the STATE panel.
   **Expected — CONFIRMED live**: the `input_attachments` row disappears
   from the STATE panel the instant the toggle is clicked (no Save/reload
   needed); `input`/`messages` remain, back to the pre-step-1 two-row state.
7. Verify in the Yaml view that the `state:` section no longer includes
   `input_attachments`.
   **Expected — CONFIRMED live, with a live nuance beyond the case's own
   wording**: switching to Yaml view (`pipeline-yaml-view`) while
   Attachments is enabled shows (read via `get_yaml_content()`):
   ```yaml
   state:
     input:
       type: str
     input_attachments:
       type: list
       default: []
     messages:
       type: list
   ```
   After disabling Attachments (still same session, no Save/reload), the
   YAML reads:
   ```yaml
   state:
     input:
       type: str
     messages:
       type: list
   ```
   — `input_attachments` is genuinely absent, satisfying the case's
   expected result. **Nuance for the implementer**: the top-level `state:`
   key ITSELF does not revert to being fully absent once it has rendered in
   this session (contrast ELITEA-2027's digest finding that a bare pipeline
   with only the built-in `input`/`messages` vars has NO `state:` key at
   all) — enabling Attachments once causes `state:` to render (with
   `input`/`messages` types now visible too), and it stays rendered after
   disabling. This is NOT a defect (the case only requires
   `input_attachments`'s absence, which holds), but the assertion must be
   "`input_attachments` not in `state_section`", not "`state` key absent
   from the parsed YAML".

## Expected Results
- Enabling "Attachments" instantly (no Save) adds an immutable
  `input_attachments` (list) row to the STATE panel, alongside `input`/`messages`.
- `input_attachments` renders with a checked toggle and no delete button
  (same structural immutability as the built-in `input`/`messages` rows).
- Disabling "Attachments" instantly removes `input_attachments` from the
  STATE panel.
- The YAML `state:` section reflects the change in both directions:
  `input_attachments: {type: list, default: []}` present while enabled,
  absent while disabled.
- Zero console errors, zero extra network requests, at every step (module
  toggle + STATE panel + YAML view are all pure client-side formik state).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Enable "Attachments" toggle in MODULES | Attachments module is enabled | step 1 | step 1: toggle `checked` via `is_tools_module_toggle_checked("attachments")` | asserted |
| 2 Click "State" button | STATE panel opens | step 2 | step 2: panel content visible (`state_add_variable_button` visible) | asserted |
| 3 STATE panel shows input(str)/messages(list)/input_attachments(list) | all three immutable variables present | step 3 | step 3: name text for all three rows via `get_state_variable_name_text()` | asserted — **same pre-existing CLARIFICATION as ELITEA-2042 (`#1154`): the panel row does not visibly render the type text; type is asserted via YAML (step 7) instead** |
| 4 input_attachments has no delete button (immutable) | no delete control | step 4 | step 4: `is_state_variable_delete_button_present("input_attachments")` is `False` | asserted |
| 5 Disable "Attachments" toggle | Attachments module is disabled | step 5 | step 5: toggle `checked` is `False` | asserted |
| 6 input_attachments removed from STATE panel | no longer appears | step 6 | step 6: `input_attachments` row absent (name-testid count 0) | asserted |
| 7 Yaml state section does not include input_attachments | absent from YAML | step 7 | step 7: parsed YAML `state` dict has no `input_attachments` key, both while checking the enabled state (has it) and the disabled state (doesn't) | asserted |
| Expected Final State: enabling adds input_attachments, disabling removes it from panel + YAML | — | steps 3,4,6,7 | steps 3,4,6,7 | asserted |
| Pass/Fail: all steps complete without errors; input_attachments added/removed correctly | — | all steps | all steps + zero console errors | asserted |

### Axis 2 — Analyst additions

- Step 1 additionally asserts **zero network requests** fire on toggle click
  (confirmed live via network capture) — *added: this is the same
  live-formik-state mechanism ELITEA-2059 already proved for this exact
  toggle; re-confirming it here with a network assertion makes the "instant,
  no Save required" claim test-enforced rather than merely narrated.*
- Step 4 additionally asserts the delete-button absence via the SAME
  dynamic testid template ELITEA-2042 already uses for `input`/`messages`
  (`pipeline-state-variable-delete-{name}`) rather than inventing a new
  handle — *added: `input_attachments` goes through the identical
  auto-added/immutable code path as the two hardcoded default variables,
  so the existing absence-assertion method needs no change, just a new
  argument value.*
- Step 7 additionally documents that the top-level `state:` YAML key,
  once rendered by enabling Attachments, does NOT revert to fully absent
  after disabling — *added: prevents an implementer from writing a
  brittle "state key does not exist" assertion that would pass on a fresh
  pipeline but fail after any prior Attachments toggle in the same test
  session; the correct, durable assertion is "`input_attachments` key is
  absent from the `state` dict", which holds either way.*
- **Not asserted (deliberately out of this case's scope)**: Save/reload
  persistence of the Attachments toggle's effect on the STATE panel. The
  case's 7 steps are entirely live-client-state assertions (module toggle →
  panel → YAML), matching the already-confirmed instant/no-Save mechanism
  for this switch (ELITEA-2059); a future case could cover
  Save+reload persistence of `internal_tools` (and therefore
  `input_attachments`) as its own scenario, but this case's Pass/Fail
  criteria don't require it.

## Cleanup

1. This session created a persistent pipeline
   (`ELITEA-2043_attachments_state`, id `8652`) on the local DEV backend via
   the UI create form. **Not deleted at the end of this session** — same
   tooling limitation as every other analyst-session pipeline in this
   feature area (`PipelineAPI` needs a `pytest`-fixture-style
   `browser_cookies` context this Playwright-MCP session doesn't expose).
   Flagging for the implementer/lead: `8652` is safe to delete in any
   stale-pipeline cleanup sweep.
2. Implementer teardown: use the existing `pipeline_id` fixture
   (`automation/fixtures/data_fixtures.py`), which creates-and-deletes an
   empty pipeline per test via `PipelineAPI`.

## Concrete Handles (discovered during exploration)

**No new testids needed anywhere in this flow** — every handle this case
touches already exists and is already wired on `PipelineDetailPage`.

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Attachments MODULES toggle | `[data-testid="agent-canvas-tools-toggle-attachments"]` (via `TOOLS_MODULE_TOGGLE` dynamic template) | **on-`automation/testids` only** (`AgentInternalToolSwitch.jsx:108`), absent on `main` — confirmed via fresh `git fetch origin` + `git grep` both refs, per the existing ELITEA-2059 digest entry. Already wired as `PipelineDetailPage.toggle_attachments_module()` / `is_tools_module_toggle_checked("attachments")`. Confirmed live this session. | none needed |
| STATE panel toggle ("State" button) | `[data-testid="pipeline-state-drawer-toggle-button"]` | **on-`automation/testids` only** — already wired as `PipelineDetailPage.state_drawer_toggle_button` / `open_state_panel()`. Confirmed live. | none needed |
| STATE panel row name label (dynamic) | `[data-testid="pipeline-state-variable-name-{name}"]` (e.g. `-input_attachments`) | **on-`automation/testids` only** (added during ELITEA-2042 implementation, `EliteaAI/EliteaUI@d120871f`) — already wired as `PipelineDetailPage.STATE_VARIABLE_NAME` / `get_state_variable_name_text()`. Confirmed live for all three rows (`input`/`messages`/`input_attachments`) this session. | none needed |
| STATE panel row toggle switch (dynamic) | `[data-testid="pipeline-state-variable-toggle-{name}"]` | **on-`automation/testids` only** (same commit as above) — already wired as `PipelineDetailPage.STATE_VARIABLE_TOGGLE` / `is_state_variable_toggle_checked()`. Confirmed live: `input_attachments`'s toggle reads `Mui-checked` immediately after the Attachments MODULES switch is clicked. | none needed |
| STATE panel row delete button — used for its ABSENCE (dynamic) | `[data-testid="pipeline-state-variable-delete-{name}"]` | **on-`automation/testids` only** (same commit) — already wired as `PipelineDetailPage.STATE_VARIABLE_DELETE` / `is_state_variable_delete_button_present()`. Confirmed live: zero matches for `input_attachments`, same as `input`/`messages`. | none needed |
| Flow/Yaml view toggle buttons | `[data-testid="pipeline-flow-view"]` / `[data-testid="pipeline-yaml-view"]` | **on-main ✓** — already wired as `PipelineDetailPage.flow_view_button` / `.yaml_view_button` / `switch_to_yaml_view()`. Confirmed live. | none needed |
| YAML editor content | `[data-testid="pipeline-yaml-editor"]` | **on-main ✓** — already wired as `PipelineDetailPage.get_yaml_content()`. Confirmed live: `state.input_attachments` present/absent exactly as documented above. This pipeline's YAML is only 6-9 lines, well under the ~32-34-line CodeMirror truncation threshold (`#1025`) — no API-readback workaround needed. | none needed |

## Network Behavior
- **Zero network requests fire from any of the 7 steps** — confirmed live
  via a full network capture across enable-toggle → open STATE panel →
  verify rows → verify no-delete → disable-toggle → verify removal → switch
  to Yaml view. The Attachments MODULES toggle mutates only
  `version_details.meta.internal_tools` in live formik state (same
  mechanism ELITEA-2059 already documented); the STATE panel and YAML view
  both read directly from that same in-memory state, not a fresh fetch. No
  Save (`PUT .../application/prompt_lib/{project}/{id}`) is required or
  performed anywhere in this case.

## Known Defects Found During Exploration

No product defects found. This session executed all 7 steps to completion
against the live local environment with zero console errors and zero
network requests at every checkpoint, in both directions (enable then
disable), including a live YAML read-back at both states.

No NEW case-text drift/clarification needed either — the only wording gap
(STATE panel rows not visually showing type text) is the SAME clarification
already filed and tracked from ELITEA-2042's analysis
(`EliteaAI/elitea-testing-public#1154`); this case reuses that existing
ticket rather than filing a duplicate.

## Blocked Steps

None. All 7 steps were executed to completion against the live local
environment, in both directions (Attachments enabled and disabled).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **No `add-data-testid` work needed** — every handle this case touches
  (Attachments MODULES toggle, STATE panel drawer/rows, Yaml view/editor)
  was already added by prior cases (ELITEA-2059, ELITEA-2042, ELITEA-2026).
  This is a pure page-object-reuse implementation.
- **Reuse `PipelineDetailPage.toggle_attachments_module()` / `is_tools_module_toggle_checked("attachments")`**
  for steps 1 and 5 (click twice, once per direction) — no new page-object
  method needed.
- **Reuse `open_state_panel()` / `get_state_variable_name_text()` /
  `is_state_variable_toggle_checked()` / `is_state_variable_delete_button_present()`**
  for steps 2-4 and 6, passing `"input_attachments"` as the `name` argument
  — same dynamic-testid methods ELITEA-2042 already exercises for
  `input`/`messages`, no new method needed.
- **Reuse `switch_to_yaml_view()` / `get_yaml_content()` + `yaml.safe_load()`**
  for step 7, exactly as `test_pipeline_state_panel_default_and_custom_variables.py`
  (ELITEA-2042) already does — parse once while Attachments is enabled
  (assert `input_attachments` present, `type: list`), toggle off, parse
  again (assert `input_attachments` absent).
- **Assertion shape for step 7's "absence"**: assert
  `"input_attachments" not in parsed.get("state", {})`, never
  `"state" not in parsed` — the top-level `state:` key persists once
  rendered in a session (see Test Steps § step 7 nuance above); asserting
  the KEY's absence would make the test session-order-dependent instead of
  testing the actual case requirement.
- `_surface.md` updated this session with a new short digest entry cross-
  referencing this AFS's step-7 nuance (the `state:` top-level key does not
  revert to absent once rendered by an Attachments toggle) as a refinement
  to the existing ELITEA-2027 digest finding.
