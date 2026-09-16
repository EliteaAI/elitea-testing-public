# Test Case: Pipeline — Add Node Menu

## Metadata
- **TMS ID**: ELITEA-2030
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`) — original analysis 2026-08-03; **re-executed 2026-09-16 on `https://dev.elitea.ai` (`APP_PREFIX=/app`, Keycloak `${TEST_USER}`) plus a localhost parity probe** (§ Adjustment)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`; real Keycloak session on DEV)
- **Analyst**: qa-engineer (Sage), cluster analysis session with ELITEA-2018/2031/2032; adjustment pass 2026-09-16 (#2317)
- **Status**: ready-for-automation *(adjust — expected node-type list changed by product change EL-6616; see § Adjustment)*

## Preconditions
- User is authenticated (localhost `auth_state` fixture; Keycloak session on deployed envs).
- A pipeline is open in Flow view (empty pipeline is sufficient — the menu's
  option set does not depend on existing canvas content).

## Test Data
### reuse-existing
- Expected node types (confirmed live 2026-09-16 on DEV **and** localhost,
  DOM order, exact): `Agent, Code, Decision, Human-in-the-loop, LLM, MCP,
  Printer, Router, State modifier, Toolkit` — **10 items**.
- **Absent by design:** `Custom` — deprecated and hidden from the picker by
  EliteaAI/EliteaUI@0cd5e792 (EL-6616). Its menu item
  (`pipeline-add-node-menu-item-custom`) must NOT render (count 0).
- The corresponding internal type keys (the `pipeline-add-node-menu-item-{type}`
  suffixes, same DOM order): `agent, code, decision, hitl, llm, mcp, printer,
  router, state_modifier, toolkit`.

### generate-per-test (in test setup, cleaned up in its own teardown)
- Empty pipeline via the existing `pipeline_id` fixture.

## Test Steps
1. Navigate to the pipeline's canvas.
   - **Verify**: `PipelineDetailPage.canvas_wrapper` visible.
2. Click the "Add node" ("+") button (`add_node_button`).
   - **Verify**: the menu container `add_node_menu`
     (`pipeline-add-node-menu`) becomes visible.
3. Read all menu item labels (`ADD_NODE_MENU_ITEM_PREFIX`, DOM order) inside the menu.
   - **Verify (a)**: labels equal, in order,
     `["Agent", "Code", "Decision", "Human-in-the-loop", "LLM", "MCP",
     "Printer", "Router", "State modifier", "Toolkit"]` — **10 items**,
     confirmed live 2026-09-16 on DEV and localhost (exact match, no extras,
     no omissions). Exact-list `==` — never `in` / subset.
   - **Verify (b) — absence, asserted AFTER (2)'s container-visible check:**
     `ADD_NODE_MENU_ITEM_BY_TYPE.format("custom")` has count 0
     (`expect(...).to_have_count(0)`). Ordering is load-bearing: a
     `to_have_count(0)` on its own is satisfied by a menu that has not
     rendered yet, so it must follow the positive container/list check
     (same shape as the EL-6460 breadcrumb precedent,
     `tests/ui/agents/test_agent_back_navigation.py` Step 3).
4. Click "LLM" (`select_add_node_menu_item("llm")`).
   - **Verify**: menu closes; an LLM node (`.react-flow__node-llm`) appears
     on canvas via `wait_for_node_on_canvas("llm")`; node count +1
     (DEV 2026-09-16: `1 -> 2`, END node pre-exists on an empty pipeline).
5. Verify the new LLM node's configuration panel is open by default.
   - **Verify**: the node's config fields (SYSTEM/TASK/CHAT HISTORY
     Type+Value, Input/Output, Toolkits, Interrupt before/after, Structured
     output — per the `_surface.md` LLM-node digest, ELITEA-2004) are
     immediately visible in the node's rendered DOM — **no click-to-expand
     step exists**; every node type on this canvas renders its full config
     inline/always-expanded (confirmed pattern across LLM/HITL/MCP/Toolkit
     nodes, `_surface.md`). "Panel open" is satisfied by the node simply
     being present (`get_node_ids()` contains the id returned in step 4;
     DEV 2026-09-16: `['END', 'LLM 1']`).
