# Test Case: Pipeline — State Modifier Node Configuration

## Metadata
- **TMS ID**: ELITEA-2035
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-08
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- **CLARIFICATION on the case's stated precondition** ("A pipeline with state
  variables exists"): live-confirmed this undersells the actual setup
  required — the state variables `issue_details` (Input) and
  `normalized_issue` (Output) are **not** built-in (only `input`/`messages`
  are) and must be created via the flow editor's own `STATE` side panel's
  "+" control before the State modifier node's Input/Output combos will
  list them — same pattern already documented for the Decision/Code node
  AFSes (ELITEA-2034/ELITEA-2009). This AFS makes that setup an explicit
  step 0.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- An empty pipeline via the `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`,
  `PipelineAPI`-backed create/delete).
- Two custom state variables added via the flow editor's `STATE` panel:
  `issue_details` (Input), `normalized_issue` (Output) — matches the case's
  own Test Data table exactly.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — verify the active browser project
  matches before creating test data via `PipelineAPI` directly (same
  project-mismatch gotcha documented in the Router/Decision AFSes).

## Test Steps

**IMPORTANT — step 0 added ahead of the case's step 1.** The case's
precondition text implies the state variables already exist; live behavior
requires explicit setup to produce them (see Coverage Map).

0. **Setup**: create a pipeline; add two custom state variables
   (`issue_details`, `normalized_issue`) via the `STATE` panel's "+" control
   (`open_state_panel()` → `add_state_variable("issue_details")` →
   `add_state_variable("normalized_issue")` → `close_state_panel()`).
   - **Verify**: the `STATE` panel lists `issue_details` and
     `normalized_issue` alongside the built-in `input`/`messages`
     (`get_state_variable_name_text()`).
1. Create a pipeline and add a State modifier node via "Add node" →
   "State modifier" (`add_node("State modifier")`).
   - **Verify**: node appears on canvas — `wait_for_node_on_canvas("state_modifier")`
     returns a non-empty id (`StateModifier 1`); node count increased by 1.
2. Observe the State modifier node's config (renders **inline on the card
   itself — no click-to-open action needed**, same always-expanded shape as
   every other pipeline node type in this codebase — matches the digest's
   already-confirmed generic finding).
   - **Verify**: sections visible top to bottom, all inline (confirmed via
     source, `StateModifierNode.jsx`): `Jinja Template` (a plain multiline
     textarea, NOT a rich/code editor despite `language="jinja"`-style props
     elsewhere in this node family), `Variables to clean` (a tool-agnostic
     multi-select combobox — see step 4's clarification), `Input` (same
     kind of select), `Output` (same kind of select). All four sections
     present — matches the case's step 2 expectation on SECTION PRESENCE
     exactly; no case-text drift there.
3. In "Jinja Template" field enter: `## GitHub Issue\n\n{{ issue_details }}`.
   - **Verify**: the textarea's value equals the entered string
     (`get_state_modifier_node_template() == value`, read via
     `.input_value()` — same reasoning as the Router/Decision/Code AFSes'
     Jinja/Description/Value fields, not a CodeMirror/Monaco editor).
4. "Expand" the "Variables to clean" section.
   - **Verify**: — **CLARIFICATION, not asserted as written.** Live-confirmed
     (source: `StateModifierNode.jsx` renders `<FlowEditorSelect.InputSelect
     label="Variables to clean" inputFieldName="variables_to_clean" .../>`,
     the SAME component as Input/Output) and via live DOM inspection: there
     is **no accordion/expand affordance** anywhere on this field — it is a
     plain multi-select combobox identical in shape to Input/Output, always
     fully visible, nothing to "expand". The case's step 4 describes a
     mechanism that does not exist. This AFS instead asserts the field is
     present and openable as a dropdown (`open_state_modifier_node_variables_to_clean_select()`
     — a click that opens the options popper), which is the closest live
     equivalent to the case's intent. Not a defect — filed as a
     CLARIFICATION (case-text drift), see Known Defects Found During
     Exploration below.
5. Set Input combobox — add variable "issue_details".
   - **Verify**: `select_state_modifier_node_input_variable("issue_details")`
     → `get_state_modifier_node_input_value() == "issue_details"`.
6. Set Output combobox — add variable "normalized_issue".
   - **Verify**: `select_state_modifier_node_output_variable("normalized_issue")`
     → `get_state_modifier_node_output_value() == "normalized_issue"`.
7. Save pipeline (`agent-save-button`).
   - **Verify**: no console errors; `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}`
     returns a 2xx (observed live: 201 Created, same as every other
     pipeline-node-configuration AFS in this suite).
