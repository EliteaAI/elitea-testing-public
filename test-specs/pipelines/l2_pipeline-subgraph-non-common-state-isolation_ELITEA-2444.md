# Test Case: Subgraph State Sharing — Non-Common State Isolation

## Metadata
- **TMS ID**: ELITEA-2444
- **Linked Story**: none
- **Priority**: l2 (source: `high`; this folder has no l1 tier in use — every pipeline
  case so far, including the `medium`-priority sibling ELITEA-2443, maps to l2/l3;
  mapped consistently, not downgraded)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-09
- **Status**: ready-for-automation
- **surface_key**: pipeline-run-details

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- **Same "Subgraph" terminology note as ELITEA-2443** (confirmed live again this
  session, same mechanism): the case's title says "Subgraph" but the dedicated
  `pipeline`/subgraph flow-editor NODE TYPE is legacy/not offered by the modern Add
  Node menu — the case's own step 3 ("Agent node calling the child pipeline") already
  names the correct, current mechanism (an `agent`-type node with a `tool:` field).
- **Same attach precondition as ELITEA-2443** (re-confirmed live this session): an
  Agent node's `tool:` YAML field alone does NOT resolve a pipeline-as-tool
  reference — the child must ALSO be attached via the Tools section's "+ Pipeline"
  popper (`agent-add-pipeline-button` → `select_pipeline_in_popper()`), even when the
  YAML already names the correct child pipeline. Confirmed live: pre-attach, the
  Agent node shows "Agent not found — select a replacement or delete this node" and
  an empty Agent combobox; post-attach (`PATCH
  .../application_relation/prompt_lib/{project}/{child_id}/{child_version_id}` →
  `201`), the combobox resolves to the child's name.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Child pipeline** — `state: {messages: list, state_1: str, state_3: str}` (NOTE:
  **no `state_2` key at all** — this is the case's defining difference from
  ELITEA-2443, which gave the child `state_2` too). One `code` node
  (`structured_output: true`, `input: [state_1, state_3]`, `output: [state_1,
  state_3]`) whose fixed `code.value` overwrites both:
  `{"state_1": "child_value", "state_3": "child_only_value"}`, `transition: END`.
- **Parent pipeline** — `state: {messages: list, state_1: str, state_2: str}` (NOTE:
  **no `state_3` key at all**). Node 1 (`CODE1`): a `code` node setting BOTH
  `state_1` AND `state_2` (unlike ELITEA-2443's parent, which set only `state_1`) —
  `{"state_1": "parent_value", "state_2": "parent_only_value"}`, `input`/`output:
  [state_1, state_2]`, `transition: AGENT1`. Node 2 (`AGENT1`): identical shape to
  ELITEA-2443's (`input: [input]`, `output: [messages]`, fixed
  `task`/`chat_history`, `tool: <child_name>`), `transition: END`.
- Both pipelines built via the GENERIC `PipelineAPI.create_pipeline()` (raw YAML
  `instructions`) — same technique as ELITEA-2443/`pipeline_with_typed_state_vars_id`.
  `create_pipeline_with_nodes()` has no `state:` support.
- Both need `pipeline_api.delete_pipeline()` teardown (`try/finally`) — confirmed
  live, order-independent (no FK constraint deleting parent before child).
- **New fixture needed** — ELITEA-2443's `pipeline_parent_child_state_sharing`
  fixture is NOT reusable as-is: its child declares `state_2` (common with parent),
  which is exactly the condition this case needs to NOT hold. A sibling fixture
  (e.g. `pipeline_parent_child_state_isolation`) with the state schema above is
  needed — same YAML-builder pattern, different `state:` blocks per pipeline.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).

## Test Steps

1. Create the child pipeline via `pipeline_api.create_pipeline()` per the recipe
   above (`state_1`+`state_3`, no `state_2`).
   - **Verify**: `201`/`200`, response has a numeric `id`.
2. Create the parent pipeline via `pipeline_api.create_pipeline()` (`state_1`+
   `state_2`, no `state_3`), Agent node's `tool:` field pre-set to the child's name.
   - **Verify**: same as step 1.
3. Navigate to the parent pipeline's configuration page
   (`${BASE_URL}/pipelines/all/{parent_id}?destTab=configuration&viewMode=owner`).
   - **Verify** (confirmed live, pipeline id 8790): canvas renders `CODE1` and
     `AGENT1`; Agent node shows "Agent not found..." and an empty Agent combobox
     pre-attach.
4. Click the Tools accordion's "+ Pipeline" button (`agent-add-pipeline-button` →
   `open_pipeline_popper()`).
   - **Verify**: picker popper opens.
5. Select the child pipeline by name (`select_pipeline_in_popper(popper, child_name,
   project_id)`).
   - **Verify**: hard-blocks on the attach PATCH → `201 Created` (confirmed live,
     same endpoint as ELITEA-2443/2064/2038).
