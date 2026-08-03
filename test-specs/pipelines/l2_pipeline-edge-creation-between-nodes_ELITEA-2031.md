# Test Case: Pipeline — Edge Creation Between Nodes

## Metadata
- **TMS ID**: ELITEA-2031
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), cluster analysis session with ELITEA-2018/2030/2032
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost `auth_state` fixture).
- A pipeline with 2 nodes exists: `LLM 1` and `Printer 1`, **each with an
  explicit `transition: END`** (i.e. both already terminating at END, NOT
  connected to each other). This is a deliberate seeding choice, not the
  bare "2 nodes" the case's precondition literally asks for — see the
  Case-text-drift note below for why an unconnected-to-each-other starting
  state is required to actually exercise "edge *creation*".

- **Case-text drift (filed as `EliteaAI/elitea-testing-public#1136`,
  clarification):** the case's Steps 2–3 describe "In the node
  configuration panel, locate the transition/routes field" and "Set the
  transition of the LLM node to point to the Printer node" as if this were
  a visible form field in the LLM node's config panel. Confirmed live: **no
  such field exists** for LLM (or Printer/Code/any non-HITL node type) —
  the LLM node's full visible config text (Trigger/SYSTEM/TASK/CHAT
  HISTORY/Input/Output/Toolkits/Interrupt-before-after/Structured output)
  contains no "Transition" or "Route" text, confirmed both via live DOM
  read and via source (`LLMNode.jsx`/`PrinterNode.jsx` — neither renders a
  transition control; the node's 3-dot menu offers only "Make Entrypoint"
  and "Delete"). **The real mechanism**: dragging a connection on the
  ReactFlow canvas from the source node's bottom (output) handle to the
  target node's top (input) handle. This AFS's Test Steps assert the real
  mechanism, not the imagined field.

## Test Data
- Source node: `LLM 1` (type `llm`)
- Target node: `Printer 1` (type `printer`)

### generate-per-test (in test setup, cleaned up in its own teardown)
- Pipeline `autotest_{test_name}` with `LLM 1` and `Printer 1`, both with
  explicit `transition: END` (see Automation Hints for exact node dicts).

## Test Steps
1. Navigate to the pipeline's canvas.
   - **Verify**: both nodes visible; `get_edge_count() == 2`
     (`LLM 1→END` and `Printer 1→END`, confirmed live from the seeded
     `transition: END` on both — neither connects to the other yet).
2. Drag a connection from `LLM 1`'s output handle to `Printer 1`'s input
   handle (`PipelineDetailPage.connect_nodes("LLM 1", "Printer 1")` —
   existing method).
   - **Verify**: no ReactFlow "create new node" context menu is left open
     (the existing `connect_nodes()` already dismisses this via Escape if
     the drag misses a handle).
3. Verify an edge appears connecting LLM Output to Printer Input.
   - **Verify**: `edge_exists("LLM 1", "Printer 1")` is `True`; the old
     `LLM 1→END` edge is gone (`edge_count()` stays at 2, not 3 — one edge
     was replaced, not added — confirmed live: `LLM 1`'s transition can
     only ever point at ONE target, so connecting to Printer necessarily
     *re-points* the existing edge rather than adding a second one from the
     same source).
4. Save, then reload — verify the edge persists.
   - **Verify**: `[data-testid="agent-save-button"]` is enabled after the
     connect (unsaved-change state) → click it → `page.reload()` →
     `wait_for_canvas()` → `edge_exists("LLM 1", "Printer 1")` still `True`.

## Expected Results
- A `LLM 1 → Printer 1` edge is visible on canvas after the drag, replacing
  the node's prior `→ END` edge.
- The edge survives Save + full page reload.
- Underlying edge testid (ReactFlow-generated, confirmed live):
  `rf__edge-xy-edge__LLM 1source-Printer 1target`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open pipeline with LLM+Printer | canvas shows both | step 1 | step 1: both nodes visible | asserted |
| 2 Locate transition/routes field in LLM panel | field visible | — | — | clarification *(no such field exists — `#1136`; real mechanism is canvas drag, asserted in step 2)* |
| 3 Set LLM transition to target Printer | transition updated | step 2 | step 2: drag-connect performed | asserted *(re-expressed via the real UI mechanism, same underlying outcome)* |
| 4 Edge line appears LLM Output→Printer Input | edge drawn | step 3 | step 3: `edge_exists()` True | asserted |
| 5 Save and reload — edge persists | edge present after reload | step 4 | step 4: `edge_exists()` True post-reload | asserted |

### Axis 2 — Analyst additions

- step 1 asserts the PRE-connect edge count (2, both nodes independently
  terminating at END) — *added: establishes the true "before" state so
  step 3's "edge count unchanged at 2" is a meaningful assertion about
  re-pointing rather than merely adding, not just a number pulled from
  nowhere.*
- step 3 asserts the OLD `LLM 1→END` edge is specifically gone (not just
  that the new edge exists) — *added: a single-source-single-transition
  model means a passing "new edge exists" check alone wouldn't catch a
  hypothetical regression where the app additively created a second
  outgoing edge instead of replacing the transition.*

