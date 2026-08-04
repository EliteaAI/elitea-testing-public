# Test Case: Pipeline — Router Node Configuration

## Metadata
- **TMS ID**: ELITEA-2033
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-04
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- **CLARIFICATION on the case's stated precondition** ("A pipeline with state
  variable 'input' and target nodes for routing exists"): live-confirmed the
  `input` variable is a **built-in state variable present on every pipeline by
  default** (the Router's `Input` combobox lists exactly `input` and `messages`
  with no setup) — it does not need to be created. What DOES need setup is the
  **target nodes for routing**, and live behavior requires them to be named
  (renamed via the canvas inline node-rename) to match the condition's literal
  output values (`approve`, `reject`) — see step 0 and the Coverage Map note
  below for why.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- An empty pipeline via the `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`,
  `PipelineAPI`-backed create/delete).
- Two Printer nodes added via the canvas and **renamed** to `approve` and
  `reject` (`PipelineDetailPage.add_node("Printer")` ×2 +
  `PipelineDetailPage.edit_node_name(...)`) — these become the Router's route
  targets. Printer was chosen as a lightweight, already-automated node type;
  any node type works as a route target.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — **see Automation Hints, "Project
  mismatch" — do not trust this value blindly against a fresh localhost
  session; verify against the actual active project first.**

## Test Steps

**IMPORTANT — step 0 added ahead of the case's step 1.** The case's
precondition text implies target nodes named "approve"/"reject" already
exist; live behavior requires an explicit setup action to produce them (see
Coverage Map). This AFS makes that setup step 0 so the implementer's fixture
maps 1:1 onto it.

0. **Setup**: create a pipeline; add two Printer nodes via the canvas "+"
   button → "Printer" (`add_node("Printer")` ×2, existing
   `PipelineDetailPage` method); rename them to `approve` and `reject` via
   `edit_node_name(node_id, new_name)` (double-click the name label → type →
   click the canvas empty pane to commit — clicking empty pane, NOT pressing
   Enter, is what commits the rename; see Automation Hints).
   - **Verify**: `get_node_ids()` includes exactly `approve` and `reject`
     (bare names, no type prefix — see Automation Hints, "Node rename
     doesn't retain type prefix").
1. Add a Router node via the canvas "+" button → "Router"
   (`add_node("Router")`).
   - **Verify**: node appears on canvas — `wait_for_node_on_canvas("router")`
     returns a non-empty id (`Router 1`); node count increased by 1.
2. Observe the Router node's config (renders **inline on the card itself —
   no click-to-open action needed**, same always-expanded shape as every
   other pipeline node type in this codebase — matches the digest's
   already-confirmed generic finding).
   - **Verify**: sections visible top to bottom: `Condition` (a Jinja-aware
     textarea), `Routes` (multi-select combobox), `Input` (multi-select
     combobox), `Default output` (single-select dropdown). All four present
     — matches the case's step 2 expectation exactly, no case-text drift
     here.
3. In `Condition`, enter the Jinja template:
   `{% if 'yes' in input %}approve{% else %}reject{% endif %}`.
   - **Verify**: the textarea's value equals the entered string (read via
     `.input_value()` once the testid exists — see Automation Hints on why
     not `.inner_text()`).
4. Open the `Routes` combobox and select `approve`, then `reject`.
   - **Verify**: both chips appear in the Routes field (`textbox` value
     becomes `approve,reject`). **Also verify (Axis 2 addition)**: the
     canvas immediately renders `Router 1 → approve` and `Router 1 → reject`
     edges the instant each route is selected — no Save needed for the
     edge to appear (`edge_testid_present("Router 1", "approve")` /
     `edge_testid_present("Router 1", "reject")` both go true).
   - **CLARIFICATION on the case's step 4 wording** ("add route values"):
     `Routes` is NOT a freeform/creatable text field — it is a picklist of
     **existing pipeline node ids** (+ a literal `END` option). Selecting
     `approve`/`reject` only works because step 0 pre-named two nodes to
     match; typing an arbitrary string that isn't a node id is not
     supported by this control. See Coverage Map for the full reasoning —
     not a defect, the case's "add route values" phrasing just undersells
     that routes are node-id references, not string tags.
5. Open the `Input` combobox and select `input`.
   - **Verify**: `Input` field shows `input` as the selected chip (textbox
     value `input`).