6. Re-inspect the Agent node.
   - **Verify**: "Agent not found" message gone; Agent combobox shows the child's
     name (confirmed live: `get_agent_node_agent_value() == child_name`).
7. Execute the parent pipeline via the embedded chat (send any message).
   - **Verify**: `wait_for_embedded_chat_response()` — response arrives, run
     completes.
8. Open Run Details (`open_run_details_panel()`).
   - **Verify**: panel opens, status badge = `"Completed"`.
9. Confirm the Timeline nests the child's own execution — **same structural shape
   ELITEA-2443's implementation found for this exact 2-node-parent/1-node-child
   recipe**: confirmed live, 4 timeline entries
   `["pyodide" (parent CODE1), "<child_name>" ×2, "pyodide" (child's own CODE1)]` —
   ending in the child's own CODE node, **not** a distinct trailing `AGENT1` entry.
   Assert structurally (count ≥ 3, child's name present among step ids), per
   ELITEA-2443's own Automation Hints, not this literal tuple.
10. **CORE CASE ASSERTION (step 8 of the TMS case) — confirm `state_3` does NOT
    appear in the parent's Run Details STATES panel at all.**
    - **Verify** (confirmed live this session, pipeline id 8790, at EVERY timeline
      step 0-3): `get_run_details_state_row_locator("state_3").count() == 0`. The
      panel renders exactly 3 accordion rows regardless of which timeline step is
      selected — `messages`, `state_1`, `state_2` — never `state_3`. This is a
      row-EXISTENCE check (no accordion to expand), not a Before/After value read.
11. Expand `state_1` (common var) with the LAST timeline step selected (matches
    ELITEA-2443's own selected-step convention).
    - **Verify**: `get_run_details_state_before_value("state_1") == '"parent_value"'`,
      `get_run_details_state_after_value("state_1") == '"child_value"'` — confirmed
      live, symmetric with ELITEA-2443's finding: common-named vars ARE shared.
      Satisfies case step 6 (state_1 Before/After differ, common var updated by
      child).
12. **IMPORTANT DISCOVERY — Run Details Before/After values are PER-TIMELINE-STEP,
    not run-level**, confirmed live this session (see § Known Defects/Platform
    Behavior below for full detail). Consequently, `state_2` (parent-only) must be
    read at **timeline step 0** (the parent's own `CODE1` execution, immediately
    before the Agent-node call) to see a populated value — at the LAST step (used
    for step 11's `state_1` read) `state_2`'s Before/After both render EMPTY, not
    because the value is unset but because the currently-selected step (the child's
    own node) doesn't declare `state_2` in its own input/output.
    - Select timeline step 0 (`select_run_details_timeline_step(0)`).
    - **Verify**: `get_run_details_state_before_value("state_2") == '""'` (empty —
      unset before CODE1 runs) and
      `get_run_details_state_after_value("state_2") == '"parent_only_value"'`
      (confirmed live: the value CODE1 itself set).
    - Select timeline step 1 (the first entry of the Agent/child call boundary).
    - **Verify**: `get_run_details_state_before_value("state_2") == '"parent_only_value"'`
      — confirmed live: identical to step 0's After value, proving continuity
      ACROSS the Agent-node boundary (the value entered the Agent step unchanged).
    - This before(step0-after)==before(step1) comparison satisfies case step 7
      ("Verify state_2 (parent-only, not in child) remains unchanged through the
      Agent node step") more precisely than a single-step read would, because a
      single step's blank rendering (e.g. at the LAST step, or mid-timeline steps
      1/2's own `After` fields, which are also blank for `state_2` since neither the
      Agent call nor the child ever writes it) could be misread as "value lost"
      rather than "step doesn't touch this variable."

## Expected Results
- **`state_3` (child-only, declared ONLY in the child pipeline's `state:` block)
  NEVER appears as a row in the parent's Run Details STATES panel, at any timeline
  step** — confirmed live, CENTRAL HYPOTHESIS OF THIS CASE CONFIRMED TRUE. Only
  variables the PARENT's own `state:` block declares (`messages`, `state_1`,
  `state_2`) render as rows; a child-only variable's existence is fully opaque to
  the parent's panel, unlike its VALUE writes for a common-named variable (which
  propagate, per ELITEA-2443).
- `state_2` (parent-only, declared ONLY in the parent's `state:` block) is set by
  the parent's own `CODE1` node and is never touched by the Agent-node call or the
  child's own execution — confirmed unchanged across the Agent-node boundary (step
  0's After == step 1's Before == `"parent_only_value"`).
- `state_1` (common-named, declared in BOTH pipelines) IS shared, symmetric with
  ELITEA-2443's finding on the same mechanism — not this case's central claim, but
  confirmed as a control/sanity check that the fixture's wiring is correct.
- No console errors beyond the pre-existing KNOWN `#1267` Stepper prop-leak warning
  (same signature as ELITEA-2443/2450/2451's documented occurrence — confirmed
  live, single occurrence, same call site `RunStateDialog.jsx`).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in | setup exists | step 3 | step 3: canvas visible | asserted |
| 1 Create child pipeline with state_1/state_3 — child modifies both | operation completes | step 1 | step 1: create response `id` present | asserted (Code node, deterministic — same rationale as ELITEA-2443) |
| 2 Create parent pipeline with state_1/state_2 | operation completes | step 2 | step 2: create response `id` present | asserted |
| 3 In parent: node sets state_1/state_2, Agent node calls child | completes without error | steps 2, 4-6 | steps 4-6: attach + Agent-node resolution confirmed live | asserted — same attach-precondition clarification as ELITEA-2443 |
| 4 Execute the parent pipeline | completes without error | step 7 | step 7: `wait_for_embedded_chat_response()` | asserted |
| 5 Open Run Details after execution | panel loads | step 8 | step 8: panel visible, status Completed | asserted |
| 6 Verify state_1 (common) updated by child — After differs from Before | condition holds | step 11 | step 11: Before `"parent_value"`, After `"child_value"` | asserted |
| 7 Verify state_2 (parent-only) remains unchanged through the Agent node step | condition holds | step 12 | step 12: step0-After == step1-Before == `"parent_only_value"` | asserted — **NEW mechanism discovery required a two-step comparison, not a single Before/After read (see step 12 note)** |
| 8 Verify state_3 (child-only) does NOT appear in parent's Run Details state panel | condition holds | step 10 | step 10: `state_3` row locator count == 0 at every timeline step | asserted — **CORE CASE ASSERTION, CONFIRMED TRUE LIVE** |

### Axis 2 — Beyond-case observables

| Observable | Why asserted |
|---|---|
| Run Details Before/After values are per-TIMELINE-STEP, not run-level (step 12) | Load-bearing platform-behavior discovery: an implementer naively reading `state_2` at the LAST timeline step (the convention ELITEA-2443 and this case's own step 11 use for `state_1`) gets BOTH Before and After as empty strings — indistinguishable from "value never set" without this context. Documented so the gap assertion doesn't silently read as a false pass/fail. |
| Timeline structural shape (parent CODE1 → child ×2 → child CODE1, no trailing AGENT1) matches ELITEA-2443's own fixture finding | Confirms the finding is a property of the 2-node-parent/1-node-child recipe shape, not a one-off — useful precedent for any THIRD case using this same parent/child pattern |
| `state_3`'s row absence holds at EVERY timeline step, not just one | Strengthens the core assertion — rules out "row only hidden for the currently-selected step" as an alternative (weaker) explanation |

## Cleanup
- `pipeline_api.delete_pipeline(child_id)` and `pipeline_api.delete_pipeline(parent_id)`
  in `finally` blocks — confirmed live this session (probe ids 8789 child / 8790
  parent), both deleted cleanly, no FK-order dependency.

## Concrete Handles (discovered during exploration)

All handles below are PRE-EXISTING `LocatorDescriptor`/page-object methods —
**zero new testid work needed for this case** (same conclusion as ELITEA-2443; this
case exercises the identical Run Details / Tools-attach surface, confirmed via
source grep of `automation/pages/pipeline_detail_page.py` this session).

| Element / action | Handle | Provenance |
|---|---|---|
| "+ Pipeline" Tools-section button | `agent-add-pipeline-button` → `PipelineDetailPage.open_pipeline_popper()` | on `automation/testids` (ELITEA-2064's `EliteaAI/EliteaUI@e2130cf4`) — re-verify on-main at implementation time |
| Pipeline picker popper rows | `toolkit-menu-item` → `Popper.select_menuitem_by_testid()` | on-main (pre-existing shared component) |
| Select pipeline + wait for attach PATCH | `PipelineDetailPage.select_pipeline_in_popper(popper, name, project_id)` | existing, `pipeline_detail_page.py:5576` (used unmodified) |
| Agent node's "Agent" combobox value | `get_agent_node_agent_value()` | existing, `pipeline_detail_page.py:4208` |
| Run label above canvas | `pipeline-run-node-label` → `open_run_details_panel()` | existing (ELITEA-2450) |
| Run Details status badge | `pipeline-run-details-status-badge` → `get_run_details_status_badge_text()` | existing (ELITEA-2450) |
| Timeline step count / node-id / select | `pipeline-run-details-timeline-step-{index}` → `get_run_details_timeline_step_count()`, `get_run_details_timeline_step_node_id(i)`, `select_run_details_timeline_step(i)` | existing (ELITEA-2451) |
| State row EXISTENCE (for the `state_3`-absence assertion) | `get_run_details_state_row_locator(variable)` → `.count()` | existing, `pipeline_detail_page.py:7171` — **NOT previously used for a count/absence check by any merged spec; this case is the first** (ELITEA-2443/2452/2453 all only ever `expand_run_details_state_row()`+read a present row) |
| State row expand / Before / After | `pipeline-run-details-state-row-{variable}` → `expand_run_details_state_row()`, `get_run_details_state_before_value()`, `get_run_details_state_after_value()` | existing (ELITEA-2452) |
| Pipeline create with raw `state:` block | `PipelineAPI.create_pipeline(name, description, instructions=<yaml>)` | existing, `automation/api/client.py:616` |

## Network Behavior
- Pipeline attach: `PATCH .../application_relation/prompt_lib/{project}/{child_id}/{child_version_id}` → `201 Created` — same mechanism as ELITEA-2443/2064/2038, confirmed live this session with real ids 8789/8790.
- Pipeline execution: Socket.IO only, no dedicated REST endpoint for run/timeline/state (same as ELITEA-2450/2443) — confirmed for this fixture shape too.
- Run Details panel: zero new network activity on timeline-step-select/row-count-check (same as ELITEA-2452's finding, extended here to the absence-check case).

## Known Defects Found During Exploration
- None new. The pre-existing `EliteaAI/elitea-testing-public#1267` (Stepper
  prop-leak console warning) fires here too — same known signature as
  ELITEA-2443/2450/2451, not a new occurrence to file.
- **Not a defect — Platform-behavior discovery (documented for the implementer,
  see Test Step 12 and Axis 2):** Run Details STATES panel Before/After values are
  computed per the CURRENTLY SELECTED timeline step's own input/output
  declaration, not as a run-level snapshot. A variable absent from the selected
  step's own input/output renders BOTH Before and After as empty strings, even
  when the variable genuinely holds a non-empty value elsewhere in the run. This
  did not surface in ELITEA-2443 because that case's child pipeline declared BOTH
  state_1 AND state_2 in its own `state:`/node input-output, so every timeline step
  had both variables in scope. It is DEFINITELY not a case-text-drift/reverse-
  masking situation — the case's own step 7 wording ("remains unchanged through the
  Agent node step") is satisfiable, just not via a single naively-chosen timeline
  step; see Test Step 12 for the two-step-comparison approach that satisfies it
  correctly.

## Blocked Steps
- None.

## Automation Hints
- **Cannot reuse ELITEA-2443's `pipeline_parent_child_state_sharing` fixture** — its
  child pipeline declares `state_2` (this case needs it OMITTED from the child). A
  new fixture is needed with the state schemas in § Test Data (suggest
  `pipeline_parent_child_state_isolation`, mirroring the existing fixture's
  structure/YAML-builder pattern, `automation/fixtures/data_fixtures.py`).
- Build via the GENERIC `PipelineAPI.create_pipeline()` (raw YAML) — same as
  ELITEA-2443/ELITEA-2453; `create_pipeline_with_nodes()` has no `state:` support.
- The `state_3`-absence assertion needs NO accordion expand — use
  `get_run_details_state_row_locator("state_3").count() == 0` directly (the row
  simply doesn't render; there's nothing to expand).
- **Do not read `state_2`'s Before/After at the LAST timeline step** (the
  convention used for `state_1` in step 11) — it will read as empty/empty and
  could be misinterpreted as a failure or a false-pass. Use timeline step 0 (the
  parent's own CODE1 execution) for `state_2`'s After value, and step 1 (first
  entry of the Agent/child boundary) for its Before value, per Test Step 12.
- Timeline entry count/order is fixture-shape-dependent (same caveat as
  ELITEA-2443) — assert structurally, not the literal tuple, unless reusing this
  AFS's exact fixture recipe verbatim.

## What the analyst filled in
- Executed live end-to-end this session (pipeline ids 8789 child / 8790 parent,
  project 399): built both pipelines via `PipelineAPI.create_pipeline()` (bypassing
  pytest, direct API script), attached the child via the Tools-section popper,
  executed the parent via embedded chat, opened Run Details, and inspected the
  STATES panel's row list + Before/After values across all 4 timeline steps via
  `page.evaluate()` DOM queries (to get exact, unambiguous text content rather than
  relying on the accessibility-tree snapshot, which omits empty-text nodes).
  Discovered and diagnosed the per-timeline-step Before/After scoping mechanism
  during this process (not documented by any prior AFS/digest entry). Both probe
  pipelines deleted at session end, confirmed via successful `delete_pipeline()`
  calls.
- Evidence: browser console messages captured via `browser_console_messages`
  (only the known `#1267` signature present); DOM state captured via
  `browser_evaluate` (see Concrete Handles / Test Step 12 for the exact values
  read).
