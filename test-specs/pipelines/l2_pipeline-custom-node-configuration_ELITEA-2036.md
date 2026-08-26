# Test Case: Pipeline — Custom Node Configuration

## Metadata
- **TMS ID**: ELITEA-2036
- **Linked Story**: none
- **Priority**: l2 (source TMS case: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst/Implementer**: test-automation-engineer (agent), combined slot, session 2026-08-08
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A project exists with access to the Pipelines feature (matches the case's
  precondition verbatim — no drift).
- **CLARIFICATION (Axis 1, precondition gap).** The case's Test Data table says
  "(none required)" and its steps never mention attaching a toolkit — but
  live-confirmed (source: `DefaultNode.jsx`, the Custom node's renderer) the
  Custom node's config is built from the SAME component tree as the Toolkit
  node (ELITEA-2010): a `Toolkit` select, a conditionally-rendered `Tool`
  select, `Input`/`Output` state-variable selects, and an `INPUT MAPPING`
  (Type + Value per parameter) section. The Tool select and INPUT MAPPING
  section are **absent from the DOM entirely** until (a) a Toolkit is
  attached to the pipeline's TOOLS section AND (b) that Toolkit is selected
  in the node's own Toolkit dropdown AND has `settings.selected_tools` set.
  The case's step 3 ("Configure the Custom node fields (Type + Value for
  input mapping, Input, Output)") is only achievable once this setup exists.
  Same class of finding already filed for the Toolkit-node case (ELITEA-2010)
  and the Router-node case (ELITEA-2033) — not a defect, the case's overall
  intent (configure Type+Value input mapping) is fully achievable, the
  wording just undersells the precondition. This AFS's step 1b makes the
  toolkit-attach setup explicit.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A fresh empty pipeline via the `pipeline_id` fixture
  (`automation/fixtures/data_fixtures.py`, `PipelineAPI`-backed create/delete).
- A GitHub credential + toolkit with `settings.selected_tools: ["search_issues"]`
  explicitly set, via the existing `github_toolkit_with_selected_tools` fixture
  (`automation/fixtures/data_fixtures.py:495`) — the SAME fixture the
  Toolkit-node case (ELITEA-2010) already uses, chosen for the identical
  reason: `search_issues` has 1 required parameter (`SEARCH QUERY`) plus 2
  optional (`MAX COUNT`, `REPO NAME`), giving the Type+Value input-mapping
  UI a real row to configure.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — see the Router-node AFS's "Project
  mismatch" gotcha (same environment, same caveat); the `pipeline_id`/
  `github_toolkit_with_selected_tools` fixtures use cookie-based auth so they
  aren't affected.

## Test Steps

**IMPORTANT — step 1b added between the case's step 1 and step 2.** See the
Preconditions CLARIFICATION above for why.

1. Create a pipeline and add a Custom node via "Add node" → "Custom"
   (`add_node("Custom")`, existing `PipelineDetailPage` method).
   - **Verify**: `wait_for_node_on_canvas("custom")` returns a non-empty id
     (`Custom 1`).
1b. **Setup**: attach the GitHub toolkit (with `selected_tools` set) to the
    pipeline's TOOLS section via the existing `open_toolkit_popper()` /
    `select_toolkit_in_popper()` methods (same flow the Toolkit-node AFS
    documents).
   - **Verify**: `is_toolkit_attached(toolkit_name)` is true.
2. Verify Custom node appears on canvas — examine config panel structure
   (renders **inline on the card itself — no click-to-open action needed**,
   same always-expanded shape as every other pipeline node type in this
   codebase — matches the digest's already-confirmed generic finding).
   - **Verify**: sections visible top to bottom: `Toolkit` select, `Input`
     select, `Output` select, `Interrupt before`/`Interrupt after` toggles,
     `Structured output` toggle, and a raw-JSON editor view of the node's
     own YAML body (`CustomNodeInput.jsx` — unique to this node type among
     the suite; every other node type's config is purely structured
     fields). **Also verify (Axis 2 addition)**: `Tool` select and any
     `INPUT MAPPING` section are absent at this point — a negative/absence
     assertion, same two-stage-reveal discipline already enforced for the
     Toolkit node.
3. Configure the Custom node fields (Type + Value for input mapping, Input,
   Output):
   a. Select the attached toolkit in the node's `Toolkit` dropdown.
      - **Verify**: combobox shows the toolkit's name.
   b. Select `search_issues` in the now-present `Tool` dropdown.
      - **Verify**: combobox shows `search_issues`; `INPUT MAPPING
        (required 1)` (parameter `SEARCH QUERY`) and `INPUT MAPPING
        (optional 2)` (`MAX COUNT`, `REPO NAME`) accordions appear.
   c. In `INPUT MAPPING (REQUIRED 1)`, set the `SEARCH QUERY` row's Type to
      `F-String` and fill its Value with `{input} error`.
      - **Verify**: Type select shows `F-String`; Value field's
        `input_value()` is `{input} error`.
4. Set Input and Output comboboxes with state variables — `Input` → `input`,
   `Output` → `messages`.
   - **Verify**: both comboboxes show the selected values.
5. Save pipeline (`agent-save-button`).
   - **Verify**: no console errors, no failed (≥400) network requests;
     `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}`
     returns a 2xx.
6. Reload — verify all Custom node fields persist (canonical URL
   `/pipelines/all/{id}?viewMode=owner`, full `page.reload()`, not just an
   API read).
   - **Verify**: after reload, the Custom node shows the persisted Toolkit,
     Tool (`search_issues`), `SEARCH QUERY` Input-mapping value, Input
     (`input`), and Output (`messages`) — confirmed live. **Also verify
     (Axis 2 addition)**: the node's own raw-JSON editor view reflects the
     SAME persisted state (`"tool": "search_issues"` and the input-mapping
     value both present in its text) — a regression where the structured
     fields and the raw-JSON view drift apart would otherwise go
     undetected, and this view is unique to the Custom node.

## Expected Results
- Custom node config renders fully inline on the canvas card (no
  modal/panel to open) — Toolkit, Input, Output, Interrupt before/after,
  Structured output, and a raw-JSON editor view all present.
- Tool select and INPUT MAPPING sections are absent until a Toolkit (with
  `selected_tools`) is selected — a real two-stage progressive-disclosure
  precondition, not a rendering defect (same pattern already confirmed for
  the Toolkit node, ELITEA-2010).
- Once a Tool is selected, INPUT MAPPING splits into REQUIRED N / OPTIONAL N
  accordions, one row per the tool's actual parameters, each with its own
  Type (Fixed/F-String/Variable) select and Value field.
- Saving persists everything; a full page reload confirms every field —
  including the raw-JSON editor view — survives unchanged.
- No console errors, no failed network requests, at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, project with Pipelines access | setup exists | Preconditions | N/A (framework auth state / project fixture) | asserted |
| 1 Create pipeline, add Custom node via "Add node" → "Custom" | Custom node appears on canvas | step 1 | step 1: `wait_for_node_on_canvas` non-empty id | asserted |
| 2 Verify Custom node appears — examine config panel structure | config panel opens | step 2 | step 2: all base sections visible (label-text/testid checks) | asserted — **CLARIFICATION: no click-to-open action exists, config is always inline; case's "config panel opens" phrasing is a no-op — it is already open. Same reverse-masking pattern already tracked for every other pipeline-node case in this suite.** |
| 3 Configure Custom node fields (Type + Value for input mapping, Input, Output) | fields accept configuration | step 3 (a/b/c) | step 3: Toolkit/Tool combobox text, Type select text, Value `input_value()` | asserted — **CLARIFICATION: "Type + Value for input mapping" is only reachable once a Toolkit+Tool are selected — this AFS's step 1b/3a/3b make that explicit precondition/setup an executed, verified part of the flow rather than an assumed given.** |
| 4 Set Input and Output comboboxes with state variables | configured | step 4 | step 4: combobox text | asserted |
| 5 Save pipeline | saves without errors | step 5 | step 5: no console errors, no failed requests, 2xx | asserted |
| 6 Reload — verify all Custom node fields persist | all persisted | step 6 | step 6: live UI round-trip of Toolkit/Tool/Input-mapping value/Input/Output | asserted |
| Expected Final State: Custom node configured with all available fields, persists after reload | — | steps 5–6 | steps 5–6 | asserted |
| Pass/Fail: all steps complete without errors; all fields persist | — | all steps | all steps | asserted |

### Axis 2 — Analyst/Implementer additions

- Step 2 additionally asserts Tool/INPUT MAPPING are **absent** before a
  Toolkit is selected (a negative/absence check) — *added for the same
  reason already documented for the Toolkit-node AFS: without this negative
  assertion, the two-stage reveal (Toolkit select → Tool+mapping appear) is
  a documented assumption rather than a test-enforced contract.*
- Step 2 additionally asserts the node's raw-JSON editor view (`CustomNodeInput.jsx`)
  is visible inline — *added because this view is unique to the Custom node
  among every other node type in this suite (every sibling node's config is
  purely structured fields), and the case's own step 2 ("examine config
  panel structure") is broad enough to cover it; omitting it would leave a
  materially different piece of this node's UI completely untested.*
- Step 6 additionally asserts the raw-JSON editor view reflects the SAME
  persisted state as the structured fields (`"tool": "search_issues"` and
  the input-mapping value both present in its text) — *added to guard
  against the two views drifting apart on save/reload, a regression class
  no other node type in this suite can exhibit (they have no raw-JSON dual
  view).*
- No console-error / no-failed-request assertion was in the original case
  text; added it to step 5 (checked across the whole flow) — *standard
  practice per this project's `test-case-analysis` skill; zero console
  errors and zero ≥400 responses were observed across every run this
  session.*

## Cleanup

1. This session created one throwaway pipeline + one throwaway GitHub
   credential/toolkit on the local DEV backend (project `UI Testing`) via
   direct UI exploration (manual add of a "Custom" node to the pre-existing
   "Pipeline UI Testing" pipeline, never saved — no persisted change) plus
   the automated test's own fixture-created data, both cleaned up by the
   test's own teardown (`pipeline_id` deletes the pipeline;
   `github_toolkit_with_selected_tools` deletes the toolkit + credential).
2. Implementer teardown: the `pipeline_id` + `github_toolkit_with_selected_tools`
   fixtures (both pre-existing, `automation/fixtures/data_fixtures.py`)
   fully cover setup/teardown — no new fixture needed.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Custom node on canvas | `.react-flow__node-custom` / `[data-testid="rf__node-Custom 1"]` (dynamic, ReactFlow's own testid convention) | **on-main ✓** — ReactFlow-injected, library-owned, sanctioned #579 third-party-widget exception (same as every other node type in this suite); confirmed live via `wait_for_node_on_canvas("custom")` | none needed |
| Custom node Toolkit select | `[data-testid="pipeline-custom-node-toolkit-select"]` | **needs-adding → added this session** via `add-data-testid`: `DefaultNode.jsx` gained a `TEST_ID_PREFIX_BY_NODE_TYPE` map (mirrors `BaseToolNode.jsx`'s existing map for Toolkit/MCP) gated to `type === 'custom'`; wired via `FlowEditorSelect.ToolSelect`'s existing `data-testid` prop — confirmed already-forwarded via source read, zero shared-component change needed. Committed to `automation/testids`. | none — flag closed |
| Custom node Tool select (conditionally rendered) | `[data-testid="pipeline-custom-node-tool-select"]` | **needs-adding → added this session**, wired via the inline `SingleSelect`'s existing `data-testid` prop, same mechanism as the Toolkit node's Tool select. | none — flag closed |
| Custom node Input select | `[data-testid="pipeline-custom-node-input-select"]` | **needs-adding → added this session**, `FlowEditorSelect.InputSelect`'s existing `dataTestId` prop (already forwards to `data-testid` — confirmed via source, same as the Toolkit/Router/MCP node AFS's). | none — flag closed |
| Custom node Output select | `[data-testid="pipeline-custom-node-output-select"]` | **needs-adding → added this session**, `FlowEditorSelect.OutputSelect`'s existing `dataTestId` prop, same mechanism. | none — flag closed |
| Custom node INPUT MAPPING (required N) heading | `[data-testid="pipeline-custom-node-input-mapping-heading"]` | **needs-adding → added this session**, `FlowEditorSettings.InputMapping`'s existing `requiredHeadingTestId` prop (same shared `InputMapping.jsx` component the Toolkit node's AFS documents). | none — flag closed |
| Custom node INPUT MAPPING (optional N) heading | `[data-testid="pipeline-custom-node-input-mapping-optional-heading"]` | **needs-adding → added this session**, `InputMapping.jsx`'s existing `optionalHeadingTestId` prop. | none — flag closed |
| Custom node INPUT MAPPING Type select (dynamic, per parameter) | `[data-testid="pipeline-custom-node-input-mapping-type-{param_name}"]` (e.g. `...-search_query`) | **needs-adding → added this session**, `InputMapping.jsx`'s existing `typeTestIdPrefix` prop, same dynamic-template mechanism already proven for the Toolkit/MCP nodes. | none — flag closed |
| Custom node INPUT MAPPING Value field (dynamic, per parameter) | `[data-testid="pipeline-custom-node-input-mapping-value-{param_name}"]` | **needs-adding → added this session**, `InputMapping.jsx`'s existing `valueTestIdPrefix` prop, same mechanism. | none — flag closed |
| Custom node Interrupt after toggle | `[data-testid="pipeline-custom-node-interrupt-after-toggle"]` | **needs-adding → added this session**, `CommonInterruptSettings.jsx`'s existing `interruptAfterTestId` prop. | none — flag closed |
| Custom node Structured output toggle | `[data-testid="pipeline-custom-node-structured-output-toggle"]` | **needs-adding → added this session**, `CommonInterruptSettings.jsx`'s existing `structuredOutputTestId` prop. | none — flag closed |
| Custom node raw-JSON editor content (`CustomNodeInput.jsx`, unique to this node) | `[data-testid="pipeline-custom-node-json-editor-content"]` | **needs-adding → added this session**: `Field.CodeMirrorEditor`'s existing `contentTestId` prop (already used by 6+ other CodeMirror instances across the codebase — `toolkit-raw-json-editor-content`, `skill-instructions-editor-content`, etc. — confirmed via `grep -rn "contentTestId=" src/`) sets `data-testid` directly on the `.cm-content` DOM node CodeMirror renders internally; `CustomNodeInput.jsx` did not forward this prop from its caller before this session — a one-line addition (`contentTestId={contentTestId}` on the `Field.CodeMirrorEditor` call, plus destructuring `contentTestId` from `props`), no shared-component change. Read via `text_content()`, NOT `input_value()` (CodeMirror is not a native input/textarea — matches this project's existing CodeMirror-content-reading convention, e.g. `mcp_form_page.py`'s YAML editor methods). | none — flag closed |
| Node Interrupt-before toggle (dynamic, node-id-keyed, shared across node types) | `[data-testid="pipeline-node-interrupt-before-toggle-{node_id}"]` | **on-main ✓** — pre-existing, shared across every node type (reused unmodified via `is_node_interrupt_before_toggle_visible`). | none needed |
| TOOLS section "+ Toolkit" popper + attached-toolkit card | `[data-testid="agent-add-toolkit-button"]`, `[data-testid="toolkit-search-input"] input`, `[data-testid="toolkit-menu-item"]`, `[data-testid="agent-toolkit-card"]` | **on-main ✓** — pre-existing, reused unmodified via `open_toolkit_popper()` / `select_toolkit_in_popper()` / `is_toolkit_attached()` (same methods the Toolkit-node AFS documents). | none needed |
| Select-dropdown options (Toolkit name / Tool name / F-String / state var) | `[data-testid="select-option-{value}"]` | **on-main ✓** — pre-existing (`SingleSelectMenuItem.jsx`'s default testid convention), reused unmodified. | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` | **on-main ✓** — pre-existing, reused unmodified. | none needed |

**Implementation status:** every `needs-adding` row above was implemented in
this same session (combined analyst+implementer slot) via direct edits to
`DefaultNode.jsx` (new `TEST_ID_PREFIX_BY_NODE_TYPE` map gated to
`type === 'custom'`, wiring 8 already-existing testid props through to the
node's fields) and `CustomNodeInput.jsx` (forwarding a new `contentTestId`
prop to its `Field.CodeMirrorEditor`). All 10 new testids were confirmed
live (via `document.querySelectorAll` after HMR) before the Playwright test
was written, and the test itself passed green twice consecutively against
them. Committed and pushed to `EliteaAI/EliteaUI`'s `automation/testids`
integration branch — see the closure record for the commit SHA.

## Network Behavior
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires
  on Save click (step 5); persists the Custom node's full config (`toolkit_name`,
  `tool`, `input_mapping`, `input`, `output`) as part of the pipeline's YAML
  `instructions` field. Confirmed live: 2xx.
- `GET .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires
  on page load/reload (step 6); the Custom node's rendered config (both the
  structured fields and the raw-JSON editor view) is parsed from this
  response's YAML `instructions`.

## Known Defects Found During Exploration

None. Once the toolkit-attach precondition is satisfied (same precondition
the Toolkit-node case ELITEA-2010 already documents), all 6 case steps
(plus this AFS's setup step 1b) produced the expected result: Custom node
adds cleanly, Toolkit/Tool selects populate and select correctly, INPUT
MAPPING sections correctly split into REQUIRED/OPTIONAL with the tool's
actual parameters, Type+Value in the required section updates correctly,
Input/Output comboboxes work identically to every other node type's, Save
returns a 2xx, and every field — including the node's unique raw-JSON
editor view — persists through a full page reload. Zero console errors,
zero failed (≥400) requests, across both runs this session.

One case-text CLARIFICATION (not a defect), filed inline in the Coverage
Map rather than as a separate ticket (matches the established pattern
already used for the identical finding on the Toolkit-node and Router-node
sibling cases — same class, fourth+ confirmed instance in this suite):
the case's precondition/step-3 wording implies "Type + Value for input
mapping" is directly configurable with no setup; live product requires a
Toolkit (with `selected_tools`) to be attached and selected first — a real,
expected two-stage progressive-disclosure precondition, not a rendering
defect.

## Blocked Steps

None. All 6 case steps (plus this AFS's setup step 1b) were executed to
completion against the live local environment — both via direct manual
exploration (add-node menu, testid verification via `document.querySelectorAll`
after HMR) and via the final automated Playwright test, which passed green
twice consecutively (`HEADLESS=true pytest tests/ui/pipelines/test_pipeline_custom_node_configuration.py`).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` — this case
  required `add-data-testid` work, done in this same session (see Concrete
  Handles). All 8 of the Custom node's interactive fields plus its unique
  raw-JSON editor view now carry stable testids, following the EXACT same
  prop-wiring mechanism already proven for the Toolkit node (ELITEA-2010) —
  every prop used (`data-testid` on `ToolSelect`/`SingleSelect`, `dataTestId`
  on `InputSelect`/`OutputSelect`, `valueTestIdPrefix`/`typeTestIdPrefix`/
  `requiredHeadingTestId`/`optionalHeadingTestId` on `InputMapping`,
  `interruptAfterTestId`/`structuredOutputTestId` on
  `CommonInterruptSettings`) was ALREADY SUPPORTED by the shared component —
  no shared-component API changes were needed, only wiring at the
  `DefaultNode.jsx` call site (mirroring `BaseToolNode.jsx`'s existing
  pattern) plus one new prop (`contentTestId`) added to `CustomNodeInput.jsx`
  itself (the one field unique to this node type).
- New page-object surface added: `automation/pages/pipeline_detail_page.py`
  gained a `custom_node_*` `LocatorDescriptor` block + methods
  (`get_custom_node_toolkit_value`, `select_custom_node_toolkit`,
  `select_custom_node_tool`, `is_custom_node_input_mapping_section_visible`,
  `select_custom_node_input_mapping_type`, `fill_custom_node_input_mapping_value`,
  `select_custom_node_input_variable`, `select_custom_node_output_variable`,
  `get_custom_node_json_editor_text`, etc.) — a straight parallel of the
  existing `toolkit_node_*` methods, same shape, different testid prefix.
  Purely additive: no existing method body was touched.
- Wait strategy: wait for the `PUT .../application/prompt_lib/{project}/{pipeline_id}`
  response before reloading/asserting persistence — not a fixed timeout
  (`save_and_wait_for_update()`, existing method, reused unmodified).
- The toolkit-attach popper's list can take several seconds to resolve past
  "Loading..." on this environment — reused the existing 20s timeout
  constant/pattern from the Toolkit-node test rather than a short fixed wait.
