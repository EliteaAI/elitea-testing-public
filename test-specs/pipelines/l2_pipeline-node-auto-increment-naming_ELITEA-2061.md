# Test Case: Pipeline — Node Auto-Increment Naming

## Metadata
- **TMS ID**: ELITEA-2061
- **Linked Story**: none
- **Priority**: l2 (source case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), session 2026-08-09
- **Status**: ready-for-automation

## Case-text note (drift, not a defect)

The source case's title is "Pipeline — Node Duplicate via Node Menu" but its
own Objective, Steps, and Expected Results describe a **different**
behavior: auto-incrementing default names ("LLM 1", "LLM 2", …) assigned when
**adding** nodes of the same type via the canvas "+" Add Node menu — not a
"Duplicate" action on an existing node's context menu (no such action exists
in the live UI; the Node menu's only actions are Delete and
Expand/Collapse — confirmed via `NodeCardHeader.jsx` read for ELITEA-2060).
Automated per the BODY (auto-naming), which is unambiguous and internally
consistent across Objective/Steps/Expected-Final-State/Pass-Fail-Criteria;
the title is stale metadata. Filed as a case-text CLARIFICATION, not a
defect — no live-product mismatch, just a title/body mismatch in the TMS
case itself.

The case's own Step 3/5 illustrative examples ("LLM 1", "Code 2" / "LLM 2",
"Code 3") mix two different node types mid-sequence in a way that doesn't
correspond to any single coherent add sequence (a real sequence starting
empty produces "LLM 1", "LLM 2" for two LLM adds, or "LLM 1" then "Code 1"
for one of each type — never "Code 2" as the SECOND node added). Read as
generic illustrative placeholders, not a literal required sequence — the
Objective and Expected Final State's own example ("LLM 1", "LLM 2", "LLM 3")
is internally consistent and is what this AFS automates literally.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline is open in Flow view. (Case Step 1 says "a pipeline with a
  configured node" — read generically per the Preconditions section's own
  "pipeline is open in Flow view", not as requiring a specific pre-existing
  node: the Objective's own literal example starts counting from 1, which
  requires the canvas be empty of that type beforehand. An **empty** pipeline
  satisfies "a pipeline is open" and is the only starting state under which
  the case's own literal "LLM 1" example holds.)

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Empty pipeline via the existing `pipeline_id` fixture (same fixture
  ELITEA-2030 uses for Add-Node-menu testing).

## Test Steps
1. Navigate to the pipeline's canvas.
   - **Verify**: `PipelineDetailPage.canvas_wrapper` visible.
2. Add an LLM node via the Add Node menu (first node of this type).
   - **Verify**: exactly one new node appears; its data-id AND its
     rendered display name both equal `"LLM 1"`.
3. Add a second LLM node via the Add Node menu.
   - **Verify**: exactly one new node appears (total node count == 2); its
     data-id AND rendered display name both equal `"LLM 2"` — the number
     incremented from the first node of the same type.
4. Add a Code node via the Add Node menu (different type, generalizing the
   case's own "any type" framing — Step 2 of the source case lists "LLM,
   Code, Printer" as example types).
   - **Verify**: exactly one new node appears (total node count == 3); its
     data-id AND rendered display name both equal `"Code 1"` — a fresh
     type's counter starts at 1 independently of the LLM counter already
     being at 2 (proves per-type numbering, not a single canvas-wide
     counter).

## Expected Results
- Nodes of the same type are auto-named with an incrementing number
  suffix ("LLM 1", "LLM 2", …), confirmed for at least two nodes of one
  type.
- A different node type's counter is independent, starting at 1 regardless
  of another type's current count.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipeline open in Flow view | pipeline open | step 1 | step 1: canvas wrapper visible | asserted |
| 1 Open a pipeline with a configured node | pipeline open | step 1 | step 1: canvas wrapper visible (see Preconditions note — empty pipeline used, so the case's own literal "LLM 1" example holds) | asserted *(case-text note above — no gap)* |
| 2 Select/add a node of any type (e.g. LLM) | node added | step 2 | step 2: node count +1, new id captured via before/after diff | asserted |
| 3 Verify added node name is "&lt;Type&gt; number" (e.g. "LLM 1") | name follows pattern | step 2 | step 2: new node's id AND rendered name both == `"LLM 1"` | asserted |
| 4 Select/add another node of the same type | second node added | step 3 | step 3: node count +1 (total 2), new id captured via diff | asserted |
| 5 Verify node name increments (e.g. "LLM 2") | name increments | step 3 | step 3: new node's id AND rendered name both == `"LLM 2"` | asserted |
| Objective: "any type" generality (case Step 2's own LLM/Code/Printer example types) | naming rule applies beyond one type | step 4 | step 4: new node's id AND rendered name both == `"Code 1"`, independent of the LLM counter | asserted |

### Axis 2 — Analyst additions

- Step 4 (a second, different node type) is an addition beyond the case's
  literal two-node/one-type minimum — *added: the case's own Step 2 explicitly
  names three example types ("LLM, Code, Printer") as illustrating "any
  type", so proving the rule generalizes (and that counters are independent
  per type, not a single canvas-wide counter) is a grounded observable
  directly motivated by the case's own phrasing, not scope creep.*
- Every verification checks BOTH the node's `data-id` (via the diff-based
  identification pattern) AND its rendered `MuiTypography-labelMedium`
  display text (`get_node_name()`), rather than relying on data-id alone —
  *added: the case asks to verify the node's displayed NAME, and the id
  happens to equal the label in this app's current implementation, but that
  equivalence is itself an implementation detail worth confirming rather
  than assuming; a future app change could decouple id from display label
  without this test catching a real display-name regression otherwise.*

## Cleanup
1. `pipeline_api.delete_pipeline(pid)` (fixture teardown, via `pipeline_id`).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Canvas wrapper | `PipelineDetailPage.canvas_wrapper` (existing) | — |
| Add node menu (open + read) | `PipelineDetailPage.get_add_node_menu_items()` (existing, ELITEA-2030, testid-based) | — |
| Add node menu (select by internal type key) | `PipelineDetailPage.select_add_node_menu_item(node_type)` (existing, ELITEA-2030, testid-based; internal type keys `"llm"`, `"code"`) | — |
| Node id inventory (before/after diff) | `PipelineDetailPage.get_node_ids()` (existing) — required over `wait_for_node_on_canvas()`'s `.first`-based return value on a canvas that already holds another node of the same type (documented live collision, `test-specs/pipelines/_surface.md` § "Flow → YAML sync + `wait_for_node_on_canvas()` same-type collision") | — |
| Node count settle (poll, not instant read) | `PipelineDetailPage.wait_for_node_count(expected_total)` (existing) | — |
| Node's rendered display name | `PipelineDetailPage.get_node_name(node_id)` (existing) | — |

No new testids or page-object methods are needed — every handle this case
needs already exists on `PipelineDetailPage`, added by prior pipeline cases
(ELITEA-2030 for the Add Node menu, ELITEA-2033 for `wait_for_node_count`,
existing `get_node_ids()`/`get_node_name()`).

## Network Behavior
- None — pure client-side canvas/menu interaction; node creation is local
  ReactFlow state until Save (same as ELITEA-2030's own Network Behavior
  note — this case never clicks Save).

## Known Defects Found During Exploration
- none found. Source read confirms the naming mechanism directly
  (`EliteaUI/src/[fsd]/features/pipelines/flow-editor/lib/helpers/
  flowEditor.helpers.js` `getNormalInitialNodeId()`: for a new node of a
  given type, tries `"<InitialNodeId[type]> 1"`, then `" 2"`, … until it
  finds a candidate id not already present among current node ids — i.e.
  exactly the incrementing behavior the case describes). Also independently
  live-confirmed in a prior session for the LLM type specifically
  (`test-specs/pipelines/_surface.md`: "adding a SECOND LLM node … the real
  new node id (`"LLM 2"`)").

## Blocked Steps
- none.

## Automation Hints
- Framework: Playwright + pytest.
- Page object: `automation/pages/pipeline_detail_page.py` — reuse
  `get_add_node_menu_items()` + `select_add_node_menu_item()` (testid-based,
  ELITEA-2030), `get_node_ids()`, `wait_for_node_count()`, `get_node_name()`.
  No new methods needed.
- `helpers._navigate_to_canvas(page, pipeline_id)` for setup navigation
  (same pattern as `test_pipeline_add_node_menu.py`).
- Identify each newly-added node's id via a `get_node_ids()` before/after
  set-difference — do NOT trust `wait_for_node_on_canvas()`'s return value
  once more than one node of a given type exists on canvas (documented
  `.first`-collision in `_surface.md`).
