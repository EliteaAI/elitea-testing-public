# Test Case: Subgraph State Sharing — Common State Variables

## Metadata
- **TMS ID**: ELITEA-2443
- **Linked Story**: none
- **Priority**: l2 (source: `medium`, matching sibling cases ELITEA-2038/ELITEA-2064's
  own medium→l2 mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-09
- **Status**: ready-for-automation
- **surface_key**: pipeline-run-details

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- **CLARIFICATION (terminology, confirmed live + via source read this session):** the
  case's title says "Subgraph" — but the dedicated `pipeline`/subgraph flow-editor
  NODE TYPE (`SubgraphNode.jsx`) is **legacy/deprecated** and is **not one of the 11
  modern node types offered by the Add Node menu** (confirmed against the merged
  `l2_pipeline-add-node-menu_ELITEA-2030.md`'s live-verified exact 11-item list —
  no "Pipeline" entry; corroborated by the bundled `elitea-pipeline` skill's
  `yaml-schema.md`: *"Nested pipelines are gone → delegate to an `agent` node"*).
  The case's own step 3 ("add an Agent node calling the child pipeline") already
  names the CORRECT, current mechanism — no case-text drift here, just a title
  that uses the legacy term for what the live product implements via the modern
  `agent` node. Document this so the implementer doesn't go looking for an
  add-node-menu "Pipeline"/"Subgraph" entry that doesn't exist.
- **A pipeline can only be selected by an Agent node's "Agent" combobox after it has
  been ATTACHED via the Tools section's "+ Pipeline" popper** (same mechanism as
  ELITEA-2064) — confirmed live this session: authoring `tool: <child_pipeline_name>`
  directly in an Agent node's YAML WITHOUT first attaching renders
  `"Agent not found — select a replacement or delete this node"` even though the
  name is byte-correct. The attach is a real precondition step, not implicit.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Child pipeline**, built via the GENERIC `PipelineAPI.create_pipeline()` (raw YAML
  `instructions` string, same technique as `pipeline_with_typed_state_vars_id` /
  ELITEA-2453's fixture) with:
  - `state: {messages: {type: list}, state_1: {type: str}, state_2: {type: number}}`
  - One `code` node (`structured_output: true`, `input: [state_1, state_2]`,
    `output: [state_1, state_2]`) whose `code.value` is a fixed Python dict literal
    that overwrites both, e.g. `{"state_1": "child_value", "state_2": 99}`,
    `transition: END`.
  - Confirmed live: this deterministic recipe is exactly what's needed — no LLM call,
    no flakiness, no ELITEA-2453-style `messages`+dict/list-in-`output` pitfall
    (this recipe's `output` never includes `messages`).
- **Parent pipeline**, same `create_pipeline()` technique, with:
  - Same `state:` block (`messages`, `state_1: str`, `state_2: number`).
  - Node 1: a `code` node identical in shape to the child's, setting ONLY
    `state_1` (e.g. `{"state_1": "parent_value"}`), `input`/`output: [state_1]`,
    `transition: <Agent node id>`.
  - Node 2: an `agent`-type node, `input: [input]`, `output: [messages]`,
    `input_mapping: {task: {type: fixed, value: "<any text>"}, chat_history:
    {type: fixed, value: []}}`, `transition: END`. **Its `tool:` field alone does
    NOT resolve the child** — see Preconditions; the attach step (below) is required
    even when the YAML already names the right pipeline.
- Both pipelines need `pipeline_api.delete_pipeline()` teardown (`try/finally`,
  same two-pipeline pattern as ELITEA-2064's Pipeline A/B fixture recipe — no
  existing fixture provisions a parent+child PAIR, so this is new, minimal, Rule-7/
  Rule-10-justified test data).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).

## Test Steps

1. Create the child pipeline via `pipeline_api.create_pipeline()` per the recipe above.
   - **Verify**: `201`/`200`, response has a numeric `id` and the version's `id`.
2. Create the parent pipeline via `pipeline_api.create_pipeline()`, with its Agent
   node's `tool:` field pre-set to the child pipeline's `name`.
   - **Verify**: same as step 1.
3. Navigate to the parent pipeline's configuration page
   (`${BASE_URL}/pipelines/all/{parent_id}?destTab=configuration&viewMode=owner`).
   - **Verify**: canvas renders both nodes; the Agent node shows
     `"Agent not found — select a replacement or delete this node"` (expected —
     the tool isn't attached yet, see Preconditions) and an empty "Agent" combobox.
4. In the left panel's Tools accordion, click the "+ Pipeline" button
   (`agent-add-pipeline-button`, `PipelineDetailPage.open_pipeline_popper()`).
   - **Verify**: a picker popper opens (search input + `toolkit-menu-item` rows).
5. Select the child pipeline by name
   (`PipelineDetailPage.select_pipeline_in_popper(popper, child_name, project_id)`).
   - **Verify**: the method's own hard-block on
     `PATCH .../application_relation/prompt_lib/{project}/{child_id}/{child_version_id}`
     → `201 Created` — confirmed live this session, same endpoint/mechanism as
     ELITEA-2064/ELITEA-2038.
6. Re-inspect the Agent node.
   - **Verify**: the "Agent not found" message is gone; the "Agent" combobox now
     shows the child pipeline's name — confirmed live
     (`get_agent_node_agent_value() == child_name`).
7. Execute the parent pipeline via the embedded chat (send any message — the entry
   trigger is Chat Message; the message text is irrelevant to this case, only the
   node graph's own logic runs).
   - **Verify**: `wait_for_embedded_chat_response()` — response arrives, run
     completes (no execution error).
8. Open Run Details (`open_run_details_panel()` — click the `pipeline-run-node-label`
   run entry above the canvas).
   - **Verify**: panel opens, header status = `"Completed"`
     (`get_run_details_status_badge_text()`).
9. Confirm the Timeline shows the CHILD pipeline's execution nested in the SAME
   panel/timeline as the parent's own nodes — **NEW finding, not covered by any of
   the single-pipeline ELITEA-2450/2451/2452/2453 sibling cases** (all of which only
   exercise a single, non-nested pipeline).
   - **Verify** (confirmed live this session, 5-entry timeline for a
     code→agent(child)→END parent):
     `["pyodide" (parent CODE node), "<child_pipeline_name>" ×2, "pyodide" (child's
     own CODE node), "AGENT1"]` — i.e. `get_run_details_timeline_step_count() == 5`
     for this exact 2-node parent + 1-node child fixture, and
     `get_run_details_timeline_step_node_id(1) == "<child_pipeline_name>"` (0-indexed;
     the child's steps appear as entries 1–3, between the parent's CODE node (0) and
     final AGENT1 wrap-up (4)). **Case step 6's "Click on the Agent node step" is
     satisfied by selecting the LAST timeline entry (`AGENT1`, index 4)** — there is
     no separate "Agent node" click target outside the timeline itself; the case's
     "click on the Agent node step in the timeline" IS clicking that timeline entry.
   - **CLARIFICATION**: exact step count/labels/order are fixture-shape-dependent
     (they will differ for a different parent/child node composition) — the
     implementer's assertion should key off structural properties (count ≥ 3, the
     child's name appears at least once, the final entry is the Agent node's own id)
     rather than hardcoding this exact 5-tuple, unless the fixture recipe above is
     used verbatim.
10. Expand the `state_1` state-variable accordion row
    (`expand_run_details_state_row("state_1")`).
    - **Verify**: `get_run_details_state_before_value("state_1") == '"parent_value"'`
      (JSON-stringified, per the existing ELITEA-2453 type-rendering rule — quoted
      string) — confirmed live: Before reflects the value the PARENT's own CODE node
      set, before the Agent node ran. This satisfies case step 7 ("Verify state
      Before shows state_1 with value set by the preceding parent node").
    - **Verify**: `get_run_details_state_after_value("state_1") == '"child_value"'`
      — confirmed live: After reflects the value the CHILD pipeline's own CODE node
      set during its nested execution. **This is the case's core assertion, CONFIRMED
      TRUE live**: common-named state variables ARE shared between a parent
      pipeline and a pipeline attached-as-tool to an Agent node — the child's write
      to `state_1` propagates back into the PARENT's own state, visible in the
      SAME Run Details panel.
11. Expand the `state_2` state-variable accordion row.
    - **Verify**: `get_run_details_state_before_value("state_2") == ''` (empty —
      confirmed live: the parent never touched `state_2`, so Before is the
      variable's un-set default) and
      `get_run_details_state_after_value("state_2") == '99'` (bare numeral, no
      quotes — per the existing ELITEA-2453 number-type rendering rule). This
      satisfies case step 8 ("Verify state After shows state_1 and state_2 updated
      by child pipeline execution") for the second variable.
12. Confirm both `state_1` and `state_2`'s After values match the child's own writes
    exactly (`"child_value"` / `99`) — satisfies case step 9 ("Confirm common-named
    variables shared data between parent and child").

## Expected Results
- A pipeline attached via the Tools section "+ Pipeline" popper becomes selectable
  in an `agent`-type node's "Agent" combobox — the SAME attach mechanism ELITEA-2064
  documents, now confirmed as the precondition an Agent node needs to resolve a
  pipeline-as-tool reference (a bare `tool:` YAML field is NOT sufficient by itself).
- Executing the parent pipeline runs the attached child pipeline's own node graph
  nested inside the SAME Run Details timeline/state panel — the child's execution is
  NOT opaque; its own timeline steps and state read/writes are visible.
- **Common-named state variables (`state_1`, `state_2`) ARE shared between parent and
  child**: a value the child's own node sets is reflected as the AFTER value of the
  SAME-NAMED variable in the parent's Run Details panel. This confirms the case's
  central hypothesis is TRUE on the current (non-deprecated, `agent`-node-based)
  mechanism — despite the modern `agent` node's documented schema (per the bundled
  `elitea-pipeline` skill) showing only a `task`-string-in / `messages`-string-out
  contract with no explicit state-passing fields. The state sharing is implicit and
  automatic for any variable that exists (by name) in BOTH pipelines' `state:` blocks
  — not something the Agent node's own `input_mapping` configures.
- No console errors beyond the pre-existing KNOWN `#1267` Stepper prop-leak warning
  (fires once per panel open regardless of nesting — same signature as
  ELITEA-2450/2451's documented occurrence).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in | setup exists | step 3 | step 3: panel visible | asserted |
| 1 Create child pipeline with state_1/state_2 + Code/LLM node modifying both | operation completes | step 1 | step 1: create response `id` present | asserted (Code node used, not LLM — deterministic, avoids LLM flakiness; both are valid "Code/LLM" per the case's own "Code/LLM node" wording) |
| 2 Create parent pipeline with state_1/state_2 | operation completes | step 2 | step 2: create response `id` present | asserted |
| 3 In parent: Code/LLM sets state_1, Agent node calls child, connect to END | completes without error | steps 2, 4-6 | step 2: YAML shape; steps 4-6: attach + Agent-node resolution confirmed live | asserted — **CLARIFICATION: the Agent node's `tool:` field must be paired with a Tools-section attach (steps 4-5); YAML alone is insufficient (see Preconditions)** |
| 4 Execute parent with input | completes without error | step 7 | step 7: `wait_for_embedded_chat_response()` | asserted |
| 5 Open Run Details after execution | panel loads | step 8 | step 8: panel visible, status Completed | asserted |
| 6 Click on Agent node step in timeline | control responds | step 9 | step 9: select last timeline entry (`AGENT1`) — **CLARIFICATION: no separate "Agent node" UI target exists outside the timeline entry itself; case step 6 IS selecting that entry** | asserted |
| 7 Verify state Before shows state_1 set by preceding parent node | condition holds | step 10 | step 10: `get_run_details_state_before_value("state_1") == '"parent_value"'` | asserted |
| 8 Verify state After shows state_1 and state_2 updated by child execution | condition holds | steps 10-11 | step 10: state_1 After = `"child_value"`; step 11: state_2 After = `99` | asserted — **CORE CASE ASSERTION, CONFIRMED TRUE LIVE** |
| 9 Confirm common-named variables shared data between parent and child | operation completes | step 12 | step 12: both After values match child's writes exactly | asserted |

### Axis 2 — Beyond-case observables

| Observable | Why asserted |
|---|---|
| Agent node shows "Agent not found" before attach (step 3) | Documents the real precondition ordering — an implementer who authors the YAML with `tool:` pre-set (the natural approach for a fixture) needs to know the attach step is still required, or their fixture will render a permanently-broken node |
| Run Details timeline nests the child's own steps (step 9) | This is the mechanism THROUGH WHICH state sharing becomes observable/provable — without it there'd be no way to assert "the child's write" independently of "the parent's own state" |
| state_2 Before = empty string (step 11) | Distinguishes "variable never touched by parent" from "variable touched but unchanged" — confirms the child, not some parent-side coincidence, is the source of the After value |

## Cleanup
- `pipeline_api.delete_pipeline(child_id)` and `pipeline_api.delete_pipeline(parent_id)`
  in `finally` blocks (order doesn't matter — no FK constraint observed deleting the
  parent before the child in this session's probe).

## Concrete Handles (discovered during exploration)

All handles below are PRE-EXISTING `LocatorDescriptor`/page-object methods —
**zero new testid work needed for this case** (confirmed via source grep of
`automation/pages/pipeline_detail_page.py` this session; every method the case
needs already ships from ELITEA-2030/2038/2042/2064/2450/2451/2452/2453's own
implementation work).

| Element / action | Handle | Provenance |
|---|---|---|
| "+ Pipeline" Tools-section button | `agent-add-pipeline-button` → `PipelineDetailPage.open_pipeline_popper()` | on-main? unconfirmed this session — added `EliteaAI/EliteaUI@e2130cf4` on `automation/testids` per ELITEA-2064's digest entry; re-verify at implementation time |
| Pipeline picker popper rows | `toolkit-menu-item` (shared `UnifiedDropdown.jsx`) → `Popper.select_menuitem_by_testid()` | on-main (pre-existing shared component) |
| Select pipeline + wait for attach PATCH | `PipelineDetailPage.select_pipeline_in_popper(popper, name, project_id)` | existing method, `pipeline_detail_page.py:5576` |
| Agent node's "Agent" combobox value | `PipelineDetailPage.get_agent_node_agent_value()` / `select_agent_node_agent()` | existing, `pipeline_detail_page.py:4208/4214` — added `EliteaAI/EliteaUI@2859a9d0` on `automation/testids` (ELITEA-2038); re-verify on-main at implementation time |
| Add Node menu → "Agent" item | `PipelineDetailPage.select_add_node_menu_item("agent")` | existing, `pipeline_detail_page.py:3106` (ELITEA-2030 testids) |
| STATE panel "+" control | `PipelineDetailPage.add_state_variable(name)` | existing, `pipeline_detail_page.py:7901` |
| Run label above canvas | `pipeline-run-node-label` → `open_run_details_panel()` | existing, `pipeline_detail_page.py:7020` (ELITEA-2450 testids) |
| Run Details status badge | `pipeline-run-details-status-badge` (`data-status`) → `get_run_details_status_badge_text()` | existing (ELITEA-2450) |
| Timeline step count / node-id / select | `pipeline-run-details-timeline-step-{index}` (+ prefix selector) → `get_run_details_timeline_step_count()`, `get_run_details_timeline_step_node_id(i)`, `select_run_details_timeline_step(i)` | existing (ELITEA-2451) |
| State row expand / Before / After | `pipeline-run-details-state-row-{variable}` → `expand_run_details_state_row()`, `get_run_details_state_before_value()`, `get_run_details_state_after_value()` | existing (ELITEA-2452) |
| Pipeline create with raw `state:` block | `PipelineAPI.create_pipeline(name, description, instructions=<yaml>)` | existing, `automation/api/client.py:616` — same technique as `pipeline_with_typed_state_vars_id` fixture |

## Network Behavior
- Pipeline attach: `PATCH .../application_relation/prompt_lib/{project}/{child_id}/{child_version_id}` → `201 Created` (same mechanism as ELITEA-2064/ELITEA-2038, confirmed live this session with real ids 8779/9041).
- Pipeline execution: Socket.IO only, no dedicated REST endpoint for run/timeline/state (same as documented for ELITEA-2450) — confirmed no new endpoint appears for the nested-child case either.
- Run Details panel: zero new network activity on step-select/row-expand (same as ELITEA-2452's finding) — confirmed for the nested-timeline case too.

## Known Defects Found During Exploration
- None new. The pre-existing `EliteaAI/elitea-testing-public#1267` (Stepper prop-leak
  console warning, one non-boolean-attribute React warning per panel open) fires
  here too — same known signature, not a new occurrence to file.

## Blocked Steps
- None.

## Automation Hints
- Build both pipelines via the generic `PipelineAPI.create_pipeline()` (raw YAML) —
  `create_pipeline_with_nodes()` has no `state:` support (documented gap, ELITEA-2453).
- The child pipeline's name must be known BEFORE constructing the parent's YAML (the
  Agent node's `tool:` field takes the child's `name` string) — create the child
  first, capture its `name` from the create response, then build the parent's YAML.
- Don't skip the Tools-section attach step even though the YAML already names the
  child pipeline — it is a real runtime precondition, confirmed live (see
  Preconditions), not an artifact of a specific fixture shape.
- Timeline entry count/order is fixture-shape-dependent (see Test Step 9's
  clarification) — assert structurally (count, child-name presence, last-entry id),
  not the literal 5-tuple, unless reusing this AFS's exact 2-node-parent/1-node-child
  recipe verbatim.

## What the analyst filled in
- Executed live end-to-end this session (pipeline ids 8779 child / 8780 parent,
  project 399), including the attach-precondition discovery, the nested-timeline
  discovery, and the Before/After state-value confirmation. Both probe pipelines
  deleted at session end (`pipeline_api.delete_pipeline()`), confirmed via delete
  API calls returning cleanly.
- Evidence: `test-results/screenshots/ELITEA-2443-step-08-state-before-after.png`
  (Run Details panel, `state_1`/`state_2` rows expanded, Before/After values visible).
