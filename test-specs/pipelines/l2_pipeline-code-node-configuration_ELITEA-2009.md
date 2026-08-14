# Test Case: Pipeline — Configure Code Node

## Metadata
- **TMS ID**: ELITEA-2009
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst/Implementer**: test-automation-engineer (agent), combined analyst+implementer session 2026-08-08
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A project exists with access to the Pipelines feature — matches the case's stated precondition exactly, no drift.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- An empty pipeline via the `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`,
  `PipelineAPI`-backed create/delete).
- **CLARIFICATION on the case's Test Data table** — the Output variable
  `result` is NOT a built-in pipeline state variable (only `input`/`messages`
  are), and the Output select (like Input) only lists EXISTING state
  variables — it is not a freeform/creatable field (confirmed live, same
  "state vars not built-in" pattern already documented for the Decision node,
  ELITEA-2034). This AFS makes creating `result` as a custom state variable
  via the `STATE` panel's "+" control an explicit setup step (step 0) before
  it can be selected in the Output combobox.

| Field | Value |
|-------|-------|
| CODE Type | Fixed |
| CODE Value | `import json\nresult = input.upper()` |
| Input variable | input (built-in) |
| Output variable | result (custom — created in step 0) |

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's live-exploration browser
  was on project "UI Testing" (id 400), which does NOT match `.env.test`'s
  `ELITEA_PROJECT_ID` (399, "Private") — same project-mismatch gotcha the
  Router/Decision AFSes flag. Not exercised as a real mismatch here (this
  session used the UI directly, not `PipelineAPI` against a specific project),
  but the implementer must still verify the active project before creating
  test data via any standalone token-auth path; the cookie-based `pipeline_id`
  fixture avoids the gotcha entirely.

## Test Steps

**IMPORTANT — step 0 added ahead of the case's step 1.** The case's Test
Data table implies the Output variable `result` simply "is" a value to set;
live behavior requires it to exist as a custom state variable first (see
Coverage Map / Known Defects Found During Exploration).

0. **Setup**: create a pipeline; add a custom state variable named `result`
   via the flow editor's `STATE` panel's "+" control
   (`open_state_panel()` + `add_state_variable("result")`), then close the
   panel (`state_drawer_close_button`) — the open drawer overlaps the canvas
   and intercepts pointer events on nodes underneath it (same gotcha as the
   Decision AFS).
   - **Verify**: `STATE` panel lists `result` alongside the built-in `input`/
     `messages`.
1. Create a pipeline and add a Code node via "Add node" → "Code"
   (`add_node("Code")`).
   - **Verify**: node appears on canvas — `wait_for_node_on_canvas("code")`
     returns a non-empty id (`Code 1`); node count increased by 1.
2. Click on Code node to open configuration panel.
   - **Verify**: no click-to-open action exists or is needed — the Code
     node's config renders fully inline/expanded on the canvas card the
     moment it's added, same always-expanded shape as every other pipeline
     node type in this codebase (matches the digest's already-confirmed
     generic finding, re-confirmed live for Code this session). "Click on
     Code node" is trivially satisfied by the node existing on canvas —
     **CLARIFICATION, not a defect** (case-text drift, same class already
     filed for sibling node-configuration cases).
3. Verify panel shows: CODE section (Type + Value), Input, Output, Interrupt
   before/after, Structured output.
   - **Verify**: sections visible top to bottom, confirmed live via the
     node's full text content: `CODE` (`Type` select + `Value` field),
     `Input` (multi-select), `Output` (multi-select), `Interrupt before` /
     `Interrupt after` switches, `Structured output` switch. All six listed
     elements present — matches the case's step 3 expectation EXACTLY, no
     case-text drift on section presence (the displayed `CODE` heading is
     CSS `text-transform: uppercase` on the literal text content `Code` —
     `Chip.HeadingChip label={capitalizeFirstChar(variableName...)}`, not a
     distinct string).
4. In CODE section: set Type to "Fixed", enter Value with Python code (e.g.,
   `import json\nresult = input.upper()`).
   - **Verify**: Type select already defaults to `Fixed` on a freshly-added
     node (confirmed live — `select_code_node_type("Fixed")` is a no-op in
     this flow but is asserted anyway to guard a future default-value
     regression); Value field accepts the multi-line string exactly
     (`get_code_node_value() == "import json\nresult = input.upper()"`,
     confirmed live via `.input_value()` immediately after typing).
