# Test Case: Pipeline — Flow to YAML Sync

## Metadata
- **TMS ID**: ELITEA-2029
- **Linked Story**: none
- **Priority**: l2 (high — as authored in the source TMS case; sibling `high`
  pipeline case in this folder uses `l2_` + `@pytest.mark.p1`, e.g. the
  reverse-direction sibling `l2_yaml-to-flow-sync_ELITEA-2028.md` — same
  mapping applied here)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids`)
- **User set**: none — API-token auth (`ELITEA_API_TOKEN`) for pipeline
  seeding/cleanup; localhost `auth_state` bypass for the UI session (no
  Keycloak login involved)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot),
  batch `pipelines-remaining-w3`
- **Status**: ready-for-automation

## Preconditions
- A pipeline with an existing node exists (case precondition: "A pipeline
  with existing nodes exists"). Seeded via the existing `pipeline_with_llm_id`
  fixture (`create_pipeline_with_llm_node()` — LLM 1 → END). No UI-driven
  setup block is needed before the case's own steps (unlike the sibling
  ELITEA-2028, this case never touches Save, so there is no dirty-state
  baseline to establish first).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Pipeline seeded via `PipelineAPI.create_pipeline_with_llm_node()` (the
  fixture-backing method for `pipeline_with_llm_id`) — unique name per test
  function, deleted in teardown via `PipelineAPI.delete_pipeline()`.

## Test Steps
(Numbered to match the TMS case's own 5 steps.)

1. Open the pipeline's detail page (`/pipelines/all/{id}`); confirm Flow
   view is the default/active view.
   - **Verify**: `pipeline-flow-view`'s canvas (`rf__wrapper`) is visible
     and active.
2. Add a new LLM node via the "Add node" button.
   - **Verify**: node count increases by exactly 1, and the newly-added
     node's `data-id` (diffed against the pre-add node-id set, see
     § Concrete Handles — ambiguity caveat) is visible on the canvas.
3. Switch to "Yaml" view.
   - **Verify**: `pipeline-yaml-editor` (YAML CodeMirror) becomes visible.
4. Verify the new node appears in the YAML definition.
   - **Verify**: `get_yaml_content()` contains a `- id: {new_node_id}` entry
     under `nodes:`, in addition to the pre-existing LLM 1 node's entry
     (both present, node count in YAML == canvas node count).
5. Switch back to "Flow" view; verify the node is still present on canvas.
   - **Verify**: `pipeline-flow-view`'s canvas is active again, the new
     node's `data-id` is still present in `get_node_ids()`, and node count
     is unchanged from step 2 (no node lost or duplicated by the two view
     switches).

## Expected Results
- The pipeline detail page defaults to Flow view with the ReactFlow canvas
  visible.
- Adding an LLM node via the Add-node menu renders it on the canvas
  immediately (client-side ReactFlow state; no network call — confirmed
  live, matches the sibling ELITEA-2030 case's own Network Behavior note)
  and increases the node count by exactly 1.
- Switching to Yaml view shows the YAML CodeMirror editor, whose content
  (read via `get_yaml_content()`) includes a `nodes:` entry for the
  newly-added node (`id: {new_node_id}`) alongside the pre-existing LLM 1
  node's entry — confirming the Flow-editor addition is immediately
  reflected in the YAML definition, no Save required.
- Switching back to Flow view re-renders the canvas with the new node still
  present — the two-way view toggle does not lose or duplicate the node.
- Zero console errors, zero failed network requests, throughout.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| precond: pipeline with existing node(s) exists | — | setup (fixture) | `pipeline_with_llm_id` fixture, before step 1 | asserted |
| 1 Open pipeline in Flow view | Canvas displayed in Flow view | step 1 | `step 1`: `is_flow_view_active()` True, `canvas_wrapper` visible | asserted |
| 2 Add a new LLM node via "Add node" button | New LLM node appears on canvas | step 2 | `step 2`: node count +1, new node's data-id present via `get_node_ids()` diff | asserted |
| 3 Switch to "Yaml" view | YAML editor displayed | step 3 | `step 3`: `pipeline-yaml-editor` visible | asserted |
| 4 Verify the new node appears in YAML definition | YAML content includes the newly added LLM node | step 4 | `step 4`: `get_yaml_content()` contains `id: {new_node_id}` | asserted |
| 5 Switch back to Flow view; node still present | LLM node remains on canvas in Flow view | step 5 | `step 5`: `is_flow_view_active()` True, new node's data-id still in `get_node_ids()`, count unchanged | asserted |

**Axis 2 — Analyst additions:**
- `step 2` also asserts the new node's data-id is found via a **before/after
  set diff** of `get_node_ids()`, not via `wait_for_node_on_canvas("llm")`
  alone — *added: live exploration showed `wait_for_node_on_canvas()` uses
  `.locator(".react-flow__node-llm").first`, which resolves to the
  **pre-existing** LLM 1 node (not the newly-added one) whenever the
  precondition pipeline already has a node of the same type — confirmed
  live: on `pipeline_with_llm_id` (which already has an "LLM 1" node),
  calling `wait_for_node_on_canvas("llm")` after adding a second LLM node
  returned `"LLM 1"`, not the new node's real id `"LLM 2"`. The method is
  fine for a bare/empty canvas (its only existing caller, ELITEA-2030's
  test) but silently wrong here — using it unguarded would make step 4's
  YAML assertion check for the WRONG node's presence, passing vacuously
  since LLM 1 was already in the YAML before the add.*
- `step 4` also asserts the pre-existing LLM 1 node's entry is still present
  in the YAML (not just the new node's) — *added: rules out a "YAML
  regenerated from only the newest node" false positive.*
- `step 5` also asserts node COUNT is unchanged from step 2's post-add value
  (not just "is visible") — *added: standard round-trip discipline, catches
  a duplicate-on-switch-back regression that a bare visibility check would
  miss.*
- Zero console errors / zero failed requests, asserted across the whole
  flow — *added: standard side-channel discipline per the skill's Phase 3
  step 3; none observed in the live exploration run.*

## Cleanup
1. Delete the seeded pipeline via `PipelineAPI.delete_pipeline(pipeline_id)`
   in fixture teardown (`pipeline_with_llm_id` standard pattern — the test
   never creates anything the fixture doesn't already own).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/role-overrides.md`,