6. Open the `Default output` dropdown and select `END` (it is already the
   default value, so this step is a real interaction that re-confirms the
   already-selected option — exercised so the select itself, not just its
   initial state, is proven functional).
   - **Verify**: `Default output` shows `END`. **Also verify (Axis 2
     addition)**: a `Router 1 → END` edge renders immediately on the canvas
     with source handle `routerNode_default_output`
     (`edge_testid_present` variant — see Automation Hints for the exact
     testid string, which is NOT the plain `EDGE_TESTID` format).
7. Click the pipeline's Save button (`agent-save-button`).
   - **Verify**: no console errors; `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` returns a 2xx (observed live: 201 Created).
8. Reload the page at the pipeline's canonical URL
   (`/pipelines/all/{id}?viewMode=owner`).
   - **Verify**: after reload, the Router node shows the persisted
     Condition text, both Routes chips (`approve`, `reject`), Input
     (`input`), and Default output (`END`) — confirmed live via a real
     `page.reload()`, not just an API read.
9. Verify canvas edges after reload.
   - **Verify**: `Router 1 → approve`, `Router 1 → reject` (routes edges)
     and `Router 1 → END` (default-output edge) are all present — matches
     the case's step 9 expectation, plus the default-output edge which the
     case text doesn't explicitly call out as a separate edge but which the
     live product renders (Axis 2 addition, see below).

## Expected Results
- Router node config renders fully inline on the canvas card (no
  modal/panel to open) — Condition, Routes, Input, Default output all
  present and independently persist through Save + reload.
- Routes is a picklist of existing node ids (+ `END`), not a freeform tag
  input — selecting route targets requires those nodes to already exist
  with matching names.
