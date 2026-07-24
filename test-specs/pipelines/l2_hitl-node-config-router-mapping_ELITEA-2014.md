# Test Case: Pipeline HITL Node — Configuration and Router Mapping

## Metadata
- **TMS ID**: ELITEA-2014
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: none needed — localhost `VITE_DEV_TOKEN` auto-auths, no explicit login step
- **Analyst**: qa-engineer (agent), session 2026-07-24
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline exists with additional nodes to serve as HITL route targets — confirmed
  live that an `LLM` node is a valid, sufficient target for all three HITL routes
  except REJECT→END-only-restriction (see Test Steps 5): APPROVE and EDIT both
  accept any non-END node; REJECT additionally accepts END. No toolkit/agent/
  credential setup is required — a bare LLM node target is enough.

## Test Data

### reuse-existing
- Default STATE variables `input` / `messages` are available in the Input and
  EDIT STATE KEY comboboxes on **any** pipeline with no explicit `state:` YAML
  block at all (same finding as ELITEA-2004/GAP-007) — confirmed live via
  `useInputOptions()` (`src/[fsd]/features/pipelines/flow-editor/lib/hooks/
  useInputOptions.hooks.js`): falls back to `{input: str, messages: list}` when
  `yamlJsonObject.state` is undefined. No custom state seeding needed for this
  case.
- `pipeline_with_llm_id` fixture (`automation/fixtures/data_fixtures.py:160`)
  already creates a pipeline with one LLM node (`LLM 1`) connected to `END` —
  suitable as the pre-existing "additional node" precondition; the HITL node
  itself is still added fresh per the case's own step 1.