## Cleanup
1. `pipeline_api.delete_pipeline(pid)` (fixture teardown).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Drag-connect | `PipelineDetailPage.connect_nodes(source_id, target_id)` (existing method — JS-computed handle coordinates + real `mouse.move/down/up` drag, not a synthesized event) | — |
| Edge existence check (NEW edge, step 3 positive assertion) | `PipelineDetailPage.edge_exists(source_id, target_id)` (existing — matches `data-testid` prefix `rf__edge-xy-edge__{source}{handle}-{target}{suffix}`, third-party ReactFlow-generated testid, sanctioned per `.agents/testing.md` § Locator policy stop+flag exception #1 — outside `EliteaUI/src`) | — |
| Old-edge-gone check (OLD `LLM 1→END` edge, step 3 negative assertion, Axis 2) | `PipelineDetailPage.edge_testid_present("LLM 1", "EliteAPipelineEnd")` (existing — exact `EDGE_TESTID` template match; see the format note below for why this is the correct tool for THIS specific check) | — |
| Edge count | `PipelineDetailPage.get_edge_count()` (existing, counts `.react-flow__edge`) | — |
| Save button | `[data-testid="agent-save-button"]` | — |

**Edge testid format inconsistency, confirmed live (worth knowing, not
blocking) — corrected 2026-08-04 (fix round 2): the split is lifecycle, not
target.** The original wording below characterized the two formats as
"edges TO END" vs "edges between two non-END nodes", which is a
correlation, not the cause — and it produced a blanket "wrong tool" claim
that contradicted this AFS's own Axis-2 addition (§ Axis 2, second bullet)
and the shipped Step-3 assertion, both of which use `edge_testid_present()`
for exactly this case's target-is-Printer edge (the OLD one). Corrected
characterization, confirmed against `EliteaUI/src/[fsd]/features/pipelines/
flow-editor/lib/helpers/parsePipeline.helpers.js::handleTransitionNode`
(`edgeId = `${EDGE_PREFIX}${id}---${currentJsonNode.transition}`` — the
`---` id format is emitted for ANY `transition:`-derived edge on a fresh
YAML→canvas parse, regardless of whether the target is `END` or another
node) and `useConnectNodes.hooks.js` → `EdgeOperationsHelpers.createNewEdge`
(spreads the raw ReactFlow `connection` object with no explicit `id`, so
`@xyflow/react`'s own `addEdge` auto-generates one from the connection's
handle ids — `{source}{sourceHandle}-{target}{targetHandle}`, no `---` —
until the next full Save + reload re-derives it via `parsePipeline`):

- An edge **loaded from the pipeline's persisted YAML** on a fresh
  navigate/reload — seeded edges at Step 1, or ANY edge post-Step-4-reload —
  always gets the app's own `{source}---{target}` id, whatever its target.
  This is the format `PipelineDetailPage.EDGE_TESTID` / `edge_testid_present()`
  match exactly.
- An edge **created live in-session via drag-connect**, before any Save +
  reload, has no explicit `id` set by the app — ReactFlow's own `addEdge`
  auto-generates one from the connection's handle ids
  (`{source}{handle}-{target}{handle}`, no `---`). This is the format
  `edge_exists()`'s prefix/substring matching tolerates (and `EDGE_TESTID`
  does NOT match).

At Step 3, both formats are live in the SAME pipeline simultaneously
because the two edges under test are in different lifecycle stages: the
NEW `LLM 1 → Printer 1` edge was JUST live-connected in this session (not
yet saved/reloaded) → `rf__edge-xy-edge__LLM 1source-Printer 1target` →
`edge_exists()` is the correct, in fact only correct, tool for confirming
it. The OLD `LLM 1 → END` edge, by contrast, was rendered on the initial
Step-1 navigate from the pipeline's seeded YAML (`transition: END`) →
`rf__edge-xy-edge__LLM 1---EliteAPipelineEnd` → `edge_testid_present()`
is the correct tool for confirming it's specifically gone (Axis 2's second
bullet), not "the wrong tool" — the prior wording's "this case's target is
Printer, not END" reasoning conflated the case's overall target (Printer)
with the specific edge under test in this one check (the OLD, END-target,
YAML-loaded edge). Use `edge_exists()` for the Step-3 positive assertion
(new edge) and `edge_testid_present()` for the Step-3 negative assertion
(old edge) — both are correct, for different edges in different lifecycle
states, not competing options for the same check.

## Network Behavior
- No dedicated network call for the drag-connect itself (ReactFlow local
  state) — the transition only persists via the same pipeline Save
  (`PUT .../application/prompt_lib/{project}/{id}`) as any other canvas
  edit.

## Known Defects Found During Exploration
- none found (product behaves correctly).
- **Case-text drift, filed as clarification**: `EliteaAI/elitea-testing-public#1136`
  — Steps 2–3 describe a config-panel field that doesn't exist. See
  Preconditions.

## Blocked Steps
- none.

## Automation Hints
- Framework: Playwright + pytest.
- Page object: `automation/pages/pipeline_detail_page.py` — `connect_nodes()`,
  `edge_exists()`, `get_edge_count()` all exist; reuse as-is.
- Seed via `PipelineAPI.create_pipeline_with_nodes()`:
  ```python
  nodes = [
      {"id": "LLM 1", "type": "llm", "input": [], "input_mapping": {
          "chat_history": {"type": "fixed", "value": []},
          "system": {"type": "fixed", "value": ""},
          "task": {"type": "fixed", "value": "hi"},
      }, "output": ["messages"], "structured_output": False,
       "transition": "END"},
      {"id": "Printer 1", "type": "printer",
       "input_mapping": {"printer": {"type": "fixed", "value": "done"}},
       "transition": "END"},
  ]
  ```
  Both nodes explicitly `transition: END` — this is the load-bearing detail:
  omitting `transition` entirely on both (confirmed live in this same
  session) auto-defaults `LLM 1` to `transition: Printer 1` already (the
  next node in the YAML list), which pre-creates the very edge this case
  is supposed to test the creation of — a false-positive precondition.
  Always seed both nodes pointing at END explicitly.