- Selecting a Routes value or the Default output value wires a real canvas
  edge immediately (before Save) — three distinct edges from one Router
  node: two "routes" edges (`routerNode_routes` handle) plus one
  "default output" edge (`routerNode_default_output` handle, a visually and
  testid-ally distinct edge from the routes edges).
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipeline with state variable "input" and target nodes for routing exists | setup exists | Preconditions clarification + step 0 | step 0: `get_node_ids()` includes `approve`/`reject`; `input` verified as a built-in option in step 5's dropdown, no creation needed | asserted — **CLARIFICATION: "state variable 'input'" needs no setup (built-in); "target nodes for routing" needs an explicit rename action the case text doesn't spell out — not a defect, case precondition undersells what live setup requires.** |
| 1 Create pipeline, add Router node via "Add node" → "Router" | Router node appears on canvas | step 1 | step 1: node count + id | asserted |
| 2 Verify Router node panel shows Condition/Routes/Input/Default output | all listed sections present | step 2 | step 2: all 4 sections visible | asserted — no case-text drift, live UI matches exactly (unlike some sibling node types where the case describes a "panel" that must be opened; Router's config, like every node type here, is always inline) |
| 3 Condition field accepts Jinja template | field accepts the value | step 3 | step 3: `.input_value()` equals entered string | asserted |
| 4 Routes combobox: add "approve", "reject" | both values added | step 4 | step 4: chips shown + edges appear | asserted — **CLARIFICATION: "add route values" reads as freeform entry; live behavior is select-from-existing-node-ids. Case's overall intent (route targets named approve/reject) is still achievable and is what this AFS's step 0 sets up.** |
| 5 Input combobox set to "input" | Input set to "input" | step 5 | step 5: chip shown | asserted |
| 6 Default output set to "END" | Default output = END | step 6 | step 6: value shown + edge appears | asserted |
| 7 Save pipeline | saves without errors | step 7 | step 7: no console errors, 2xx (201 observed) | asserted |
| 8 Reload — verify Condition, Routes, Input, Default output persist | all fields restored | step 8 | step 8: live UI round-trip of all 4 field groups | asserted |
| 9 Canvas shows edges from Router to target nodes matching route values | edges connect Router to approve/reject | step 9 | step 9: 3 edges present (2 routes + 1 default-output) | asserted — **the case names only the routes-matching edges; live product additionally always renders a default-output edge (Router → END here), which is asserted as an Axis-2 addition below, not silently dropped** |
| Expected Final State: fully configured, persists after reload, canvas edges reflect routes | — | steps 7–9 | steps 7–9 | asserted |
| Pass/Fail: all steps complete without errors; fields + edges persist | — | all steps | all steps | asserted |

**CLARIFICATION on precondition + step 4 (route target nodes):** the case
text implies "target nodes for routing" simply "exist" and that you "add
route values" into the Routes combobox as if typing tags. Live-confirmed
(source: `RouteSelect.jsx`'s `useNodeOptions` hook) the Routes combobox is
backed by **existing pipeline node ids** (+ a synthetic `END` option) — it
is not a creatable/freeform field. To reproduce the case's intent (routes
named "approve"/"reject" matching the condition's Jinja output), the
precondition pipeline must contain nodes literally renamed `approve` and
`reject`. This AFS's step 0 makes that setup explicit. Not filed as a
defect — the case's overall intent is fully achievable, the wording is just
imprecise about the mechanism. **Filed as a CLARIFICATION**, see Known
Defects Found During Exploration below.

### Axis 2 — Analyst additions

- Step 4 additionally asserts that selecting a Routes value wires a real
  canvas edge **immediately, before Save** — *added: this is a materially
  different persistence model than "edges appear after Save" and is worth
  guarding against a regression that defers edge creation to save-time.*
- Step 6 additionally asserts a separate `Router 1 → END` edge appears when
  Default output is set — *added: this edge is visually and
  testid-ally distinct from the two "routes" edges (different ReactFlow
  source handle: `routerNode_default_output` vs `routerNode_routes`, and a
  different edge-id/testid shape — see Automation Hints). The case's step 9
  ("edges from Router to target nodes matching route values") could be
  read as covering only the 2 routes edges; asserting the 3rd (default
  output) edge closes that gap and matches what the live product actually
  renders.*
- No console-error assertion was in the original case text; added it
  throughout as a side-channel check — zero console errors were observed
  in this session (both on initial configuration and after reload).
- Step 7 additionally asserts the exact HTTP status (201 Created, observed
  live) rather than a generic "no errors" — *added: pins the exact expected
  status so a future regression to e.g. a 200-with-error-body doesn't
  silently pass a looser "2xx-ish" check.*

## Cleanup

1. This session created a persistent pipeline (`autotest_router_2033`, ids
   `7397` then `7398` — the first attempt landed in the wrong project, see
   Automation Hints) on the local DEV backend. Both deleted at the end of
   this session via `PipelineAPI.delete_pipeline()` — confirmed removed.
2. Implementer teardown: use the existing `pipeline_id` fixture
   (`automation/fixtures/data_fixtures.py`), which creates-and-deletes an
   empty pipeline per test via `PipelineAPI`; add + rename nodes inside the
   test via `PipelineDetailPage` methods rather than seeding a hand-built
   topology (renaming, unlike HITL's route dict, isn't expressible via
   `create_pipeline_with_nodes`'s node-dict shape without first knowing the
   exact YAML `id` field semantics — the canvas rename flow is simpler and
   already proven by `edit_node_name`).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Router node on canvas | `[data-testid="rf__node-{node_id}"]` (dynamic, e.g. `rf__node-Router 1`) | **on-main ✓** — ReactFlow's own testid convention (library-injected on the node wrapper via the node's `id`, not app-authored — confirmed absent from app source via `git grep` on both `origin/main` and `origin/automation/testids`, i.e. it needs no app change and is present on any branch running this ReactFlow version); sanctioned third-party-widget handle per `.agents/testing.md` § Locator policy stop+flag exception #579 (same pattern as the existing HITL/MCP-node AFS's). Also usable: `.react-flow__node-router` CSS class + `data-id` attribute (confirmed live) — matches `PipelineDetailPage.wait_for_node_on_canvas("router")` / `get_node_ids()` (existing methods, reused unmodified). | none needed |
| `Condition` textarea (Jinja) | scoped inside the Router node container, no stable selector today (`name="condition"`, React-generated random `id` e.g. `:r6r:` — confirmed non-deterministic, useless as a locator) | **needs-adding**: `testid needed: pipeline-router-node-condition-input`. Wiring path confirmed via source: `AIAssistantInput` → `Input.InputBase` → `MuiTextField` with `slotProps.htmlInput: inputProps` — the SAME `inputProps={{'data-testid': dataTestId}}` pattern the HITL AFS documented for `InputMappingItem.jsx`/`SimpleLLMInputItem.jsx`. One-line addition at the `RouterNode.jsx` call site (`<AIAssistantInput ... inputProps={{'data-testid': 'pipeline-router-node-condition-input'}} />`) — no shared-component change needed since `InputBase` already forwards `inputProps` to the real DOM node. | none — flag to `add-data-testid`, do not ship a positional/CSS handle |
| `Routes` multi-select combobox | scoped inside the Router node, `id="simple-select-Routes"` (**non-unique** — collides with a 2nd Router node's own Routes select on the same pipeline, same class of issue as HITL's duplicated `id="simple-select-Route"`) | **needs-adding**: `testid needed: pipeline-router-node-routes-select`. Unlike `InputSelect`, `RouteSelect.jsx` does **NOT** currently accept/forward a `dataTestId`/`data-testid` prop at all (confirmed via source read) — this needs BOTH (1) a new `dataTestId` prop added to `RouteSelect.jsx` that forwards to its inner `Select.SingleSelect`'s `data-testid` (mirrors `InputSelect.jsx`'s existing pattern exactly), AND (2) wiring that prop at the `RouterNode.jsx` call site. A slightly larger lift than the other Router fields (2-line fix, not 1-line), but same shape as prior art. | `#simple-select-Routes` only while a pipeline has exactly one Router node — do not rely on this, flag to `add-data-testid` |
| `Routes`/`Input`/`Default output` dropdown option (target node name / state var / `END`) | `[data-testid="select-option-{value}"]` (e.g. `select-option-approve`, `select-option-input`, `select-option-END`) | **on-main ✓** — confirmed via `git grep` on `origin/main`: `SingleSelectMenuItem.jsx:117` (`data-testid={option.testId ?? \`select-option-${option.value}\`}`) defaults every option's testid this way when no explicit `option.testId` is set; also confirmed live via click interaction (`select-option-approve`, `select-option-reject`, `select-option-input`, `select-option-END` all fired real clicks). Same pattern as the HITL/MCP-node AFS's toolkit/tool option locators. | none needed |
| `Input` multi-select combobox | scoped inside the Router node, `id="simple-select-Input"` (same non-uniqueness caveat as Routes) | **needs-adding**: `testid needed: pipeline-router-node-input-select`. `FlowEditorSelect.InputSelect` **already accepts and forwards** a `dataTestId` prop straight through to `data-testid` on its inner `SingleSelect` (confirmed via source: `InputSelect.jsx` destructures `dataTestId` and passes `data-testid={dataTestId}`) — this is a genuine one-line wiring fix at the `RouterNode.jsx` call site only (`<FlowEditorSelect.InputSelect ... dataTestId="pipeline-router-node-input-select" />`), no shared-component change, same class of fix the HITL AFS documented for the same component. | none — flag to `add-data-testid`, do not ship a positional/CSS handle |
| `Default output` single-select dropdown | scoped inside the Router node, `id="simple-select-Default_output"` (confirmed live via the click-target selector that resolved successfully; non-uniqueness caveat as above) | **needs-adding**: `testid needed: pipeline-router-node-default-output-select`. The underlying `SingleSelect` already accepts a `data-testid` prop directly (confirmed: `SingleSelect.jsx` destructures `'data-testid': dataTestId` and applies it to the trigger + `-combobox` suffix on open) — `RouterNode.jsx`'s inline `<SingleSelect ... />` call for Default output just needs `data-testid="pipeline-router-node-default-output-select"` added, a one-line fix, no prop-plumbing needed anywhere else. | none — flag to `add-data-testid` |
| Routes edge (Router → route target) | `[data-testid="rf__edge-xy-edge__{router_node_id}---{target_node_id}"]` (e.g. `rf__edge-xy-edge__Router 1---approve`) | **on-main ✓** — ReactFlow-injected on the edge wrapper using the edge's own `id` field (app-constructed in `RouteSelect.jsx` as `${EDGE_PREFIX}${id}---${value}`, i.e. plain `---` separator, NO source-handle suffix). Matches the existing `PipelineDetailPage.EDGE_TESTID` template (`'[data-testid="rf__edge-xy-edge__{}---{}"]'`) and `edge_testid_present()`/`get_edge_locator()` **exactly, unmodified** — confirmed live: `edge_testid_present("Router 1", "approve")` and `edge_testid_present("Router 1", "reject")` both resolve correctly with zero new page-object code. | none needed — reuse `edge_testid_present()` / `get_edge_locator()` as-is |
| Default-output edge (Router → default output target) | `[data-testid="rf__edge-xy-edge__{router_node_id}default_output---{target_node_id}"]` (e.g. `rf__edge-xy-edge__Router 1default_output---END`) | **on-main ✓** but **NOT the plain `EDGE_TESTID` shape** — app-constructed in `RouterNode.jsx`'s `handleDefaultOutput` as `${EDGE_PREFIX}${id}default_output---${value}` (note: **no separator between the node id and the literal `default_output`** — same no-separator-concatenation gotcha as HITL's `HITL 1reject-ENDtarget`). Confirmed live via `.react-flow__edge[data-testid]` enumeration after reload: exactly `rf__edge-xy-edge__Router 1default_output---END`. `edge_testid_present()`/`get_edge_locator()` still work if the caller passes the pre-concatenated string as the "source" argument (e.g. `get_edge_locator(f"{node_id}default_output", "END")`) — no new page-object method needed, just correct call-site string construction; document this clearly for the implementer since it is easy to get wrong. | none needed once the call-site concatenation is correct |
| Pipeline Save button | `[data-testid="agent-save-button"]` | **on-main ✓** — confirmed present, already wired as `PipelineFormPage.save_button` (inherited by `PipelineDetailPage`); confirmed live firing a `PUT .../application/prompt_lib/{project}/{pipeline_id}` → 201. | none needed |
| Add-node "+" button / menu items | `[data-testid="pipeline-add-node-button"]`, `[data-testid="pipeline-add-node-menu-item-{type}"]` (e.g. `pipeline-add-node-menu-item-router`, `pipeline-add-node-menu-item-printer`) | **on-`automation/testids` only** (awaiting human promotion to `main`) — confirmed via `git grep` on both refs after a fresh `git fetch origin`: present at `src/pages/Pipelines/Components/AddNodeMenu.jsx` on `origin/automation/testids`, absent on `origin/main`. **Not used directly by this AFS's own locators** (the existing `PipelineDetailPage.add_node()` method already drives this via a CSS-class + role-based approach, unrelated to these testids, per its own docstring/implementation) — noted here only as provenance context in case a future case wants to switch `add_node()` to testid-based locating. | n/a — informational only, no page-object change implied by this AFS |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation (step 0's prerequisite, if not using the `pipeline_id` fixture).
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on Save click (step 7); persists the Router node's full config (`condition`, `routes`, `input`, `default_output`) as part of the pipeline's YAML `instructions` field. Confirmed live: returns **201 Created** (not 200). Wait for this response before reloading/asserting persistence in step 8, not a fixed timeout.
- `GET .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on page load/reload (step 8); the Router node's rendered config is parsed directly from this response's YAML `instructions`.

## Known Defects Found During Exploration

**None found in the Router node's configuration/persistence/edge-wiring
behavior itself** — Condition, Routes (both routes edges), Input, and
Default output (including its own distinct edge) all configure and persist
correctly through Save + a real UI reload, with zero console errors.

One case-text drift was identified and should be filed as a CLARIFICATION
(not a bug), per the reverse-masking guard:

- **[INFO] Case precondition/step-4 wording ("target nodes for routing
  exist" / "add route values") doesn't match how the live UI's Routes field
  actually works** — it's a picklist of existing node ids, not a freeform
  tag input, so target nodes must be pre-named to match the condition's
  literal output values. Recommend filing as an
  `EliteaAI/elitea-testing-public` `question`-labelled clarification (same
  shape as `#1104`/`#1136`/`#1137` filed against sibling pipeline cases)
  so the TMS case text can be corrected to spell out the node-rename setup
  step. **Not yet filed by this analyst session** — see Automation Hints /
  handoff note; the implementer or lead should file it alongside PR
  creation, quoting this AFS's Coverage Map clarification as the body.

