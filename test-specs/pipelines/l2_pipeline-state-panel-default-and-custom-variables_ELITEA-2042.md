# Test Case: Pipeline — State Panel (Default and Custom Variables)

## Metadata
- **TMS ID**: ELITEA-2042
- **Linked Story**: none
- **Priority**: l2 (high — as authored in the source TMS case; see
  `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md` —
  implementer should use `@pytest.mark.p1`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-04
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed
  envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline is open in Flow view — satisfied via the `pipeline_id` fixture
  (fresh empty pipeline) + `PipelineDetailPage.navigate(pipeline_id)`, which
  lands on Flow view by default (matches this session's live exploration:
  created pipeline id 7522 via the create form, landed on
  `/pipelines/all/7522?viewMode=owner` in Flow view with no extra navigation).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- An empty pipeline via the `pipeline_id` fixture
  (`automation/fixtures/data_fixtures.py`, `PipelineAPI`-backed create/delete).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project
  was "Private" (id 399), matching `.env.test`.
- Custom variable name/type from the case's Test Data table: `custom_output` / `String`.

## Test Steps

1. Navigate to a pipeline in Flow view (`pipeline_id` fixture + `navigate()`).
   **Expected**: canvas is displayed (confirmed live — `rf__wrapper`/`rf__background`
   render, END node present).
2. Click the `State` button above the canvas (`pipeline-state-drawer-toggle-button`).
   **Expected**: STATE panel opens on the right side, overlapping the canvas
   (confirmed live).
3. Verify the STATE panel shows a close (X) button.
   **Expected**: `pipeline-state-drawer-close-button` visible (confirmed live).
4. Verify the two default immutable state variables are present:
   `input` and `messages`, each with its toggle switch checked, and **neither
   row renders a delete/remove control**.
   **Expected — CONFIRMED live, but with a case-text CLARIFICATION on how the
   type is exposed (see Coverage Map + Known Defects Found During
   Exploration below):** both rows show name text (`"input"` / `"messages"`)
   and a checked (`Mui-checked`) toggle switch; source-verified
   (`StateVariableItemActions.jsx`) that the `showToggle` branch renders
   **only** the toggle — the delete `IconButton` lives in the mutually
   exclusive `else` branch — so "no delete button on default rows" is a
   structural guarantee, not just a visual observation this session. The
   case's parenthetical "(str, toggle on)" / "(list, toggle on)" wording
   implies the row visibly shows the variable's TYPE — live UI does **not**
   display a type badge/icon on these collapsed rows (confirmed via full
   `outerHTML` capture: each row is exactly `<p>{name}</p>` + `<Switch>`,
   nothing else). The type is only visible via the YAML view (see step 11)
   or, for a custom variable, next to its own row's type-select icon (step 7).
5. Click the `+` button to add a new state variable
   (`pipeline-state-add-variable-button`, visible label `"Context"`).
   **Expected**: a new-variable name input appears inline in the STATE list
   (`pipeline-state-add-variable-name-input`, placeholder `"name"`). Confirmed
   live. **Automation hint**: this button's Playwright-computed accessible
   name (`"Context"`) is ambiguous per this feature's `_surface.md` digest
   (ELITEA-2033/2034 session) — use the testid, never
   `get_by_role("button", {name: "Context"})`.
6. Enter variable name `custom_output` into the name input, then commit it
   (press `Enter` — confirmed live; there is no separate confirm/checkmark
   button, per `StateVariableItem.jsx`'s `handleNameBlur`/`handleNameKeyDown`
   source).
   **Expected**: the name field is populated with `custom_output`, and on
   Enter the row transitions from create-mode (name input + a **disabled**
   type-selector icon) to display-mode, now showing `custom_output` as
   static text plus an **enabled** `"Select data type"` icon button, an
   `"Add default value (optional)"` icon button, and a delete icon button.
   Confirmed live both before AND after commit — the type-selector button is
   genuinely disabled while the row is still in create-mode
   (`StateVariableItemActions.jsx`: `disableTypeSelector={isCreateMode ||
   !editable}`), so the case's step 7 (click the type button) is only
   reachable AFTER this commit step, not before it — the case's own step
   ordering (6 then 7) already reflects this correctly.
7. Click the type button on the `custom_output` row (default icon = `Abc`
   for String) and verify the dropdown lists exactly 4 options: String
   (`Abc` icon), Number (`#`/hash icon), List, Json.
   **Expected**: dropdown (`role="menu"`) opens with `menuitem`s "String"
   (pre-selected/active), "Number", "List", "Json", in that order — confirmed
   live via `browser_snapshot`, exact match to the case. **Type-value gotcha
   (source-verified, `flowEditor.constants.js` `StateVariableTypes`):** the
   4 display labels map to internal type VALUES `str` / `number` / `list` /
   **`dict`** (not `json`) — `Json` is a display label only; a future
   extension of this test selecting "Json" must assert the persisted/YAML
   type as `dict`, not `json`.
8. Select String (case's example — "keep as String", i.e. dismiss the menu
   without changing the pre-selected option, or explicitly click the
   `"String"` menu item — both leave the type at `str`).
   **Expected**: String type retained (confirmed live: `custom_output`
   row's type-select button stayed on the `Abc` icon after clicking "String").
9. Verify the new variable `custom_output` appears in the STATE panel list.
   **Expected**: `custom_output` row visible alongside `input`/`messages`
   (confirmed live, 3 rows total).
10. Save the pipeline (`agent-save-button`).
    **Expected**: saves without errors — confirmed live: `PUT
    .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` →
    **201 Created**; zero console errors throughout steps 1–10.
11. Switch to Yaml view (`pipeline-yaml-view`) and verify the `state:`
    section.
    **Expected — confirmed live, exact match to the case**:
    ```yaml
    state:
      custom_output:
        type: str
        value: ''
      input:
        type: str
      messages:
        type: list
    ```
    (read via `pipeline-yaml-editor`'s `get_yaml_content()`; key order in the
    live YAML was `custom_output`, `input`, `messages` — assert by key
    presence/value, not by exact line order, since ordering is not a
    documented contract).
12. Verify `custom_output` is now available in a node's Input/Output
    combobox dropdowns.
    **Expected**: added an LLM node (`pipeline-add-node-button` →
    `pipeline-add-node-menu-item-llm`), opened its Input select
    (`pipeline-llm-node-input-select`) — confirmed live via DOM query:
    exactly 3 options rendered, `select-option-input`, `select-option-messages`,
    `select-option-custom_output`. Any node type with a tool-agnostic
    Input/Output select works identically (Router/Decision/HITL/Toolkit/MCP
    all share the same state-variable option source, per this feature's
    `_surface.md` digest); LLM was chosen because its Input/Output select
    testids are already confirmed present and it needs no toolkit/target-node
    setup.

## Expected Results
- STATE panel opens/closes correctly with a close button.
- Default `input` (str) and `messages` (list) variables are listed,
  each showing a checked toggle and no delete control — but note the
  panel's collapsed row does NOT visually display the type (step 4
  clarification).
- Adding `custom_output` (String) succeeds; the type-selector dropdown
  shows exactly String/Number/List/Json.
- Pipeline saves without errors (201).
- YAML `state:` section contains `input` (str), `messages` (list),
  `custom_output` (str, value `''`).
- `custom_output` is selectable in a node's Input/Output combobox.
- Zero console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline in Flow view | canvas displayed | step 1 | step 1: `rf__wrapper`/`rf__background` present | asserted |
| 2 Click "State" button | STATE panel opens | step 2 | step 2: panel content visible | asserted |
| 3 Verify close (X) button | panel visible w/ close button | step 3 | step 3: `pipeline-state-drawer-close-button` visible | asserted |
| 4 Default vars "input"(str, toggle on)/"messages"(list, toggle on), no delete | both listed, no delete | step 4 | step 4: name text + `Mui-checked` toggle + structural absence of delete `IconButton` (source-verified) | asserted — **CLARIFICATION: the collapsed row does not visibly render a type badge/text ("str"/"list") next to the name — only name + toggle. Type is observable via YAML (step 11) or the custom row's own type-select icon (step 7), not on the default rows.** |
| 5 Click "+" to add variable | new variable input appears | step 5 | step 5: name input visible | asserted |
| 6 Enter name "custom_output" | name field populated | step 6 | step 6: input value = "custom_output"; row commits on Enter | asserted |
| 7 Click type button (default "Abc"/String) → dropdown shows String/Number/List/Json | dropdown shows all 4 | step 7 | step 7: 4 `menuitem`s present, labels match exactly | asserted |
| 8 Select desired type (String) | String type selected | step 8 | step 8: type-select icon stays `Abc` | asserted |
| 9 Verify "custom_output" appears in panel list | listed | step 9 | step 9: 3rd row present | asserted |
| 10 Save pipeline | saves without errors | step 10 | step 10: 201 response, zero console errors | asserted |
| 11 Yaml view — state: section has input/messages/custom_output w/ correct types | all present | step 11 | step 11: YAML text content matches | asserted |
| 12 custom_output available in node Input/Output comboboxes | appears as option | step 12 | step 12: `select-option-custom_output` present in LLM node's Input select | asserted |
| Expected Final State: panel shows defaults + custom var; YAML reflects all; custom var in comboboxes | — | steps 4,9,11,12 | steps 4,9,11,12 | asserted |
| Pass/Fail: all steps complete without errors; custom var saved/in YAML/in comboboxes | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 4 additionally asserts, via source (`StateVariableItemActions.jsx`),
  that the absence of a delete control on default rows is **structural**
  (the `showToggle` branch is mutually exclusive with the delete-button
  branch), not merely "not observed this session" — *added: makes the
  assertion robust to a future variable-count change; the test doesn't need
  to enumerate "every default row" separately from "every non-default row",
  it can assert on the `showToggle`-driven button-count directly.*
- Step 6 additionally documents that the type-selector button is genuinely
  `disabled` during create-mode (verified both via live DOM and source) —
  *added: prevents an implementer from trying to click the type button
  before pressing Enter, which would silently no-op against a disabled
  element.*
- Step 7 additionally documents the display-label-vs-internal-value gap
  (`Json` → `dict`) — *added: this case never selects Json, but the gap is a
  live trap for any future extension of this test and is cheap to record now
  while the source is already open.*
- Step 10 additionally asserts the exact HTTP status (201 Created, observed
  live) and zero console errors — *added: consistent with every other
  pipeline-node-configuration AFS in this feature area.*
- Step 11 additionally notes the live key order (`custom_output`, `input`,
  `messages`) is NOT the case's documented order (`input`, `messages`,
  `custom_output`) — *added: the AFS instructs asserting by key
  presence/value, not line order, so the test doesn't become order-brittle
  against a future YAML-serialization change.*
