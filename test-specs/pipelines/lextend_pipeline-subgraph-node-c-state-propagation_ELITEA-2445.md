# Test Case: Subgraph Execution — Verify State Flow in Run Details

## Metadata
- **TMS ID**: ELITEA-2445
- **Linked Story**: none
- **Priority**: l2 (source: `medium`, matching sibling ELITEA-2443's own medium→l2
  mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend, project 399)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN`
  auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-09
- **Status**: extend-existing
- **surface_key**: pipeline-run-details
- **Extension target**: `automation/tests/ui/pipelines/test_pipeline_subgraph_state_sharing.py`
  (`test_subgraph_state_sharing_common_vars`, ELITEA-2443 — already merged onto
  this batch's trunk `tests/batch-pipelines-remaining-w7`). AFS:
  `test-specs/pipelines/l2_pipeline-subgraph-state-sharing-common-vars_ELITEA-2443.md`.

## Why extend-existing, not a fresh spec

ELITEA-2445's case text is structurally the SAME parent/child-attach/execute/
Run-Details flow ELITEA-2443 already builds and asserts — same "Subgraph" =
`agent`-node-with-pipeline-tool terminology note, same attach-precondition
(bare `tool:` YAML alone doesn't resolve; the Tools-section "+ Pipeline" popper
attach is required), same nested-timeline mechanism, same Before/After state
rendering. Re-implementing all of that in a fresh spec would duplicate
maintenance for zero new signal.

ELITEA-2445 differs from ELITEA-2443 in exactly two respects, both confirmed
live this session:

1. **Case step 6** ("Click Node_A step — verify shared_data Before is
   empty/initial, After has Node_A's output") wants the assertion made AT
   `CODE1`'s OWN timeline entry (index 0). The merged ELITEA-2443 test never
   selects index 0 — it only ever selects the LAST timeline entry and reads
   `state_1`/`state_2` there. Confirmed live: `RunStateDialog.jsx`'s
   `valueBefore`/`valueAfter` ARE keyed off the selected timeline step
   (`data.timeline[selectedStep - 1]` / `data.timeline[selectedStep]`), so
   selecting index 0 genuinely produces a DIFFERENT (and currently unasserted)
   Before/After pair than selecting the last index. This is a real, small gap.
2. **Case steps 5 and 8** want a THIRD parent node (`Node_C`) placed AFTER the
   Agent node, reading the child-modified state. Neither ELITEA-2443 nor
   ELITEA-2444's fixtures ever chain anything after `AGENT1` — both end
   `AGENT1`'s own `transition:` at `END`. Live-probing this exact shape this
   session (`CODE1 → AGENT1(tool=attached child) → CODE2 → END`) surfaced a
   **genuine, reproducible product defect**: `CODE2` never executes — filed as
   `EliteaAI/elitea-testing-public#1381`. See § Known Defects below. Per
   `.agents/testing.md`'s analysis-time sanctioned-RED entry, this is written
   as `expect.soft()` + `# Known defect: #1381`, not skipped — it does not
   block the rest of the case (step 6's gap above, and everything ELITEA-2443
   already proves, remain independently testable).

Both gaps are small, additive assertions/fixture extensions on top of the
covering test — not a near-rewrite — so `extend-existing` applies (boundary
call per the skill: a near-rewrite would instead be `ready-for-automation`).

## Preconditions
- Same as ELITEA-2443's AFS: user authenticated (localhost auto-auth via
  `VITE_DEV_TOKEN`); the "Subgraph" terminology note (case text names the
  legacy term, the live mechanism is an `agent`-type node with a `tool:`
  field — no case-text drift, just an outdated title); the Tools-section
  "+ Pipeline" attach is a REAL runtime precondition even when the Agent
  node's `tool:` YAML field already names the child pipeline correctly.
- **NEW precondition confirmed this session**: a node placed after an Agent
  node's nested-pipeline tool call (via `transition:`) is affected by the
  confirmed defect `#1381` — the test must anticipate this via `expect.soft()`,
  not treat it as a setup failure.

## Test Data