5. Set Input combobox — add variable "input".
   - **Verify**: `Input` field shows "input" as a selected chip
     (`get_code_node_input_value() == "input"`).
6. Set Output combobox — add variable "result".
   - **Verify**: `Output` field shows "result" as a selected chip
     (`get_code_node_output_value() == "result"`) — only reachable because
     step 0 pre-created `result` as a custom state variable (see
     CLARIFICATION above).
7. Save pipeline (`agent-save-button`).
   - **Verify**: no console errors; `PUT
     .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` returns
     a 2xx (observed live: 201 Created, same as every other pipeline-node
     AFS in this suite).
8. Reload — verify CODE Type "Fixed", Value, Input, and Output persist.
   - **Verify**: after a real `page.reload()` (navigation, not just an API
     read), the Code node shows the persisted Type (`Fixed`), Value (the
     exact multi-line string), Input chip (`input`), and Output chip
     (`result`) — confirmed live via a full reload round-trip this session.

## Expected Results
- The Code node's config renders fully inline on the canvas card (no
  modal/panel to open) — CODE (Type + Value), Input, Output, Interrupt
  before/after, Structured output all present and independently persist
  through Save + reload.
- The CODE section's Value field is a plain MUI textarea (`#code-value`,
  stable unique DOM id), NOT a CodeMirror/Monaco editor, despite the
  component receiving a `language="python"` prop — that prop only affects
  the SEPARATE full-screen AI Assistant modal (same pattern as the Router
  node's Condition field / Decision node's Description field).
- The Output combobox (like Input) only lists EXISTING pipeline state
  variables — `result` must be pre-created via the `STATE` panel before it
  can be selected; it is not a freeform/creatable field.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in, project with Pipelines access | met | Preconditions | n/a (localhost auto-auth) | asserted — no drift |
| 1 Create a pipeline and add a Code node via "Add node" → "Code" | Code node appears on canvas | step 1 | step 1: node count + id via `wait_for_node_on_canvas("code")` | asserted |
| 2 Click on Code node to open configuration panel | Configuration panel opens | step 2 | step 2: node existence (no click-to-open action needed) | asserted — **CLARIFICATION: no click-to-open panel exists; config is always inline/expanded, same as every other node type in this codebase.** |
| 3 Verify panel shows CODE (Type+Value), Input, Output, Interrupt before/after, Structured output | all listed sections present | step 3 | step 3: full node text content includes all 6 elements | asserted — no case-text drift, live UI matches exactly |
| 4 In CODE section: set Type "Fixed", enter Value with Python code | CODE section accepts the value | step 4 | step 4: `get_code_node_value()` equals entered string | asserted |
| 5 Set Input combobox — add "input" | "input" added to Input | step 5 | step 5: `get_code_node_input_value()` | asserted |
| 6 Set Output combobox — add "result" | "result" added to Output | step 6 | step 6: `get_code_node_output_value()` | asserted — **CLARIFICATION: "result" is not a built-in state variable and the Output field is not freeform — it must be pre-created via the STATE panel first (this AFS's step 0).** |
| 7 Save pipeline | saves without errors | step 7 | step 7: no console errors, 2xx (201 observed) | asserted |
| 8 Reload — verify CODE Type, Value, Input, Output persist | all fields restored | step 8 | step 8: live UI round-trip of all 4 field groups after a real `page.reload()` | asserted |
| Expected Final State: fully configured, persists after reload | — | steps 7–8 | steps 7–8 | asserted |
| Pass/Fail: all steps complete without errors; fields persist after reload | — | all steps | all steps | asserted |

**CLARIFICATION on Test Data / step 6 (Output variable `result` not
built-in):** the case's Test Data table lists `result` as simply the Output
variable value, implying it's directly selectable. Live-confirmed (source:
`OutputSelect.jsx` uses the SAME `useInputOptions()` hook as `InputSelect.jsx`
— both list only existing pipeline state variables, no freeform/creatable
option) and via live DOM inspection: before creating `result` via the STATE
panel, the Output combobox's option list is `["input", "messages"]` only —
identical to Input's list. After adding `result` via `add_state_variable()`,
the option list becomes `["input", "messages", "result"]` and selection
succeeds. Not a defect — the case's overall intent (Output = "result") is
fully achievable via this AFS's step 0 setup; the wording just undersells the
precondition, the SAME class of finding already filed for the Decision node
(`normalized_issue`/`metadata_json`, ELITEA-2034) and other pipeline-node
cases (`#1104`/`#1136`/`#1137`/`#1144`).

