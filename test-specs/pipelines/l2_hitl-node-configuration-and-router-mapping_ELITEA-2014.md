# Test Case: Pipeline HITL Node — Configuration and Router Mapping

## Metadata
- **TMS ID**: ELITEA-2014
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-02 (cluster dispatch with ELITEA-2015)
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline exists with at least two other nodes to serve as HITL route targets. This session provisioned one via the API (`PipelineAPI.create_pipeline_with_nodes`) with topology `LLM 1 → HITL 1 → Printer 1 → END` so the HITL node's APPROVE/EDIT/REJECT selects have real non-`END` targets (`LLM 1`, `Printer 1`) to choose between, plus `END` itself.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline (`autotest_hitl_<unique>`) with nodes `LLM 1 → HITL 1 → Printer 1 → END`, HITL node seeded with `routes: {approve: "Printer 1", reject: "END"}` and `user_message: {type: fixed, value: "..."}` so the node has real content before the test starts interacting.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`).

## Test Steps

**IMPORTANT — step ordering differs from the original case text.** The original case
lists "configure ROUTER MAPPING (step 5)" before "set EDIT STATE KEY (step 6)", but
live behavior requires EDIT STATE KEY to be set FIRST — the EDIT route select is
`aria-disabled` until EDIT STATE KEY has a value (confirmed via `aria-disabled`
attribute flipping from `"true"` to absent). APPROVE/REJECT routes have no such
gating and can be set at any time. The steps below reorder EDIT STATE KEY ahead of
the EDIT route selection to match what the live UI actually requires; see Coverage
Map for the case-text drift note.