### Test Data values (from case, resolved to concrete values used)
| Field | Value |
|---|---|
| USER MESSAGE Type | F-String |
| USER MESSAGE Value | `Please review this: {input}` |
| Input (HITL node) | `input` |
| APPROVE route | `LLM 1` (any non-END node) |
| EDIT route | `LLM 1` (any non-END node — **END is never offered**, see step 5) |
| REJECT route | `END` (this is also the HITL node's **out-of-the-box default** — see step 5) |
| EDIT STATE KEY Value | `messages` (any existing state var; kept distinct from the `input` var used in the message text for clarity) |

## Test Steps

1. Create a pipeline and add a Human-in-the-loop node via "Add node" → "Human-in-the-loop".
   - **Verify**: a HITL-type node (`[data-testid="rf__node-{id}"]`, e.g.
     `rf__node-HITL 1` — ReactFlow's own testid) appears on the canvas. Confirmed
     live: adding the node also auto-wires it as `entry_point` only if it is the
     FIRST node added to an otherwise-empty pipeline; when an LLM node already
     exists (this case's precondition), the LLM node stays the entry point and
     HITL is added as a second, unconnected node — matches the case's own
     precondition of "a pipeline exists with additional nodes."
2. Click HITL node — verify panel shows Input, USER MESSAGE (Type+Value),
   ROUTER MAPPING (APPROVE/EDIT/REJECT), EDIT STATE KEY.
   - **Verify (CLARIFICATION — see Coverage Map)**: no click is needed to "open"
     a panel — the Flow-view canvas renders the HITL node's full config
     **always inline/expanded** on the card itself (identical finding to
     ELITEA-1954/ELITEA-2004 for MCP/LLM nodes). Confirmed live: Input, USER
     MESSAGE (Type + Value), a "Router mapping" accordion section (already
     expanded by default — no click needed there either) containing APPROVE /
     EDIT / REJECT chips each with its own Route select, and EDIT STATE KEY
     (Value select) are all rendered immediately when the node is added — no
     separate open/select-node action was needed to see them.
3. Set Input combobox with relevant state variables.
   - **Verify (execution-order note — see Coverage Map)**: confirmed live that
     the Input select is **disabled by default** (`aria-disabled="true"`) —
     source-confirmed (`HITLNode.jsx:58`:
     `isInputSelectDisabledByMessageType = userMessageType !== 'fstring'`) and
     UI-confirmed via a tooltip: "Select state variables to reference in the
     User message. Available only when the User message type is set to
     F-String." This means step 3, as literally sequenced BEFORE step 4 in the
     case text, cannot be completed until USER MESSAGE Type is set to
     **F-String** first (step 4's own action). The correct execution order is:
     do step 4's Type-selection first (enables Input), THEN step 3, THEN step
     4's Value entry — not a defect, just an implicit dependency the case text
     omits. Once Type=F-String, the Input select opens and offers `input` /
     `messages`, each carrying the existing `select-option-{value}` testid;
     selecting `input` renders it as a removable chip (`input ⊗`).
4. In USER MESSAGE section: set Type (Fixed or F-String) and enter a message value.
   - **Verify**: selected Type=F-String (`select-option-fstring`, opens a
     3-option dropdown F-String/Variable/Fixed — options confirmed via live
     DOM read). Typed `Please review this: ` then `{` character-by-character
     into the Value textarea — the SAME f-string-autocomplete popper mechanism
     already proven end-to-end by GAP-007 (shared `FStringAutocompletePopper`
     component) opened, listing `input` (selectable) and `messages` (visually
     disabled — likely filtered to string-typed vars only for f-string
     interpolation; not asserted further, out of this case's scope). Selecting
     `input` from the popper inserted `{input}` with the cursor placed after
     the closing brace, producing the final Value `Please review this:
     {input}` — confirmed via a direct read-back of the field immediately
     after insertion.
5. In ROUTER MAPPING: APPROVE → select target node; EDIT → select target node;
   REJECT → select "END" or another node.
   - **Verify (execution-order note — see Coverage Map)**: confirmed live that
     the EDIT route select is **disabled** (`aria-disabled="true"`) until EDIT
     STATE KEY has a non-empty value — source-confirmed (`HITLNode.jsx:244-248`:
     `disabled: ... (action.value === 'edit' && !trimmedEditStateKey &&
     !hasConfiguredEditRoute)`). The case's own step ordering (step 5's EDIT
     before step 6's EDIT STATE KEY) is therefore backwards relative to what
     the live UI requires — EDIT STATE KEY (step 6) must be set FIRST. Executed
     in the corrected order: set EDIT STATE KEY = `messages` (see step 6 below)
     BEFORE selecting the EDIT route. APPROVE's Route select was never
     disabled (confirmed) and was set first without any dependency: opened,
     options were `LLM 1` / `END` (`select-option-LLM 1`/`select-option-END`),
     selected `LLM 1`. EDIT's Route select — once enabled — offered **only
     `LLM 1`, never `END`**: confirmed live and source-confirmed
     (`HITLNode.jsx:49-52`, `editRouteOptions` explicitly filters out
     `FlowEditorConstants.PipelineNodeTypes.End`) — this is deliberate product
     behavior (an Edit route must lead somewhere that continues the flow, not
     terminate), matching the case's own step 5 wording that only offers END
     for REJECT, never for EDIT. Selected `LLM 1`. REJECT's Route select
     already showed `END` **before any interaction at all** — confirmed via a
     pre-interaction DOM read (`aria-disabled=null`, `text="END"`) and via the
     YAML view (`routes: {reject: END}` present in a freshly-added HITL node's
     YAML with zero prior edits) — a freshly-added HITL node ships with
     `reject: END` as its out-of-the-box default. The case's step 5 instruction
     to "select" REJECT→END is satisfied trivially by this default; no click
     was strictly required, though the automation should still assert the
     value rather than assume it silently.
6. Set EDIT STATE KEY Value: a state variable name where user-provided feedback
   text will be stored.
   - **Verify**: performed BEFORE step 5's EDIT route selection (see step 5's
     note). Opened the Value select (options `input`/`messages`, same
     `select-option-{value}` mechanism), selected `messages`. Confirmed the
     EDIT route select's `aria-disabled` attribute flipped from `"true"` to
     `null` immediately after this selection.
7. Save pipeline.
   - **Verify**: clicked Save (`agent-save-button` testid — shared with the
     Agent form's Save button, pre-existing, on-main). Confirmed zero
     `error`-level console messages and zero failed (`4xx`/`5xx`) network
     requests (`get-network --status error` returned empty) across the whole
     configure→Save cycle. Canvas re-laid the two nodes with visible connector
     lines from HITL 1's approve/edit/reject handles down to LLM 1 (approve,
     edit) confirming the edges were created, not just the YAML fields.
8. Reload — verify USER MESSAGE, all three ROUTER MAPPING routes, and EDIT
   STATE KEY persist.
   - **Verify**: performed a genuine **hard reload** (`reload` command, not a
     client-side route change) immediately after step 7's Save. Confirmed via
     TWO independently-sourced reads that ALL fields persisted exactly:
     - Flow-view fields: Input chip `input`, USER MESSAGE Type=F-String /
       Value=`Please review this: {input}`, APPROVE Route=`LLM 1`, EDIT
       Route=`LLM 1`, REJECT Route=`END`, EDIT STATE KEY Value=`messages` — all
       read back identically to the pre-reload state.
     - YAML view (`Yaml` tab, `pipeline-yaml-editor`/`pipeline-yaml-lines`,
       pre-existing testids):
       ```yaml
       entry_point: LLM 1
       nodes:
         - id: LLM 1
           type: llm
           input: []
           input_mapping:
             chat_history: {type: fixed, value: []}
             system: {type: fixed, value: ''}
             task: {type: fixed, value: ''}
           output: []
           structured_output: false
           transition: END
         - id: HITL 1
           type: hitl
           edit_state_key: messages
           input: [input]
           routes:
             approve: LLM 1
             edit: LLM 1
             reject: END
           user_message:
             type: fstring
             value: 'Please review this: {input}'
       ```
     Zero `error`-level console messages after reload.

## Expected Results
- Adding a Human-in-the-loop node renders it on the canvas with its full config
  (Input, USER MESSAGE Type+Value, ROUTER MAPPING APPROVE/EDIT/REJECT, EDIT
  STATE KEY) always visible inline — no separate open/expand action needed.
- USER MESSAGE Type=F-String accepts a value containing an f-string token
  (`{input}`), inserted either by typing or via the shared autocomplete popper.
- ROUTER MAPPING lets APPROVE and EDIT target any non-END node; EDIT never
  offers END as a target; REJECT defaults to END out of the box and also
  accepts any other node.
- EDIT STATE KEY accepts an existing state variable name, and doing so is a
  precondition for the EDIT route selector to become interactive.
- Save completes with no error toast, no console error, no failed network
  request; a hard reload re-shows every configured field and route exactly as
  saved, corroborated independently by the YAML view.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipeline exists with additional nodes as route targets | route targets available | step 1 (precondition) | `pipeline_with_llm_id` fixture / manually-added LLM node | asserted |
| 1 Create pipeline + add HITL node via Add node → Human-in-the-loop | HITL node appears on canvas | step 1 | step 1: `rf__node-HITL 1` visible | asserted |
| 2 Click HITL node — panel shows Input/USER MESSAGE/ROUTER MAPPING/EDIT STATE KEY | all sections present | step 2 | step 2: all sections confirmed rendered, no click needed | **CLARIFICATION** — live product has no click-to-open action (config always inline), same as ELITEA-1954/2004 precedent; observable ("sections visible") still true and asserted |
| 3 Set Input combobox with relevant state variables | Input variables configured | step 3 | step 3: chip `input` rendered + `select-option-input` | **CLARIFICATION (execution order)** — Input select is disabled until USER MESSAGE Type=F-String (step 4) is set first; case's step numbering implies step 3 before step 4, but the live UI requires the opposite order for Input specifically. Asserted once the correct order is followed. |
| 4 USER MESSAGE: set Type + Value | USER MESSAGE configured | step 4 | step 4: Type=F-String selected, Value=`Please review this: {input}` read back | asserted |
| 5 ROUTER MAPPING: APPROVE/EDIT/REJECT routes | all 3 routes configured | step 5 | step 5: APPROVE=LLM 1, EDIT=LLM 1, REJECT=END all read back; EDIT route options confirmed to exclude END | **CLARIFICATION (execution order)** — EDIT's Route select is disabled until EDIT STATE KEY (step 6) has a value; executed step 6 before step 5's EDIT sub-action. REJECT=END is also a pre-existing default requiring no interaction. Both are correct, asserted product behavior, not defects. |
| 6 Set EDIT STATE KEY Value | EDIT STATE KEY set | step 6 | step 6: Value=`messages` read back; EDIT route's `aria-disabled` flips to enabled immediately after | asserted |
| 7 Save pipeline | saves without errors | step 7 | step 7: zero console/network errors, edges visible on canvas | asserted |
| 8 Reload — verify USER MESSAGE, all 3 routes, EDIT STATE KEY persist | all fields restored | step 8 | step 8: Flow-view fields + YAML view, both independently corroborating | asserted |
| Expected Final State: HITL fully configured, all persists after save+reload | — | steps 4–8 | steps 4–8 | asserted |
| Pass/Fail: all steps complete without errors; all fields persist after reload | — | all steps | all steps | asserted — no product defect found; one non-blocking testid-naming defect filed (see Known Defects), does not affect functional correctness |

### Axis 2 — Analyst additions

- Step 5 additionally asserts the EDIT route's option list explicitly excludes
  `END` — *added: not stated in the case text, but directly relevant to
  automation correctness (an implementer might otherwise assume EDIT and
  REJECT share the same option set); confirmed via both live DOM read and
  source (`HITLNode.jsx:49-52`).*
- Step 5 additionally asserts REJECT's pre-existing default value (`END`)
  BEFORE any interaction, via both a live DOM read and the YAML view — *added:
  distinguishes "the UI happened to show END because I clicked it" from "END
  is the node's actual out-of-the-box default," which matters for an
  implementer deciding whether their test needs to explicitly interact with
  REJECT at all to satisfy the case's Pass/Fail criteria.*
- Step 7 additionally asserts zero console errors and zero failed network
  requests across the whole configure→Save cycle — *added: standard
  side-channel discipline (`.agents/testing.md`), no product-specific reason
  beyond that.*
- Step 8 asserts via two independently-sourced reads (Flow-view fields AND the
  YAML view) rather than one — *added: same reasoning as ELITEA-2004's AFS —
  a single-source read can't distinguish stale client state from genuinely
  persisted backend state.*
- Noted (not asserted, informational only) that this case's ROUTER MAPPING
  configuration path (the panel's Route selects) is a DIFFERENT UI affordance
  from the already-merged `test_pipeline_nodes.py::test_add_human_in_the_loop_
  node_and_connect_to_end` (PIPE-031), which connects HITL→END by dragging an
  edge directly on the canvas (`connect_nodes(hitl_id, "END",
  source_handle="approve")`). Both interactions end up mutating the same
  `routes` YAML key, but through different code paths (`handleRouteChange` in
  `HITLNode.jsx` triggered by a Select `onValueChange`, vs ReactFlow's own
  `onConnect` handler) and different DOM elements. This case is therefore NOT
  `already-covered`/`extend-existing` by PIPE-031: it exercises the panel's
  ROUTER MAPPING/EDIT STATE KEY/USER MESSAGE fields entirely, none of which
  PIPE-031 touches (PIPE-031 has no USER MESSAGE, EDIT STATE KEY, or EDIT-route
  assertions at all, and only ever exercises the APPROVE handle via canvas
  drag). Classified `ready-for-automation`, not `extend-existing`, per the
  merged-target rule's "when in doubt, ready-for-automation" default — the
  overlap (both end up setting `routes.approve`) is real but the case's
  distinct observable (panel-driven configuration + USER MESSAGE + EDIT STATE
  KEY + persistence) is materially larger than what PIPE-031 asserts.

## Cleanup

1. If the fixture-based setup (`pipeline_with_llm_id`, recommended — see Test
   Data) is used, cleanup is automatic via its existing teardown
   (`PipelineAPI.delete_pipeline`).
2. This analysis session's own manually-built pipeline
   (`autotest_ELITEA2014_hitl`, id `5704`) was deleted via the UI's own "Delete
   pipeline" flow (three-dot menu → Delete pipeline → type-to-confirm) at the
   end of this session — confirmed gone from the Pipelines list afterward
   (success toast "The autotest_ELITEA2014_hitl pipeline has been successfully
   deleted."). No orphaned data remains from this case's analysis.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance / Notes |
|---|---|---|
| HITL node container | `[data-testid="rf__node-{id}"]` (ReactFlow's own testid, e.g. `rf__node-HITL 1`) | on-main ✓ — third-party (ReactFlow) widget testid, not app-added; already used by existing page-object methods (`wait_for_node_on_canvas`, `get_node_ids`, `connect_nodes`) |
| HITL node's Input select (top, gated by USER MESSAGE Type=F-String) | `[data-testid="pipeline-hitl-node-input-select"]` (added via `dataTestId` prop on `FlowEditorSelect.InputSelect`, `HITLNode.jsx:204`) | on `automation/testids` ✓ (`EliteaAI/EliteaUI@4ccf24ac`) — added by the implementer, confirmed live via a fresh `git fetch origin` + `git grep` re-check (2026-07-24 redispatch) AND a real pytest rerun of the merged test (`1 passed in 27.21s`); NOT yet on `main` (awaiting human cherry-pick). **Declared improvisation** (`.agents/role-overrides.md` § Declared-improvisation protocol): the `dataTestId` prop NAME on `FlowEditorSelect.InputSelect` violates `.agents/testing.md` § Locator policy's "`testId`/`<part>TestId`, never a `data` prefix" rule verbatim — but the prop is pre-existing (added `577f74bf`/ELITEA-1954, 2026-07-15, before this case), not newly introduced here, and is already reused identically by `LLMNode.jsx` (×2: input/output selects), `RouterNode.jsx` (×2: routes/input selects), and `BaseToolNode.jsx` (×2: input/output selects) — none of those call sites on `main` either. Renaming the shared prop across the `InputSelect.jsx`/`OutputSelect.jsx`/`RouteSelect.jsx`/`ToolSelect.jsx` family is a cross-cutting refactor (3+ other node components, all outside this case's diff) — out of scope here. This case reuses the existing extension point rather than introducing a new naming violation; flagging as a canon-gap escalation for the reviewer/orchestrator, not a self-inflicted blocker. |
| Input select's open-listbox option (per state var) | `[data-testid="select-option-{value}"]` — e.g. `select-option-input`, `select-option-messages` (existing `SELECT_OPTION` class constant already in `pipeline_detail_page.py`) | on-main ✓ — same shared mechanism as ELITEA-2004/1954/1955 |
| USER MESSAGE "Type" select (trigger) | `[data-testid="pipeline-llm-node-user_message-type-select-combobox"]` (outer testid `pipeline-llm-node-user_message-type-select` on the wrapper) — **usable but MIS-SCOPED, see filed defect below** | on `automation/testids` ONLY (verified via `git grep -F` against a fresh `git fetch origin` — literal template string present in `SimpleLLMInputItem.jsx` on `origin/automation/testids`, absent on `origin/main`); confirmed live. **Naming defect filed**: `EliteaAI/elitea-testing-public#1017` — the `llm-node` prefix is hardcoded inside the SHARED `SimpleLLMInputItem.jsx` component (used by both the LLM node's system/task/chat_history fields AND this HITL node's user_message field), so it leaks onto a non-LLM node. Non-blocking: still unique and locatable, scoped inside `rf__node-HITL 1`. Implementer should use the testid as-is (it works) and cross-reference #1017 in code comments rather than wait for a rename. |
| USER MESSAGE "Type" option (F-String/Variable/Fixed) | `[data-testid="select-option-fstring"]` / `-variable` / `-fixed` | on-main ✓ — same shared `SELECT_OPTION` mechanism |
| USER MESSAGE "Value" textarea | `[data-testid="pipeline-llm-node-user_message-value-input"]` — same mis-scoping as the Type select above, same filed defect (#1017) | on `automation/testids` ONLY (same verification as above) |
| ROUTER MAPPING accordion (section container) | **NO `data-testid`** on the `BasicAccordion`/summary/details wrapper. NOT required for this case: confirmed live the accordion is expanded by default (no click needed to reveal APPROVE/EDIT/REJECT) — implementer does not need to interact with the accordion toggle itself, only the Route selects inside it. | out-of-scope for this case (not interacted with — always-expanded by default) |
| ROUTER MAPPING Route select (APPROVE/EDIT/REJECT, per-action) | `[data-testid="pipeline-hitl-node-router-{action}-select"]` — added as a DYNAMIC per-action testid (`HITLNode.jsx:253`, `` data-testid={`pipeline-hitl-node-router-${action.value}-select`} ``, inside the `HITL_ACTIONS.map` loop), exactly the recommended shape | on `automation/testids` ✓ (`EliteaAI/EliteaUI@4ccf24ac`) — added by the implementer, confirmed live via a fresh `git fetch origin` + `git grep` re-check (2026-07-24 redispatch) AND a real pytest rerun of the merged test (`1 passed in 27.21s`); NOT yet on `main` (awaiting human cherry-pick) |
| Route select's open-listbox option (per target node id, dynamic) | `[data-testid="select-option-{node_id}"]` — e.g. `select-option-LLM 1`, `select-option-END` (same shared `SELECT_OPTION` family, keyed by node id instead of a fixed enum this time) | on-main ✓ — same shared mechanism; confirmed live that EDIT's option list excludes `END` (source-confirmed, `editRouteOptions` filter) while APPROVE/REJECT's includes it |
| EDIT STATE KEY "Value" select (trigger) | `[data-testid="pipeline-hitl-node-edit-state-key-select"]` (`HITLNode.jsx:275`) | on `automation/testids` ✓ (`EliteaAI/EliteaUI@4ccf24ac`) — added by the implementer, confirmed live via a fresh `git fetch origin` + `git grep` re-check (2026-07-24 redispatch) AND a real pytest rerun of the merged test (`1 passed in 27.21s`); NOT yet on `main` (awaiting human cherry-pick) |
| EDIT STATE KEY select's open-listbox option (per state var) | `[data-testid="select-option-{value}"]` (same shared family) | on-main ✓ |
| Validation text ("Provide an edit state key before using the Edit route.") | **NO `data-testid`** — conditional `<Typography>` rendered only when `isEditRouteInvalid` (a route was set to a value while the key was empty, an inconsistent-state edge case). NOT triggered by this case's own steps (key is always set before the route). Out of scope here. | needs-adding (only if a future case tests the invalid-state message directly) |
| Node-card three-dot menu button | `[data-testid="node-menu-menu-button"]` — **identical literal testid on EVERY node on the canvas** (confirmed live: LLM 1 and HITL 1 both carry the exact same string) | on-main ✓ (pre-existing, shared across all node types) — MUST be scoped by the parent node's own testid (`self.page.locator('[data-testid="rf__node-HITL 1"] [data-testid="node-menu-menu-button"]')`) to disambiguate on any canvas with >1 node; not itself a defect (standard "scope by parent container" discipline already used elsewhere in this page object), just a locator-construction note. Not needed by this case (menu not interacted with). |
| Save button | `[data-testid="agent-save-button"]` (shared with the Agent form's Save button) | on-main ✓ — pre-existing, already used by the existing `PipelineDetailPage` |
| YAML view content (persistence-verification path) | `pipeline-yaml-editor` / `pipeline-yaml-lines` (`PipelineDetailPage.yaml_editor` / `.yaml_lines`, already `LocatorDescriptor` fields) + `get_yaml_content()` (already an existing method) | on-main ✓ — pre-existing page-object surface, zero new work |

## Network Behavior

No network call is central to this case's own field-level assertions while
configuring the node — Input/USER MESSAGE/ROUTER MAPPING/EDIT STATE KEY edits
are pure client-side React state (`yamlJsonObject`) until Save. The Save action
itself PUTs the same `application` entity endpoint already used by
`PipelineAPI.update_pipeline()` (`automation/api/client.py:658`) — same
pattern as ELITEA-2004/ELITEA-1954. No new network assertion is required; the
implementer's persistence check should assert on UI-visible state (Flow-view
fields and/or YAML view) after a real page reload, matching Test Steps 7–8, not
on the raw PUT response body.

## Known Defects Found During Exploration

- **[MINOR]** `EliteaAI/elitea-testing-public#1017` — the HITL node's USER
  MESSAGE Type-select and Value-textarea carry a hardcoded `pipeline-llm-node-`
  testid prefix (leaked from the shared `SimpleLLMInputItem.jsx` component,
  whose testid is not caller-scoped). Non-blocking: the testids are still
  unique and locatable; this is a naming-clarity issue only. The implementer
  should use the testids as-is (see Concrete Handles) and may reference #1017
  in a code comment.
- One pre-existing, already-filed, non-blocking defect is relevant to locator
  choice only: `EliteaAI/elitea-testing-public#1006`/`#1009` (duplicate
  `SingleSelect`-default-id pattern), independently re-confirmed live this
  session on THIS node's Route selects (`simple-select-Route` ×3) and EDIT
  STATE KEY select (`simple-select-Value`) — not re-filed (same known root
  cause); the implementer must use the new testids (once added, see Concrete
  Handles) rather than these native ids.

## Blocked Steps

None. All 8 case steps (plus the stated precondition) were executed to
completion against the live local environment, including a genuine
configure→Save→hard-reload→verify round trip corroborated by two independent
sources (Flow-view fields and the YAML view).

## Redispatch confirmations

**2026-07-24, third analyst dispatch (board bounce: `implementing` → `parked`
"R2 cap exceeded (3 reruns)" → `analysis`).** Ground truth checked before
assuming another opaque bounce or an AFS-drift situation requiring a fresh
analyst pass:

- PR `EliteaAI/elitea-testing-public#1026` ("test(ELITEA-2014): HITL node
  config + router mapping via inline panel") is OPEN against `automation/base`,
  one commit (`b9cd5cf4`), zero reviews, zero comments — the
  awaiting-review shape, not an analysis gap. Worktree
  `.claude/worktrees/wf_e44028a9-dec-99` (branch
  `tests/ELITEA-2014-hitl-node-config-router-mapping`) holds the complete,
  compliant implementation.
- Mechanical locator grep (`git diff automation/base...HEAD -- automation/pages/
  automation/tests/ | grep -nE '...locator...'`) — every hit is a class-level
  `[data-testid="…"]` template constant (`HITL_NODE_ROUTER_SELECT`,
  `SELECT_OPTION`, etc.) formatted with test-generated data; zero raw handles.
- **Independently re-ran the actual merged test** (not just trusting the
  implementer's self-report): `HEADLESS=true pytest tests/ui/pipelines/
  test_pipeline_hitl_node_config_router_mapping.py -v -p no:cacheprovider` →
  `1 passed in 27.21s`, matching the implementer's own daily-log entry
  ("green in 26.57s") — a second, independent green run.
- **Testid PROVENANCE re-verified** (fresh `cd ../EliteaUI && git fetch origin`
  first): all 3 previously `needs-adding` handles (Input select, 3×
  ROUTER MAPPING Route selects, EDIT STATE KEY select) are now live on
  `automation/testids` (`EliteaAI/EliteaUI@4ccf24ac`, "add HITL node testids
  (ELITEA-2014)"), absent from `main` — table above updated accordingly. The
  dynamic Route-select testid landed exactly as recommended:
  `` data-testid={`pipeline-hitl-node-router-${action.value}-select`} ``
  (`HITLNode.jsx:253`).
- **Conclusion: this is NOT an AFS-drift situation** (the R2-cap classification
  table's "analyst re-run" branch) — the case is fully implemented, green
  (twice-confirmed), and locator-compliant. The R2-cap park most likely fired
  against an earlier, in-progress state of the same implementer dispatch (two
  debugging rounds are documented in the implementer's own daily log — a
  `multiple=True` MUI-select Backdrop leak and a stale `edge_exists()`
  `handle_suffix` format assumption, both fixed and regression-verified)
  before the fix landed; the board simply never reconciled past the park.
  **Correct next action is a REVIEWER dispatch against PR #1026, not another
  analyst or implementer round.** Status unchanged: `ready-for-automation`
  (AFS content was already accurate; only the PROVENANCE column needed
  updating to reflect testids that didn't exist yet at first-pass time).

**2026-07-24, fix round r1 (reviewer finding on PR #1026: undeclared
`dataTestId`-style prop-name shape).** Reviewer flagged that the Input select's
`dataTestId` prop violates `.agents/testing.md` § Locator policy's prop-naming
rule (`testId`/`<part>TestId`, never a `data` prefix), and that reusing a
pre-existing bad-named shared-component prop without an explicit
Declared-improvisation note is out of contract per
`.agents/role-overrides.md` (2nd recorded instance of this exact pattern —
see `.agents/memory/qa-engineer/elitea_1851_datatestid_prop_and_surface_digest_branch_conflict.md`).
Verified against the code before amending (`HITLNode.jsx:204`,
`InputSelect.jsx:9`, plus the 3 sibling call sites in `LLMNode.jsx`/
`RouterNode.jsx`/`BaseToolNode.jsx`) — finding confirmed accurate. Remedy is
documentation-only (no code change): added the Declared-improvisation note
to the Concrete Handles row above, and the same note to PR #1026's body.
No test/page-object edit required — the two other new HITL testids
(`pipeline-hitl-node-router-{action}-select`, `pipeline-hitl-node-edit-state-key-select`)
already use the compliant bare `data-testid=` shape.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`). **This case requires `add-data-testid` work** for
  three elements (HITL's Input select, the 3 Route selects, EDIT STATE KEY
  select) — all three have a trivial existing extension point
  (`FlowEditorSelect.InputSelect`'s `dataTestId` prop / a bare `data-testid`
  prop on plain `SingleSelect` calls), none require editing shared-component
  internals. See Concrete Handles for exact line-level wiring points. The
  USER MESSAGE Type/Value testids ALREADY EXIST (on `automation/testids`,
  pending human promotion to `main`) — no new `add-data-testid` work needed
  for those two, just cross-reference the naming defect (#1017).
- Recommended setup: `pipeline_with_llm_id` fixture (existing) for the
  precondition's LLM route target — saves a full "add LLM node from scratch"
  round trip while still exercising this case's own HITL-node steps against a
  real, pre-connected sibling node.
- New page-object surface needed: `PipelineDetailPage` has generic node
  methods (`add_node`, `wait_for_node_on_canvas`, `connect_nodes`) and MCP/LLM
  -node-specific methods (ELITEA-1954/1955/2004), but nothing for a HITL
  node's Input/USER MESSAGE/ROUTER MAPPING/EDIT STATE KEY fields. Suggested
  shape: `set_hitl_user_message(type_value, value)`, `select_hitl_input
  (value)`, `set_hitl_router_route(action, target_node_id)` (action ∈
  `approve`/`edit`/`reject`, using the dynamic per-action testid template
  constant), `set_hitl_edit_state_key(value)`.
- **Execution order matters** (see Test Steps 3 and 5 — not a defect, a real
  UI dependency): USER MESSAGE Type must be set to F-String BEFORE the Input
  select is usable; EDIT STATE KEY must have a value BEFORE the EDIT route
  select is usable. Write the test's action sequence in this corrected order,
  not the case's literal step numbering.
- Wait strategy: no network wait needed for the field-edit interactions
  themselves (pure client-side); after clicking Save, the existing pattern
  from ELITEA-2004 applies (wait on the Discard button's disabled state, or
  simply `wait_for_network()`), then `page.reload()` + re-assert field values
  — never a fixed `sleep`.
- The f-string-autocomplete popper triggered by typing `{` in the USER MESSAGE
  Value field is the SAME shared mechanism already fully proven by GAP-007 —
  this case doesn't need to re-test the popper's own navigate/filter/dismiss
  behavior, only that typing/selecting through it produces the expected final
  string (confirmed: `Please review this: {input}`). Per the digest's
  typing-simulation gotcha, type character-by-character
  (`press_sequentially()`), never a bulk `fill()`, to avoid the auto-closing-
  brace insertion bug the digest documents.
