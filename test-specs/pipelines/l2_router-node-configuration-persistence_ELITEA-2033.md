# Test Case: Pipeline — Router Node Configuration

## Metadata
- **TMS ID**: ELITEA-2033
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: none needed — localhost `VITE_DEV_TOKEN` auto-auths, no explicit login step
- **Analyst**: qa-engineer (agent), session 2026-07-24
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline exists with a state variable `input` and target nodes for routing.
  Confirmed live (source: `useNodeOptions.hooks.js`) that a node's ROUTES /
  Default-output option list is populated purely from **other existing node
  ids in the pipeline** (`{ label: node.id, value: node.id }`) plus a
  synthetic `END` entry — it is **not** a free-text field. This means the
  case's literal test-data values `approve`/`reject` must be actual node ids
  already present in the pipeline, not typed strings. Confirmed separately
  (source: `useInputOptions.hooks.js`, same finding as ELITEA-2004/2014/
  GAP-007) that `input`/`messages` are available in the Input combobox on
  **any** pipeline with no explicit `state:` YAML block at all — no state
  seeding is required to satisfy "state variable `input` exists."

## Test Data

### reuse-existing
- `input`/`messages` implicit built-in state variables (no seeding needed,
  see Preconditions).

### generate-per-test (in test setup, cleaned up in its own teardown)
- Two target nodes literally named `approve` and `reject`, pre-seeded via
  `PipelineAPI.create_pipeline_with_nodes()` **so their ids match the case's
  test data exactly** — sidesteps a UI rename detour (see Blocked Steps /
  Axis 2 for why renaming via the UI is fragile and unnecessary here):
  ```python
  nodes = [
      {
          "id": "approve",
          "type": "printer",
          "input_mapping": {"printer": {"type": "fixed", "value": "Approved"}},
          "transition": "END",
      },
      {
          "id": "reject",
          "type": "printer",
          "input_mapping": {"printer": {"type": "fixed", "value": "Rejected"}},
          "transition": "END",
      },
  ]
  pipeline = pipeline_api.create_pipeline_with_nodes(
      name, description, entry_point="approve", nodes=nodes
  )
  ```
  Confirmed live that arbitrary (non-type-prefixed) node ids are accepted by
  the API/YAML layer without any validation error — the `{Type} {N}` naming
  convention (`Printer 1`, `Router 1`, …) is purely a UI-generated DEFAULT
  name assigned by the "Add node" menu, not a schema constraint (also used
  by the existing `_printer_node()`/`_router_node()` helpers in
  `tests/api/export_import/test_export_import_pipelines.py`).

### Test Data values (from case, resolved to concrete values used)
| Field | Value |
|---|---|
| Condition (Jinja) | `{% if 'yes' in input %}approve{% else %}reject{% endif %}` |
| Routes | `approve`, `reject` (pre-seeded node ids, see above) |
| Input variable | `input` |
| Default output | `END` |

## Test Steps

1. Create a pipeline and add a Router node via "Add node" → "Router".
   - **Verify**: a Router-type node (`[data-testid="rf__node-{id}"]`, e.g.
     `rf__node-Router 1` — ReactFlow's own testid) appears on the canvas.
     Confirmed live: the node's config (Condition, Routes, Input, Default
     output) is rendered **always inline/expanded** — no click-to-open step,
     identical finding to every other node type explored on this surface
     (LLM/MCP/HITL, ELITEA-1954/2004/2014).
2. Verify Router node panel shows: Condition (Jinja template text area),
   Routes (combobox), Input combobox, Default output dropdown.
   - **Verify**: confirmed live via a full `textContent` dump of the fresh
     node immediately after adding it: `Router 1ConditionRoutes​Input​Default
     outputENDInputOutputDefault output` — all four sections present with
     zero interaction. `Default output` already **displays** `END` before
     any click (see step 6's clarification below — display default ≠
     persisted value).
3. In "Condition" field enter Jinja template:
   `{% if 'yes' in input %}approve{% else %}reject{% endif %}`.
   - **Verify**: the field is `AIAssistantInput` → a real `<textarea
     name="condition">` (native, auto-generated MUI id, e.g. `:r6t:` — not
     label-derived, no collision risk). Typed via real keyboard events
     (`type` command); read back via `textarea.value` immediately after —
     exact match, no truncation/mangling of the Jinja syntax (quotes,
     braces, `%` delimiters all preserved verbatim).
