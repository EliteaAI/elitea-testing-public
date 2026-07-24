# Test Case: Pipeline Canvas — Delete Node

## Metadata
- **TMS ID**: ELITEA-2018
- **Linked Story**: none (sibling case `ELITEA-0853` "Pipeline Node Operations - Add, Edit, Delete, Connect" exists in a different TMS folder (`tests/elitea-platform/pipelines/`) and *claims* delete-node automation already exists — see Coverage Map / Known Defects for why that claim is stale and does not make this case `already-covered`)
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-07-24
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline exists with 3 nodes connected by edges: `LLM 1 → Code 1 → END` (entry point = `LLM 1`, `LLM 1.transition = Code 1`, `Code 1.transition = END`).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline (`autotest_<test-name>`) with exactly this shape, created via **a new fixture** `pipeline_with_llm_code_end_id`, mirroring the existing `pipeline_with_llm_id` fixture's pattern (`automation/fixtures/data_fixtures.py:159-194`) but calling `PipelineAPI.create_pipeline_with_nodes()` (already exists, `automation/api/client.py:759-815` — no new API-client method needed) with:
  ```python
  nodes = [
      {
          "id": "LLM 1", "type": "llm", "input": [],
          "input_mapping": {
              "chat_history": {"type": "fixed", "value": []},
              "system": {"type": "fixed", "value": ""},
              "task": {"type": "fixed", "value": ""},
          },
          "output": [], "structured_output": False,
          "transition": "Code 1",
      },
      {
          "id": "Code 1", "type": "code", "input": [], "output": [],
          "source_code": "print('hi')",
          "transition": "END",
      },
  ]
  create_pipeline_with_nodes(name, description, "LLM 1", nodes)
  ```
  Confirmed live this session: the Flow-view canvas correctly auto-renders all 3 nodes (`LLM 1`, `Code 1`, `END`) and both edges from this API-created YAML alone — no UI "Add node" clicks needed to satisfy the case's own step-1 precondition. Teardown: `PipelineAPI.delete_pipeline(pid)`, identical to the existing fixture's teardown.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).

## Test Steps

### Test 1 — `test_delete_node_via_menu` (primary path — full persistence chain)

1. Navigate to the fixture pipeline's canonical detail URL (`${BASE_URL}/pipelines/all/{pipeline_id}?viewMode=owner`) via `_navigate_to_canvas()` (existing helper, `tests/ui/pipelines/helpers.py`).
   - **Verify**: canvas shows exactly 3 nodes (`get_node_ids()` → `{"LLM 1", "Code 1", "END"}`); edge `LLM 1 → Code 1` exists; edge `Code 1 → END` exists (see Automation Hints for the corrected target-id needed for the second check).
2. Click the **Code 1** node's title/name label (the plain `<Typography>` text "Code 1" in the node's header — NOT a click at the card's bounding-box center, which lands on an inner form field, see Automation Hints) to select **and** focus the node in one gesture.
   - **Verify**: the node's container (`[data-testid="rf__node-Code 1"]`) gains ReactFlow's own `selected` CSS class (`.react-flow__node.selected`) — confirmed live; no new testid needed, this is `@xyflow/react`'s own built-in mechanism.
3. Open the node's three-dot menu (`node-menu-menu-button`, scoped inside the `rf__node-Code 1` container — this testid is shared/non-unique across every node on the canvas, confirmed live: 2 elements share it on a 2-menu-having-node canvas) and click **"Delete"** (testid needed, see Concrete Handles).
   - **Verify**: a confirmation dialog (`role="dialog"`) appears with title "Delete confirmation" (`delete-confirm-title`) and message "Are you sure to delete the **Code 1** node? It can't be restored." (`delete-confirm-message`, node name interpolated as a nested span).
4. Click the dialog's **Delete** button (`delete-confirm-button`).
   - **Verify**: dialog closes; `get_node_ids()` no longer contains `Code 1` (now exactly `{"LLM 1", "END"}`); edge `Code 1 → *` and `* → Code 1` no longer exist; a **new** edge `LLM 1 → END` now exists (ReactFlow auto-rewired `LLM 1`'s transition to `Code 1`'s own downstream target the instant `Code 1` was removed — confirmed live, this is the concrete mechanism behind "edges connected to Code node are removed"); `LLM 1` and `END` nodes are still present and unchanged.