8. Reload — verify Jinja Template text, Input, and Output persist.
   - **Verify**: after reload (real `page.reload()`/navigation, not just an
     API read), `get_state_modifier_node_template()`,
     `get_state_modifier_node_input_value()`, and
     `get_state_modifier_node_output_value()` all read back the same values
     set in steps 3/5/6.

## Expected Results
- State modifier node config renders fully inline on the canvas card (no
  modal/panel to open) — Jinja Template, Variables to clean, Input, Output
  all present.
- `Variables to clean` is a plain tool-agnostic multi-select combobox
  (`FlowEditorSelect.InputSelect`, same shape as Input), NOT an
  expandable/accordion section as the case text implies.
- Jinja Template, Input, and Output values independently persist through
  Save + a real page reload.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipeline with state variables exists | setup exists | Preconditions clarification + step 0 | step 0: STATE panel lists both custom vars | asserted — **CLARIFICATION: the custom state variables `issue_details`/`normalized_issue` don't exist by default; explicit setup is needed, same pattern as sibling node-configuration cases.** |
| 1 Create pipeline, add State modifier node via "Add node" → "State modifier" | State modifier node appears on canvas | step 1 | step 1: node count + id | asserted |
| 2 Verify State modifier node panel shows Jinja Template/Variables to clean/Input/Output | all listed sections present | step 2 | step 2: all 4 sections visible | asserted — no case-text drift on SECTION PRESENCE; live UI matches exactly (always inline, matches every other node type in this codebase) |
| 3 In "Jinja Template" field enter the template string | field accepts the value | step 3 | step 3: `.input_value()` equals entered string | asserted |
| 4 Expand "Variables to clean" section (if applicable) | section expands as expected | step 4 | step 4: field present + openable as a dropdown | asserted — **CLARIFICATION: "expand" reads as an accordion affordance; live behavior is a plain multi-select combobox identical in shape to Input/Output, nothing to expand. Case's "(if applicable)" qualifier already hints this may not apply — confirmed it doesn't.** |
| 5 Set Input combobox — add variable "issue_details" | "issue_details" is added to Input | step 5 | step 5: selected-chip display text | asserted |
| 6 Set Output combobox — add variable "normalized_issue" | "normalized_issue" is added to Output | step 6 | step 6: selected-chip display text | asserted |
| 7 Save pipeline | Pipeline saves without errors | step 7 | step 7: no console errors, 2xx (201 observed) | asserted |
| 8 Reload — verify Jinja Template text, Input, and Output persist | all State modifier fields are correctly restored after reload | step 8 | step 8: live UI round-trip of all 3 field groups | asserted |
| Expected Final State: fully configured, persists after reload | — | steps 7–8 | steps 7–8 | asserted |
| Pass/Fail: all steps complete without errors; fields persist after reload | — | all steps | all steps | asserted |

**CLARIFICATION on precondition + step 4 ("Variables to clean" expandable
section):** the case text implies "Variables to clean" is an expandable/
accordion section distinct in kind from Input/Output. Live-confirmed
(source: `StateModifierNode.jsx` — `<FlowEditorSelect.InputSelect label="Variables
to clean" inputFieldName="variables_to_clean" .../>`, and live DOM inspection: no
accordion, no expand icon, no collapsed state) it is the SAME
tool-agnostic multi-select component as Input/Output — a plain combobox that
opens a dropdown listing existing pipeline state variables, nothing to
"expand". Not filed as a defect — the case's overall intent (verify the
field exists and is usable) is fully achievable via the dropdown-open
mechanism this AFS uses instead. Same class of finding as the sibling
pipeline-node cases' Decision-outputs/Routes clarifications
(`#1104`/`#1136`/`#1137`/`#1144`).

### Axis 2 — Analyst additions

- Step 7 additionally asserts the exact HTTP status (201 Created, observed
  live) rather than a generic "no errors" — *added: pins the exact expected
  status so a future regression to e.g. a 200-with-error-body doesn't
  silently pass a looser "2xx-ish" check. Consistent with every other
  pipeline-node-configuration AFS in this feature area.*
- No console-error assertion was in the original case text; added it
  throughout as a side-channel check — zero console errors were observed in
  this session (both on initial configuration and after reload).
