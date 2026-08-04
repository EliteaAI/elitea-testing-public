# Test Case: Pipeline — Decision Node Configuration

## Metadata
- **TMS ID**: ELITEA-2034
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-04
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- **CLARIFICATION on the case's stated precondition** ("A pipeline with state
  variables and branch nodes exists"): live-confirmed this undersells the
  actual setup required —
  - the state variables `normalized_issue`/`metadata_json` are **not** built-in
    (unlike Router's `input`/`messages`) and must be created via the flow
    editor's own `STATE` side panel's "+" control before the Decision node's
    `Input` combobox will list them;
  - the "branch nodes" must be **pre-named to match the exact DECISION OUTPUTS
    values** (`bug_responder`, `feature_responder`, `question_responder`) —
    see step 5's clarification for why. This AFS makes both an explicit setup
    step 0.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- An empty pipeline via the `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`,
  `PipelineAPI`-backed create/delete).
- Two custom state variables added via the flow editor's `STATE` panel:
  `normalized_issue`, `metadata_json` (no type/default value needed — a bare
  name is sufficient for this case).
- Three Printer nodes added via the canvas and **renamed** to `bug_responder`,
  `feature_responder`, `question_responder` (`PipelineDetailPage.add_node("Printer")`
  ×3 + `PipelineDetailPage.edit_node_name(...)`) — these become the Decision
  node's DECISION OUTPUTS targets, same pattern as the Router AFS's `approve`/
  `reject` setup (ELITEA-2033). Printer was chosen as a lightweight,
  already-automated node type; any node type works as a target.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project
  was "Private" (id 399), matching `.env.test` — no project-mismatch repeat of
  the ELITEA-2033 gotcha this time, but the implementer should still verify
  the active project before creating test data (see the Router AFS's
  Automation Hints for the full gotcha writeup; same fixtures avoid it).

## Test Steps

**IMPORTANT — step 0 added ahead of the case's step 1.** The case's
precondition text implies state variables and target nodes already exist;
live behavior requires explicit setup to produce them (see Coverage Map).
This AFS makes that setup step 0 so the implementer's fixture maps 1:1 onto it.

0. **Setup**: create a pipeline; add two custom state variables (`normalized_issue`,
   `metadata_json`) via the `STATE` panel's "+" control; add three Printer nodes
   via the canvas "+" button → "Printer" (`add_node("Printer")` ×3) and rename
   them to `bug_responder`, `feature_responder`, `question_responder` via
   `edit_node_name(node_id, new_name)` (double-click the name label → type →
   click the canvas empty pane to commit).
   - **Verify**: `get_node_ids()` includes exactly `bug_responder`,
     `feature_responder`, `question_responder`; the `STATE` panel lists
     `normalized_issue` and `metadata_json` alongside the built-in `input`/
     `messages`.
1. Add a Decision node via the canvas "+" button → "Decision" (`add_node("Decision")`).
   - **Verify**: node appears on canvas — `wait_for_node_on_canvas("decision")`
     returns a non-empty id (`Decision 1`); node count increased by 1.
