# Test Case: Pipeline — Agent Node Integration

## Metadata
- **TMS ID**: ELITEA-2038
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst/Implementer**: test-automation-engineer (agent, combined analysis+build slot), session 2026-08-08
- **Status**: ready-for-automation
- **surface_key**: pipeline-agent-node

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- An existing agent is available in the project (Test Data's "IssueTriageSpecialist" is illustrative — this
  session used a fresh, disposable agent created via `AgentAPI.create_agent()`, matching the sibling
  ELITEA-2037's pattern of not depending on a specific pre-existing name).
- **CLARIFICATION (case-text drift, same class as the sibling node cases in this family — Code/2009,
  State modifier/2035, Custom/2036, MCP/2037):** the case's Test Data table lists `normalized_issue`,
  `kb_results` (Input) and `triage_summary` (Output) as if directly selectable. Live-confirmed (this
  session): a fresh pipeline's Input/Output combos on the Agent node list only `input`/`messages` until
  the 3 variables are added as custom pipeline state variables via the STATE panel's "+" control first —
  they are not freeform/creatable fields. Handled as a Step 0 (setup) ahead of the case's own step 1,
  same convention as the sibling AFSes.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A **fresh, empty pipeline** (no nodes/edges pre-seeded — this case IS the "from scratch" flow: attach
  Agent to Tools, add the node, configure it). `PipelineAPI.create_pipeline(name, description)` (empty
  `pipeline_settings`), same as ELITEA-2037's fixture choice.
- A **fresh, disposable agent** to attach — reuse the existing `agent_id` fixture
  (`automation/fixtures/data_fixtures.py:82`, `AgentAPI.create_agent()`, auto torn down). The fixture
  yields only the numeric id; the test resolves the display name via `agent_api.get_agent(agent_id)["name"]`
  (no new fixture needed — `agent_api` is already a registered session-scoped fixture).
- 3 custom pipeline state variables (`normalized_issue`, `kb_results`, `triage_summary`), added via the
  STATE panel's "+" control (Step 0 — see Preconditions clarification above).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).

## Test Steps

0. **(Setup, not a case step)** Create the 3 custom state variables via the STATE panel.
   - **Verify**: STATE panel lists all 3 after adding.
1. Navigate to a fresh, empty pipeline's configuration page.
   - **Verify**: Configuration panel is visible; canvas loads with only the `END` node.
2. In the left panel "Tools" section, click "+ Agent" button (`agent-add-agent-button`, inside
   `agent-toolkits-section`).
   - **Verify**: an agent-picker popup (listbox of project agents) opens.
3. From the Agent picker, select an existing agent (the fixture-created agent).
   - **Verify**: the popup's listbox item (`toolkit-menu-item` testid, exact name match) is clicked;
     the picker auto-persists immediately — `PATCH .../application_relation/prompt_lib/{project}/{agent_id}/{agent_version_id}`
     returns `201 Created` (confirmed live this session — **a DIFFERENT endpoint from the sibling
     Toolkit/MCP pickers**, which use `PATCH .../tool/prompt_lib/{project}/`; same auto-persist-on-select
     *behavior*, different underlying mutation — `useAgentPipelineAssociation.hooks.js`'s
     `updateApplicationRelation`, not `ToolMenu.jsx`'s generic toolkit-attach path). Dismiss the popper
     with `Escape`.
4. Verify agent appears in Tools list under Agent sub-tab.
   - **Verify**: an attached-item card (`agent-toolkit-card`, shared with Toolkit/MCP) renders with the
     agent's name. **Same "no sub-tab" clarification already filed for the sibling MCP/Agent-level Tools
     sections (`EliteaAI/elitea-testing-public#1149`, sibling of `#530`)** — the Toolkit/MCP/Agent/Pipeline
     buttons are 4 independent ADD triggers sharing ONE flat attached-items list, not view-filter tabs.
     Not re-filed as a new issue — same root cause, already tracked.
5. Click "Add node" on canvas (`pipeline-add-node-button`) → select "Agent" (`pipeline-add-node-menu-item-agent`).
   - **Verify**: an "Agent 1" node appears on the canvas (ReactFlow wrapper `[data-testid="rf__node-Agent 1"]`),
     auto-wired as the pipeline's entry point (first/only node).
6. Verify Agent node panel shows: Agent dropdown, Input combobox, Output combobox, INPUT MAPPING
   (REQUIRED 1) with TASK section (Type+Value), Interrupt before/after switches.
   - **Verify — confirmed live, split into two sub-states (same two-stage-reveal pattern as the sibling
     Toolkit/MCP/Custom nodes, ELITEA-2010/2037/2036)**:
     - **Before any Agent is selected**: Trigger (entry-point-only, "Chat Message"), **Agent** select
       (empty), **Input**, **Output**, **Interrupt before** (switch, `disabled` — entry point), **Interrupt
       after** (switch, `disabled` — default transition is `END`) are ALL present immediately.
       **INPUT MAPPING is ABSENT from the DOM** (not just hidden) until an Agent is selected —
       `AgentNode.jsx`'s `{!isOrphan && <InputMapping .../>}` gate. **No "Structured output" switch
       exists at all for this node type** (`AgentNode.jsx` passes `showStructuredOutput={false}` to
       `CommonInterruptSettings`, confirmed via source AND live DOM — this is a genuine, permanent
       divergence from the case text's step 6 wording, which does not mention Structured output either,
       so no clarification is needed; just an Axis-2 absence assertion).
     - **After the Agent is selected**: "Input mapping (required 1)" accordion appears with one row
       labelled **"Task"** (raw schema key `task`, capitalised for display — same `capitalizeFirstChar`
       convention as every other node's Input-mapping labels).
7. Select attached agent from "Agent" dropdown.
   - **Verify**: Agent combobox shows the selected agent's name; the INPUT MAPPING section appears (see
     step 6's split verification above).
8. Set Input combobox — add state variables "normalized_issue", "kb_results".
   - **Verify**: both variables show as selected chips in the Input combobox (multi-select,
     `role="listbox" aria-multiselectable="true"`, same as every sibling node's Input field).
9. Set Output combobox — add output variable "triage_summary".
   - **Verify**: Output combobox shows "triage_summary" (single-select — closes the popper on selection).
10. In INPUT MAPPING (REQUIRED 1) → TASK: set Type to "F-String", Value: "Triage this critical GitHub
    issue. Issue: {normalized_issue}".
    - **Verify — CLARIFICATION (case-text drift, minor)**: Type's default value for the TASK field is
      **already "F-String"** (confirmed live, this session) — not "Fixed" as every sibling node's
      Input-mapping default (Toolkit/MCP tool parameters default to `Fixed`). The case's step 10 phrasing
      ("set Type to F-String") implies an action; live behavior makes this a verification of the
      pre-existing default rather than a state change. Not a defect — the test asserts the Type value
      equals `"F-String"` either way (whether by explicit selection or by confirming the default), so the
      case's expected result is satisfied regardless of which reading is correct. Fill the Value field.
11. Save pipeline.
    - **Verify**: `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}`
      returns `201 Created`; zero console errors across the whole flow (confirmed live this session).
12. Reload — verify Agent selection, Input, Output, and TASK mapping persist.
    - **Verify**: after reload, the Agent node shows the persisted state — Tools-section attachment card
      still present, node's Agent/Input/Output/TASK Type+Value all match what was configured in steps
      7–10, byte-for-byte (confirmed live this session — full round-trip verified).

## Expected Results
- An agent can be attached to a pipeline's Tools section via the "+ Agent" button, rendering as a
  flat-list attached card (no "sub-tab", same established pattern as Toolkit/MCP).
- A fresh Agent node can be added via the canvas "Add node" → "Agent" menu; its config panel is
  always-expanded inline with no click-to-open step.
- The static config fields (Agent, Input, Output, Interrupt before/after) are present immediately on an
  unconfigured node; NO Structured output switch ever renders for this node type; INPUT MAPPING (TASK)
  renders conditionally once an Agent is selected.
- Selecting an Agent reveals exactly one required Input-mapping field (TASK), defaulting to Type
  "F-String".
- Filling the TASK value, setting Input/Output, and saving persists everything; a full page reload with
  the canonical URL confirms all of it survives unchanged.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in; an existing agent available | setup exists | steps 1–3 | step 1: panel visible; step 3: agent selectable | asserted |
| 1 Open a pipeline | Pipeline is open for editing | step 1 | step 1: config panel + canvas visible | asserted |
| 2 Click "+ Agent" button | Agent picker opens | step 2 | step 2: popup listbox visible | asserted |
| 3 Select an existing agent from the picker | Agent is selected | step 3 | step 3: option clicked + 201 attach response | asserted |
| 4 Verify agent appears in Tools list under Agent sub-tab | Agent listed under the Agent sub-tab | step 4 | step 4: `agent-toolkit-card` presence + name | asserted — **CLARIFICATION, same root cause as `#1149`/sibling `#530`: no "sub-tab" exists live, one flat list. Not re-filed.** |
| 5 Add node → select "Agent" | Agent node added to canvas | step 5 | step 5: `rf__node-Agent 1` present | asserted |
| 6 Verify Agent node panel shows: Agent dropdown, Input, Output, INPUT MAPPING (REQUIRED 1) with TASK (Type+Value), Interrupt before/after switches | All listed sections present | steps 6–7 | step 6: static sections present pre-Agent-select + absence of Structured output; step 7: Input-mapping section present post-Agent-select | asserted — **split across pre/post-select states, same two-stage-reveal pattern as sibling node types; documented, not a defect.** |
| 7 Select attached agent from "Agent" dropdown | Agent selected in dropdown | step 7 | step 7: combobox value | asserted |
| 8 Set Input combobox — add "normalized_issue", "kb_results" | Both variables added | step 8 (+ Step 0 setup) | step 8: combobox chips | asserted |
| 9 Set Output combobox — add "triage_summary" | "triage_summary" added | step 9 (+ Step 0 setup) | step 9: combobox value | asserted |
| 10 TASK: set Type to "F-String", Value to the given text | TASK mapping configured | step 10 | step 10: Type value + Value text | asserted — **CLARIFICATION: default Type is already "F-String", not "Fixed" like sibling nodes. Case's expected result satisfied either way.** |
| 11 Save pipeline | Pipeline saves without errors | step 11 | step 11: 201 + zero console errors | asserted |
| 12 Reload — verify Agent, Input, Output, TASK mapping persist | All configuration persists | step 12 | step 12: full field-by-field re-read | asserted |
| Expected Final State: Agent node fully configured, persisting after save+reload | — | steps 7–12 | steps 7–12 | asserted |
| Pass/Fail: all steps complete without errors; config persists after reload | — | all steps | all steps | asserted |

### Axis 2 — Analyst/implementer additions

- Step 0 (setup) creates the 3 custom state variables ahead of the case's own step 1 — *added because the
  case's Test Data table implies they pre-exist, but live behavior requires them to be created first
  (same pattern as every sibling node-config case in this family).*
- Step 6 additionally asserts the **absence** of the INPUT MAPPING section before an Agent is selected,
  AND the **permanent absence** of a Structured output switch for this node type (`to_have_count(0)` /
  not-in-DOM checks) — *added because a naive implementation might assert only the post-configuration
  state and silently miss verifying the empty/gated state, which is exactly what a future regression
  (e.g. INPUT MAPPING rendering before an Agent is chosen) needs to be caught by.*
- Step 3 additionally asserts the specific attach endpoint (`/application_relation/prompt_lib/`, NOT
  `/tool/prompt_lib/`) — *added because this is a genuine implementation divergence from the sibling
  Toolkit/MCP pickers that share the same UI component; a regression guard here catches either endpoint
  silently breaking.*
- No console-error assertion was in the original case text; added it throughout as a side-channel check —
  standard practice per this project's `test-case-analysis` skill; zero console errors were observed
  across the whole flow this session.

## Cleanup

1. This session's live exploration created a disposable probe agent (`autotest_2038_probe_agent`, id
   `8127`) and a disposable probe pipeline (`autotest_2038_probe_pipe`, id `8128`) — **both deleted by
   this session** via `AgentAPI.delete_agent()` / `PipelineAPI.delete_pipeline()` immediately after
   exploration. No residue left in the environment.
2. Implementer teardown for its OWN test data: the `agent_id` fixture's own teardown
   (`AgentAPI.delete_agent()`) + `PipelineAPI.delete_pipeline(pipeline_id)` for the fixture-created
   pipeline.

## Concrete Handles (discovered during exploration)

**PROVENANCE — verified this session via `cd ../EliteaUI && git fetch origin` + `git grep` against BOTH
`origin/main` and `origin/automation/testids` (2026-08-08).**

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Add-Agent button (Tools section) | `agent_add_agent_button` / `[data-testid="agent-add-agent-button"]` — pre-existing, shared with agent forms (already an `AgentDetailPage` field, newly ported to `PipelineDetailPage`) | **on-main** | none needed |
| Tools-section container | `[data-testid="agent-toolkits-section"]` | **on-main** | none needed |
| Attached agent card (shared) | `[data-testid="agent-toolkit-card"]` | **on-main** | none needed |
| Agent-in-search-popper option | `toolkit-menu-item` testid (same `UnifiedDropdown` mechanism as Toolkit/MCP pickers) | **on-main** | none needed |
| Agent node on canvas | `[data-testid="rf__node-{node_display_name}"]` (dynamic, e.g. `rf__node-Agent 1`) | on-automation/testids only (ReactFlow's own convention — sanctioned #579 exception) | none — testid-only |
| Add-node menu "Agent" item | `[data-testid="pipeline-add-node-menu-item-agent"]` — confirmed working live | on-automation/testids only (`main:no`) | none needed |
| Agent node's Agent select | `agent_node_agent_select` / `[data-testid="pipeline-agent-node-agent-select"]` — **NEW this session**, added via `add-data-testid` (`AgentNode.jsx`) | needs-adding — `EliteaAI/EliteaUI@2859a9d0` on `automation/testids` | none needed |
| Agent node's Input select | `agent_node_input_select` / `[data-testid="pipeline-agent-node-input-select"]` — **NEW this session** | needs-adding — `EliteaAI/EliteaUI@2859a9d0` on `automation/testids` | none needed |
| Agent node's Output select | `agent_node_output_select` / `[data-testid="pipeline-agent-node-output-select"]` — **NEW this session** | needs-adding — `EliteaAI/EliteaUI@2859a9d0` on `automation/testids` | none needed |
| Agent node's Input-mapping "required N" heading | `agent_node_input_mapping_required_heading` / `[data-testid="pipeline-agent-node-input-mapping-heading"]` — **NEW this session** | needs-adding — `EliteaAI/EliteaUI@2859a9d0` on `automation/testids` | none needed |
| Agent node's TASK Value field | `AGENT_NODE_INPUT_MAPPING_VALUE` class constant / `[data-testid="pipeline-agent-node-input-mapping-value-task"]` — **NEW this session** | needs-adding — `EliteaAI/EliteaUI@2859a9d0` on `automation/testids` | none needed |
| Agent node's TASK Type select | `AGENT_NODE_INPUT_MAPPING_TYPE` class constant / `[data-testid="pipeline-agent-node-input-mapping-type-task"]` — **NEW this session** | needs-adding — `EliteaAI/EliteaUI@2859a9d0` on `automation/testids` | none needed |
| Agent node's Interrupt after toggle | `agent_node_interrupt_after_toggle` / `[data-testid="pipeline-agent-node-interrupt-after-toggle"]` — **NEW this session** | needs-adding — `EliteaAI/EliteaUI@2859a9d0` on `automation/testids` | none needed |
| Agent node's Interrupt before toggle | `NODE_INTERRUPT_BEFORE_TOGGLE` class constant / `[data-testid="pipeline-node-interrupt-before-toggle-{node_id}"]` (dynamic, keyed by node id, unconditional for every node type) — already exists on `PipelineDetailPage` | on-automation/testids only (`main:no`, per the ELITEA-2034 correction) | none needed |
| Select dropdown option (Agent/Input/Output share this pattern) | `[data-testid="select-option-{value}"]` — confirmed working, e.g. `select-option-autotest_2038_probe_agent`, `select-option-normalized_issue`, `select-option-triage_summary` | on-automation/testids only (generic `SingleSelect` mechanism) | none needed |
| STATE panel add-variable button/input | `pipeline_state_add_variable_button` / `pipeline_state_add_variable_name_input` — pre-existing `PipelineDetailPage` fields | on-automation/testids only | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` — confirmed, shared with agent/pipeline create-and-edit forms | **on-main** | none needed |

**No `optionalHeadingTestId`/`structuredOutputTestId` were wired** — the Agent node's INPUT MAPPING never
renders an optional section (the agent-as-tool schema has exactly one required key, `task`, and zero
optional ones), and `CommonInterruptSettings` never renders Structured output for this node type at all
(`showStructuredOutput={false}`) — wiring either would be an unreferenced, coverage-metric-corrupting
addition per `.agents/testing.md` § Locator policy.

## Network Behavior
- `PATCH ${ELITEA_API_BASE}/elitea_core/application_relation/prompt_lib/${PROJECT_ID}/{agent_id}/{agent_version_id}`
  — fires immediately on the Agent-attach popper selection (step 3), `201 Created` on success. **This is a
  DIFFERENT endpoint from the sibling Toolkit/MCP pickers** (`/tool/prompt_lib/{project}/`) — same
  auto-persist-on-select *behavior*, different underlying mutation
  (`useAgentPipelineAssociation.hooks.js`'s `updateApplicationRelation`, confirmed via source read AND
  live network capture this session).
- `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on the
  pipeline Save click (step 11); `201 Created` on success; this single request persists BOTH the
  Tools-section Agent attachment AND the node's Agent/Input/Output/TASK-mapping state.
- `GET ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on page
  load/reload (step 12); confirms persisted node config is what the Flow-view canvas renders from.

## Known Defects Found During Exploration

**None found in the Agent-node fresh-attach/add/configure/persist flow itself.** All 12 case steps
produced the expected result once the documented CLARIFICATIONs (Tools "sub-tab" wording — same root
cause as the already-tracked `#1149`/`#530`; TASK Type's pre-set "F-String" default; the custom-state-var
precondition) are accounted for: attach, add-node, Agent selection, Input-mapping fill, Input/Output
selection, save, and full-reload persistence all worked correctly with zero console errors across the
entire flow.

No new clarification issue filed — the "no sub-tab" finding is the same root cause already tracked as
`EliteaAI/elitea-testing-public#1149` (Tools section, sibling of `#530`), which covers this node type too
(the popper/attach mechanism is shared UI, `ToolMenu.jsx`).

## Blocked Steps

None. All 12 case steps were executed to completion against the live local environment (probe pipeline
8128 / probe agent 8127, both cleaned up).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`).
- Fixtures: `pipeline_id` (fresh empty pipeline, auto-torn-down) + `agent_id` (fresh disposable agent,
  auto-torn-down) — both already registered, no new fixture needed. Resolve the agent's display name via
  `agent_api.get_agent(agent_id)["name"]`.
- New page-object methods on `PipelineDetailPage`: `open_agent_popper()`, `select_agent_in_popper()`
  (mirrors `select_mcp_in_popper()` but waits on the `/application_relation/` PATCH, not `/tool/`),
  `select_agent_node_agent()`, `open_agent_node_input_select()` / `select_agent_node_input_variable()` /
  `get_agent_node_input_value()`, the Output equivalents, `is_agent_node_input_mapping_section_visible()`,
  `get_agent_node_input_mapping_type()`, `get_agent_node_input_mapping_value()`,
  `fill_agent_node_input_mapping_value()`.
- Wait strategy: wait for the `/application_relation/` PATCH (`201`) on attach, and
  `PUT .../application/prompt_lib/{project}/{pipeline_id}` (`201`) before reloading/asserting persistence
  — not fixed timeouts.
- Console-error capture: register `page.on("console", ...)` BEFORE Step 0 (matches the sibling AFSes'
  precedent) — this session's assertion covers the whole flow.