4. In Routes combobox add route values: `approve`, `reject`.
   - **Verify**: opened the combobox (native id `simple-select-Routes`, no
     `data-testid`) — options rendered were exactly `Printer 1`/`Printer 2`/
     `END` in this session's exploration pipeline (analogous to `approve`/
     `reject`/`END` under the recommended precondition setup above), each
     carrying the existing shared testid `select-option-{node_id}` (e.g.
     `select-option-approve`). Selected both non-END options — the field is
     a genuine multi-select (chips render for each selection, each with its
     own remove `⊗` icon); the combobox stays open between selections
     (confirmed: selected the first option, then the second, without
     needing to reopen the menu).
5. Set Input combobox to state variable `input`.
   - **Verify**: opened the combobox (native id `simple-select-Input`),
     options were exactly `input`/`messages` (the implicit built-ins, no
     seeding needed — see Preconditions), each with the shared
     `select-option-{value}` testid. Selected `input` — rendered as a
     removable chip, same pattern as the Routes field.
6. Set "Default output" dropdown to "END".
   - **Verify (CLARIFICATION — see Coverage Map)**: confirmed live that the
     Default-output select **already displays "END"** the instant the node
     is added, with **zero interaction** — source-confirmed
     (`RouterNode.jsx`: `default_output_node = yamlNode?.default_output ||
     'END'`, a client-side JS fallback for the DISPLAY value only). This is
     the same "pre-populated default" pattern already documented for HITL's
     REJECT route (ELITEA-2014). **Critically, the display default and the
     persisted state are NOT the same thing here** — confirmed via the YAML
     view that a freshly-added, never-touched Router node's `default_output`
     key is initialized to an **empty string** (`default_output: ''`,
     `createRouterNodeData()` in `flowEditor.constants.js` — CORRECTED
     during implementation from this AFS's original "no key at all" claim,
     which was inaccurate; the key IS present, just unset), and **no canvas
     edge** renders to END until the field is explicitly (re-)selected. The
     case's step 6 instruction to "set" Default output to END is therefore
     intended as a real, necessary interaction (not a no-op the way it might
     appear from the display alone) — **however, see the CONFIRMED Known
     Defect below (`EliteaAI/elitea-testing-public#1036`): clicking the
     already-visually-selected "END" option on a FRESH node does NOT
     actually write `default_output: END`** (MUI's Select suppresses
     `onChange` when the clicked option's value matches the Select's
     current `value` prop, which is already "END" via the display
     fallback) — this AFS's original claim that a clean single click
     persists it was based on a repro that (unknowingly) selected a
     DIFFERENT value first; see Known Defects Found for the full
     correction.
7. Save pipeline.
   - **Verify**: clicked Save (`agent-save-button` testid, shared with the
     Agent form). Confirmed zero `error`-level console messages across the
     full configure→Save cycle.
8. Reload — verify Condition text, Routes values, Input, and Default output
   persist.
   - **Verify**: performed a genuine hard `reload` (not a client-side tab
     switch) after Save. Confirmed via a direct Flow-view field read
     immediately after reload: Condition text-area = full Jinja string
     unchanged; Routes chips = both pre-seeded target node ids, unchanged;
     Input chip = `input`, unchanged; Default output = `END`, unchanged.
9. Verify canvas shows edges from Router to target nodes matching route
   values.
   - **Verify**: confirmed via `.react-flow__edge[data-testid]` enumeration,
     both before AND after the reload (identical set both times):
     - `rf__edge-xy-edge__Router 1---Printer 1` (Routes edge, target 1)
     - `rf__edge-xy-edge__Router 1---Printer 2` (Routes edge, target 2)
     - `rf__edge-xy-edge__Router 1default_output---END` (Default-output edge)
     **Edge-testid format differs between the two edge KINDS** — both
     Routes edges use a **triple-dash** separator (`Router 1---Printer 1`,
     no handle suffix embedded even though the underlying `sourceHandle`
     state value is the shared `routerNode_routes` string for both), while
     the Default-output edge embeds the literal handle name **directly
     before** the triple-dash (`Router 1default_output---END`). See
     Automation Hints for the exact implication on the existing
     `edge_exists()` page-object helper.