2. Observe the Decision node's config (renders **inline on the card itself —
   no click-to-open action needed**, same always-expanded shape as every other
   pipeline node type in this codebase — matches the digest's already-confirmed
   generic finding).
   - **Verify**: sections visible top to bottom: `Input` (multi-select
     combobox), `Description` (a plain multiline textarea, NOT a rich/code
     editor despite `language="jinja"`-style props elsewhere in this node
     family), `Decision outputs` (an initially-EMPTY chip container — no
     add/type control inside it, see step 5's clarification), `Interrupt
     before` / `Interrupt after` switches. All four sections present — matches
     the case's step 2 expectation exactly, no case-text drift on section
     presence.
3. Open the `Input` combobox and select `normalized_issue`, then `metadata_json`.
   - **Verify**: `Input` field shows both as selected chips (textbox value
     becomes `normalized_issuemetadata_json`, concatenated with no separator
     in the DOM text — the underlying MUI multi-select renders each chip as a
     separate element; assert via chip labels, not string-equality on
     `.text_content()`).
4. Fill `Description` with the classification prompt: `Classify this input
   into one category: - bug_responder: reports a defect - feature_responder:
   requests new functionality`.
   - **Verify**: the textarea's value equals the entered string (read via
     `.input_value()` once the testid exists — see Automation Hints on why
     not `.inner_text()`, same reasoning as the Router AFS's Condition field).
5. Add the three DECISION OUTPUTS by **dragging a canvas connection** from the
   Decision node's `Output` source handle (`data-handleid="nodes"`) to each of
   the three renamed target nodes (`connect_nodes("Decision 1", "bug_responder",
   source_handle="nodes")`, then `feature_responder`, then `question_responder`).
   - **Verify**: after each drag, a new chip labeled with the target's name
     appears under `Decision outputs` (`bug_responder`, then
     `feature_responder`, then `question_responder`), AND a canvas edge from
     `Decision 1` to that target appears immediately — no Save needed
     (`edge_exists("Decision 1", "bug_responder")` etc. go true; see
     Automation Hints for the exact-format caveat).
   - **CLARIFICATION on the case's step 5 wording** ("add target node names as
     chips"): `Decision outputs` is **not a typeable/freeform chip input** —
     live-confirmed via source (`DecisionNodeShared.jsx`'s `DecisionOutputs`
     component renders ONLY a heading + an empty bordered box; no `TextField`/
     `Autocomplete` exists inside it) and via live DOM inspection (the
     `Decision outputs` box has zero interactive children until at least one
     output exists). The ONLY confirmed mechanism that adds an output chip is
     dragging a canvas edge from the node's `Output` handle to an existing
     target node (`conditionDecisionBuilders.helpers.js`'s `buildNewDecision`
     appends `connection.target` to the node's `nodes` array on `onConnect`) —
     the chip's label is simply the connected target node's id. This is the
     SAME underlying mechanism as HITL's ROUTER MAPPING, NOT Router node's
     dropdown-picklist `Routes` field (ELITEA-2033) — despite Decision and
     Router both producing "output chips wired to existing node ids," the
     INTERACTION MECHANISM differs (drag-connect vs. select-from-dropdown).
     Not a defect — the case's overall intent (three outputs named to match
     the classification categories) is fully achievable; the wording just
     undersells the mechanism, same class of finding as ELITEA-2033's Routes
     clarification. Each output chip also carries a delete affordance
     (`onRemoveOutput` — an "x" that removes both the array entry and the
     matching edge), not exercised by this AFS (out of the case's scope) but
     available for a future negative-path case.
6. Save the pipeline (`agent-save-button`).
   - **Verify**: no console errors; `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` returns a 2xx (observed live: 201 Created, same as every other pipeline-node AFS in this suite).
7. Reload the page at the pipeline's canonical URL (`/pipelines/all/{id}?destTab=configuration&viewMode=owner`).
   - **Verify**: after reload, the Decision node shows the persisted `Input`
     chips (`normalized_issue`, `metadata_json`), `Description` text, and all
     three `Decision outputs` chips (`bug_responder`, `feature_responder`,
     `question_responder`) — confirmed live via a real `page.reload()`
     (navigation), not just an API read.
8. Verify canvas shows both output handles.
   - **Verify**: the Decision node's rendered text includes the literal labels
     `Output` (the `nodes` source handle's label) and `Default output` (the
     `default_output` source handle's label) — matches the case's step 8
     wording EXACTLY, no case-text drift here (unlike step 5). Both handles
     are present on the node from the moment it's added, independent of
     whether any output/edge has been wired yet.
9. Verify canvas edges after reload (Axis 2 addition — not in the case's
   numbered steps, but implied by "Expected Final State").
   - **Verify**: `Decision 1 → bug_responder`, `Decision 1 → feature_responder`,
     `Decision 1 → question_responder` (the three DECISION OUTPUTS edges) are
     all present post-reload via `edge_exists()` — **see Automation Hints,
     "Edge testid shape changes across save/reload" — this is the single
     most important gotcha in this AFS.**

## Expected Results
- Decision node config renders fully inline on the canvas card (no
  modal/panel to open) — Input, Description, Decision outputs, Interrupt
  before/after all present and independently persist through Save + reload.
- `Decision outputs` is a drag-connect-driven chip list (mechanism = wiring a
  canvas edge from the node's `Output` handle to an existing target node),
  NOT a freeform/typeable field — adding an output requires that target node
  to already exist with a matching name.
- Connecting an `Output`-handle edge wires a real canvas edge immediately
  (before Save) and simultaneously adds the output chip — same
  before-Save-immediacy pattern as Router's Routes field (ELITEA-2033).
- The node exposes exactly two labeled source handles at all times: `Output`
  (bottom-left, `data-handleid="nodes"`, the DECISION OUTPUTS wiring target)
  and `Default output` (bottom-right, `data-handleid="default_output"`,
  present but NOT exercised by this case's numbered steps — the case's own
  step 8 only asserts both handles are VISIBLE, not that a default-output
  edge is wired).
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipeline with state variables and branch nodes exists | setup exists | Preconditions clarification + step 0 | step 0: STATE panel lists both custom vars; `get_node_ids()` includes all 3 renamed targets | asserted — **CLARIFICATION: neither the state variables nor the correctly-named branch nodes exist by default; both need explicit setup the case's precondition text doesn't spell out.** |
| 1 Create pipeline, add Decision node via "Add node" → "Decision" | Decision node appears on canvas | step 1 | step 1: node count + id | asserted |
| 2 Verify Decision node panel shows Input/Description/DECISION OUTPUTS/Interrupt switches | all listed sections present | step 2 | step 2: all 4 sections visible | asserted — no case-text drift, live UI matches exactly (Decision's config, like every node type in this codebase, is always inline, never a click-to-open panel) |
| 3 Set Input combobox with "normalized_issue", "metadata_json" | both variables added to Input | step 3 | step 3: chip labels shown | asserted |
| 4 Fill Description with classification prompt | field accepts the value | step 4 | step 4: `.input_value()` equals entered string | asserted |
| 5 In DECISION OUTPUTS: add target node names as chips | all three output chips added | step 5 | step 5: chips shown + edges appear | asserted — **CLARIFICATION: "add ... as chips" reads as freeform typing; live behavior is drag-connect-from-existing-node. Case's overall intent (three outputs named to match the classification categories) is still fully achievable and is what this AFS's step 0 sets up.** |
| 6 Save pipeline | saves without errors | step 6 | step 6: no console errors, 2xx (201 observed) | asserted |
| 7 Reload — verify Input, Description, DECISION OUTPUTS persist | all fields restored | step 7 | step 7: live UI round-trip of all 3 field groups | asserted |
| 8 Verify canvas shows "Output" and "Default output" handles | both handles visible | step 8 | step 8: node text includes both literal labels | asserted — no case-text drift, matches live UI exactly |
| Expected Final State: fully configured, persists after reload, canvas shows correct output handles | — | steps 6–8 | steps 6–8 | asserted |
| Pass/Fail: all steps complete without errors; fields persist after reload; canvas output handles correct | — | all steps | all steps | asserted |

**CLARIFICATION on precondition + step 5 (DECISION OUTPUTS mechanism):** the
case text implies "target nodes for routing" simply "exist" and that you "add
[them] as chips" into DECISION OUTPUTS as if typing tags. Live-confirmed
(source: `DecisionNodeShared.jsx`'s `DecisionOutputs` component + `conditionDecisionBuilders.helpers.js`'s
`buildNewDecision`) the ONLY mechanism that populates a DECISION OUTPUTS chip
is dragging a canvas edge from the Decision node's `Output` handle to an
EXISTING target node — there is no text input inside the `Decision outputs`
box at all (confirmed both via source read and live DOM inspection: zero
interactive children when the array is empty). To reproduce the case's intent
(outputs named `bug_responder`/`feature_responder`/`question_responder`
matching the classification prompt's categories), the precondition pipeline
must contain nodes literally renamed to those three values. This AFS's step 0
makes that setup explicit. Not filed as a defect — the case's overall intent
is fully achievable, the wording is just imprecise about the mechanism, the
SAME pattern already filed for the sibling Router (ELITEA-2033, issue
`EliteaAI/elitea-testing-public#1144`) and other pipeline node cases
(`#1104`/`#1136`/`#1137`). **Filed as a CLARIFICATION**, see Known Defects
Found During Exploration below.

### Axis 2 — Analyst additions

- Step 5 additionally asserts that connecting a DECISION OUTPUTS edge wires a
  real canvas edge **immediately, before Save** — *added: this is a
  materially different persistence model than "edges appear after Save" and
  is worth guarding against a regression that defers edge creation to
  save-time — same reasoning as the Router AFS's equivalent addition.*
- Step 9 (post-reload edge verification) was added entirely — the case's
  numbered steps stop at step 8 (handle visibility), but "Expected Final
  State" implies the wiring persists too; asserting it closes that gap.
- No console-error assertion was in the original case text; added it
  throughout as a side-channel check — zero console errors were observed in
  this session (both on initial configuration and after reload).
- Step 6 additionally asserts the exact HTTP status (201 Created, observed
  live) rather than a generic "no errors" — *added: pins the exact expected
  status so a future regression to e.g. a 200-with-error-body doesn't
  silently pass a looser "2xx-ish" check. Consistent with every other
  pipeline-node-configuration AFS in this feature area.*
- **Not asserted (deliberately out of this case's scope):** the `Default
  output` handle/field is visible (step 8) but never WIRED by this case — the
  case's own steps never mention setting a default output value, unlike the
  Router case which explicitly exercises it. Left unexercised here rather than
  invented; a future case could add "Decision node default output wiring" as
  its own scenario if desired.

## Cleanup

1. This session created a persistent pipeline (`autotest_decision_2034`, id
   `7452`) on the local DEV backend. **Not deleted at the end of this
   session** — `PipelineAPI` requires a live Playwright `browser_cookies`
   context to instantiate (`PipelineAPI(browser_cookies)`), which this
   analyst session's tooling (Playwright MCP, not a `pytest` fixture context)
   doesn't expose; a same-origin `fetch()` DELETE from the browser console
   also failed (`TypeError: Failed to fetch`, likely a CORS/auth-header gap
   for a raw in-page fetch outside the app's own RTK-Query client). Left in
   place — same precedent as several other analyst-session pipelines already
   visible in this project's `Pipelines: all` list (`probe-pipeline`,
   `debug_router_manual`, `FullDetailsPipe_probe`, `FullDetailsPipe_probe2`).
   Flagging for the implementer/lead: if a cleanup sweep of stale localhost
   pipelines is ever run, `7452` is safe to delete.
2. Implementer teardown: use the existing `pipeline_id` fixture
   (`automation/fixtures/data_fixtures.py`), which creates-and-deletes an
   empty pipeline per test via `PipelineAPI`; add state variables + target
   nodes inside the test via `PipelineDetailPage`/flow-editor methods rather
   than seeding a hand-built topology (same reasoning as the Router AFS:
   renaming isn't expressible via `create_pipeline_with_nodes()`'s node-dict
   shape without first knowing the exact YAML `id` field semantics).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Decision node on canvas | `[data-testid="rf__node-{node_id}"]` (dynamic, e.g. `rf__node-Decision 1`) | **on-main ✓** — ReactFlow's own testid convention (library-injected, not app-authored — same sanctioned #579 exception as every other node type in this suite); confirmed live. Also usable: `.react-flow__node-decision` CSS class + `data-id` attribute — matches `PipelineDetailPage.wait_for_node_on_canvas("decision")` / `get_node_ids()` (existing methods, reused unmodified). | none needed |
| `Input` multi-select combobox | scoped inside the Decision node, `id="simple-select-Input"` (**non-unique** — collides with a 2nd Decision node's own Input select on the same pipeline, same class of issue as Router's/HITL's duplicated select ids) | **needs-adding**: `testid needed: pipeline-decision-node-input-select`. Confirmed via source: `NormalDecisionNode.jsx`'s `<FlowEditorSelect.InputSelect id={id} inputFieldName={'input'} disabled={isRunningPipeline} />` call site does **NOT** pass the `dataTestId` prop that `InputSelect.jsx` already accepts/forwards (same component, same already-plumbed prop the Router AFS documented for `RouterNode.jsx`'s Input field) — a genuine one-line wiring fix at the `NormalDecisionNode.jsx` call site only, no shared-component change. | none — flag to `add-data-testid`, do not ship a positional/CSS handle |
| `Input` dropdown option (state var name) | `[data-testid="select-option-{value}"]` (e.g. `select-option-normalized_issue`, `select-option-metadata_json`) | **on-main ✓** — confirmed via `git grep` on `origin/main`: `SingleSelectMenuItem.jsx:117` (same mechanism the Router AFS documented); also confirmed live via click interaction for both custom state vars added this session. | none needed |
| `Description` textarea | scoped inside the Decision node, `id="description"` (a LITERAL static id, not React-random — but **non-unique across multiple Decision nodes on one pipeline**, same caveat as `Input`'s select id) | **needs-adding**: `testid needed: pipeline-decision-node-description-input`. Wiring path confirmed via source: same `AIAssistantInput` → `Input.InputBase` → `MuiTextField` pattern the Router AFS documented for its `Condition` field (`inputProps={{'data-testid': dataTestId}}`) — one-line addition at the `NormalDecisionNode.jsx` call site. | none — flag to `add-data-testid`, do not ship a positional/CSS handle |
| `Decision outputs` container | scoped inside the Decision node; no id/testid on the heading `<Box>` or the chip-list `<Box>` (`DecisionNodeShared.jsx`'s `decisionOutputsContainer`/`outputsBorderContainer`) | **needs-adding**: `testid needed: pipeline-decision-node-outputs-container` on the `outputsBorderContainer` Box (`DecisionNodeShared.jsx`). Not currently plumbed at all (no existing prop to wire, unlike Input/Description) — a slightly larger lift: add a `data-testid` prop directly on the `<Box sx={styles.outputsBorderContainer}>` element. | scope inside the Decision node's own testid once it exists (`[data-testid="rf__node-{id}"] >> text=Decision outputs`) is NOT sanctioned as a standing locator — flag to `add-data-testid` |
| Decision output chip (per-output) | rendered as `<StyledChip label={item} ... />` — no testid, but has an accessible `button`/`role` matching the chip's own delete affordance, accessible name = the output's literal value (e.g. `button "bug_responder"`) | **needs-adding**: `testid needed: pipeline-decision-node-output-chip-{value}` (dynamic, templated — same UPPER_CASE class-constant pattern as the Router AFS's dynamic testids). Not currently plumbed — `StyledChip` accepts arbitrary props and could forward a `data-testid`; a one-line addition at the `DecisionOutputs` (`DecisionNodeShared.jsx`) call site, templated with `item`. | while unavailable, the chip's OWN accessible name (`get_by_role("button", name=output_value)`) scoped inside the Decision node's own container is a reasonable interim non-testid-scope-violating READ (existence/count assertions only) — but per this project's policy any NEW locator added to a page object must still be testid-based; use this only for a live probe, not for a shipped `LocatorDescriptor`. |
| `Output` / `Default output` handle labels (plain visible text) | node's own rendered text content — `[data-testid="rf__node-Decision 1"]` scoped, `get_by_text("Output", exact=True)` / `get_by_text("Default output", exact=True)` | **N/A — assert via node text content, not a dedicated handle testid.** Case step 8 only requires the labels be VISIBLE; no interaction is performed on the handle itself for this case (dragging FROM the handle is covered by the `Output`-source-handle drag in step 5, keyed by `data-handleid="nodes"`, not by the visible label). | none needed |
| Decision node's `nodes`/`default_output` source handles (drag targets) | `[data-id="Decision 1"] [data-handlepos="bottom"][data-handleid="nodes"]` / `...[data-handleid="default_output"]` | **on-main ✓** — ReactFlow's own handle-id convention (library-injected via `<FlowEditorNodes.CustomHandle type="source" id="nodes" .../>` / `id="default_output"` in `NormalDecisionNode.jsx`); confirmed live via direct DOM query and successful drag-connect using these exact selectors. Matches `PipelineDetailPage.connect_nodes(source_node_id, target_node_id, source_handle="nodes")` unmodified — no page-object change needed. | none needed |
| DECISION OUTPUTS edge (Decision → output target), **PRE-SAVE (live drag state)** | `[data-testid="rf__edge-xy-edge__{decision_node_id}nodes-{target_node_id}target"]` (e.g. `rf__edge-xy-edge__Decision 1nodes-bug_respondertarget`) | **on-main ✓** — ReactFlow-injected via the live `onConnect` handler's default id-construction (the SAME `{source}{sourceHandle}-{target}target` shape `edge_exists()`'s own docstring documents for HITL, e.g. `HITL 1reject-ENDtarget`); confirmed live via DOM enumeration immediately after each drag-connect, before Save. | none needed |
| DECISION OUTPUTS edge (Decision → output target), **POST-RELOAD (parsed-from-YAML state)** | `[data-testid="rf__edge-xy-edge__{decision_node_id}---{target_node_id}"]` (e.g. `rf__edge-xy-edge__Decision 1---bug_responder`) | **on-main ✓** — ReactFlow-injected via `parsePipeline.helpers.js`'s `handleNewDecisionNode`, which constructs the edge id as `` `${EDGE_PREFIX}${id}---${branch}` `` (plain `---` separator, **no `nodes` handle-suffix** — the SAME format as Router's routes edges, confirmed live: the DOM testid for the identical logical edge CHANGED from the pre-save shape above to this shape after Save + `page.reload()`). | none needed |
| Default-output edge (Decision → default output target), **PRE-SAVE** | `[data-testid="rf__edge-xy-edge__{decision_node_id}default_output-{target_node_id}target"]` (e.g. `rf__edge-xy-edge__Decision 1default_output-ENDtarget`) | **on-main ✓** — same live `onConnect` id-construction as the DECISION OUTPUTS pre-save shape, using the `default_output` handle id instead of `nodes`. Confirmed live via DOM enumeration before Save. | none needed |
| Default-output edge (Decision → default output target), **POST-RELOAD** | `[data-testid="rf__edge-xy-edge__{decision_node_id}default_output---{target_node_id}"]` (e.g. `rf__edge-xy-edge__Decision 1default_output---END`) | **on-main ✓** — `parsePipeline.helpers.js`'s `handleNewDecisionNode` constructs this id as `` `${EDGE_PREFIX}${id}default_output---${default_output}` `` — note this is a THIRD distinct shape: it KEEPS the `default_output` handle-suffix (unlike the plain `nodes`-handle edges, which drop their suffix entirely post-reload) but switches from no-separator-concatenation (`default_output-ENDtarget`) to `---`-separated (`default_output---END`). Confirmed live via DOM enumeration after Save + reload. | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` | **on-main ✓** — confirmed present, already wired as `PipelineFormPage.save_button`; confirmed live firing a `PUT .../application/prompt_lib/{project}/{pipeline_id}` → 201. | none needed |
| `STATE` panel "+" (add state variable) button | scoped inside the STATE panel; no `data-testid`, plain icon `<IconButton>` with no `aria-label`/`title` (its Playwright-computed accessible name resolved unreliably to `"Context"` in this session — do NOT rely on `get_by_role("button", {name: "Context"})`, it is ambiguous/matches unrelated elements elsewhere on the page and caused this session to accidentally type into the pipeline's own Name field twice — see Automation Hints) | **needs-adding**: `testid needed: pipeline-state-add-variable-button`. Not currently plumbed. | none — flag to `add-data-testid`; until then, locate via DOM position (last button inside the STATE panel's variable-list container) rather than accessible role/name |
| `STATE` panel new-variable name input (after clicking "+") | accessible name `"name"` exactly (`get_by_role("textbox", {name: "name", exact: True})`) — **NOT** `input[name="name"]` (that CSS selector ALSO matches the pipeline's own General "Name" field, `id="name" name="name"`, and — critically — `querySelector`/`locator()` without `exact` role scoping resolves to THAT field first, since it precedes the STATE panel in DOM order) | **needs-adding**: `testid needed: pipeline-state-add-variable-name-input`. Not currently plumbed; the accessible-name collision with the unrelated pipeline Name field is a live, reproducible trap (hit twice this session — see Automation Hints) that a dedicated testid would eliminate outright. | until added, use the role-based locator (`get_by_role("textbox", {name: "name", exact: True})`), NEVER a raw `input[name="name"]` CSS selector |
| `STATE` panel new-variable confirm (checkmark) button | scoped inside the newly-opened variable row; no testid | **needs-adding**: `testid needed: pipeline-state-add-variable-confirm-button`. Not currently plumbed. | locate as the last button inside the specific new-row container (obtained via a fresh snapshot immediately after typing the name — do not reuse a stale ref/selector captured before the row rendered) |
| Add-node "+" button / menu items | `[data-testid="pipeline-add-node-button"]`, `[data-testid="pipeline-add-node-menu-item-decision"]`, `[data-testid="pipeline-add-node-menu-item-printer"]` | **on-`automation/testids` only** (awaiting human promotion to `main`) — confirmed via `git grep` on both refs after a fresh `git fetch origin`, same status as every other pipeline-node AFS's Add-node menu row. Used directly by this AFS's live exploration (dev server runs `automation/testids`); the existing `PipelineDetailPage.add_node()` method already drives this via its own existing approach. | n/a — informational only |
| Interrupt before switch | `input[data-testid="pipeline-node-interrupt-before-toggle-{node_id}"]` (e.g. `pipeline-node-interrupt-before-toggle-Decision 1`) | **on-`automation/testids` only** (awaiting human promotion to `main`) — CORRECTS the pipelines digest's prior "unconditional, every node type" framing: `git grep` after a fresh `git fetch origin` found this testid ONLY on `origin/automation/testids` (`CommonInterruptSettings.jsx`), NOT yet on `origin/main`. Confirmed live present and correctly `disabled` while the Decision node is the pipeline's entry point (matches `CommonInterruptSettings.jsx`'s own `disabled={yamlJsonObject.entry_point === id || disabled}` logic — expected behavior, not a defect). | none needed once promoted; the digest entry for this testid needs the same correction (see role-memory write) |
| Interrupt after switch | scoped inside the Decision node; no testid (`CommonInterruptSettings.jsx`'s `interruptAfterTestId` prop is caller-supplied/opt-in, and `NormalDecisionNode.jsx`'s call site does not pass it) | **needs-adding**: `testid needed: pipeline-decision-node-interrupt-after-toggle`. One-line addition at the `NormalDecisionNode.jsx` call site (`<FlowEditorSettings.CommonInterruptSettings ... interruptAfterTestId="pipeline-decision-node-interrupt-after-toggle" />`), same opt-in-per-caller shape the shared component already documents in its own source comment. | none — flag to `add-data-testid` |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation (step 0's prerequisite, if not using the `pipeline_id` fixture).
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on Save click (step 6); persists the Decision node's full config (`input`, `description`, `nodes` [the DECISION OUTPUTS array], `default_output`) plus the two new custom state variables as part of the pipeline's YAML `instructions` field. Confirmed live: returns **201 Created** (not 200), same as every other pipeline-node-configuration AFS.
- `GET .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on page load/reload (step 7); the Decision node's rendered config AND the edge testid shapes are re-derived directly from this response's YAML `instructions` (see the Concrete Handles table's pre-save vs. post-reload edge-shape rows — this endpoint's response is WHY the shape changes).

## Known Defects Found During Exploration

No product defects found. This session's exploration executed all 10 steps
(case's 9 plus this AFS's setup step 0) to completion against the live local
environment with zero console errors at every checkpoint, including a real
Save-click + full `page.reload()` persistence round-trip for every field and
every edge.

One case-text drift was identified and is filed as a CLARIFICATION (not a
bug), per the reverse-masking guard, bundled with the same DECISION-OUTPUTS-
mechanism pattern already tracked for sibling pipeline-node cases:

- **[INFO] Case precondition/step-5 wording ("target nodes for routing
  exist" / "add target node names as chips") doesn't match how the live UI's
  DECISION OUTPUTS field actually works** — it's populated exclusively by
  dragging a canvas edge from the node's `Output` handle to an existing,
  correctly-named target node; there is no typeable/freeform chip input.
  Target nodes must be pre-named to match the classification prompt's literal
  output values. Same shape as `#1104`/`#1136`/`#1137`/`#1144` filed against
  sibling pipeline cases (ELITEA-2018/2031/2032/2033) — **to be filed as a
  new CLARIFICATION issue by the implementer/lead per the standard bug-filing
  routing** (this analyst session did not file a tracker issue directly;
  flagging here per this AFS's Known Defects section so the routing isn't
  dropped — dedup first against the existing `#1104`/`#1136`/`#1137`/`#1144`
  cluster, as this may be bundle-eligible under the same umbrella pattern
  rather than a fresh strict-per-bug filing).

## Blocked Steps

None. All 10 steps (case's 9 plus this AFS's setup step 0) were executed to
completion against the live local environment, including a real Save-click +
full `page.reload()` persistence round-trip and live edge-testid enumeration
before AND after reload (which is what surfaced the pre-save/post-reload edge
shape difference documented above).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` — **this
  case requires `add-data-testid` work before implementation**: 6 of the
  interactive Decision-node/STATE-panel elements have no `data-testid` today
  (`Input` select, `Description` textarea, `Decision outputs` container, the
  per-output chips, `Interrupt after`, and the STATE panel's add-variable
  controls). See Concrete Handles for exact guidance and naming per element.
- **Edge testid shape changes across save/reload — the single most important
  gotcha in this AFS.** Live-confirmed via DOM enumeration both immediately
  after each drag-connect (pre-Save) AND after Save + a real `page.reload()`:
  the SAME logical edge's `data-testid` is DIFFERENT in the two states.
  - `nodes`-handle (DECISION OUTPUTS) edges: pre-save
    `Decision 1nodes-bug_respondertarget` → post-reload
    `Decision 1---bug_responder` (the `nodes` handle-suffix DISAPPEARS after
    reload).
  - `default_output`-handle edge: pre-save `Decision 1default_output-ENDtarget`
    → post-reload `Decision 1default_output---END` (the handle-suffix STAYS
    but the separator changes from no-separator-concatenation to `---`).
  - **Recommended pattern: use `PipelineDetailPage.edge_exists(source_id,
    target_id)` WITHOUT the `handle_suffix` parameter** for all Decision-node
    edge assertions, both pre-save and post-reload — its prefix+substring
    matching (`testid.startswith(f"rf__edge-xy-edge__{source_id}")` AND
    `f"-{target_id}" in testid`) tolerates BOTH shapes without modification,
    confirmed by re-deriving the match logic against all 8 observed edge
    testids in this session (4 pre-save, 4 post-reload). Do **NOT** use
    `edge_testid_present()`/`EDGE_TESTID`/`get_edge_locator()` for Decision
    node edges — those require the EXACT `---`-only shape and will silently
    report "not found" for the pre-save state (contrast with the Router AFS,
    ELITEA-2033, which correctly recommends `edge_testid_present()` because
    Router's routes edges use the `---` shape in BOTH states — Decision does
    not share that stability).
- **`STATE` panel's add-variable "+" button has an unreliable computed
  accessible name (`"Context"`) that caused two real mistakes this session** —
  worth a dedicated automation-hint entry since a future implementer WILL hit
  this if they reach for `get_by_role("button", {name: "Context"})`: it
  matched ambiguously (this session's tooling resolved it to the SAME
  locator text every time regardless of which of 3 different distinct DOM
  buttons was the actual click target across 3 separate attempts), and,
  separately, the raw CSS selector `input[name="name"]` for the resulting
  new-row text input ALSO matched the WRONG element (the pipeline's own
  unrelated General "Name" field, which happens to carry a literal
  `id="name" name="name"` and precedes the STATE panel in DOM order) —
  **twice** overwriting the pipeline's Name field with the state-variable
  name being typed. The RELIABLE pattern that worked cleanly all 3 times:
  take a FRESH snapshot immediately before each interaction (never reuse a
  ref/selector across a re-render), and target the new row's textbox via
  `get_by_role("textbox", {name: "name", exact: True})` scoped to a snapshot
  taken AFTER the "+" click, not a CSS attribute selector. This is exactly
  the kind of trap `add-data-testid` work on this panel would eliminate —
  see Concrete Handles' `needs-adding` rows for the STATE panel.
- **State variables are NOT built-in for a fresh pipeline** (unlike Router's
  `input`/`messages`, which ARE built-in) — a Decision node's `Input`
  combobox on a brand-new pipeline lists only `input`/`messages` until custom
  state variables are added via the `STATE` panel. This AFS's step 0 makes
  that setup explicit; a future implementer reusing the `pipeline_id` fixture
  must add the state variables in-test (no existing fixture parameter seeds
  custom state vars today — flag if this recurs across other cases as a
  candidate for a shared fixture helper).
- **Project mismatch gotcha (see the Router AFS, ELITEA-2033, for the full
  writeup)** — this session's active browser project happened to match
  `.env.test`'s `ELITEA_PROJECT_ID` (both "Private"/399), so the gotcha did
  NOT reproduce this time, but the same verification discipline (check the
  browser's active project before creating test data via a standalone
  token-auth script) still applies for any implementer using `PipelineAPI`
  directly rather than the cookie-based `pipeline_id` fixture.
- No existing page-object method reads/writes a Decision node's inline
  config — `automation/pages/pipeline_detail_page.py` has generic node
  methods (`add_node`, `wait_for_node_on_canvas`, `delete_node`,
  `edit_node_name`, `connect_nodes`, `edge_exists`) but nothing
  Decision-specific. New page-object surface needed, e.g.
  `configure_decision_node(node_id, input_vars=[...], description=...,
  outputs=[...])` on `PipelineDetailPage` (the `outputs` list drives a loop of
  `connect_nodes(node_id, target, source_handle="nodes")` calls, NOT a single
  select-and-fill call), following the same shape as the Router/HITL AFSes'
  suggested `configure_router_node()`/`configure_hitl_node()`.
- Wait strategy: wait for the `PUT .../application/prompt_lib/{project}/{pipeline_id}`
  response (201, confirmed) before reloading/asserting persistence — not a
  fixed timeout.
- The `Description` field's underlying element is a plain MUI `TextField`
  (multiline `<textarea>`), same `AIAssistantInput` component family as the
  Router AFS's `Condition` field — normal `.input_value()`-readable
  Playwright textarea, NOT a CodeMirror/Monaco editor, so it needs none of
  the `.agents/testing.md` #579 CodeMirror-line-scoping technique.