- **Not asserted (deliberately out of this case's scope):** the node's
  ReactFlow `Input`/`Output` source/target HANDLE labels (distinct from the
  Input/Output config FIELDS — the case text does not distinguish these,
  and confusing the two would be a false positive) are visible on the
  canvas card below the config fields — present from the moment the node is
  added, unrelated to this case's Save/reload persistence intent. Left
  unexercised, same as the Decision AFS's unwired `Default output` handle.
- **Not asserted (deliberately out of this case's scope):** whether the
  node is the pipeline's entry point (it renders an extra "Trigger" field
  when it is, per `NodeCard.jsx`'s shared entry-point behavior — same
  mechanism already documented for every other node type in the digest).
  This AFS's single-node setup makes the State modifier node the sole/entry
  node, so the Trigger field DOES render live, but the case doesn't mention
  it and this AFS doesn't assert against it either way (same precedent as
  the Decision/Router AFSes, which also added their node as the pipeline's
  only node without asserting the Trigger field's presence or absence).

## Cleanup

1. This session created a persistent pipeline (`autotest_state_mod_2035`, id
   `160`) on the local DEV backend, under the "UI Testing" project (not
   `.env.test`'s configured `ELITEA_PROJECT_ID=399` — this analyst session's
   active browser project happened to be a different one; **flagging as the
   same project-mismatch gotcha documented in the Router AFS** for the
   implementer to verify before seeding real test data via `PipelineAPI`).
   **Not deleted at the end of this session** — same tooling gap as every
   other analyst-session pipeline in this project (`PipelineAPI` needs a
   live Playwright `browser_cookies` context this session's MCP tooling
   doesn't expose). Flagging for the implementer/lead: if a cleanup sweep of
   stale localhost pipelines is ever run, id `160` is safe to delete.
2. Implementer teardown: use the existing `pipeline_id` fixture
   (`automation/fixtures/data_fixtures.py`), which creates-and-deletes an
   empty pipeline per test via `PipelineAPI`; add the two custom state
   variables inside the test via `PipelineDetailPage` methods rather than
   seeding a hand-built topology (same reasoning as the Decision/Router
   AFSes).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| State modifier node on canvas | `.react-flow__node-state_modifier` (CSS class) / `[data-id="StateModifier 1"]` | **on-main ✓** — ReactFlow's own class/attribute convention (library-injected, not app-authored — same sanctioned #579 exception as every other node type in this suite); confirmed live. Matches `PipelineDetailPage.wait_for_node_on_canvas("state_modifier")` / `get_node_ids()` (existing methods, reused unmodified). | none needed |
| `Jinja Template` textarea | `[data-testid="pipeline-state-modifier-node-template-input"]` | **added — this session, `automation/testids`** (awaiting human promotion to `main`). Wired `inputProps={{ 'data-testid': 'pipeline-state-modifier-node-template-input' }}` on `StateModifierNode.jsx`'s `AIAssistantInput` call site (same `AIAssistantInput` → `Input.InputBase` → `MuiTextField` pattern the Decision/Router AFSes documented for their Description/Condition fields). Confirmed live rendering + fill + persistence round-trip via DOM query. | none needed |
| `Variables to clean` multi-select | `[data-testid="pipeline-state-modifier-node-variables-to-clean-select"]` (+ auto-derived `-combobox` suffix on the inner display div) | **added — this session, `automation/testids`** (awaiting human promotion to `main`). Wired `dataTestId="pipeline-state-modifier-node-variables-to-clean-select"` on `StateModifierNode.jsx`'s first `FlowEditorSelect.InputSelect` call site (prop was already plumbed by `InputSelect.jsx`, same as the Code/Decision AFSes' Input field). Confirmed live rendering via DOM query. | none needed |
| `Input` multi-select | `[data-testid="pipeline-state-modifier-node-input-select"]` (+ `-combobox` suffix) | **added — this session, `automation/testids`** (awaiting human promotion to `main`). Same mechanism as `Variables to clean`, on the second `FlowEditorSelect.InputSelect` call site. Confirmed live rendering + select + persistence round-trip. | none needed |
| `Output` multi-select | `[data-testid="pipeline-state-modifier-node-output-select"]` (+ `-combobox` suffix) | **added — this session, `automation/testids`** (awaiting human promotion to `main`). Wired `dataTestId="pipeline-state-modifier-node-output-select"` on `StateModifierNode.jsx`'s `FlowEditorSelect.OutputSelect` call site (`OutputSelect.jsx` already accepted the prop, same as Code node's Output field). Confirmed live rendering + select + persistence round-trip. | none needed |
| `Input`/`Output` dropdown option (state var name) | `[data-testid="select-option-{value}"]` (e.g. `select-option-issue_details`, `select-option-normalized_issue`) | **on-main ✓** — confirmed via `git grep` on `origin/main`: `SingleSelectMenuItem.jsx:117` (same mechanism every sibling pipeline-node AFS documents); also confirmed live via click interaction for `input`/`messages` (the built-in vars) this session. | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` | **on-main ✓** — confirmed present, already wired as `PipelineFormPage.save_button`; confirmed live firing a `PUT .../application/prompt_lib/{project}/{pipeline_id}` → 201. | none needed |
| Add-node "+" button / menu item | `[data-testid="pipeline-add-node-button"]`, `[data-testid="pipeline-add-node-menu-item-state_modifier"]` | **on-`automation/testids` only** (awaiting human promotion to `main`) — confirmed via live click this session, same status as every other pipeline-node AFS's Add-node menu row. | n/a — informational only |
| `STATE` panel controls (toggle/close/add-variable button/name input) | `[data-testid="pipeline-state-drawer-toggle-button"]` / `-close-button` / `pipeline-state-add-variable-button` / `pipeline-state-add-variable-name-input` | **on-`automation/testids` only** (awaiting human promotion to `main`) — pre-existing from the Decision AFS session (ELITEA-2034), reused unmodified this session; confirmed live via `open_state_panel()`/`add_state_variable()` methods already on `PipelineDetailPage`. | none needed |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation (step 0's prerequisite, if not using the `pipeline_id` fixture).
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on Save click (step 7); persists the State modifier node's full config (`template`, `variables_to_clean`, `input`, `output`) plus the two new custom state variables as part of the pipeline's YAML `instructions` field. Confirmed live: returns **201 Created** (not 200), same as every other pipeline-node-configuration AFS.
- `GET .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on page load/reload (step 8); the State modifier node's rendered config is re-derived directly from this response's YAML `instructions`.