## Expected Results
- Adding a Router node renders its full config (Condition, Routes, Input,
  Default output) inline immediately — no separate open/expand action.
- Condition accepts an arbitrary Jinja template string verbatim, via a real
  textarea (no CodeMirror/rich-editor quirks to route around).
- Routes and Default output are NOT free-text fields — both are selects
  whose options are the pipeline's OTHER existing node ids plus a synthetic
  `END` entry; typing/selecting "approve"/"reject" requires those to already
  exist as real node ids in the pipeline.
- Default output visually defaults to "END" before any interaction, but this
  is a display-only JS fallback — the case's step 6 instruction to select it
  is a required, real interaction. **CONFIRMED DEFECT**
  (`EliteaAI/elitea-testing-public#1036`, found during implementation): on a
  FRESHLY-ADDED node, clicking the already-displayed "END" option is a
  silent no-op — MUI's Select suppresses `onChange` because the clicked
  option's value already matches the Select's current `value` prop (the
  display fallback) — so `default_output: END` is NOT persisted into the
  YAML and its canvas edge does not survive a reload. This is the one real
  reverse-masking-guard-relevant nuance in this case, and it is a confirmed,
  filed, isolated defect — not a pass.
- Save completes with no console error; a hard reload re-shows the
  Condition, Routes, and Input fields exactly as saved, and the 2 Routes
  canvas edges persist identically across the reload. The Default-output
  edge does NOT persist across the reload (see the confirmed defect above)
  — only 2 of the 3 canvas edges survive.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipeline with state var `input` + target nodes for routing | preconditions satisfied | Preconditions / Test Data | `input` confirmed implicit-builtin (no seeding); `approve`/`reject` pre-seeded via `create_pipeline_with_nodes()` | asserted |