6. Re-open the Add node menu, then press Escape.
   - **Verify**: `wait_for_popup_menu_hidden()` — `POPUP_MENU_TESTIDS`
     count 0 after Escape (confirmed live DEV 2026-09-16) and node count
     unchanged (no node was added; DEV: `2 -> 2`).

## Expected Results
- The Add node menu lists exactly the **10** node types above, in that
  order, no more, no fewer — and does **not** list `Custom`
  (`pipeline-add-node-menu-item-custom` count 0).
- Selecting LLM adds one LLM node with its full config immediately visible.
- Escape dismisses the menu without adding a node.
- No console errors during the flow (DEV 2026-09-16: 0 via
  `utils/console_errors.collect_console_errors`).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Test Data: expected node types list | matches live menu — **10 types, Custom absent (EL-6616)** | step 3 | step 3(a): exact list equality; 3(b): Custom item count 0 | asserted *(case text still says 11 incl. Custom — stale; § Proposed TMS case-text change)* |
| 1 Open pipeline in Flow view | canvas displayed | step 1 | step 1: canvas wrapper visible | asserted |
| 2 Click "Add node" button | popup menu appears | step 2 | step 2: `pipeline-add-node-menu` visible | asserted |
| 3 Verify all node types listed | all **10** present, Custom absent | step 3 | step 3(a) exact list match + 3(b) absence | asserted *(was "all 11")* |
| 4 Click "LLM" | LLM node added | step 4 | step 4: node visible via `wait_for_node_on_canvas`, count +1 | asserted |
| 5 New LLM node visible, config panel open | node visible + panel open | step 5 | step 5: node id present in `get_node_ids()` (always-inline config, no separate "open" trigger) | asserted *(the case's phrasing implies a click-to-open interaction that doesn't exist for any node type on this canvas — not a defect, just this app's uniform node-config pattern; documented so the implementer doesn't go looking for a nonexistent "expand" control)* |
| 6 Escape / click-outside dismisses menu without adding | menu closes, no node added | step 6 | step 6: popup-menu count 0 + node count unchanged | asserted |

### Axis 2 — Analyst additions

- step 3(a) asserts DOM *order* of the 10 menu items, not just set
  membership — *added: catches a future menu reorder even though the case
  doesn't require a specific order; cheap to assert since the list was read
  in DOM order anyway, and a stable order is worth guarding.*