5. Click the pipeline's **Save** button (`agent-save-button`, existing `save_and_wait_for_update()` method).
   - **Verify**: the underlying `PUT /elitea_core/application/prompt_lib/{project}/{pipeline_id}` returns `201`; zero **error**-level console messages (the ambient `[React Flow]: It looks like you've created a new nodeTypes...` message that fires on canvas re-renders is `warning`-level and pre-existing/unrelated — see Known Defects note, don't fail on it).
6. Reload the page at the same canonical URL; wait for the canvas (`wait_for_canvas()`).
   - **Verify**: canvas shows exactly 2 nodes (`LLM 1`, `END`); exactly 1 edge, `LLM 1 → END`; `Code 1` does not reappear.
7. Cross-verify via the YAML tab (`get_yaml_content()`, existing method).
   - **Verify**: YAML shows `entry_point: LLM 1`, a single node block `LLM 1` with `transition: END`, and no `Code 1` node block anywhere — matches the canvas state from step 6 exactly (second independent source).
8. Cross-verify via the API (`PipelineAPI.get_pipeline(pipeline_id)`).
   - **Verify**: server-side `instructions` YAML matches step 7's Flow/YAML-tab content byte-for-byte on `entry_point`/`nodes`/`transition` (third independent source — catches a UI-cache-vs-backend divergence class of bug).

### Test 2 — `test_delete_node_via_keyboard_delete_key` (alternate activation — case step 3's "OR")

1. Fresh instance of the same fixture pipeline (`LLM 1 → Code 1 → END`).
2. Navigate + wait for canvas (same as Test 1 step 1).
3. Click the **Code 1** node's title/name label (same click target as Test 1 step 2 — this is what makes the node's own `[tabindex="0"]` container the real `document.activeElement`, which is required for the next step; a click that lands on an inner field instead focuses that field, and the global Delete-key listener silently ignores the keypress — see Automation Hints).
   - **Verify**: node has `.selected` class (same as Test 1 step 2).
4. Press the **Delete** keyboard key (do **not** open the three-dot menu this time).
   - **Verify**: the identical confirmation dialog from Test 1 step 3 appears (same testids, same interpolated node name) — confirms this alternate trigger reaches the same deletion flow, not a separate/divergent one.