| 1 Create pipeline + add Router node via Add node → Router | Router node appears on canvas | step 1 | step 1: `rf__node-Router 1` visible | asserted |
| 2 Verify panel shows Condition/Routes/Input/Default output | all listed sections present | step 2 | step 2: full node `textContent` dump confirms all four sections, zero interaction | asserted |
| 3 Enter Jinja condition | Condition field accepts template | step 3 | step 3: `textarea.value` read-back, exact match | asserted |
| 4 Add route values approve/reject | both route values added | step 4 | step 4: chips rendered for both selections, `select-option-{id}` testid confirmed | **CLARIFICATION** — "route values" are existing node ids selected from a combobox, not free-typed strings; case text's phrasing ("add route values") could be misread as a text-entry action. Asserted as the live product behaves. |
| 5 Set Input to `input` | Input set to `input` variable | step 5 | step 5: chip `input` rendered | asserted |
| 6 Set Default output to END | Default output set to END | step 6 | step 6: display-default pre-check (no edge yet) + the explicit selection is performed; persistence proof deferred to the test's final Known-defect step (YAML `default_output` + canvas edge, post-Save/post-reload) | **CLARIFICATION + CONFIRMED DEFECT** (`EliteaAI/elitea-testing-public#1036`) — the field VISUALLY shows END with zero interaction (JS display fallback); the case's instruction to "set" it is performed as a real interaction, but on a FRESHLY-ADDED node this specific click is a silent no-op (MUI's Select suppresses `onChange` because the current `value` prop already equals "END") — `default_output` is NOT persisted and its edge does not survive a reload. Asserted as the correct expected behavior via a deferred, isolated Known-defect check (sanctioned-RED exception, `.agents/testing.md` § Merge gate), not worked around. |
| 7 Save pipeline | saves without errors | step 7 | step 7: zero console errors | asserted |
| 8 Reload — verify Condition/Routes/Input/Default output persist | all fields restored | step 8 | step 8: Flow-view field read-back + YAML corroboration post-reload for Condition/Routes/Input (3 of the 4 fields); Default output's read-back is deferred to the test's final Known-defect step (see row 6 / Known Defects) — NOT asserted in this step's own block | Condition/Routes/Input asserted; Default output is a **CONFIRMED DEFECT** (`EliteaAI/elitea-testing-public#1036`) — deferred, not asserted here |
| 9 Verify canvas edges from Router to target nodes matching routes | edges connect Router to approve/reject targets | step 9 | step 9: `edge_exists()` for both Routes edges, asserted ONCE after the Step-8 reload (post-save, post-reload) — satisfies the case's own step 9, which follows step 8 in sequence. No separate pre-save Routes-edge check exists in the shipped test (only the Default-output edge gets an explicit pre-check, at Step 6 — see that row); the AFS's own live-exploration narrative (Test Steps, step 9 body) checked both pre- and post-reload during analysis, but that is analyst methodology, not a claim about what the automated test asserts | asserted |
| Expected Final State: Router fully configured, all persisting after save+reload, canvas edges reflect routes | — | steps 3–9 | steps 3–9 | Condition/Routes/Input + their 2 Routes edges: asserted. Default output + its edge: **CONFIRMED DEFECT** (`EliteaAI/elitea-testing-public#1036`) — does NOT reach "fully configured, persisting" on a freshly-added node; see Known Defects |
| Pass/Fail: all steps complete without errors; all fields persist; edges match | — | all steps | all steps | asserted for Condition/Routes/Input/Save/Routes-edges; Default-output persistence + its edge are a **CONFIRMED, filed, isolated defect** (`EliteaAI/elitea-testing-public#1036`) — a deferred Known-defect check per the sanctioned-RED exception, not a pass |

### Axis 2 — Analyst additions

- Step 4 additionally asserts that the Routes combobox is a genuine
  **multi-select that stays open between selections** (no need to reopen
  the menu per route) — *added: directly relevant to the implementer's
  interaction-sequence design, not stated in the case text.*
- Step 6 additionally distinguishes the DISPLAY default ("END" shown with
  zero interaction) from the PERSISTED default (absent from YAML until an
  explicit selection, confirmed via a before/after YAML diff) — *added: the
  single most implementer-relevant nuance in this case; without it, a naive
  implementation might skip the Default-output interaction entirely
  (assuming the visual default already satisfies the case) and then fail
  step 9's edge assertion for the Default-output edge specifically.*
- Step 9 additionally documents the edge-testid FORMAT DIFFERENCE between
  Routes edges (triple-dash, no handle suffix embedded) and the
  Default-output edge (handle suffix embedded before the triple-dash) —
  *added: not stated in the case text at all, but directly determines
  whether the existing `edge_exists()` page-object helper's `handle_suffix`
  parameter can be used safely (see Automation Hints — it cannot, for
  either edge kind, without special care).*
- Verified (not part of the case's own steps, informational) that renaming
  a UI-added node via `edit_node_name()`/double-click is a fragile detour
  for THIS case's precondition (nodes get type-prefixed default names like
  `Printer 1`) — the API-based `create_pipeline_with_nodes()` precondition
  setup recommended above sidesteps this entirely by specifying the exact
  ids `approve`/`reject` directly, which is both simpler and a truer match
  to the case's literal test data. *Added: an execution-path decision, not
  a case requirement, but directly informs the recommended test-data setup.*

## Cleanup

1. If the recommended `create_pipeline_with_nodes()`-based setup is used in
   a fixture, cleanup is automatic via `PipelineAPI.delete_pipeline()`
   (matching the existing `pipeline_id`/`pipeline_with_llm_id` fixture
   pattern in `automation/fixtures/data_fixtures.py`).
2. This analysis session's own manually-built pipeline
   (`AFS-2033-Router-Node`, id `5772`) was left in place for the duration of
   this session only; it should be deleted via `PipelineAPI.delete_pipeline
   (5772)` or the UI's "Delete pipeline" flow as a follow-up if not already
   cleaned up by the time this AFS is picked up for implementation.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance / Notes |
|---|---|---|
| Router node container | `[data-testid="rf__node-{id}"]` (ReactFlow's own testid, e.g. `rf__node-Router 1`) | on-main ✓ — third-party (ReactFlow) widget testid, not app-added; already used by existing page-object methods (`wait_for_node_on_canvas`, `get_node_ids`, `connect_nodes`) |
| Condition textarea | **NO `data-testid` today** — native `id` is React-auto-generated (`:r6t:`-style, non-deterministic, do NOT locate by it), `name="condition"` is stable but not testid-only per policy. **Flag to `add-data-testid`**: `RouterNode.jsx`'s `<AIAssistantInput ... />` call spreads `...leftProps` straight onto `Input.InputBase`, which already supports an `inputProps` prop forwarded to the native textarea's `slotProps.htmlInput` (identical wiring point already documented for the LLM node's System/Task/Chat-History Value fields, ELITEA-2004) — add `inputProps={{'data-testid': 'pipeline-router-node-condition-input'}}` at the `RouterNode.jsx` call site. Zero shared-component edits needed. | on-automation/testids only (awaiting human promotion to main) — added EliteaAI/EliteaUI@e5259559 |
| Routes combobox (trigger) | **NO `data-testid` today** — native id `simple-select-Routes` (label-derived, not testid-only). **Flag to `add-data-testid`**: unlike Input/Default-output below, `FlowEditorSelect.RouteSelect` (`ui/select/RouteSelect.jsx`) does **not yet destructure/forward a `dataTestId` prop at all** — it needs a NEW prop threaded through to its inner `Select.SingleSelect` call (same one-line pattern already used by `InputSelect.jsx`: destructure `dataTestId`, pass `data-testid={dataTestId}` to `Select.SingleSelect`), THEN `RouterNode.jsx`'s `<FlowEditorSelect.RouteSelect id={id} label="Routes" fieldName="routes" ... />` call needs `dataTestId="pipeline-router-node-routes-select"` added. Two small edits (component + call site), still zero shared-`SingleSelect`-internals changes. | on-automation/testids only (awaiting human promotion to main) — added EliteaAI/EliteaUI@e5259559 |
| Routes/Input/Default-output open-listbox option (per node id / state var) | `[data-testid="select-option-{value}"]` — e.g. `select-option-approve`, `select-option-reject`, `select-option-END`, `select-option-input` (existing `SELECT_OPTION` class constant already in `pipeline_detail_page.py`) | on-main ✓ — same shared mechanism as ELITEA-2004/1954/2014, confirmed live for router-specific values too |
| Input combobox (trigger) | **NO `data-testid` today** — native id `simple-select-Input` (same string as the LLM/MCP node's own Input select — cross-node-type duplicate-id family, same root cause as already-filed `EliteaAI/elitea-testing-public#1006`, NOT re-filed). **Flag to `add-data-testid`**: `FlowEditorSelect.InputSelect` (`ui/select/InputSelect.jsx`) **already supports** a `dataTestId` prop (destructures it, forwards as `data-testid={dataTestId}` to `Select.SingleSelect`) — the ONLY missing piece is passing it at the call site: `RouterNode.jsx`'s `<FlowEditorSelect.InputSelect id={id} label="Input" inputFieldName="input" disabled={...} />` needs `dataTestId="pipeline-router-node-input-select"` added. Zero component-internals edits needed — same one-line-fix shape already used for the LLM node (ELITEA-2004). | on-automation/testids only (awaiting human promotion to main) — added EliteaAI/EliteaUI@e5259559 |
| Default output dropdown (trigger) | **NO `data-testid` today** — native id `simple-select-undefined` (worse than the ordinary duplicate-string case: `RouterNode.jsx` passes `labelNode={<Chip.HeadingChip label="Default output" />}` instead of a plain `label` string, so `SingleSelect.jsx`'s `id={id \|\| 'simple-select-' + label}` default coerces the missing `label` to the literal string `"undefined"` — same root-cause FAMILY as `#1006`/`#1009`, not a new bug, not re-filed). **Flag to `add-data-testid`**: this field is a bare inline `<SingleSelect labelNode=... value=... onValueChange=... options=... .../>` call in `RouterNode.jsx` (not routed through `InputSelect`/`RouteSelect`) — `SingleSelect.jsx` already supports a `data-testid` prop directly (destructured as `'data-testid': dataTestId`), so simply add `data-testid="pipeline-router-node-default-output-select"` straight onto this call. Zero shared-component edits, zero new prop threading — the SIMPLEST of the four fields to wire. | on-automation/testids only (awaiting human promotion to main) — added EliteaAI/EliteaUI@e5259559 |
| Save button | `[data-testid="agent-save-button"]` (shared with the Agent form's Save button) | on-main ✓ — pre-existing, already used by `PipelineDetailPage` |
| Routes edge (Router → route target) | `[data-testid="rf__edge-xy-edge__{router_id}---{target_id}"]` — e.g. `rf__edge-xy-edge__Router 1---Printer 1` — **triple-dash separator, NO handle suffix embedded** even though the underlying edge's `sourceHandle` state value is the shared `routerNode_routes` string for every route | on-main ✓ — ReactFlow's own rendered testid (`EDGE_PREFIX = 'xy-edge__'` + `${id}---${value}`, `flowEditor.constants.js`); confirmed live for 2 simultaneous route edges |
| Default-output edge (Router → default target) | `[data-testid="rf__edge-xy-edge__{router_id}default_output---{target_id}"]` — e.g. `rf__edge-xy-edge__Router 1default_output---END` — handle name `default_output` embedded directly before the triple-dash | on-main ✓ — same ReactFlow mechanism, distinct edge-id template (`${id}default_output---${value}`, `RouterNode.jsx`'s `handleDefaultOutput`) |

## Network Behavior

No network call is central to this case's own field-level assertions while
configuring the node — Condition/Routes/Input/Default-output edits are pure
client-side React state (`yamlJsonObject`) until Save. The Save action PUTs
the same `application` entity endpoint already used by
`PipelineAPI.update_pipeline()` (`automation/api/client.py:658`) — same
pattern as ELITEA-2004/1954/2014. No new network assertion is required; the
implementer's persistence check should assert on UI-visible state (Flow-view
fields) and/or the YAML view after a real page reload, matching Test Steps
7–9, not on the raw PUT response body.

## Known Defects Found During Exploration

**CONFIRMED — filed as `EliteaAI/elitea-testing-public#1036`** (found during
implementation, not this analysis session; documented here per team
convention for AFS corrections). This supersedes the "not a product defect"
conclusion below — the analyst's own clean repro ("confirmed twice: once
selecting a non-END value, once selecting END again") accidentally exercised
a DIFFERENT transition (non-END → END, a genuine value change) rather than
the case's literal first action on a fresh node (END → END, since the
display already shows END). The two are not equivalent:

- On a **freshly-added** Router node, clicking the "END" option in Default
  output — the case's own literal step 6 action, and the single most
  natural thing a user would do — is a **silent no-op**. Confirmed via 3
  independent reads (immediate, after an extra 1.5s settle, and the actual
  Save PUT payload + a direct API refetch): all show `default_output: ''`
  even though the display continues to show "END" and a canvas edge
  (`rf__edge-xy-edge__{id}default_output---END`) is drawn — that edge is a
  client-side-only `flowEdges` artifact, not backed by any real
  `default_output` value, and does not survive a reload.
- Root cause (source-confirmed): `RouterNode.jsx` displays
  `yamlNode?.default_output || 'END'` as a fallback for the freshly-
  initialized empty value; MUI's `SelectInput.js` (`handleItemClick`) only
  fires `onChange` when the clicked option's value differs from the
  Select's current `value` PROP — since that prop is already the fallback
  string `"END"`, clicking the "END" option is `value !== newValue` ⇒
  `false`, so `onChange` (and therefore `handleDefaultOutput`, the only
  code path that persists this field) never fires.
- Implication for the case: selecting a DIFFERENT value first, then
  re-selecting "END", DOES persist correctly (a genuine value transition) —
  this is the AFS's own accidental repro path and is documented as the
  *workaround* in the filed issue, not a substitute for testing the case's
  literal instruction. The implementer's test performs the literal action
  and asserts the correct expected behavior (not worked around), isolating
  the resulting failure as a deferred, clearly-labeled Known-defect check
  per `.agents/testing.md` § Merge gate's sanctioned-RED exception —
  confirmed deterministic across 3 separate local runs (identical single
  assertion, identical failure).

Two PRE-EXISTING, already-filed, non-blocking defects are relevant to
locator choice only (same root-cause family as HITL/LLM findings,
independently re-confirmed live this session on the Router node's own
selects, NOT re-filed):
- `EliteaAI/elitea-testing-public#1006`/`#1009` (duplicate `SingleSelect`
  default-id pattern) — confirmed on Router's `simple-select-Input` (shares
  the literal string with the LLM/MCP node's own Input select) and
  `simple-select-undefined` (Default output, via the `labelNode`-instead-
  of-`label` variant of the same root cause).

## Blocked Steps

None. All 9 case steps (plus the stated precondition) were executed to
completion against the live local environment, including a genuine
configure→Save→hard-reload→verify round trip, corroborated by both
Flow-view field reads and direct `.react-flow__edge` DOM enumeration
before and after the reload.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`). **This case requires `add-data-testid` work** for
  all four Router-node fields (Condition, Routes, Input, Default output) —
  all four have a trivial existing extension point, though Routes needs one
  extra step (new prop threading in `RouteSelect.jsx` itself, not just the
  call site) versus Input/Default-output (call-site-only) and Condition
  (call-site-only via `inputProps`). See Concrete Handles for exact
  line-level wiring points.
- **Reverse-masking-guard-relevant nuance (see Step 6 / Axis 1)**: do NOT
  skip the Default-output interaction just because the field visually shows
  "END" on a freshly-added node — that is a display-only fallback. The test
  MUST perform an explicit select-"END" interaction and then assert BOTH
  the YAML `default_output: END` key AND the
  `rf__edge-xy-edge__{id}default_output---END` canvas edge; asserting only
  the visual display value would pass vacuously even if the underlying
  persistence/edge-creation logic were broken — **and it currently IS
  broken**: `EliteaAI/elitea-testing-public#1036` (confirmed during
  implementation) — the explicit selection on a freshly-added node is a
  silent no-op, so both the YAML-key and canvas-edge assertions above are a
  deferred, isolated Known-defect check (sanctioned-RED exception) rather
  than a pass, until the product fix ships.
- **`edge_exists()` usage — call WITHOUT `handle_suffix` for BOTH Router
  edge kinds.** The existing `PipelineDetailPage.edge_exists(source_id,
  target_id, handle_suffix=None)` helper's `handle_suffix`-aware branch
  builds `expected_prefix = f"rf__edge-xy-edge__{source_id}{handle_suffix}-
  {target_id}"` (SINGLE dash before the target). Router's actual edge
  testids use a **TRIPLE dash** in both cases (`{source}---{target}` for
  Routes edges, `{source}{handle}---{target}` for the Default-output edge)
  — passing `handle_suffix="default_output"` would make the prefix check
  fail (`"...default_output-END"` does not match the start of
  `"...default_output---END"`). Calling `edge_exists(router_id, target_id)`
  **without** `handle_suffix` uses the fallback branch instead
  (`expected_prefix = f"rf__edge-xy-edge__{source_id}"`, plus a
  `f"-{target_id}" in testid` substring check), which correctly matches
  BOTH edge kinds as confirmed live. This is a real usage gotcha for this
  case specifically, not a bug in the helper (the helper was designed
  against HITL's edge-id shape, which differs from Router's).
- **Synthetic-vs-real-click hygiene** (see Known Defects): never mix a
  probing `page.evaluate("el => el.click()")` with a subsequent real
  Playwright `.click()` on the same MUI `Select` trigger within one test —
  use ONE clean interaction path per select (open → read options → click
  the target option, all via Playwright's native click/locator API).
- Recommended setup: extend `automation/fixtures/data_fixtures.py` with a
  new fixture (e.g. `pipeline_with_route_targets_id`) built on
  `PipelineAPI.create_pipeline_with_nodes()` per the Test Data section
  above — mirrors the existing `pipeline_with_llm_id` pattern, yields the
  pipeline id, cleans up via `delete_pipeline()`.
- New page-object surface needed: `PipelineDetailPage` has generic node
  methods (`add_node`, `wait_for_node_on_canvas`, `get_edge_count`,
  `edge_exists`) and MCP/LLM/HITL-node-specific methods, but nothing for a
  Router node's Condition/Routes/Input/Default-output fields. Suggested
  shape (once testids are added): `set_router_condition(jinja_text)`,
  `select_router_routes(node_ids: list[str])` (multi-select, loop-clicking
  `select-option-{id}` per target), `select_router_input(value)`,
  `select_router_default_output(node_id)`.
- Wait strategy: no network wait needed for the field-edit interactions
  themselves (pure client-side); after clicking Save, follow the existing
  ELITEA-2004/2014 pattern (`wait_for_network()` or wait on Discard-button
  disabled state), then `page.reload()` + re-assert field values and edge
  presence — never a fixed `sleep`.
- Typing the Jinja Condition text: it is a plain `<textarea>` (not
  CodeMirror), so ordinary `press_sequentially()`/`type()` is sufficient —
  none of the f-string-autocomplete-popper gotchas documented for the
  LLM/HITL Value fields apply here (Condition is a raw Jinja text field,
  not an f-string-interpolation field).