- step 3(b) asserts the **absence** of the Custom menu item as a first-class
  observable — *added 2026-09-16 (#2317): the EL-6616 deprecation is a
  product contract ("hidden from the node picker"); an exact-list assertion
  alone would also fail if Custom came back, but a named absence assertion
  turns the deprecation into a precisely-reported invariant instead of a
  generic list-mismatch, and it keeps the drift test-enforced rather than
  comment-documented (EL-6460 precedent).*
- step 6 additionally asserts the node count is unchanged after Escape (the
  case only asserts "menu closes") — *added: rules out a race where Escape
  both closes the menu AND leaves a stray node behind, which "menu
  dismisses" alone wouldn't catch.*

## Cleanup
1. `pipeline_api.delete_pipeline(pid)` (fixture teardown).

## Handles Reference (testid-only)

Provenance verified 2026-09-16 after `cd ../EliteaUI && git fetch origin`,
two-stage grep (`-i`, `[:=]`) per `.agents/workflow.md` § Closure record:

```
pipeline-add-node-button           main:YES  testids:YES
pipeline-add-node-menu             main:YES  testids:YES
pipeline-add-node-menu-item-       main:YES  testids:YES
```
(`origin/main:src/pages/Pipelines/Components/AddNodeMenu.jsx:76, :93, :120/:143`)

| Element | Page-object handle (`automation/pages/pipeline_detail_page.py`) | Testid | PROVENANCE |
|---|---|---|---|
| Add node ("+") button | `add_node_button` (`LocatorDescriptor`) | `pipeline-add-node-button` | on-main ✓ |
| Menu container | `add_node_menu` (`LocatorDescriptor`) | `pipeline-add-node-menu` | on-main ✓ |
| Every rendered menu item, DOM order | `ADD_NODE_MENU_ITEM_PREFIX` (`[data-testid^="pipeline-add-node-menu-item-"]`) via `get_add_node_menu_items()` | `pipeline-add-node-menu-item-{type}` (template, `AddNodeMenu.jsx:120/143`) | on-main ✓ |
| One menu item by internal type (select "llm"; **absence** of "custom") | `ADD_NODE_MENU_ITEM_BY_TYPE` (`[data-testid="pipeline-add-node-menu-item-{}"]`) via `select_add_node_menu_item("llm")`; `.format("custom")` for the count-0 assertion | `pipeline-add-node-menu-item-llm` / `pipeline-add-node-menu-item-custom` (the latter must not render) | on-main ✓ (template) |
| Any canvas popup menu (dismiss check) | `POPUP_MENU_TESTIDS` via `wait_for_popup_menu_hidden()` / `is_popup_menu_visible()` | `pipeline-add-node-menu`, `pipeline-connection-dropdown-menu` | on-main ✓ |
| Node appears on canvas | `wait_for_node_on_canvas("llm")`, `get_node_ids()`, `get_node_count()` (existing) | — (ReactFlow `.react-flow__node-*` / `data-id`, pre-policy tech debt #25/#42, not extended here) | n/a |

**No new testid and no new `LocatorDescriptor` field is needed for the
adjustment.** The absence assertion is served by the existing class-level
template constant `ADD_NODE_MENU_ITEM_BY_TYPE.format("custom")` — the same
compliant dynamic-testid shape `select_add_node_menu_item()` already uses
(`.agents/testing.md` § Locator policy, dynamic testids). Nothing in
`.agents/role-overrides.md` requires a static field for a value that is
only ever asserted absent.

**Testid gap CLOSED (implementer amendment, review round 1).** The original
exploration below is kept for its provenance value, but its own
recommendation did not survive review:

> ~~Testid gap, not blocking: the Add-node "+" button and its 11 menu items
> carry zero `data-testid`s... Recommend (a) [reuse the existing raw-handle
> `add_node()` method as-is]... flagging for the lead rather than deciding
> unilaterally.~~

`.agents/role-overrides.md` § Every role — locator policy states the
escalation test is **OR, not AND**: a missing testid ALONE is enough to
require `add-data-testid`, regardless of whether reusing a raw handle would
also work and regardless of an AFS's own "not blocking" framing — an AFS
recommendation doesn't waive the hard-override. Reviewer flagged this in
round 1; testids were added onto `AddNodeMenu.jsx`'s trigger button, `Menu`,
and each `MenuItem` (keyed by internal node type) instead. They have since
been promoted to EliteaUI `main` (provenance block above).

**Step 4 update (fix round 4).** `add_node()` (Step 4, pre-existing tech debt
shared with `test_pipeline_nodes.py::TestAddNode`) was initially left
untouched as out of this case's scope. Round 3 review flagged the companion
`select_add_node_menu_item()` method as dead code (zero callers anywhere in
the branch — canon ruling #511, a method isn't "exercised" by merely
existing). Rather than delete it, round 4 wired it into this test's own
Step 4 (`get_add_node_menu_items()` to open + `select_add_node_menu_item("llm")`
to select), closing the dead-code finding AND completing the testid-clean
sweep for this case's own steps. `add_node()` itself is untouched and
remains correct, in-use tech debt for every OTHER pipeline test that calls
it — this is a same-file, same-case change, not a re-scope of that debt.

## Network Behavior
- None — pure client-side canvas/menu interaction, no XHR involved in
  opening the menu, listing items, or adding a node (node creation is
  local ReactFlow state until Save). The visible list is computed
  client-side by `getVisibleNodeTypes()` (`AddNodeMenu.jsx:23-28`) from
  `FlowEditorConstants.PipelineNodeTypes` minus
  `DeprecatedConstants.DeprecatedOrInvisibleNode`.

## Fidelity Declaration
- None. Every observable (menu list, Custom absence, LLM node, Escape
  dismissal) is produced by the live product; the only test-side data is
  the empty pipeline the `pipeline_id` fixture creates via API — a
  precondition the case itself leaves unspecified ("a pipeline is open"),
  not a substitution of anything observed.

## Known Defects Found During Exploration
- none found (2026-08-03 and 2026-09-16).

## Blocked Steps
- none.

## Adjustment (2026-09-16, #2317)

**Trigger.** UI Tests DEV Stable [main] run #166 (35096309187) failed
`automation/tests/ui/pipelines/test_pipeline_add_node_menu.py::test_add_node_menu_lists_types_adds_node_and_dismisses`
at Step 2/3: menu returned 10 labels vs `EXPECTED_NODE_TYPES` (11, incl.
`"Custom"`). Not a promotion gap — spec + AFS byte-identical on `origin/main`
and `origin/automation/base`, and all three testids are on `main` (provenance
block above).

**Triage class: A — UI drift caused by a deliberate product change.** The
four "deliberate vs regression" tells, all live-confirmed:

| Tell | Evidence |
|---|---|
| Targeted diff | EliteaAI/EliteaUI@0cd5e792 (*feat: [EL-6616] Deprecate and hide Custom node from pipeline node picker (#993)*, MikalaiB, 2026-09-11) — 2 files, +5/−1: adds `PipelineNodeTypes.Custom` to `DeprecatedNodes` in `src/[fsd]/features/pipelines/flow-editor/lib/constants/deprecated.constants.js` and drops "Custom" from the pipeline tour copy. Ancestor of `origin/main` **and** `origin/automation/testids` (`git merge-base --is-ancestor` both true). |
| Authored intent in source | `DeprecatedTips[Custom].text` = *"This node is deprecated and hidden from the node picker. Existing Custom nodes will keep working — please select a specific node type (Toolkit, MCP, LLM, Code, etc.) instead."* |
| Scoped feature ticket | EL-6616, in the commit subject. |
| Affordance preserved elsewhere | A pre-existing Custom node (seeded via YAML `type: custom`) still renders on the canvas with a "Deprecated!" badge whose tooltip is the authored tip above (`NodeCardHeader.jsx:307` renders `DeprecatedTips[type]`) — live on localhost 2026-09-16, screenshot below. |

Mechanism: `AddNodeMenu.jsx:23-28` `getVisibleNodeTypes()` filters
`PipelineNodeTypes` against `DeprecatedOrInvisibleNode`, which is built from
`DeprecatedNodes` — so once `Custom` is in `DeprecatedNodes` the item is never
rendered. Same behaviour on DEV (production bundle) and localhost (dev server,
same commit).

**What drifted (old → new).** Menu list
`[Agent, Code, Custom, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State modifier, Toolkit]` (11)
→ `[Agent, Code, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State modifier, Toolkit]` (10).
Testid suffixes now rendered, DOM order:
`agent, code, decision, hitl, llm, mcp, printer, router, state_modifier, toolkit`;
`pipeline-add-node-menu-item-custom` count 0. No handle renamed, moved or removed.

**Live re-execution 2026-09-16 (real Keycloak session on DEV, suite page objects, no substitution):**

| Step | Observed on `https://dev.elitea.ai` | localhost:5173 parity probe |
|---|---|---|
| 1 Canvas | `canvas_wrapper` visible on `/app/pipelines/all/10907` | canvas rendered |
| 2 "+" click | `pipeline-add-node-menu` visible | menu opened |
| 3 List | 10 labels, order as above; `…-item-custom` count 0 | same 10 `menuitem`s, same order; no Custom |
| 4 LLM | `LLM 1` added, node count 1 → 2, menu closed | not re-run (list parity was the probe's purpose) |
| 5 Panel | `LLM 1` in `get_node_ids()` → `['END', 'LLM 1']` (inline config, no expand step) | — |
| 6 Escape | popup-menu count 0, node count 2 → 2 | Escape closed the menu (0 `menuitem`s) |
| Console | 0 errors | — |

![ELITEA-2030 Step 3 — Add node menu on DEV, 10 items, no Custom](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2030-step-03-add-node-menu-dev.png)

![ELITEA-2030 — existing Custom node still renders with the EL-6616 deprecation tip (localhost)](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2030-existing-custom-node-deprecated-tip-localhost.png)

**Expected-result changes.** Exactly one: the expected node-type list goes
from 11 items (incl. Custom) to the 10 items above. This is a **genuine
change of the case's expected result caused by product change EL-6616**, not
a weakened assertion — the comparison stays exact-list `==`, in DOM order,
and gains a new first-class absence assertion. **No other expected-result
changes**: Steps 1, 2, 4, 5, 6 and every existing assertion (menu visible,
LLM added with count +1, node id tracked, Escape dismisses with count
unchanged) are preserved verbatim.

**Implementer guidance (Step 7 of `adjust-automated-test`, out of this
slot's scope):**
- `EXPECTED_NODE_TYPES` → the 10-item list; keep `assert menu_items == EXPECTED_NODE_TYPES`
  (exact, ordered). Update the "11" wording in the docstring/assert message.
- Add, inside the Step 2/3 `allure.step` and **after** the list/container
  positive check: `expect(page.locator(PipelineDetailPage.ADD_NODE_MENU_ITEM_BY_TYPE.format("custom"))).to_have_count(0)`
  — preferably via a small page-object method (e.g.
  `expect_add_node_menu_item_absent(node_type)`) so the locator construction
  stays inside `pipeline_detail_page.py`, using the existing class-level
  template constant; **no new `LocatorDescriptor` field and no new testid**.
  A one-line comment naming EL-6616 / EliteaAI/EliteaUI@0cd5e792 next to it.
- Keep markers, `@allure.issue` link and every `allure.step("Step N — …")`
  block as they are.
- Gate on `https://dev.elitea.ai` (the red came from DEV; all testids are on
  `main`), 3 separate invocations, then a localhost run for parity.

### Proposed TMS case-text change
File (edit by exact path, keep `automation_test_id` unchanged):
`tests/automated-full-regression-ui/pipelines/ELITEA-2030_pipeline-add-node-menu.md`

**Test Data row** — replace with:

| Field | Value |
|-------|-------|
| Expected node types | Agent, Code, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State modifier, Toolkit |
| Hidden node types | Custom — deprecated and hidden from the node picker since EL-6616 (existing Custom nodes keep working) |

**Step 3** — replace with:

| # | Action | Expected Result |
|---|--------|-----------------|
| 3 | Verify the popup menu lists the following node type options: Agent, Code, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State modifier, Toolkit — and does not list "Custom" | All 10 node types are listed in the menu; "Custom" is not offered (deprecated, EL-6616) |

**Expected Final State** — replace with:

> The "Add node" menu lists all 10 available node types and does not offer the deprecated "Custom" node. Selecting a type adds the node to the canvas and opens its configuration panel. The menu dismisses when Escape is pressed.

**Pass/Fail Criteria** — replace the second Pass bullet and the second Fail bullet with:

> **Pass:** All 10 node types are listed and "Custom" is absent, LLM node is added and its panel opens, menu dismisses on Escape.
> **Fail:** Node types are missing from the menu, "Custom" is offered in the menu, node is not added, or menu does not dismiss.

(Objective sentence may stay as is — "all available node types" is still
accurate.)

## Automation Hints
- Framework: Playwright + pytest.
- Page object: `automation/pages/pipeline_detail_page.py` — `wait_for_node_on_canvas()`,
  `get_node_count()`, `get_node_ids()` exist, reuse as-is; Step 4 uses the testid-based
  `get_add_node_menu_items()` + `select_add_node_menu_item("llm")` pair
  (round 4 — see Handles Reference § Step 4 update), not `add_node()`.
- `helpers._navigate_to_canvas(page, pipeline_id)` for setup navigation.
- Step 3(b) absence check: `ADD_NODE_MENU_ITEM_BY_TYPE.format("custom")` +
  `expect(...).to_have_count(0)`, asserted after the positive list check
  (see § Adjustment → Implementer guidance).