5. Click `delete-confirm-button`.
   - **Verify**: `Code 1` removed from canvas; `LLM 1` and `END` remain (lighter assertion set — Test 1 already proves the Save/reload/YAML/API persistence chain; this test's own purpose is proving the keyboard trigger, not re-proving persistence).
6. **Verify**: zero error-level console messages.

## Expected Results
- A node in the middle of a pipeline chain (`Code 1`, between `LLM 1` and `END`) can be deleted either via its three-dot menu → Delete, or by selecting it and pressing the Delete key — both reach the identical "Delete confirmation" dialog.
- Deleting the node removes it from the canvas and automatically rewires the upstream node's transition to point at the deleted node's own downstream target (here: `LLM 1`'s transition flips from `Code 1` to `END`), so the graph stays structurally valid — not just visually tidy.
- `LLM 1` and `END` are never affected by deleting `Code 1`.
- The deletion persists after Save + full reload, confirmed identically via the Flow-view canvas, the YAML tab, and a direct API read of the saved pipeline.
- No console errors at any step (aside from a documented, pre-existing, unrelated ReactFlow dev-mode warning).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create a pipeline with LLM → Code → END (3 nodes + edges) | pipeline created with all 3 nodes + edges | Test Data (fixture) + Test 1 step 1 | Test 1 step 1: `get_node_ids()` == 3 nodes, both edges present | asserted *(decomposed: creation moved to a fixture per project convention — ELITEA-2010's precedent — instead of driving 2× "Add node" clicks in the test body; step 1's own verification is re-derived by reading the live canvas immediately after navigating, so the fixture's correctness is still asserted, not assumed)* |
| 2 Select the Code node on canvas | Code node is selected/highlighted | Test 1 step 2, Test 2 step 3 | `.react-flow__node.selected` CSS class present on `rf__node-Code 1` | asserted |
| 3 Delete it (press Delete key OR use node menu → Delete) | delete action triggered | Test 1 steps 3–4 (menu path); Test 2 steps 4–5 (keyboard path) | Test 1: confirmation dialog + Delete-button click; Test 2: Delete-key press + confirmation dialog + Delete-button click | asserted *(decomposed into 2 separate tests — one per activation gesture the case names as valid alternatives, so both are actually exercised rather than picking one and leaving the other unautomated)* |
| 4 Verify Code node is removed from canvas | Code node no longer appears | Test 1 step 4, Test 2 step 5 | `get_node_ids()` no longer contains `Code 1` | asserted |
| 5 Verify edges connected to Code node are also removed | all edges to/from Code node gone | Test 1 step 4 | `edge_exists()` false for `Code 1`'s former edges; **additionally** confirmed the concrete mechanism: `LLM 1`'s YAML `transition` auto-flips from `Code 1` to `END`, and a live `LLM 1 → END` edge appears in its place | asserted *(enriched — the case only asks "are Code 1's edges gone"; asserting the auto-rewire proves the graph is still structurally valid, not just visually tidy)* |
| 6 Verify LLM and END nodes remain | LLM 1 and END still present | Test 1 step 4, Test 2 step 5 | `get_node_ids()` still contains `LLM 1` and `END` | asserted |
| 7 Save — verify deletion persists after reload | canvas shows LLM+END only, Code node gone | Test 1 steps 5–8 | step 6: canvas after reload; step 7: YAML tab; step 8: direct API read (three independent sources) | asserted |
| Expected Final State: Code node + edges permanently removed, LLM/END remain, persists after save+reload | — | Test 1 steps 4–8 | as above | asserted |
| Pass/Fail: all steps complete without errors; node+edges removed correctly, LLM/END unaffected, persists | — | Test 1 (full), Test 2 (activation-gesture slice) | all steps above + zero-console-error checks | asserted |

### Axis 2 — Analyst additions

- **Zero console errors** at every step — *added: standard side-channel check. Confirmed a pre-existing, unrelated `warning`-level (NOT `error`-level) ReactFlow dev message (`[React Flow]: It looks like you've created a new nodeTypes or edgeTypes object...`) fires repeatedly on canvas re-renders regardless of this feature — documented here and in `test-specs/pipelines/_surface.md` so no future analyst mis-files it as a delete-node regression.*
- **API-level (server-side) verification** of the persisted YAML, in addition to the Flow-view canvas and the YAML tab — *added: third independent source, per this project's established multi-source persistence-verification pattern (see `_surface.md` § "Save/reload persistence"); catches a UI-cache-vs-backend divergence class of bug the other two sources alone would miss.*
- **The transition auto-rewire itself** (`LLM 1.transition` flips from `Code 1` to `Code 1`'s own former transition target, `END`) — *added: this is the concrete mechanism behind the case's step 5 ("edges are removed"); asserting it via the YAML `transition:` field (not just "the edge visually disappeared") proves the pipeline is still executable/valid after the delete, which is the actual product concern behind that step.*
- **The keyboard-Delete-key alternate activation gets its own full pass** (Test 2), rather than only automating the menu path and leaving the case's explicit "OR press Delete key" alternative unautomated — *added: the case names it as an equally-valid trigger, so it gets equal coverage, with a documented focus-gotcha (see Automation Hints) since a naive click-then-press-Delete attempt silently no-ops if the click landed on an inner form field instead of the node's own focusable container.*
- **END node confirmed to have zero menu/delete affordance** (`node.querySelectorAll('button').length === 0` on `rf__node-END`) — *added: cheap boundary-condition observation, confirms there is no way to accidentally trigger an END-node delete path via this same mechanism; not asserted as a dedicated test step, noted here for the record.*
- No defect filed against the delete-node **feature** itself — every observed behavior (both activation paths, edge cleanup, transition rewire, 3-source persistence) was correct. A **tracking/metadata** finding (unrelated to this case's own product behavior) was filed separately — see Known Defects note below.

## Cleanup
1. This session created two throwaway pipelines directly via `PipelineAPI.create_pipeline_with_nodes()` (ids `5705`, `5708`, projet `399`) to explore the menu path and the keyboard path independently. **Both were deleted by this analyst session** (`PipelineAPI.delete_pipeline`).
2. Implementer teardown: the new `pipeline_with_llm_code_end_id` fixture's own `PipelineAPI.delete_pipeline(pid)` teardown (mirroring `pipeline_with_llm_id`) — no manual cleanup needed in the test bodies themselves.

## Concrete Handles (discovered during exploration)

Provenance verified this session via `cd ../EliteaUI && git fetch origin` immediately before checking (`.agents/role-overrides.md` § Analyst slot). Command used for each row below: `git grep -- "<testid>" origin/main -- src/` vs `origin/automation/testids -- src/`.

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Node container (any type) | `[data-testid="rf__node-{id}"]` e.g. `rf__node-Code 1`, `rf__node-LLM 1`, `rf__node-END` | N/A — `@xyflow/react` library-level convention, not app JSX (`grep -rn "rf__node" src/` = 0 hits); present on any branch/build | Confirmed live for all 3 node types this session |
| Node `selected` state | `.react-flow__node.selected` CSS class on the node container above | N/A — same library-level mechanism | No app testid needed; asserting a class on an already-testid'd element is compliant (state via attribute, not a state-switched testid) |
| Edge between two nodes | `[data-testid="rf__edge-xy-edge__{source}---{target}"]` — **note the triple-dash separator** and that the **END node's edge-endpoint id is the literal string `EliteAPipelineEnd`, NOT `END`** (confirmed live: `rf__edge-xy-edge__Code 1---EliteAPipelineEnd`, `rf__edge-xy-edge__LLM 1---EliteAPipelineEnd` after the delete) | N/A — ReactFlow library-level, ids assigned by EliteaUI's own YAML→graph transformer for edges derived from `transition:`/`entry_point` (as opposed to a user-dragged connection, which uses a *different* id shape per the existing `edge_exists()` docstring) | **Mandatory heads-up for the implementer** — see Automation Hints; the existing `edge_exists()` page-object method's `.startswith()`-based matching happens to still work correctly here by loose substring match, EXCEPT when checking an edge into `END` by its displayed name (`edge_exists(x, "END")` returns a **false negative** — verified: `"-END" not in "rf__edge-xy-edge__Code 1---EliteAPipelineEnd"`). Call it with `edge_exists(source, "EliteAPipelineEnd")` instead, or fix the method to alias `"END"` |
| Node's three-dot menu button | `node-menu-menu-button`, scoped inside the node's own `rf__node-{id}` container | **on-main ✓ AND on-automation/testids ✓** (identical — `DotMenu.jsx`'s `data-testid={id ? \`${id}-menu-button\` : undefined}` driven by the caller's literal `id="node-menu"` in `NodeCardHeader.jsx:331`) | **Shared/non-unique across every node on the canvas** (confirmed live: 2 identical hits) — container-scoping is REQUIRED and sufficient; no `add-data-testid` needed for this button itself. *(Optional, non-blocking improvement for a future case: parameterize `NodeCardHeader.jsx`'s `id="node-menu"` by the node's own `id` prop for a per-node-unique testid — not required since scoping already disambiguates correctly.)* |
| "Delete" menu item | none today | **needs-adding** | `NodeCardHeader.jsx`'s `menuItems` `useMemo` (lines ~208–253) builds 3 mutually-exclusive array branches, each containing a `{ label: 'Delete', icon, disabled, onClick: handleDelete }` object with **no `key` field set**. `DotMenu.jsx` already supports per-item testids via `testId: item.key` → `<MenuItem data-testid={testId ? \`${testId}-menuitem\` : undefined}>` (`DotMenu.jsx` `BasicMenuItem`) — **zero shared-component changes needed**, just add `key: 'pipeline-node-delete'` to all 3 "Delete" object literals (same literal string is safe — the 3 branches are mutually exclusive per node instance) → yields `data-testid="pipeline-node-delete-menuitem"` |
| "Make entrypoint" menu item | none today | **out of scope for this case — do not add** | Same `menuItems` array, sibling object `{ label: 'Make entrypoint', ... }` — this test never clicks it (canon ruling #511/role-overrides "touches" rule); leave for whichever case tests entry-point promotion via this menu |
| Node title/name label (click target to select+focus a node) | none today | **needs-adding** | `NodeCardHeader.jsx:280-286`, a bare `<Typography sx={styles.nameText} onDoubleClick={onDoubleClickName}>{inputtedName}</Typography>` — no testid. Recommend generic `pipeline-node-title-label` (shared component, `{section}-{element}-{type}` naming at the call site's own generic level since `NodeCardHeader` itself has no feature-specific section). **Required for this case**: clicking this element (vs. the node card's bounding-box center) is what reliably selects **and** DOM-focuses the node without risking a click landing on an inner MUI Select/Input field instead (see Automation Hints) |
| END node — no menu/delete affordance | `[data-testid="rf__node-END"]` has zero `<button>` descendants | N/A | Confirmed live; boundary-condition observation only, no locator needed |
| Delete-confirmation dialog | `role="dialog"` (Playwright `get_by_role("dialog")`) | — | Root `[role="dialog"]` element does NOT itself carry the `delete-confirm-dialog` testid live (confirmed) despite `DeleteEntityModal.jsx` passing `data-testid="delete-confirm-dialog"` to `Modal.BaseModal` → `<Dialog data-testid={dataTestId}>` — MUI's `Dialog` applies it to an ancestor wrapper, not the inner `Paper` that carries `role="dialog"`. Not blocking: don't rely on this testid to scope the dialog, use `get_by_role("dialog")` (only one dialog is ever open at a time in this flow) plus the 4 field-level testids below |
| Delete-confirmation title | `delete-confirm-title` | **on-automation/testids only** (awaiting human promotion to main) | Text: "Delete confirmation" |
| Delete-confirmation message | `delete-confirm-message` | **on-automation/testids only** (awaiting human promotion to main) | Contains the node name as a nested `<span>`; full text "Are you sure to delete the {name} node? It can't be restored." |
| Delete-confirmation Cancel button | `delete-confirm-cancel-button` | **on-automation/testids only** (awaiting human promotion to main) | Not exercised by this case's steps (case doesn't test cancelling) |
| Delete-confirmation Delete/confirm button | `delete-confirm-button` | **on-automation/testids only** (awaiting human promotion to main) | This click is client-side only — does NOT itself call any network endpoint; persistence only happens on the pipeline's own Save |
| YAML tab / editor | `pipeline-yaml-editor` / `pipeline-yaml-lines` | on-main ✓ (pre-existing, already wired via `get_yaml_content()`) | Reused as-is |
| Pipeline Save button | `agent-save-button` | on-main ✓ (pre-existing, shared with agent forms) | Reused as-is, via `save_and_wait_for_update()` |

## Network Behavior
- No request fires on selecting a node, opening its menu, clicking Delete, or confirming the dialog — the entire delete + edge-rewire operation is **client-side only** (confirmed: the node/edge/YAML state all updated before any Save click).
- `PUT /elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on the pipeline **Save** click; `201 Created`; this is the single request that persists the deletion + the rewired `transition`. Wait for this response (`save_and_wait_for_update()`, already implemented), not a fixed timeout.
- `GET /elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on page load/reload; backs both the Flow-view canvas render and the YAML tab; also directly callable via `PipelineAPI.get_pipeline()` for the step-8 API cross-check.

## Known Defects Found During Exploration

**None found in the delete-node feature itself.** Both activation paths (three-dot menu, keyboard Delete key), edge cleanup, the transition auto-rewire, and 3-source persistence (canvas / YAML tab / API) all behaved correctly across two independent live sessions (one per activation path), including a from-scratch pristine-context re-verification of the keyboard path after an initial attempt was confounded by the analyst's own residual browser focus state (see Automation Hints — self-inflicted tooling artifact, not a product issue, ruled out per this project's synthetic-input-hygiene discipline before treating it as a finding).

- **[INFO, filed separately] `EliteaAI/elitea-testing-public#1018`** — while checking whether this case was `already-covered` (merged-target rule), found that the sibling TMS case `ELITEA-0853` (`tests/elitea-platform/pipelines/`) claims `status: ready` + `execution_type: automated` with 9 `automation_test_id` entries, but only 1 of the 9 actually exists as a real test in `automation/tests/ui/pipelines/test_pipeline_nodes.py` — including BOTH of its `TestDeleteNode.*` entries, which is exactly this case's scope. This is TMS/tracking metadata drift (not a product bug, not blocking) — filed as a clarification for whoever owns TMS bookkeeping. **Recommendation for the implementer/orchestrator**: naming this case's new test class/methods `TestDeleteNode.test_delete_node_via_menu` (used above) retroactively satisfies one of ELITEA-0853's two phantom `TestDeleteNode` refs "for free" — the `automation_test_id` field is a list and one test may cover several TMS cases (`.agents/testing.md` § Coverage tagging), so consider back-writing this same ref onto ELITEA-0853 too during the batch's mirror sweep (orchestrator decision, not analyst-executed).

## Blocked Steps

None. All case steps were executed to completion against the live local environment, across both activation paths.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`). **This case requires a small `add-data-testid` pass** — 2 elements need testids (the "Delete" menu item ×1 `key` addition covering all 3 branches, and the node title/name label), both trivial one-line changes to `NodeCardHeader.jsx`, no shared-component internals need touching for either.
- **Focus gotcha (mandatory read before writing the keyboard-delete test):** the app's own delete-on-keypress logic (`useDeleteItems.hooks.js`, `useKeyPress(['Delete'], { target: null })` from `@xyflow/react`) reacts to whichever nodes carry ReactFlow's internal `selected` state — but a chat-message `<textarea>` has **default page-load focus**, and while it (or another still-focused MUI form field left over from an earlier interaction) holds `document.activeElement`, a Delete keypress is swallowed before ever reaching this app-level listener. Clicking the node's own title/name label (recommended new testid `pipeline-node-title-label`) is what moves real DOM focus onto the node's own `[tabindex="0"]` container — confirmed live: only after this specific click did `document.activeElement` become the `rf__node-Code 1` div itself, and only then did pressing Delete open the confirmation dialog. Clicking anywhere else inside the node's card body (a Select/Input field) instead focuses that inner field and silently no-ops the Delete key — this cost a full extra debugging pass this session (self-inflicted stray-click artifact, documented and ruled out per synthetic-input-hygiene discipline, not a product defect).
- **Edge-locator gotcha (mandatory read before asserting "edge to END exists"):** see the Concrete Handles row above — `edge_exists(source, "END")` on the EXISTING page-object method returns a **false negative** for edges auto-derived from the YAML transition graph (as opposed to user-dragged connections, which the method's docstring was written for). Call `edge_exists(source, "EliteAPipelineEnd")` instead, or extend the method to alias `"END"` → `"EliteAPipelineEnd"` internally (recommended — future callers asserting "connects to END" on a YAML-derived pipeline will hit the identical trap otherwise; the docstring only documents the drag-created-connection ID shape today).
- New fixture: `pipeline_with_llm_code_end_id` in `automation/fixtures/data_fixtures.py`, alongside `pipeline_with_llm_id` (same file, same pattern: function-scoped, `request.node.name`-derived name truncated to 32 chars, `PipelineAPI.create_pipeline_with_nodes()` call, `delete_pipeline()` teardown).
- New page-object methods on `PipelineDetailPage` (`automation/pages/pipeline_detail_page.py`): a `select_node(node_id)` that clicks the node's title/name-label testid (not the existing raw-selector `delete_node()`'s approach) to both select and focus a node in one call — reused by both Test 1 step 2 and Test 2 step 3.
- **Existing `delete_node()` method (`pipeline_detail_page.py:621-659`) uses a raw `evaluate()`-based JS click on `button.MuiIconButton-colorTertiary` (2nd match) instead of the now-confirmed `node-menu-menu-button` testid, and `Dialog.click_button(dialog, "Delete")` (text-based) instead of the confirmed `delete-confirm-button` testid.** Recommend updating this existing method to use the testid-scoped locators instead of the positional/text-based ones while implementing this case — it is exactly the kind of raw handle role-overrides.md flags as tracked tech debt, and this case is a natural point to fix it since the method is otherwise unused by any merged test today (`grep -rn "delete_node\b" automation/tests/` = 0 hits before this batch).
- Wait strategy: no network wait needed for select/menu/confirm (client-side only, see Network Behavior); wait on the `PUT .../application/prompt_lib/{project}/{pipeline_id}` `201` response after Save (`save_and_wait_for_update()`, already implemented); wait on `wait_for_canvas()` after reload (Suspense "Preparing the flow editor..." fallback, per `_surface.md`'s existing guidance).
- Console-error check: filter to `level == "error"` only — the ambient `[React Flow]: ...nodeTypes or edgeTypes...` message is `warning`-level and fires on unrelated canvas re-renders throughout this whole surface, not specific to delete-node.
