# Test Case: Pipeline — Add Node Menu (lists all 11 types, adds a node, dismisses without adding)

## Metadata
- **TMS ID**: ELITEA-2030
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-07-24
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline exists and is open in Flow view. The existing `pipeline_id` fixture
  (bare pipeline, single `END` node, already used by `test_add_human_in_the_loop_node_and_connect_to_end`
  in `test_pipeline_nodes.py`) is sufficient — this case needs no special node/edge
  topology, just a canvas to open the menu on.

## Test Data

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- Existing `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`) — fresh
  pipeline per test, deleted in its own teardown.
- Expected node-type menu contents (verbatim from the source enum, confirmed
  live — see Concrete Handles): `{"agent": "Agent", "code": "Code", "custom":
  "Custom", "decision": "Decision", "hitl": "Human-in-the-loop", "llm": "LLM",
  "mcp": "MCP", "printer": "Printer", "router": "Router", "state_modifier":
  "State modifier", "toolkit": "Toolkit"}` — exactly 11 entries, exactly matching
  the case's own Test Data table (order in the table is already alphabetical,
  which is also the confirmed live DOM order — see Automation Hints on whether
  to assert order).

## Test Steps

### Test 1 — `test_add_node_menu_lists_all_types_and_adds_llm_node` (primary path, case steps 1–6 using the Escape gesture)

1. Navigate to the fixture pipeline's canvas (`_navigate_to_canvas()`, existing helper) and switch to Flow view (default).
   - **Verify**: canvas wrapper visible (`wait_for_canvas()`); exactly 1 node present (`END`) via `get_node_count() == 1`.