## Blocked Steps

None. All 10 steps (case's 9 plus this AFS's setup step 0) were executed to
completion against the live local environment, including a real Save-click
+ full `page.reload()` persistence round-trip and live edge-testid
enumeration before and after reload.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` — **this
  case requires `add-data-testid` work before implementation**: 4 of the 4
  interactive Router-node fields (Condition, Routes, Input, Default output)
  have no `data-testid` today. Three are one-line prop additions at the
  `RouterNode.jsx` call sites (`Condition` via `inputProps`, `Input` via the
  already-supported `dataTestId` prop, `Default output` via the
  already-supported `data-testid` prop); `Routes` needs a small 2-line fix
  (new prop added to `RouteSelect.jsx` itself, then wired at the call
  site) — see Concrete Handles for exact guidance and naming.
- **Project mismatch — verify the active project before creating test data
  (real gotcha hit this session, cost ~10 minutes).** `.env.test`'s
  `ELITEA_PROJECT_ID=399` ("Private") does NOT necessarily match the
  browser session's currently-active project — this localhost session
  defaulted to a DIFFERENT project ("Elitea Testing Team", id `471`) which
  had **no create-pipeline permission** for the dev-token user (`403
  access_denied`, missing `models.applications.applications.create`).
  Creating a pipeline via `PipelineAPI` with the default
  `settings.elitea_project_id` while the UI session is on a different
  project produces a pipeline the UI then 400s trying to load (wrong
  `project_id` in the URL). **Fix**: either create pipelines purely via UI
  (which correctly uses whatever project is currently active in the
  sidebar selector — switch it to "Private" first via
  `[data-testid="project-selector-trigger-combobox"]` →
  `[data-testid="select-option-399"]` if it isn't already), or, if using
  `PipelineAPI` directly, confirm the browser's active project id first
  (read the sidebar's `Project:` textbox value) and pass it explicitly as
  `project_id=`. This is a session/environment quirk, not a product defect
  — flagging for the implementer and any future analyst on this suite so it
  isn't re-discovered the hard way. The existing `pipeline_id`/`pipeline_api`
  fixtures already use cookie-based auth (`browser_cookies`) rather than the
  bare token, which inherits the correct active project automatically — this
  gotcha is specific to standalone token-auth API scripts run outside a
  browser session, exactly what this analyst session did while exploring.
- **Node rename doesn't retain the type prefix — page-object docstring
  drift found.** `PipelineDetailPage.edit_node_name()`'s docstring claims
  "the type prefix stays... renaming 'LLM 1' to 'MyNode' sets the data-id
  to 'LLM MyNode'". **Live-confirmed this is WRONG** (or stale/no longer
  true): renaming "Printer 1" → "approve" produces a clean data-id of
  exactly `approve`, no `Printer` prefix. Confirmed by direct DOM
  inspection (`data-id` attribute) before and after the rename, for two
  separate nodes. This is a discrepancy in our OWN page-object
  documentation, not a product defect — flagged here so the implementer
  doesn't write an assertion around the wrong expected id, and so the
  docstring can be corrected in the same PR (small fix, `pipeline_detail_page.py:1765-1767`).
- **Node rename commit mechanism**: pressing `Enter` after typing the new
  name does **NOT** commit the rename (confirmed live: `data-id` stayed
  unchanged after `Enter`). Only clicking the canvas empty pane
  (`.react-flow__pane`) — i.e. blurring the input via a real mouse click —
  commits it. `edit_node_name()`'s existing implementation already does
  this correctly (via `self._deselect_all()`), so no page-object change
  needed here; noted only because it would be an easy thing to get wrong
  if re-implementing from scratch.
- No existing page-object method reads/writes a Router node's inline
  config — `automation/pages/pipeline_detail_page.py` has generic node
  methods (`add_node`, `wait_for_node_on_canvas`, `delete_node`,
  `edit_node_name`, `connect_nodes`, `edge_exists`, `edge_testid_present`,
  `get_edge_locator`) but nothing Router-specific. New page-object surface
  needed, e.g. `configure_router_node(node_id, condition=..., routes=[...],
  input_vars=[...], default_output=...)` on `PipelineDetailPage`, following
  the same shape as the HITL-node AFS's suggested `configure_hitl_node()`.
- Wait strategy: wait for the `PUT .../application/prompt_lib/{project}/{pipeline_id}`
  response (201, confirmed) before reloading/asserting persistence — not a
  fixed timeout.
- The `Condition` field's underlying element is a plain MUI `TextField`
  (multiline `<textarea>`), NOT a CodeMirror/Monaco editor, despite the
  `language="jinja"` prop passed to `AIAssistantInput` — that prop only
  affects syntax highlighting inside the "AI Assistant" full-screen modal
  the field can expand into, not the inline textarea itself. So this is a
  normal `.input_value()`-readable Playwright textarea, not a case needing
  the CodeMirror-line-scoping technique from `.agents/testing.md`'s #579
  exception (`mcp_form_page.py`'s `fill_raw_json_line()`).