`.agents/testing.md` § Locator policy) — no role/text/CSS ladder. All of the
following testids are CONFIRMED present and already wired as
`LocatorDescriptor` fields on `PipelineDetailPage` (`automation/pages/
pipeline_detail_page.py`) — **no new testid work needed for this case**:

| Element | Testid | Page-object field / method | Notes |
|---|---|---|---|
| Switch to Yaml view button | `pipeline-yaml-view` | `yaml_view_button` | existing |
| Switch to Flow view button | `pipeline-flow-view` | `flow_view_button` | existing |
| YAML editor container | `pipeline-yaml-editor` | `yaml_editor` | existing; wraps CodeMirror; `get_yaml_content()` reads it |
| Add-node button | `pipeline-add-node-button` | opened via `get_add_node_menu_items()` | testid-based (ELITEA-2030), prefer over legacy raw-handle `add_node()` |
| Add-node menu | `pipeline-add-node-menu` | `get_add_node_menu_items()` | testid-based |
| Add-node menu item (by internal type) | `pipeline-add-node-menu-item-{type}` (`ADD_NODE_MENU_ITEM_BY_TYPE` template) | `select_add_node_menu_item("llm", …)` | testid-based; internal type key `"llm"`, not the display label |
| ReactFlow canvas wrapper | `rf__wrapper` | `canvas_wrapper` | existing; sanctioned #579 third-party-widget exception |
| Canvas node (per-node) | `.react-flow__node[data-id=…]` (ReactFlow-generated) | `get_node_ids()` / `get_node_count()` / `wait_for_node_on_canvas()` (existing methods) | sanctioned #579 exception (ReactFlow internal) |

**Ambiguity caveat (confirmed live, this case's own precondition triggers
it):** `wait_for_node_on_canvas("llm")` resolves via
`.locator(".react-flow__node-llm").first` — DOM/document order, not
identity. On a pipeline that ALREADY has an LLM node (this case's own
precondition), adding a second LLM node and calling
`wait_for_node_on_canvas("llm")` returns the pre-existing node's id, not
the new one. The reliable pattern here (used in this AFS): capture
`get_node_ids()` **before** the add, capture it again **after**, and take
the set difference — `wait_for_node_on_canvas("llm", …)` is still called
first (to settle/wait for the new node's render), but its return value is
NOT trusted as the new node's id in this case. This is a pre-existing
method limitation (its docstring doesn't document the caveat), not a
defect introduced by this case; flag it for the page object, no fix made
here (its only other existing caller, ELITEA-2030's test, adds to an EMPTY
canvas where `.first` happens to be correct).

## Network Behavior
- None of steps 1–5 fire any network request — adding a node (client-side
  ReactFlow state until Save, confirmed live and matching ELITEA-2030's own
  Network Behavior note), switching Yaml ⇄ Flow view, and reading YAML
  content are all purely client-side. This case never clicks Save, so no
  persistence call happens at all.

## Known Defects Found During Exploration
None found. All 5 case steps executed cleanly against the live product;
the only finding was the pre-existing `wait_for_node_on_canvas()`
same-type-collision limitation documented above (not a product defect —
a test-automation page-object gap), routed via the Coverage Map Axis-2 note
and `_surface.md`, not filed as a bug.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, project standard).
- Page object: extend `automation/pages/pipeline_detail_page.py`
  (`PipelineDetailPage`) — reuse `is_flow_view_active()`,
  `switch_to_yaml_view()`, `switch_to_flow_view()`, `get_yaml_content()`,
  `get_add_node_menu_items()`, `select_add_node_menu_item()`,
  `wait_for_node_on_canvas()`, `get_node_ids()`, `get_node_count()`,
  `canvas_wrapper` as-is. No new page-object method needed — this case is
  purely additive reuse of existing methods, correctly sequenced per the
  ambiguity caveat above.
- Fixture: `pipeline_with_llm_id` (`automation/fixtures/data_fixtures.py:163`)
  is the correct starting seed (LLM 1 → END).
- **New-node YAML shape confirmed live (worth recording in `_surface.md`):**
  a freshly-added, unconnected second node (added via the canvas Add-node
  menu, never Saved) has **no `transition:` key at all** in its YAML
  entry — unlike a single/entry-point node, which always carries
  `transition: END` even with no outgoing edge (per the existing
  `_surface.md` § "Node config via YAML" note). The two facts don't
  conflict: `transition: END` is the entry-point/only-node default: a
  second, not-yet-wired node has no transition target assigned at all
  until the user connects it or saves. Confirmed live via a real
  `get_yaml_content()` read.
- Wait strategy: `select_add_node_menu_item()` already settles ~1s
  internally; `wait_for_node_on_canvas("llm", …)` is still called after it
  (to wait for the new node to be attached to the DOM) even though its
  return value isn't the trusted new-node id here. No explicit network
  wait needed anywhere in this flow — everything is client-side (see
  § Network Behavior).