### Axis 2 — Analyst additions

- Step 7 additionally asserts the exact HTTP status (201 Created, observed
  live) rather than a generic "no errors" — *added: pins the exact expected
  status so a future regression to e.g. a 200-with-error-body doesn't
  silently pass a looser "2xx-ish" check. Consistent with every other
  pipeline-node-configuration AFS in this feature area.*
- No console-error assertion was in the original case text; added it
  throughout as a side-channel check — zero console errors/warnings were
  observed in this session at every checkpoint (initial configuration, Save,
  and post-reload).
- Step 4 additionally asserts the Type select's default value is `Fixed`
  even though the case's own test data already specifies `Fixed` — *added:
  guards against a regression to a different default Type on a freshly-added
  node, matching the LLM/HITL node AFSes' equivalent default-value
  assertions.*
- **Not asserted (deliberately out of this case's scope):** the Interrupt
  before/after switches' disabled/enabled states (Interrupt before is
  disabled while the Code node is the pipeline's entry point; Interrupt
  after is disabled while its `transition` is `END` — both confirmed live,
  same `CommonInterruptSettings.jsx` logic as every other node type) and the
  Structured output switch's toggled state are visible (step 3) but never
  exercised by this case's numbered steps. Left unasserted here rather than
  invented — matches the case's own scope (it only asks that the sections be
  *present*, not that Interrupt/Structured-output be *toggled*).

## Cleanup