## Known Defects Found During Exploration

No product defects found. This session's exploration executed all 9 steps
(case's 8 plus this AFS's setup step 0) to completion against the live local
environment with zero console errors at every checkpoint, including a real
Save-click + full page reload persistence round-trip for the Jinja Template,
Input, and Output fields.

One case-text drift was identified and is filed as a CLARIFICATION (not a
bug), per the reverse-masking guard, bundled with the same
node-configuration-field-shape pattern already tracked for sibling pipeline-
node cases:

- **[INFO] Case step 2/4 wording ("Variables to clean" expandable section)
  doesn't match how the live UI's Variables to clean field actually works**
  — it's the SAME tool-agnostic multi-select combobox component as
  Input/Output, not an accordion/expandable section. Same shape as
  `#1104`/`#1136`/`#1137`/`#1144` filed against sibling pipeline cases
  (ELITEA-2018/2031/2032/2033) and ELITEA-2034's Decision-outputs
  clarification — **to be filed as a new CLARIFICATION issue by the lead
  per the standard bug-filing routing**, dedup first against the existing
  cluster as this may be bundle-eligible under the same umbrella pattern.

## Blocked Steps

None. All 9 steps (case's 8 plus this AFS's setup step 0) were executed to
completion against the live local environment, including a real Save-click +
full `page.reload()` persistence round-trip for every field.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` — all
  testids this case needs are now added and pushed to `automation/testids`
  this session: `Jinja Template` textarea, `Variables to clean`/`Input`/
  `Output` selects. See Concrete Handles for exact selectors. No further
  `add-data-testid` work is needed for this case.
- **State variables are NOT built-in for a fresh pipeline** (unlike Router's
  `input`/`messages`, which ARE built-in) — the State modifier node's
  Input/Output combos on a brand-new pipeline list only `input`/`messages`
  until custom state variables are added via the `STATE` panel. This AFS's
  step 0 makes that setup explicit; reuses the existing
  `open_state_panel()`/`add_state_variable()`/`close_state_panel()` methods
  unmodified (added during the Code node AFS's implementation, ELITEA-2009).
- **`Jinja Template` field commits via native `input` event
  (`onInput={handleTemplateFilling}`)** — confirmed live that Playwright's
  `fill()` correctly triggers this handler (unlike most MUI `TextField`s in
  this codebase, which need `press_sequentially()` per
  `.claude/rules/mui-patterns.md`); `_fill_node_field_value()` (the existing
  shared private helper, already used by Code/LLM/Router/Decision fields)
  handles both cases uniformly via click + press_sequentially, which also
  works correctly here — reused unmodified rather than special-cased.
- No existing page-object method read/wrote a State modifier node's inline
  config before this session — added `fill_state_modifier_node_template()` /
  `get_state_modifier_node_template()` / `open_state_modifier_node_*_select()`
  / `select_state_modifier_node_*_variable()` / `get_state_modifier_node_*_value()`
  on `PipelineDetailPage`, following the exact same shape as the Code node
  AFS's methods (ELITEA-2009).
- Wait strategy: wait for the `PUT .../application/prompt_lib/{project}/{pipeline_id}`
  response (201, confirmed) before reloading/asserting persistence — not a
  fixed timeout. Existing `save_and_wait_for_update()` method reused
  unmodified.
- The `Jinja Template` field's underlying element is a plain MUI `TextField`
  (multiline `<textarea>`), same `AIAssistantInput` component family as the
  Router AFS's `Condition` field and the Decision AFS's `Description` field
  — normal `.input_value()`-readable Playwright textarea, NOT a
  CodeMirror/Monaco editor, so it needs none of the `.agents/testing.md`
  #579 CodeMirror-line-scoping technique.