2. Click the "Add node" button (testid needed — see Concrete Handles).
   - **Verify**: the menu is open — `aria-expanded="true"` on the trigger button (existing native attribute, read off the new testid'd element, not a new locator).
3. Read all 11 menu-item labels by their known, fixed internal type slugs (testid needed, dynamic family — see Concrete Handles) and compare against the expected map above.
   - **Verify**: all 11 labels match exactly: `Agent, Code, Custom, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State modifier, Toolkit`. (Live-confirmed count via `document.querySelectorAll('[role=menuitem]').length === 11` and exact text match against this same list, in this same DOM order — see Automation Hints for the order-assertion recommendation.)
4. Click the "LLM" menu item (via its own dynamic testid, `type=llm`).
   - **Verify**: menu closes (`pipeline-add-node-menu` — MUI's own portal root — no longer in DOM); `get_node_count()` increased by 1 (from 1 to 2); a new `.react-flow__node-llm` element is present (`wait_for_node_on_canvas("llm")`, existing method) with a non-empty `data-id` (e.g. `LLM 1`).
5. Read the new LLM node's own text content via its `rf__node-{id}` testid (existing library-provided handle, confirmed free — see Concrete Handles) without any additional click.
   - **Verify**: the text contains `"System"`, `"Task"`, and `"Chat history"` (the three inline field-group labels that only render once the node's default configuration panel is open — confirmed live this session: they are present in the DOM the instant the node is added, no separate expand step exists for this node type).
6. Re-open the "Add node" menu (click the trigger button again) and press **Escape**.
   - **Verify**: the menu closes (`pipeline-add-node-menu` no longer in DOM); `get_node_count()` is unchanged (still 2 — no node was added by the Escape dismissal).

### Test 2 — `test_add_node_menu_dismiss_via_click_outside` (alternate activation for the dismiss gesture — case step 6's "OR click outside")

1. Fresh instance of the same `pipeline_id` fixture; navigate + wait for canvas.
   - **Verify**: `get_node_count() == 1`.
2. Click the "Add node" button.
   - **Verify**: menu open (`aria-expanded="true"`, same check as Test 1 step 2).
3. Click a point on the canvas clearly outside the menu's own popup panel (see Automation Hints — **mandatory read**, a naive "click the backdrop element's own bounding-box center" approach can accidentally land back on a menu item instead of truly outside the panel, because the backdrop's DOM bounding box is the full viewport but its *visual* center is usually obscured by the smaller popup Paper painted on top of it).
   - **Verify**: the menu closes (`pipeline-add-node-menu` no longer in DOM); `get_node_count()` is unchanged (still 1 — no node was added).

## Expected Results
- Clicking "Add node" opens a popup menu listing exactly the 11 currently-supported
  node types (Agent, Code, Custom, Decision, Human-in-the-loop, LLM, MCP, Printer,
  Router, State modifier, Toolkit) — confirmed to be an exhaustive, source-derived
  list (see Concrete Handles: the deprecated/hidden types — Tool, Function,
  Condition, Pipeline, Loop, Loop from tool — plus the internal-only End/Ghost/
  Default types are correctly excluded by the app's own filter, not by coincidence).
- Selecting a type (LLM, in this case) adds a node of that type to the canvas
  immediately (client-side, no network request), with its default configuration
  panel already rendered/open — there is no separate "expand" interaction for
  this node type.
- Pressing Escape, or clicking genuinely outside the menu's popup panel, closes
  the menu without adding any node — both are equally valid dismissal gestures.
- No console errors at any step (aside from the documented, pre-existing,
  unrelated ReactFlow dev-mode warnings already logged in `_surface.md`).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline in Flow view | canvas displayed | Test 1 step 1 | `wait_for_canvas()` + `get_node_count() == 1` | asserted |
| 2 Click "Add node" button (+ icon) | popup menu appears | Test 1 step 2, Test 2 step 2 | `aria-expanded="true"` on trigger button | asserted |
| 3 Verify popup menu lists all 11 node types (Agent, Code, Custom, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State modifier, Toolkit) | all 11 listed | Test 1 step 3 | per-slug testid text-content compare against the expected map | asserted |
| 4 Click "LLM" to add an LLM node | LLM node added | Test 1 step 4 | `get_node_count()` delta + `wait_for_node_on_canvas("llm")` | asserted |
| 5 Verify new LLM node appears with default configuration panel open | node visible, panel open | Test 1 step 5 | node's own `rf__node-{id}` text contains System/Task/Chat history labels | asserted |
| 6 Press Escape or click outside to close menu without adding (verify menu dismisses) | menu closes, no node added | Test 1 step 6 (Escape); Test 2 steps 2–3 (click outside) | menu removed from DOM + `get_node_count()` unchanged, both gestures | asserted *(decomposed into 2 tests — one per dismissal gesture the case names as valid alternatives, so both are actually exercised, per this project's established pattern for case-named "OR" alternatives — see `l2_pipeline-canvas-delete-node_ELITEA-2018.md`)* |
| Test Data: expected node types list | 11 types, exact names | Test 1 step 3 | as above | asserted |
| Expected Final State: menu lists all 11, selecting adds+opens panel, Escape dismisses | — | Test 1 (full) | as above | asserted |
| Pass/Fail: all steps complete without errors; 11 types listed, LLM added+panel open, menu dismisses on Escape | — | Test 1 (full), Test 2 (dismiss-gesture slice) | all steps above + zero-console-error checks | asserted |

### Axis 2 — Analyst additions

- **Zero console errors** at every step — *added: standard side-channel check. Confirmed only the pre-existing, unrelated `warning`-level ReactFlow messages already documented in `_surface.md` (parent-container width/height on first paint, and the ambient `nodeTypes`/`edgeTypes` re-render message) — neither is `error`-level, neither is specific to this feature.*
- **Confirmed the 11-item list is exhaustive-by-source, not by observation alone** — *added: read `flowEditor.constants.js`'s `PipelineNodeTypes`/`deprecated.constants.js`'s `DeprecatedOrInvisibleNode` and traced `getVisibleNodeTypes()`'s filter logic (see Concrete Handles) to confirm the excluded types (Tool, Function, Condition, Pipeline, Loop, Loop from tool — all deprecated per `DeprecatedNodes`; End, Ghost, Default — internal/structural, never user-addable) are excluded BY DESIGN, not because this session happened to miss them. This makes the "exactly 11, never more/fewer" assertion durable against a future node-type addition/removal, since it's grounded in the same source list the app itself filters from.*
- **Verified the click-outside dismissal against the TRUE invisible backdrop, not a naive bounding-box-center click** — *added: see Automation Hints for the tooling gotcha this session hit and worked around (a raw `.MuiBackdrop-root` selector's own center coincided with a rendered menu item and produced a false "click outside added a node" result on the first attempt). Documented so the implementer's Playwright code doesn't repeat it.*
- No defect filed — every observed behavior (11-item enumeration, LLM add + open panel, Escape dismiss, click-outside dismiss) was correct on first true (non-tooling-confounded) execution.

## Cleanup
1. This session used the existing shared "GetUserName" pipeline (id `153`, project `Elitea Testing Team`) for live exploration via `browser-verify`/CDP (Playwright MCP's shared browser was locked by a concurrent lane — see notes). **No Save was ever clicked**, so the two exploratory nodes added during this session (`LLM 2`, and one accidental `Agent 1` from a tooling misstep — see Automation Hints) were never persisted; the browser session was closed without saving, leaving the shared pipeline's saved state untouched. Confirmed via the app's own "Node-graph changes need pipeline's own Save click" behavior (already documented in `_surface.md`).
2. Implementer teardown: none needed beyond the existing `pipeline_id` fixture's own teardown (deletes the pipeline it creates) — this case adds no persistent test data of its own since neither test clicks Save.

## Concrete Handles (discovered during exploration)

Provenance verified this session via `cd ../EliteaUI && git fetch origin` immediately
before checking (`.agents/role-overrides.md` § Analyst slot). Command used for each
row below: `git grep -- "<testid>" origin/main -- src/` vs `origin/automation/testids -- src/`.
Source file for all NEW handles below: `src/pages/Pipelines/Components/AddNodeMenu.jsx`
(confirmed via `git diff origin/main origin/automation/testids -- <file>` = empty —
zero pending work on this file from any other in-flight case in this batch).

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| "Add node" trigger button | testid needed: `pipeline-add-node-button` | **needs-adding** (confirmed absent on both `main` and `automation/testids`) | `AddNodeMenu.jsx:75-90` — the `<IconButton>` already carries `id="pipeline-add-node-menu-action"` (native DOM id, not a testid) and `aria-label="Add node"` — trivial one-line `data-testid="pipeline-add-node-button"` addition, same file, no shared-component edits (this `IconButton` is feature-local, not `src/components/shared`). `aria-expanded` is already present and correctly toggles (confirmed live) — read it off the new testid'd element for the open/closed state check, no new locator needed for that. |
| Menu popup — node-type items (11, one per type) | testid needed, dynamic family: `pipeline-add-node-menu-item-{type}` where `{type}` = the internal enum slug already computed in the JSX loop (`item.type` — `agent`, `code`, `custom`, `decision`, `hitl`, `llm`, `mcp`, `printer`, `router`, `state_modifier`, `toolkit`) | **needs-adding** (confirmed absent on both branches) | `AddNodeMenu.jsx:115-134` (left column, `leftColumnItems.map`) and `:137-156` (right column, `rightColumnItems.map`) — both `<MenuItem>` loops already have `key={item.type}` (a React key, not a DOM attribute) — add `data-testid={`pipeline-add-node-menu-item-${item.type}`}` directly on each `<MenuItem>` in both loops (2 one-line edits, same file, `item.type` already in scope). This is the closed/finite-set analogue of the project's existing dynamic-testid pattern (`SKILL_TAG_OPTION`/`SELECT_OPTION` families) — the implementer's page object should declare `ADD_NODE_MENU_ITEM = '[data-testid="pipeline-add-node-menu-item-{}"]'` as an UPPER_CASE class constant and loop over the 11 KNOWN slugs (not a wildcard/prefix query — the set is closed, so no new "enumerate all instances of a template" pattern is needed, avoiding a declared-improvisation call). |
| Menu popup container (the `ul[role=menu]`) | not required for this case | out of scope | `AddNodeMenu.jsx:91` — the `<Menu id="pipeline-add-node-menu">` root has no testid either (native `id` only). This case doesn't need to locate the container itself (it opens the menu via the trigger button's `aria-expanded` state, and each item is located individually by its own new dynamic testid) — not requesting a testid here to keep this pass scoped to exactly what the case touches (role-overrides.md § "touches" rule). |
| Node container (any type) | `[data-testid="rf__node-{id}"]`, e.g. `rf__node-LLM 1` | N/A — `@xyflow/react` library-level convention, not app JSX (`grep -rn "rf__node" src/` = 0 hits); present on any branch/build, confirmed live and already documented in `_surface.md` | Reused as-is for both the node-count/type check (existing `wait_for_node_on_canvas("llm")`, `get_node_count()`) and the new "config panel is open" text-content read (step 5) — the latter is a NEW small helper recommended below, not an existing method. |
| LLM node's inline field labels ("System", "Task", "Chat history") | read via the node's own `rf__node-{id}` container `.text_content()` — no per-field testid needed for THIS case | N/A | `_surface.md` already documents these fields render with **zero** `data-testid` today (a separate, larger gap tracked under ELITEA-2004's own AFS for editing them). This case only needs to prove the panel is *open* (fields present at all, immediately after add), not to edit any of them — so a scoped text-content substring check off the already-testid'd node container satisfies the case without requesting new field-level testids this case doesn't otherwise touch. |
| Pipeline canvas wrapper / Flow view | `rf__wrapper` / `pipeline-flow-view` | on-main ✓ (pre-existing) | Reused as-is via existing `wait_for_canvas()` / Flow-view-is-default behavior. |

## Network Behavior
- No request fires on opening the menu, reading its contents, selecting a type
  (adding the node), or dismissing it (Escape or click-outside) — the entire
  flow is **client-side only**, confirmed live (Save button transitions from
  disabled to enabled after adding LLM, but no network call fires until Save
  is actually clicked — which this case's steps never do).
- If a future case chains a Save after this flow, the relevant request is
  `PUT /elitea_core/application/prompt_lib/{project}/{pipeline_id}` (already
  documented in `l2_pipeline-canvas-delete-node_ELITEA-2018.md` and `_surface.md`)
  — not exercised here, out of scope for this case's own Pass/Fail criteria.

## Known Defects Found During Exploration

**None found in the Add Node menu feature itself.** All 11 expected node types
are listed, in the exact expected names, exactly once each; selecting LLM adds
the node with its configuration panel already open; both dismissal gestures
(Escape, click-outside) correctly close the menu without adding a node.

- **[Tooling-only artifact, not a defect, not filed]** — this session's own first
  attempt at "click outside" used a raw `document.querySelector('.MuiBackdrop-root')`
  selector's own bounding-box CENTER as the click coordinate. Because the invisible
  backdrop's DOM bounding box is the full viewport, its geometric center coincided
  with a menu item rendered on top of it at that same screen position — the click
  landed on that foreground "Agent" menu item instead of the true backdrop, closing
  the menu AND accidentally adding an Agent node. Re-verified cleanly in the same
  session using `document.elementFromPoint()` at a coordinate genuinely outside the
  popup panel's own rect, confirming the true backdrop is hit and the dismissal is
  clean (no node added). Ruled out as an analyst-tooling artifact (not a product
  defect) per this project's synthetic-input-hygiene discipline before writing this
  AFS — see Automation Hints for how the real Playwright test avoids the same trap.

## Blocked Steps

None. All case steps were executed to completion against the live local environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
  **This case requires a small `add-data-testid` pass** — 12 new testids total (1
  trigger button + 11 menu items), all in a single file (`AddNodeMenu.jsx`), all
  trivial one-line additions, zero shared-component edits.
- **Recommend fixing the existing `add_node()` method's raw selectors while
  implementing this case** (`pipeline_detail_page.py:550-575`) — it currently
  clicks the trigger via `page.locator("button.MuiIconButton-colorPrimary").first`
  (a raw CSS class selector) and the menu item via `page.get_by_role("menuitem",
  name=node_type, exact=True)` (a role+accessible-name lookup) — both are exactly
  the kind of raw handle `role-overrides.md` flags as tracked tech debt, and this
  case is a natural point to fix it since it already needs the new testids for its
  own assertions. **Keep the method's existing signature** (`node_type: str`
  display name, e.g. `"LLM"`, `"Human-in-the-loop"`) so the 6+ existing call
  sites across `test_pipeline_advanced.py` / `test_pipeline_nodes.py` /
  `test_pipeline_mcp_node_*.py` keep working unchanged — internally map the
  display name to the new testid's slug (a small dict: `{"LLM": "llm", "Code":
  "code", "Custom": "custom", "Decision": "decision", "Human-in-the-loop": "hitl",
  "Agent": "agent", "MCP": "mcp", "Printer": "printer", "Router": "router",
  "State modifier": "state_modifier", "Toolkit": "toolkit"}`) and locate via
  `self.ADD_NODE_MENU_ITEM.format(slug)` instead of the role-based lookup.
- **Click-outside gotcha (mandatory read before writing Test 2):** do NOT click a
  raw `.MuiBackdrop-root` (or any full-viewport overlay) selector's own computed
  center as "the outside click" — see Known Defects for exactly how this
  self-confounded this session's first attempt (the center coincided with a
  foreground menu item and added a node instead of dismissing cleanly). In real
  Playwright, the safe pattern is `page.mouse.click(x, y)` at an explicit
  coordinate confirmed (via a quick `page.evaluate("document.elementFromPoint(x,y)")`
  check, or simply a point known to be outside the popup Paper's own
  `bounding_box()`) to land on empty canvas / the true backdrop — not a
  selector-center click on the backdrop element itself. Escape (Test 1) has no
  such gotcha and is the more reliable of the two gestures to lead with.
- New page-object additions recommended on `PipelineDetailPage`
  (`automation/pages/pipeline_detail_page.py`, alongside the existing
  `add_node()`/canvas-node methods):
  - `add_node_button = LocatorDescriptor(testid="pipeline-add-node-button")`
  - `ADD_NODE_MENU_ITEM = '[data-testid="pipeline-add-node-menu-item-{}"]'` (class constant)
  - `is_add_node_menu_open() -> bool` — reads `aria-expanded` off `add_node_button`
  - `get_add_node_menu_item_label(type_slug: str) -> str` — `.format()`s
    `ADD_NODE_MENU_ITEM` and reads `.text_content()`
  - `RF_NODE = '[data-testid="rf__node-{}"]'` (class constant, not yet present
    anywhere in this file — needed for step 5's config-panel-open text read;
    reusable by future cases that need to read a node's own rendered text without
    per-field testids)
- Wait strategy: no network wait needed anywhere in this case (client-side only,
  see Network Behavior); `wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)`
  (existing constant/method) for the node-appears check; no `wait_for_timeout`/sleep
  needed for the menu open/close transitions in the real Playwright suite — MUI's
  `Menu`/`Popover` mount is synchronous enough that `expect(locator).to_be_visible()`
  polling (Playwright's built-in auto-wait) is sufficient (this session's own
  300ms `wait_for_timeout` in the existing `add_node()` is a pre-existing pattern,
  not something this case needs to add more of).
- Console-error check: filter to `level == "error"` only — see `_surface.md` for
  the already-documented, unrelated `warning`-level ReactFlow messages that fire
  on this same surface regardless of this feature.

## Redispatch confirmations

**Pass 2 (analyst-slot redispatch, 2026-07-24, ~07:xx).** Board `case.md` History:
`ready-for-automation`(03:05:55Z) → `implementing`(03:05:57Z) → `ready-for-review`(03:27:27Z,
green 1x local) → `approved-static`(03:47:02Z) → `analysis`(06:53:05Z) — the same
`approved-static → analysis` bounce with zero recorded reason seen repeatedly this session
on other cases (ELITEA-1828, ELITEA-1880, ELITEA-2170, ELITEA-1934, ELITEA-2004, ELITEA-2005,
ELITEA-2018, …) — this is now yet another distinct case with the identical shape.

Ground truth (varied axis, not a repeat of the original live-interaction pass):
- `env -u GITHUB_TOKEN gh pr view 1034 --json state,mergeable,mergeStateStatus,commits,reviews`
  → `OPEN`, `mergeStateStatus/mergeable: UNKNOWN` (GitHub hasn't computed it yet — not itself
  a blocker signal), `reviews: []` (this pipeline's reviewer verdicts live on the board, not
  posted as GitHub PR reviews — consistent with every other case this session). PR #1034's
  remote branch (`origin/tests/ELITEA-2030-add-node-menu`) carries only the 2 pre-fix-round
  commits (`ccd918e4` implementer test, `d925b1a1` memory log) — matches `gh pr view`'s
  `commits` list exactly.
- **Same "fix round IS real and correct, sits on a local-only branch that was never pushed"
  shape already seen on ELITEA-2004/ELITEA-2018.** Found worktree `wf_e44028a9-dec-151`,
  branch `fixround/ELITEA-2030-review-r1`, 2 commits ahead of `origin/tests/ELITEA-2030-add-node-menu`:
  `f667f1e0` (test fix, 06:40:37+03:00 = 03:40:37Z) + `cfd89650` (memory log, 06:43:14+03:00 =
  03:43:14Z) — both **predate** the board's `approved-static` transition (03:47:02Z) by a few
  minutes, confirming this is the R1 fix round that PRODUCED the approval (reviewer saw the
  fixed diff, approved it), not a later unexplained edit sitting on top of an already-approved
  state. Read the fix-round
  diff in full (`git show f667f1e0`): additive-only (`git diff | grep -E '^-[^-]'` on the commit
  → 0 hits, confirmed independently) — adds `PipelineDetailPage.get_add_node_menu_item_count()`
  (exhaustive-count assertion, addresses "menu could show 12 items and the per-slug loop
  wouldn't catch it"), registers `console_errors` capture in both tests + asserts empty at the
  end, and adds a symmetric `assert not is_add_node_menu_open()` to Test 1's Escape step. All
  three additions are exactly the reviewer findings named in the fix-round's own commit
  message; nothing here contradicts or amends this AFS's own content (the fix round touches
  only `pipeline_detail_page.py` + the test file, never `test-specs/`) — so there is nothing
  to re-sync in this AFS. Commit message states "Both tests green twice consecutively
  (HEADLESS=true, -p no:cacheprovider)" — a stronger confirmation than a browser spot-check
  would add, since it's the actual implemented assertions passing live, not a manual replay
  of the same steps this AFS's original pass already proved once.
- Did **zero** live browser re-exploration this pass — the original analysis (Pass 1) was a
  full 6+3-step live run against localhost:5173, and the fix round's own stated green-twice
  run is strictly stronger re-confirmation of the same code path than a manual browser replay
  would be. Nothing in the fix round touches this AFS's claims (Concrete Handles, Coverage Map,
  Known Defects, Automation Hints all unchanged and unaffected).

**Classification unchanged: `ready-for-automation`.** No further analyst dispatch is needed —
this case has already cleared analyst → implement → review → fix-round, and the fix round is
complete, additive, and self-verified green. **The only real gap is mechanical, not content:**
the fix-round commits (`f667f1e0`, `cfd89650`) sit in a local worktree branch that was never
pushed to `origin/tests/ELITEA-2030-add-node-menu`, so PR #1034 still shows only the
pre-fix-round diff and has never been re-reviewed against the fix round. **Correct next
action:** push (or cherry-pick) `fixround/ELITEA-2030-review-r1`'s 2 commits onto the PR
branch so the fix round actually reaches GitHub, then let review finalize against it — an
implementer/orchestrator action, not another analyst, implementer-from-scratch, or
reviewer-from-scratch dispatch. Flagging explicitly per this session's running pattern: this
is now one of several cases (ELITEA-2004, ELITEA-2018, plus this one) sharing the exact
"real fix round, never pushed" root cause behind the `approved-static → analysis` bounce —
worth the orchestrator treating as a single systemic gap (a step that reliably fails to push
fix-round worktree branches) rather than re-diagnosing case-by-case.