- Step 12 additionally documents that ANY node type with a tool-agnostic
  Input/Output select would satisfy this step (not just LLM) — *added: gives
  the implementer a documented reason for picking the lightest-setup node
  type rather than treating "LLM" as load-bearing.*
- **Not asserted (deliberately out of this case's scope):** clicking the
  custom row's own delete button, or the "Add default value (optional)"
  affordance — the case's steps never exercise deleting/removing
  `custom_output` or setting an explicit non-empty default value. Left
  unexercised rather than invented; a future case could cover
  add/remove-custom-variable lifecycle or default-value round-tripping as
  its own scenario.

## Cleanup

1. This session created a persistent pipeline
   (`autotest_ELITEA-2042_state_panel`, id `7522`) on the local DEV backend,
   plus one LLM node added to it. **Not deleted at the end of this
   session** — same tooling limitation as every other analyst-session
   pipeline in this feature area (`PipelineAPI` needs a `pytest`-fixture-style
   `browser_cookies` context this Playwright-MCP session doesn't expose).
   Flagging for the implementer/lead: `7522` is safe to delete in any
   stale-pipeline cleanup sweep.
2. Implementer teardown: use the existing `pipeline_id` fixture
   (`automation/fixtures/data_fixtures.py`), which creates-and-deletes an
   empty pipeline per test via `PipelineAPI`; add the custom state variable
   and the LLM node inside the test via `PipelineDetailPage`/flow-editor
   methods.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| STATE panel toggle ("State" button, collapsed state) | `[data-testid="pipeline-state-drawer-toggle-button"]` | **on-`automation/testids` only** (awaiting human promotion to `main`) — confirmed via `git grep` after a fresh `git fetch origin`; already wired as `PipelineDetailPage.state_drawer_toggle_button` / used by `open_state_panel()`. Confirmed live. | none needed |
| STATE panel close ("x") button | `[data-testid="pipeline-state-drawer-close-button"]` | **on-`automation/testids` only** — already wired as `PipelineDetailPage.state_drawer_close_button` / `close_state_panel()`. Confirmed live. | none needed |
| STATE panel "+" (add variable) button | `[data-testid="pipeline-state-add-variable-button"]` (visible label `"Context"`) | **on-`automation/testids` only** — already wired as `PipelineDetailPage.state_add_variable_button`. Confirmed live. | none needed |
| STATE panel new-variable name input (create mode only) | `[data-testid="pipeline-state-add-variable-name-input"]` (placeholder `"name"`) | **on-`automation/testids` only** — already wired as `PipelineDetailPage.state_add_variable_name_input`; confirmed via source (`StateVariableItem.jsx`: `dataTestId={isCreateMode ? 'pipeline-state-add-variable-name-input' : undefined}` — same-element-conditional-pair compliant shape, PR #581/#277 rulings). Confirmed live: typed + Enter committed the row. | none needed |
| Default-variable row name label ("input"/"messages") | `testid needed: pipeline-state-variable-name-{name}` (dynamic, e.g. `pipeline-state-variable-name-input`, `pipeline-state-variable-name-messages`) | **needs-adding.** Source: `StateVariableItem.jsx`'s display-mode branch — `<Typography sx={styles.nameText}>{name}</Typography>`, no testid or accessible role currently. Confirmed live via full `outerHTML` capture (bare `<p>` tag, no attributes beyond MUI classes). | none needed |
| Default-variable row toggle switch | `testid needed: pipeline-state-variable-toggle-{name}` (dynamic); state read via the native `checked` attribute (not a `data-*` re-encoding — the testid itself is stable, `is_checked()`/`aria-checked` reads state separately, so this is compliant with the testid=stable-identity ruling) | **needs-adding.** Source: `StateVariableItemActions.jsx`'s `showToggle` branch → `Switch.BaseSwitch`, no testid prop threaded. Confirmed live: `role="switch"`, `checked` attribute present on both `input`/`messages`. | none needed |
| Default-variable row: absence of a delete control | `testid needed: pipeline-state-variable-delete-{name}` (dynamic; requested for its ABSENCE-assertion use on `input`/`messages` rows — canon ruling #511 extension, absence assertions count as references) | **needs-adding** (same testid also covers the custom-row existence case below — one template, two uses). Source-verified structural guarantee: `StateVariableItemActions.jsx`'s `showToggle` branch is mutually exclusive with the delete-`IconButton` branch. | none needed |
| Custom-variable row's "Select data type" button | `testid needed: pipeline-state-variable-type-select-{name}` (dynamic, e.g. `pipeline-state-variable-type-select-custom_output`) | **needs-adding.** Source: `StateTypeSelector.jsx` → `StateVariableIconButton` (`tooltip="Select data type"`, the accessible name/tooltip text this session used to locate it) — `StateVariableIconButton.jsx` threads no testid prop at all currently. This case's step 7 REQUIRES clicking this element. | none needed once added; interim only: `get_by_role("button", {name: "Select data type"})` scoped to the row (not testid-compliant, exploration-only) |
| Custom-variable row's delete button | `testid needed: pipeline-state-variable-delete-{name}` (same dynamic template as the default-row absence-assertion row above) | **needs-adding.** Source: `StateVariableItemActions.jsx`'s non-`showToggle` branch, plain `IconButton` with no `aria-label` and no testid at all. Confirmed live (present on `custom_output` row, absent on `input`/`messages`). | none needed |
| Type-selector dropdown menu items (String/Number/List/Json) | `testid needed: pipeline-state-type-option-{typeKey}` (static per type, e.g. `pipeline-state-type-option-str`, `-number`, `-list`, `-dict` — **use the INTERNAL value, not the display label**: `StateVariableTypes = { String: 'str', Number: 'number', List: 'list', Json: 'dict' }`, `flowEditor.constants.js`) | **needs-adding.** Source: `StateTypeSelector.jsx`'s `Menu`/`MenuItem` map over `stateTypeOptions`, no testid on any `MenuItem`. Confirmed live: exactly 4 `menuitem`s, "String"/"Number"/"List"/"Json", first pre-selected. | none needed once added; interim only: `get_by_role("menuitem", {name: "String"})` (exploration-only, not testid-compliant) |
| LLM node Input select | `[data-testid="pipeline-llm-node-input-select"]` | **on-`automation/testids` only** — already wired as `PipelineDetailPage.llm_node_input_select`. Confirmed live via DOM query on a freshly-added LLM node. | none needed |
| LLM node Input select's option (state var name) | `[data-testid="select-option-{value}"]` (e.g. `select-option-custom_output`) | **on-main ✓** — confirmed via `git grep` on `origin/main`: `SingleSelectMenuItem.jsx:117` (`data-testid={option.testId ?? `select-option-${option.value}`}`). Confirmed live: exactly `select-option-input`, `select-option-messages`, `select-option-custom_output` rendered after opening the select. | none needed |
| Add-node "+" button / LLM menu item | `[data-testid="pipeline-add-node-button"]`, `[data-testid="pipeline-add-node-menu-item-llm"]` (dynamic `pipeline-add-node-menu-item-{item.type}`, `AddNodeMenu.jsx`) | **on-`automation/testids` only** — confirmed via `git grep` (dynamic template, not a literal string — a naive literal-substring grep for `pipeline-add-node-menu-item-llm` gives a FALSE NEGATIVE; must grep the template `pipeline-add-node-menu-item-` or search the source file directly). Not on `main` (`AddNodeMenu.jsx` exists there without the testid). Already used unmodified by `PipelineDetailPage.add_node("LLM")`. | none needed |
| Flow/Yaml view toggle buttons | `[data-testid="pipeline-flow-view"]` / `[data-testid="pipeline-yaml-view"]` | **on-main ✓** — confirmed via source read: `GroupedButton.jsx` computes `data-testid={item.testid \|\| \`pipeline-${item.value}-view\`}`, a dynamic template (also a literal-substring-grep false negative — same caveat as the Add-node menu item above); the underlying `GroupedButton.jsx` file and this exact line are present on `origin/main`. Already wired as `PipelineDetailPage.flow_view_button` / `.yaml_view_button`. | none needed |
| YAML editor content | `[data-testid="pipeline-yaml-editor"]` | **on-main ✓** — confirmed via `git grep` on `origin/main`. Already wired as `PipelineDetailPage.get_yaml_content()`. Confirmed live: `state:` section read back exactly as documented in step 11. | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` | **on-main ✓** — confirmed present; already wired as `save_button` / `save_and_wait_for_update()`. Confirmed live firing `PUT .../application/prompt_lib/{project}/{pipeline_id}` → 201. | none needed |

## Network Behavior
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires
  on Save click (step 10); persists the pipeline's full YAML `instructions`
  field including the new `state.custom_output` entry. Confirmed live:
  returns **201 Created**, zero console errors.
- `GET .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` —
  fires on initial page load (step 1); not re-verified via reload in this
  session (the case does not require a reload/persistence round-trip — it
  only requires Save + immediate YAML/combobox verification, both of which
  read from in-memory client state, not a fresh fetch).

## Known Defects Found During Exploration

No product defects found. This session executed all 12 steps to completion
against the live local environment with zero console errors at every
checkpoint, including a real Save-click → 201 round-trip and a live
DOM-level verification of the type-selector dropdown, the YAML `state:`
section, and a node's Input select options.

One case-text drift was identified and is filed as a CLARIFICATION (not a
bug), per the reverse-masking guard:

- **[INFO] Case step 4's wording ("input (str, toggle on) and messages
  (list, toggle on)") implies the STATE panel's collapsed row visibly shows
  each variable's type** — live UI (confirmed both by DOM inspection and by
  reading `StateVariableItem.jsx`/`StateVariableItemActions.jsx` source)
  renders ONLY the variable's name and its toggle switch on default rows;
  there is no type badge, icon, or text anywhere on that row. The type is
  only observable via the YAML view (case step 11) or, for a non-default
  variable, via that row's own type-select icon (case step 7). The case's
  overall intent (assert `input`/`messages` are present, immutable, and
  correctly typed per the YAML) is still fully achievable — this AFS's step 4
  asserts what's actually visible (name + toggle + no-delete) and defers the
  type assertion to step 11 (YAML) where it genuinely is observable. **Filed
  as a new CLARIFICATION issue** (dedup checked against the existing
  `[Clarification]`/`[CLARIFICATION]` cluster on pipeline-node cases —
  `#1104`/`#1122`/`#1125`/`#1134`/`#1136`/`#1137`/`#1144`/`#1149` — none of
  which cover the STATE panel's row-display content, so this is a new,
  non-duplicate filing): `EliteaAI/elitea-testing-public#1154`.

## Blocked Steps

None. All 12 steps were executed to completion against the live local
environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **Testid gaps this case needs before implementation** (see Concrete
  Handles): 4 new dynamic-template testids — default/custom row name label,
  row toggle, row delete button, and the type-selector's 4 menu items — plus
  the type-select button itself. All live in the same
  `StateVariableItem.jsx` → `StateVariableItemActions.jsx` →
  `StateTypeSelector.jsx` → `StateVariableIconButton.jsx` component chain
  under `src/[fsd]/features/pipelines/flow-editor/ui/state/`. Run
  `add-data-testid` on this chain before writing the test; the four
  already-wired STATE-panel testids (drawer toggle/close, add-variable
  button/name-input) need no further work.
- **Type-value trap**: the type dropdown's 4th option displays `"Json"` but
  its internal/YAML value is `dict`, not `json` (`StateVariableTypes` in
  `flowEditor.constants.js`). Any future test selecting Json must assert
  `type: dict` in the YAML, not `type: json`.
- **Literal-substring `git grep` false negatives**: two of this AFS's
  already-existing handles (`pipeline-flow-view`/`pipeline-yaml-view`,
  `pipeline-add-node-menu-item-llm`) are constructed via JS template
  literals (`` `pipeline-${item.value}-view` ``, `` `pipeline-add-node-menu-item-${item.type}` ``)
  rather than written as literal strings — a `git grep` for the exact
  literal testid string returns NO hits even though the testid genuinely
  renders live. Confirm provenance for any templated testid by grepping the
  template PREFIX (`pipeline-add-node-menu-item-`) or reading the source
  component directly, not the fully-interpolated string.
- **Type-selector button is disabled during create-mode** — don't attempt to
  click it before the name-input row commits (Enter/blur); it's a real,
  source-verified `disabled` state, not a timing flake.
- `_surface.md` updated this session with a new "STATE panel — default vs.
  custom variable rows" section covering all of the above (testid gaps,
  type-value trap, structural no-delete-on-default guarantee, `git grep`
  template caveat).