**Implementer-discovered addendum (2026-08-02, ELITEA-2014 automation pass):** the
`Input` combobox (step 3) is itself `disabled` unless USER MESSAGE Type is
`F-String` — confirmed via `HITLNode.jsx`'s `isInputSelectDisabledByMessageType`
(`userMessageType !== 'fstring'`) and the select's own tooltip ("Available only
when the User message type is set to F-String"). Since the default USER MESSAGE
Type is `Fixed`, driving the case's literal step order (Input, step 3, before
USER MESSAGE, step 4) times out waiting for the Input dropdown to open. The
shipped test therefore sets USER MESSAGE Type = F-String FIRST, then the Input
combobox, reversing steps 3 and 4 below — the same class of case-text drift as
the EDIT STATE KEY reordering above (technique-level, not a scope change; both
steps' assertions are unchanged, only their execution order is).

1. Create a pipeline and add a Human-in-the-loop node via the canvas "+" button →
   "Human-in-the-loop" (`add_node("Human-in-the-loop")`, existing `PipelineDetailPage`
   method).
   - **Verify**: node appears on canvas (`wait_for_node_on_canvas("hitl")` returns a
     non-empty id); node count increased by 1.
2. Click/select the HITL node on the canvas.
   - **Verify**: the node's config renders **inline on the card itself — no
     click-to-open action needed** (same always-expanded shape as every other
     pipeline node type in this codebase, e.g. the MCP node). Sections visible, top
     to bottom: `Input`, `USER MESSAGE` (Type + Value), `ROUTER MAPPING` accordion
     (APPROVE/EDIT/REJECT, each with its own "Route" select), `EDIT STATE KEY`
     (a "Value" select). This differs from the case text's step 2 wording ("Click
     HITL node — verify panel shows...") only in that there is no separate panel to
     open; the observable (all listed sections present) is unchanged and asserted.
3. Set the `Input` combobox with one or more state variables (e.g. `input`).
   - **Verify**: `Input` combobox shows the selected variable(s) as chips.
4. In `USER MESSAGE`: set Type = `F-String`, then set `Input` (from step 3) so a
   variable is available, and enter a message value referencing it (or leave Type =
   `Fixed` and enter a literal message — both are valid per the case's "Fixed or
   F-String" test data).
   - **Verify**: Type shows the selected value; Value field shows the entered text
     (visually confirmed via screenshot — `textarea#user_message-value`'s content is
     NOT reliably readable via Playwright's `inner_text()` on the node container, see
     Automation Hints).
5. In `EDIT STATE KEY`: click the `Value` select and choose a listed state variable
   (e.g. `input`).
   - **Verify**: `EDIT STATE KEY` `Value` select shows the chosen variable. The EDIT
     route select (`ROUTER MAPPING` → EDIT → Route) becomes enabled the instant this
     is set (confirmed: `aria-disabled` attribute on that specific select goes from
     `"true"` to absent/`null`).
6. In `ROUTER MAPPING`: set APPROVE → an existing node (e.g. `Printer 1`); set EDIT →
   an existing non-END node (e.g. `LLM 1`) — now selectable because of step 5; set
   REJECT → `END` (or another node).
   - **Verify**: all three Route selects show their chosen target. EDIT's options
     list excludes `END` (confirmed live: `['LLM 1', 'Printer 1']` only, no `END`
     entry) — APPROVE/REJECT options include every other node plus `END`.
7. Click the pipeline's Save button (`agent-save-button`).
   - **Verify**: no console errors; `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` returns 2xx.
8. Reload the page at the pipeline's canonical URL.
   - **Verify**: after reload, the HITL node shows the persisted USER MESSAGE
     Type+Value, all three ROUTER MAPPING routes, and EDIT STATE KEY value —
     confirmed live via UI round-trip (not just an API read): APPROVE=`Printer 1`,
     EDIT=`LLM 1`, REJECT=`END`, EDIT STATE KEY=`input` all survived a real
     Save-click + full `page.reload()`.

## Expected Results
- HITL node config renders fully inline on the canvas card (no modal/panel to open).
- `Input`, `USER MESSAGE` (Type+Value), `ROUTER MAPPING` (APPROVE/EDIT/REJECT), and
  `EDIT STATE KEY` are all configurable and independently persist through Save +
  reload.
- EDIT route is only selectable once EDIT STATE KEY has a value — this is intended
  product behavior (validated live), not a defect; case texts must sequence EDIT
  STATE KEY before the EDIT route.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipeline exists with additional nodes to serve as HITL route targets | setup exists | Test Data / precondition | pipeline fixture topology | asserted |
| 1 Create pipeline, add HITL node via "Add node" → "Human-in-the-loop" | HITL node appears on canvas | step 1 | step 1: node count + id | asserted |
| 2 Click HITL node — verify panel shows Input/USER MESSAGE/ROUTER MAPPING/EDIT STATE KEY | all sections present | step 2 | step 2: all 4 sections visible | asserted — **CLARIFICATION: no click-to-open action exists; config is always inline/expanded on the card, same as every other node type in this codebase (MCP, LLM, etc.) — case text describing a "panel" that must be opened is stale relative to the live UI (reverse-masking guard). Not a defect: the sections themselves are exactly as described and are asserted.** |
| 3 Set Input combobox with relevant state variables | Input configured | step 3 | step 3: chips shown | asserted |
| 4 Set USER MESSAGE Type + Value | configured | step 4 | step 4: values shown | asserted |
| 5 In ROUTER MAPPING: APPROVE/EDIT/REJECT targets | all 3 routes configured | steps 5–6 | step 6: 3 Route selects | asserted *(decomposed — EDIT STATE KEY moved ahead of the EDIT route, see note below)* |
| 6 Set EDIT STATE KEY value | configured | step 5 | step 5: Value select shows chosen var | asserted |
| 7 Save pipeline | saves without errors | step 7 | step 7: no console errors, 2xx | asserted |
| 8 Reload — verify USER MESSAGE, all 3 routes, EDIT STATE KEY persist | all fields restored | step 8 | step 8: live UI round-trip of all 4 field groups | asserted |
| Expected Final State: HITL fully configured, all fields persist after reload | — | steps 7–8 | steps 7–8 | asserted |
| Pass/Fail: all steps complete without errors; all fields persist | — | all steps | all steps | asserted |

**CLARIFICATION on step ordering (case steps 5 then 6):** the case lists configuring
all three ROUTER MAPPING routes (step 5, including EDIT) BEFORE setting EDIT STATE
KEY (step 6). Live-confirmed: the EDIT route select is `aria-disabled` until EDIT
STATE KEY has a value, so following the case's literal order would leave the EDIT
route un-settable at step 5. This AFS's Test Steps reorder EDIT STATE KEY (AFS step
5) ahead of the EDIT route selection (part of AFS step 6) to match the live product's
actual requirement — a reverse-masking case-text drift, not a defect (filed as an
`EliteaAI/elitea-testing-public` `question`-labelled clarification, see Known
Defects). APPROVE/REJECT are unaffected by this ordering and can be set at any time.

### Axis 2 — Analyst additions

- Step 6 additionally asserts that the EDIT route's option list excludes `END` —
  *added: observed live (`['LLM 1', 'Printer 1']`, no `END`) and it is a real product
  constraint (an EDIT loop can't target the terminal node) worth guarding against a
  future regression that silently allowed it.*
- Step 5 additionally asserts the `aria-disabled` state flip on the EDIT route select
  before/after setting EDIT STATE KEY — *added: this is the mechanism behind the
  step-ordering clarification above; asserting it directly (not just "EDIT route is
  eventually settable") pins down exactly which product behavior justifies the
  reordered steps, so a future reviewer doesn't have to re-derive it.*
- No console-error assertion was in the original case text; added it throughout as a
  side-channel check — zero console errors were observed in this session.

## Cleanup

1. This session created a persistent pipeline (`autotest_hitl_2014_2015`, id `6757`)
   on the local DEV backend (project `399`) via the API for exploration, shared with
   ELITEA-2015's analysis in the same session. Deleted at the end of this session via
   `PipelineAPI.delete_pipeline(6757)` — confirmed removed.
2. Implementer teardown: use the existing `pipeline_id` fixture
   (`automation/fixtures/data_fixtures.py`) which creates-and-deletes an empty
   pipeline per test via `PipelineAPI`; add nodes via `PipelineDetailPage.add_node()`
   inside the test rather than seeding via a hand-built topology.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| HITL node on canvas | `[data-testid="rf__node-{node_id}"]` (dynamic, e.g. `rf__node-HITL 1`) | **on-main ✓** — ReactFlow's own testid convention; sanctioned third-party-widget handle per `.agents/testing.md` § Locator policy stop+flag exception #579 (same pattern as the existing MCP-node AFS). Also usable: `.react-flow__node-hitl` CSS class + `data-id` attribute — already relied on by `automation/pages/pipeline_detail_page.py`'s existing `wait_for_node_on_canvas("hitl")` / `get_node_ids()` methods (precedent, don't duplicate). | none needed |
| `Input` select (tool-agnostic state vars) | scoped inside the HITL node container, no stable selector today | **needs-adding**: `testid needed: pipeline-hitl-node-input-select`. The underlying `FlowEditorSelect.InputSelect` component ALREADY accepts a `dataTestId` prop that forwards to `data-testid` — this is a one-line wiring fix at the `HITLNode.jsx` call site (`<FlowEditorSelect.InputSelect id={id} ... dataTestId="pipeline-hitl-node-input-select" />`), not new component work. | none — flag to `add-data-testid`, do not ship a positional/CSS handle |
| `USER MESSAGE` Type select | scoped inside the HITL node, `id="simple-select-Type"` (NOT unique — collides with any other same-labeled select on the page) | **needs-adding**: `testid needed: pipeline-hitl-node-user-message-type-select`. `SimpleLLMInputItem.jsx` (shared component, also used by LLM/Printer nodes) has NO testid plumbing today — implementer must add a new prop. Per naming rule (testId/`<part>TestId`, never `dataTestId`), name it e.g. `typeSelectTestId` — do not reuse `InputSelect`'s existing `dataTestId` name for this NEW prop. | none — `id="simple-select-Type"` is non-unique, do not use even as a fallback |
| `USER MESSAGE` Value field | `textarea#user_message-value` (id is fixed per-node-TYPE, not per-instance — **will collide if a pipeline ever has 2+ HITL nodes**, a pre-existing latent issue, not introduced by this case) | **needs-adding**: `testid needed: pipeline-hitl-node-user-message-value-input`. Closest existing precedent: `InputMappingItem.jsx`'s `inputProps={dataTestId ? {'data-testid': dataTestId} : undefined}` pattern — apply the same shape to `NodeFieldInput`'s `commonProps` in `SimpleLLMInputItem.jsx`. | none — flag to `add-data-testid` |
| `ROUTER MAPPING` accordion (section container) | `BasicAccordion` — accepts a top-level `data-testid` prop already, just unset at the HITLNode.jsx call site | **needs-adding**: `testid needed: pipeline-hitl-node-router-mapping-section` (or a per-item `testId` field on the `items` array entry — `BasicAccordion` supports both mechanisms already). | none needed once wired — this is a one-line prop addition, no new component code |
| `ROUTER MAPPING` → APPROVE/EDIT/REJECT "Route" select (×3) | scoped inside the HITL node, `id="simple-select-Route"` — **confirmed duplicated 3× in the DOM** (all three share the same generic id because they share `label="Route"`); only positional `nth(0/1/2)` targeting works today | **needs-adding**: `testid needed:` dynamic per-action, `pipeline-hitl-node-route-select-{action}` (`{action}` ∈ `approve`/`edit`/`reject`) — same class-constant-template mechanism as other dynamic testids in this codebase (`.agents/testing.md` § Locator policy). `SingleSelect` already accepts `data-testid` and auto-derives `${data-testid}-combobox` — this is a one-line prop addition per action at the HITLNode.jsx call site (`data-testid={`pipeline-hitl-node-route-select-${action.value}`}`). | `nth()` positional only — brittle, do not ship without the testid |
| Route-select dropdown option (target node name) | `[data-testid="select-option-{node_name}"]` (e.g. `select-option-Printer 1`, `select-option-END`) | **on-main ✓** — `SingleSelect`'s option rendering already defaults every option's testid to `select-option-{value}` when no explicit `option.testId` is set; confirmed present and reliable, same pattern as the MCP-node AFS's toolkit/tool option locators. | none needed |
| `EDIT STATE KEY` "Value" select | scoped inside the HITL node, `id="simple-select-Value"` (non-unique — collides with any other "Value"-labeled select rendered elsewhere on the same node, though none currently coexist when USER MESSAGE Type=Fixed/F-String) | **needs-adding**: `testid needed: pipeline-hitl-node-edit-state-key-select`. `SingleSelect` already accepts `data-testid` — one-line prop addition at the HITLNode.jsx call site. | `#simple-select-Value` only while no other "Value" select coexists on the same node — do not rely on this, flag to `add-data-testid` |
| Pipeline Save button | `[data-testid="agent-save-button"]` | **on-main ✓** — confirmed present, already wired as `PipelineFormPage.save_button` (inherited by `PipelineDetailPage`). | none needed |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation (step 1's prerequisite, if not using the `pipeline_id` fixture).
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on Save click (step 7); persists the HITL node's full config (`user_message`, `routes`, `edit_state_key`) as part of the pipeline's YAML `instructions` field. Wait for this response (2xx) before reloading/asserting persistence in step 8, not a fixed timeout.
- `GET .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on page load/reload (step 8); the HITL node's rendered config is parsed directly from this response's YAML `instructions`, not from `pipeline_settings` (which only stores canvas layout metadata).

## Known Defects Found During Exploration

**None found in the HITL node's static configuration/persistence behavior itself** —
all of Input, USER MESSAGE (Type+Value), ROUTER MAPPING (all 3 routes), and EDIT
STATE KEY configure and persist correctly through Save + a real UI reload.

One case-text drift was identified and filed as a CLARIFICATION (not a bug), per the
reverse-masking guard:

- **[INFO] Case step ordering (ROUTER MAPPING before EDIT STATE KEY) doesn't match
  what the live UI requires** — the EDIT route select stays disabled until EDIT
  STATE KEY has a value. Filed as `EliteaAI/elitea-testing-public#1104` (label
  `question`) so the TMS case text can be corrected to sequence EDIT STATE KEY
  before the EDIT route. This AFS's Test Steps already reflect the corrected order.

Also see the sibling AFS `l2_hitl-node-runtime-behavior_ELITEA-2015.md` for a
**runtime** defect (`EliteaAI/elitea-testing-public#1103`) — the HITL node's resume
mechanism (Approve/Reject after pause) does not route as configured. That defect
does NOT affect this case (ELITEA-2014 never executes the pipeline; it only
configures and reloads), so this case's status stays `ready-for-automation`.

## Blocked Steps

None. All 8 case steps (as reordered) were executed to completion against the live
local environment, including a real Save-click + full `page.reload()` persistence
round-trip.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` — **this case
  requires `add-data-testid` work before implementation**: 6 of the 7 interactive
  HITL-node fields (Input, USER MESSAGE Type, USER MESSAGE Value, 3× Router-mapping
  Route, EDIT STATE KEY Value) have no `data-testid` today. Most are one-line prop
  additions at the `HITLNode.jsx` call sites (the underlying shared components
  already support `data-testid`/`dataTestId`); only `SimpleLLMInputItem.jsx` (USER
  MESSAGE Type+Value) needs new prop plumbing added to the shared component itself
  — see Concrete Handles for exact guidance and naming.
- No existing page-object method reads/writes an HITL node's inline config —
  `automation/pages/pipeline_detail_page.py` has generic node methods (`add_node`,
  `wait_for_node_on_canvas`, `delete_node`, `edit_node_name`, `connect_nodes`,
  `edge_exists`) but nothing for the HITL-specific fields. New page-object surface
  needed, e.g. `configure_hitl_node(node_id, user_message=..., routes={...},
  edit_state_key=...)` on `PipelineDetailPage`, following the same shape as the
  MCP-node AFS's suggested `configure_mcp_node()`.
- `textarea#user_message-value`'s content was NOT reliably readable via
  `Locator.inner_text()` when called on the whole node container (textarea values
  don't surface in `innerText`) — read it via `.input_value()` on the scoped
  textarea locator instead, once the testid exists.
- Wait strategy: wait for the `PUT .../application/prompt_lib/{project}/{pipeline_id}`
  response (2xx) before reloading/asserting persistence — not a fixed timeout.
- `PipelineAPI.create_pipeline_with_nodes(name, description, entry_point, nodes)`
  (`automation/api/client.py`) is the right helper for seeding a multi-node HITL
  precondition pipeline via YAML — confirmed working this session (created pipeline
  `6757` with the exact `LLM 1 → HITL 1 → Printer 1 → END` topology this case and
  ELITEA-2015 both need).