### generate-per-test (NEW fixture needed — the existing `pipeline_parent_child_state_sharing` fixture's parent has only 2 nodes)
- **Child pipeline** — SAME shape as ELITEA-2443's: `state: {messages: list,
  state_1: str, state_2: number}`, one `code` node overwriting BOTH
  (`{"state_1": "child_value", "state_2": 99}`), `transition: END`.
- **Parent pipeline** — same `state:` block, but THREE nodes instead of two:
  - `CODE1`: sets ONLY `state_1` (`{"state_1": "parent_value"}`),
    `input`/`output: [state_1]`, `transition: AGENT1` (identical to ELITEA-2443's
    parent CODE1).
  - `AGENT1`: identical shape to ELITEA-2443's (`input: [input]`,
    `output: [messages]`, fixed `task`/`chat_history`, `tool: <child_name>`),
    but `transition: CODE2` instead of `transition: END`.
  - `CODE2` (= case's "Node_C"): reads `state_1` via
    `alita_state.get("state_1", "MISSING")`, `input`/`output: [state_1]`,
    `structured_output: true`, `transition: END`. **Confirmed live: this node
    never runs (defect #1381)** — its own code value is otherwise irrelevant
    to the assertion (the test asserts the node's ABSENCE from the observable
    run, not its output).
  - New minimal fixture, e.g. `pipeline_parent_child_state_sharing_three_node`
    in `automation/fixtures/data_fixtures.py`, reusing the SAME
    `PipelineAPI.create_pipeline()` raw-YAML technique and the SAME two-pipeline
    teardown (`try/finally`, order-independent delete) as
    `pipeline_parent_child_state_sharing`. Do NOT modify the existing
    `pipeline_parent_child_state_sharing`/`_build_parent_child_state_sharing_parent_instructions`
    — ELITEA-2443's merged test depends on its exact 2-node shape.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).

## Test Steps (gap only — everything else is already asserted by the covering ELITEA-2443 test)

1. *(Already asserted — covering test steps 1-6: attach the child pipeline via
   the Tools-section popper, execute, open Run Details, status Completed.)*
   Use the NEW 3-node fixture instead of the covering test's 2-node one.
2. Select timeline step **index 0** (`CODE1`'s own entry) — **NEW gap
   assertion, satisfies case step 6**.
   - **Verify**: `get_run_details_state_before_value("state_1") == '""'`
     (empty/initial — confirmed live: before `CODE1` runs, `state_1` has never
     been set) and `get_run_details_state_after_value("state_1") ==
     '"parent_value"'` (confirmed live: `CODE1`'s own write) — this is a
     DIFFERENT Before/After pair than the covering test's last-index selection
     (`"parent_value"` → `"child_value"`), proving the panel keys Before/After
     off the SELECTED step, not a run-level aggregate.
3. Confirm the timeline does **NOT** contain a distinct entry for `CODE2` —
   **NEW gap assertion, documents case steps 5/8's blocked premise**.
   - **Verify** (`expect.soft()` + `# Known defect: EliteaAI/elitea-testing-public#1381`):
     `get_run_details_timeline_step_count()` stays at the SAME count the
     2-node-parent fixture produces (4, per ELITEA-2443's own confirmed shape)
     despite the 3-node parent's extra `CODE2` node being present on canvas
     (`get_node_ids()` includes `"CODE2"`) — i.e. `CODE2` is wired into the
     graph but never appears in the run.
4. Attempt case step 8 ("Click Node_C step — verify shared_data Before shows
   the child-modified value") — **NEW gap assertion, BLOCKED by `#1381`**.
   - **Verify** (`expect.soft()` + `# Known defect: EliteaAI/elitea-testing-public#1381`):
     there is no timeline entry whose node-id aria-label matches `"CODE2"`
     (`get_run_details_timeline_step_node_id(i)` for every `i` in
     `range(get_run_details_timeline_step_count())`) — confirming the node
     genuinely never executed rather than merely rendering under a different
     label.
5. Timestamps render on every timeline step and are non-decreasing across the
   run — **NEW gap assertion, satisfies case step 5's "with timestamps in
   execution order" wording** (the covering test never calls
   `get_run_details_timeline_step_timestamp()`, an existing, unused handle).
   - **Verify**: `get_run_details_timeline_step_timestamp(i)` returns a
     non-empty `HH:mm:ss` string for every `i`, and the parsed times are
     monotonically non-decreasing across `i = 0..count-1`.

## Expected Results
- Selecting a DIFFERENT timeline step produces a DIFFERENT, step-specific
  Before/After pair for the same state variable — confirming the mechanism
  case step 6 relies on (index 0 = `CODE1`'s own write, not the run's final
  aggregate).
- **CONFIRMED DEFECT (`#1381`)**: a node chained via `transition:` immediately
  after an Agent node's nested-pipeline tool call never executes — the run
  still reports `Completed`. This blocks case steps 5 (timeline showing all
  THREE parent nodes) and 8 (`Node_C`'s own Before value) as literally
  written. The defect is isolated to this exact shape (agent-with-pipeline-tool
  → next node) — a control probe proved a plain two-`code`-node chain
  (`CODE1 → CODE2`, no agent hop) executes both nodes correctly.
- Every rendered timeline step exposes a real, monotonically-ordered timestamp
  (existing `pipeline-run-details-timeline-timestamp-{index}` handle,
  previously unused by any merged pipeline test).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in | setup exists | covering test step 1 | covering test | asserted (already covered) |
| 1 Create parent with 3 nodes: Node_A→Agent_Node→Node_C→END | operation completes | gap step 1 (NEW fixture) | new 3-node fixture create response `id`s present | asserted |
| 2 Parent/child share common state var | completes without error | covering test steps 1-2 + gap fixture's same `state:` block | covering test + new fixture | asserted (already covered) |
| 3 Node_A writes, child modifies, Node_C reads shared_data | completes without error | covering test steps 1-4 (Node_A write, child modify) + gap steps 3-4 (Node_C read) | covering test + gap steps 3-4 | asserted for Node_A/child; **BLOCKED for Node_C by `#1381`** |
| 4 Execute the parent pipeline | completes without error | covering test step 4 | covering test | asserted (already covered) |
| 5 Open Run Details — timeline shows all 3 nodes with timestamps in order | target loads, condition holds | covering test step 5 (panel loads) + gap steps 3, 5 (3-node count, timestamps) | covering test + gap steps 3, 5 | **partially blocked — timeline never shows 3 nodes (`#1381`); timestamp-ordering assertion is new, unblocked coverage** |
| 6 Click Node_A step — Before empty/initial, After has Node_A's output | control responds | gap step 2 | gap step 2: index-0 selection, Before=`'""'`, After=`'"parent_value"'` | asserted (NEW) |
| 7 Click Agent_Node step — Before shows Node_A's output, After shows child's modification | control responds | covering test steps 6-9 (selects LAST index) | covering test | asserted (already covered — the covering test's last-index selection IS the Agent-node step in the 4-entry shape) |
| 8 Click Node_C step — Before shows the child-modified value | control responds | gap step 4 | gap step 4: `expect.soft()` + `# Known defect: #1381` | **BLOCKED — CONFIRMED DEFECT, soft-asserted, not masked** |
| 9 Verify "Completed" badge on run header | condition holds | covering test step 5 | covering test | asserted (already covered) |

### Axis 2 — Beyond-case observables

| Observable | Why asserted |
|---|---|
| `CODE2` present on canvas (`get_node_ids()`) but absent from the run timeline | Distinguishes "node never wired into the graph" (a fixture bug) from "node wired but never executed" (the real product defect) — without this check, a reader can't tell which failure mode occurred |
| Timeline timestamps are non-decreasing | The case's own step 5 wording ("with timestamps in execution order") is otherwise unasserted by any existing pipeline test — cheap, unblocked, real coverage of an existing-but-unused handle |

## Known Defects Found During Exploration
- **`EliteaAI/elitea-testing-public#1381`** — a node chained via `transition:`
  immediately after an `agent`-type node whose `tool:` resolves to a nested
  pipeline (attached via the Tools-section "+ Pipeline" popper) never
  executes; the run still reports `Completed`. Confirmed live 2/2 against
  fresh pipelines; a control probe (plain `code`-node-only chain, no agent
  hop) proved multi-hop `transition:` chaining otherwise works correctly —
  isolating the defect to this specific node-type transition. Directly
  blocks case steps 5 and 8 as literally written; write those two assertions
  as `expect.soft()` + `# Known defect: #1381`, per `.agents/testing.md`'s
  analysis-time sanctioned-RED entry — this preserves every OTHER passing
  assertion in the same test and flips green once the product fix ships.
- The pre-existing `EliteaAI/elitea-testing-public#1267` (Stepper prop-leak
  console warning) fires here too — same known signature as ELITEA-2443/
  2450/2451/2452, not a new occurrence to file.

## Blocked Steps
- Case steps 5 (partially — the "3 nodes" portion) and 8 are blocked by
  `#1381`. Not classified `defect-found` per `.agents/testing.md`'s
  analysis-time entry: the defect sits at the TAIL of the case (steps 5/8 of
  9) and does not prevent exploring or asserting the rest — `expect.soft()`
  is the correct shape, not a paused case.

## Automation Hints
- Build the new 3-node parent fixture the SAME way as
  `pipeline_parent_child_state_sharing` (`automation/fixtures/data_fixtures.py:689`)
  — generic `PipelineAPI.create_pipeline()` raw YAML, NOT
  `create_pipeline_with_nodes()` (no `state:` support, ELITEA-2453's
  documented gap). Do not parametrize/modify the EXISTING 2443 fixture — add a
  new one so ELITEA-2443's own merged test is untouched.
- The Tools-section attach step is still required even with the 3-node
  parent — same mechanism, same `select_pipeline_in_popper()` call.
- Reuse `_navigate_to_canvas` / the same console-error listener pattern
  (`_is_known_1267_stepper_prop_leak`) as the covering test.
- Structural assertions only for timeline count/order (fixture-shape-dependent
  per ELITEA-2443's own Automation Hints) — do not hardcode a literal count
  beyond what THIS fixture recipe is confirmed to produce (4, per this
  session's live probe, matching ELITEA-2443's 2-node-parent shape exactly
  because `CODE2` never joins the timeline).
- `# Known defect: EliteaAI/elitea-testing-public#1381` comment goes directly
  above each `expect.soft()` call per the project's no-masking decision tree.

## What the analyst filled in
- Executed live end-to-end this session via a throwaway analysis probe
  (reusing the exact `PipelineDetailPage` methods/handles ELITEA-2443's merged
  test already uses — zero new testid work). Two probe pipelines created and
  deleted (`pipeline_api.delete_pipeline()`, confirmed clean) for the 3-node
  defect repro; a third, simpler probe (plain 2-node `code`-only chain, no
  agent) served as the control that isolated the defect's cause. Probe test
  files were NOT committed (throwaway, per the skill's evidence-not-automation
  boundary) — the defect and its exact repro recipe are captured in this AFS
  and in issue `#1381` instead.
- Filed `EliteaAI/elitea-testing-public#1381` this session (dedup-checked
  against all existing `bug`-labelled issues in this repo first — no match).