1. This session created a persistent pipeline (`autotest_code_node_2009`, id
   `159`, project 400 "UI Testing") on the local DEV backend. **Not deleted
   at the end of this session** — same tooling limitation already documented
   in the Decision/Router AFSes (`PipelineAPI` requires a live Playwright
   `browser_cookies` context this analyst-style exploration session's
   tooling doesn't expose). Flagging for the implementer/lead: safe to
   delete if a cleanup sweep of stale localhost pipelines is ever run.
2. Implementer teardown: use the existing `pipeline_id` fixture
   (`automation/fixtures/data_fixtures.py`), which creates-and-deletes an
   empty pipeline per test via `PipelineAPI`; add the custom state variable
   inside the test via `PipelineDetailPage.open_state_panel()` +
   `add_state_variable("result")` rather than seeding a hand-built topology.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Code node on canvas | `[data-testid="rf__node-{node_id}"]` (dynamic, e.g. `rf__node-Code 1`) | **on-main ✓** — ReactFlow's own testid convention (library-injected, sanctioned #579 exception, same as every other node type in this suite); confirmed live. Also usable: `.react-flow__node-code` CSS class + `data-id` — matches `PipelineDetailPage.wait_for_node_on_canvas("code")` (existing method, reused unmodified). | none needed |
| CODE section Type select | `[data-testid="pipeline-code-node-type-select"]` | **added — `EliteaAI/EliteaUI@92fc6ec4` on `automation/testids`** (awaiting human promotion to `main`). Wired `testIdsByKey={{code: {typeSelectTestId: 'pipeline-code-node-type-select', ...}}}` on `CodeNode.jsx`'s `SimpleLLMInputs` call site (prop plumbing already existed generically, same mechanism ELITEA-2004 used for the LLM node's SYSTEM/TASK/CHAT HISTORY sections). Confirmed live rendering via DOM query + interaction. | none needed |
| CODE section Value field | `[data-testid="pipeline-code-node-value"]` | **added — `EliteaAI/EliteaUI@92fc6ec4` on `automation/testids`** (awaiting human promotion to `main`). Same `testIdsByKey` map, `valueFieldTestId` key. Confirmed live: typed a 2-line Python string, read back via `.input_value()`, matched exactly; also confirmed the underlying element is a plain `<textarea id="code-value">`, not CodeMirror. | Interim, pre-testid: `#code-value` (stable unique DOM id, same shape as LLM node's `#system-value`/`#task-value`/`#chat_history-value`) — no longer needed now the testid exists |
| Input multi-select | `[data-testid="pipeline-code-node-input-select"]` | **added — `EliteaAI/EliteaUI@92fc6ec4` on `automation/testids`** (awaiting human promotion to `main`). Wired `dataTestId="pipeline-code-node-input-select"` on `CodeNode.jsx`'s `InputSelect` call site (prop already plumbed by `InputSelect.jsx`). Confirmed live. | none needed |
| Output multi-select | `[data-testid="pipeline-code-node-output-select"]` | **added — `EliteaAI/EliteaUI@92fc6ec4` on `automation/testids`** (awaiting human promotion to `main`). Wired `dataTestId="pipeline-code-node-output-select"` on `CodeNode.jsx`'s `OutputSelect` call site. Confirmed live — option list correctly reflects STATE-panel-created custom variables (`select-option-result` appeared only after `add_state_variable("result")`). | none needed |
| Input/Output dropdown option (state var name) | `[data-testid="select-option-{value}"]` (e.g. `select-option-input`, `select-option-result`) | **on-main ✓** — confirmed via `git grep` on `origin/main`: `SingleSelectMenuItem.jsx:117` (same mechanism every other node-type AFS documents); confirmed live via click interaction. | none needed |
| Interrupt after switch | `[data-testid="pipeline-code-node-interrupt-after-toggle"]` | **added — `EliteaAI/EliteaUI@92fc6ec4` on `automation/testids`** (awaiting human promotion to `main`). Wired `interruptAfterTestId="pipeline-code-node-interrupt-after-toggle"` on `CodeNode.jsx`'s `CommonInterruptSettings` call site (opt-in-per-caller shape the shared component already documents). Confirmed live rendering via DOM query. | none needed |
| Structured output switch | `[data-testid="pipeline-code-node-structured-output-toggle"]` | **added — `EliteaAI/EliteaUI@92fc6ec4` on `automation/testids`** (awaiting human promotion to `main`). Wired `structuredOutputTestId="pipeline-code-node-structured-output-toggle"` on the same `CommonInterruptSettings` call site. Confirmed live rendering via DOM query. | none needed |
| Interrupt before switch | `[data-testid="pipeline-node-interrupt-before-toggle-{node_id}"]` (e.g. `pipeline-node-interrupt-before-toggle-Code 1`) | **on-`automation/testids` only** (awaiting human promotion to `main`) — pre-existing dynamic testid (ELITEA-2008, unconditional across every node type sharing `CommonInterruptSettings.jsx`); confirmed live present and correctly `disabled` while Code 1 is the pipeline's entry point. Matches `PipelineDetailPage.NODE_INTERRUPT_BEFORE_TOGGLE` template constant (existing, unmodified). | none needed |
| `STATE` panel toggle / close / add-variable button / name input | `pipeline-state-drawer-toggle-button` / `pipeline-state-drawer-close-button` / `pipeline-state-add-variable-button` / `pipeline-state-add-variable-name-input` | **on-`automation/testids` only** (awaiting human promotion to `main`) — pre-existing (ELITEA-2034), reused unmodified via `PipelineDetailPage.open_state_panel()` / `add_state_variable()`. Confirmed live this session. | none needed |
| Add-node "+" button / menu item | `[data-testid="pipeline-add-node-button"]`, `[data-testid="pipeline-add-node-menu-item-code"]` | **on-`automation/testids` only** (awaiting human promotion to `main`) — pre-existing; used directly by this session's live exploration. `PipelineDetailPage.add_node("Code")` already drives this via its own existing (non-testid, `get_by_role("menuitem", name="Code", exact=True)`) approach — informational only, no page-object change needed. | n/a |
| Pipeline Save button | `[data-testid="agent-save-button"]` | **on-main ✓** — confirmed present, already wired as `PipelineFormPage.save_button`; confirmed live firing `PUT .../application/prompt_lib/{project}/{pipeline_id}` → 201. | none needed |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation (step 0's prerequisite, if not using the `pipeline_id` fixture).
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on Save click (step 7); persists the Code node's full config (`code` object with `type`/`value`, `input`, `output`) plus the new custom `result` state variable as part of the pipeline's YAML `instructions` field. Confirmed live: returns **201 Created**.
- `GET .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on page load/reload (step 8); the Code node's rendered config is re-derived directly from this response's YAML `instructions`.

## Known Defects Found During Exploration

No product defects found. This session's exploration executed all 9 steps
(case's 8 plus this AFS's setup step 0) to completion against the live local
environment with zero console errors/warnings at every checkpoint, including
a real Save-click + full `page.reload()` persistence round-trip for every
field (Type, Value, Input, Output).

One case-text drift was identified and is filed as a CLARIFICATION (not a
bug), per the reverse-masking guard, bundled with the same
"state-vars-not-built-in" pattern already tracked for the sibling Decision
node case:

- **[INFO] Case Test Data table lists Output variable `result` as if it's
  directly selectable — live-confirmed the Output combobox (like Input) only
  lists EXISTING pipeline state variables, and `result` isn't one until
  explicitly created via the `STATE` panel.** Same shape as
  `#1104`/`#1136`/`#1137`/`#1144` filed against sibling pipeline cases
  (ELITEA-2018/2031/2032/2033) and the Decision node's equivalent finding
  (ELITEA-2034) — **to be filed as a new CLARIFICATION issue by the
  implementer/lead per the standard bug-filing routing** (dedup first
  against the existing cluster, as this may be bundle-eligible under the
  same umbrella pattern).

## Blocked Steps

None. All 9 steps (case's 8 plus this AFS's setup step 0) were executed to
completion against the live local environment, including a real Save-click +
full `page.reload()` persistence round-trip.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` — all
  testids this case needed were added and pushed to `automation/testids` in
  a single commit (`EliteaAI/EliteaUI@92fc6ec4`): CODE Type select, CODE
  Value field, Input select, Output select, Interrupt after, Structured
  output. No further `add-data-testid` work is needed for this case.
- **The CODE section's Value field is a plain textarea, NOT CodeMirror** —
  confirmed via both source read (`AIAssistantInput.jsx`: the `language`
  prop only feeds `detectedLanguage`/`specifiedLanguage` for the SEPARATE
  full-screen AI Assistant modal, not the inline field itself) and live DOM
  (`document.querySelector('#code-value').tagName === 'TEXTAREA'`). Uses the
  SAME `_fill_node_field_value()` / `.input_value()` mechanics as the LLM
  node's SYSTEM/TASK/CHAT HISTORY fields and the Router/Decision nodes'
  Condition/Description fields — no CodeMirror-line-scoping technique
  needed. Multi-line text (`\n`) types and reads back correctly via
  `press_sequentially()`.
- **Output variable must pre-exist as a state variable — same gotcha as
  Decision's Input.** `OutputSelect.jsx` and `InputSelect.jsx` both use the
  identical `useInputOptions()` hook; neither supports freeform/creatable
  entries. A fresh pipeline's Output/Input option list is `["input",
  "messages"]` only. Use `open_state_panel()` + `add_state_variable(name)`
  (existing `PipelineDetailPage` methods, unmodified) to create `result`
  BEFORE attempting `select_code_node_output_variable("result")` — closing
  the STATE drawer afterward (`state_drawer_close_button`) is required
  before interacting with the canvas node, or the open drawer intercepts
  pointer events (same gotcha the Decision AFS documents).
  Reused unmodified for this case.
- **Interrupt before/after disabled-state depends on node position**,
  confirmed live: Interrupt before is `disabled` while the Code node is the
  pipeline's entry point (true for the first node added to an empty
  pipeline); Interrupt after is `disabled` while the node's `transition` is
  `END` (also true for a single freshly-added node with no outgoing edge).
  Neither is exercised by this case's numbered steps (see Axis 2), but an
  implementer writing a toggle-interaction test for either switch on a
  single-node pipeline will need a second node + an edge first.
- **Project mismatch gotcha** (see the Router/Decision AFSes for the full
  writeup) — this session's live-exploration browser was on project "UI
  Testing" (400), NOT `.env.test`'s `ELITEA_PROJECT_ID` (399, "Private").
  Not a real mismatch here since no `PipelineAPI` calls were made directly
  during exploration (UI-only), but the implementer should use the
  cookie-based `pipeline_id` fixture (which authenticates against whatever
  project the test's own auth state resolves to) rather than a standalone
  token-auth script, to avoid the gotcha entirely.
- No existing page-object method read/wrote a Code node's inline config
  before this session — `automation/pages/pipeline_detail_page.py` now has
  a dedicated Code node section (`get_code_node_type`,
  `select_code_node_type`, `fill_code_node_value`, `get_code_node_value`,
  `open_code_node_input_select`, `select_code_node_input_variable`,
  `get_code_node_input_value`, `open_code_node_output_select`,
  `select_code_node_output_variable`, `get_code_node_output_value`) —
  simpler than the LLM node's 3-section dispatch (`_LLM_NODE_SECTIONS`)
  since the Code node has exactly one CODE section, but reuses the same
  generic helpers (`_fill_node_field_value`,
  `_select_multi_select_option_and_close`, `_wait_for_open_popovers_closed`).
- Wait strategy: wait for the `PUT .../application/prompt_lib/{project}/{pipeline_id}`
  response (201, confirmed) before reloading/asserting persistence — not a
  fixed timeout.
