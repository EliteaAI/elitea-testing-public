# Test Case: Pipeline — Trigger Shown on Entry Point Node Only

## Metadata
- **TMS ID**: ELITEA-2041
- **Priority**: medium (as authored in the source TMS case; project convention maps
  medium → `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-08
- **Status**: extend-existing
- **surface_key**: `pipeline-entry-point-trigger` (same surface as ELITEA-2005/2006/2007/2008,
  per `test-specs/pipelines/_surface.md`)

## Covering Spec (dedup / extension proof)

- **Covering spec**: `automation/tests/ui/pipelines/test_pipeline_entry_point_trigger_types_persist.py`
  (TMS ELITEA-2005), merged to `origin/automation/base` (`0d90c117`).
- **Behavioural overlap**: ELITEA-2005's merged test already proves the Trigger control's
  PRESENCE on the entry point node (steps 2/3, default "Chat Message" + 3 options), that it is
  rendered by the same node-type-agnostic `NodeCard.jsx` component regardless of node type (step
  9), and — as a *side effect* of transferring the entry point from the LLM node to a Code node —
  asserts `pipeline_page.trigger_select.count() == 1` immediately after the transfer (proving the
  PREVIOUS entry-point node's Trigger control disappeared once it stopped being the entry point).
  `test_pipeline_entry_point_trigger_restricted_interactive_nodes.py` (ELITEA-2008, merged
  `4689ecd5`) separately proves the Chat-Message-only RESTRICTION logic for Printer/HITL/interrupt
  nodes, but never clicks/inspects a non-entry node's own card, and never touches the Information
  section.
- **The gap**: neither merged spec ever verifies the Trigger control's ABSENCE by inspecting a
  SPECIFIC non-entry node's own card while the entry point stays fixed (ELITEA-2005's count==1
  check is a side effect of an entry-point *transfer*, not a direct per-node absence check on
  multiple simultaneous non-entry siblings), and neither ever asserts the Information section's
  "Trigger:" row mirrors the entry node's current selection. This is the case's own ask: "Trigger
  dropdown is only visible in the configuration panel of the entry point node, and not on any
  other node in the pipeline" (case Objective) plus the Information-section cross-check (case step
  6) — a genuinely new, previously-unexercised assertion surface on the identical
  `pipeline_with_llm_id` fixture/page-object methods ELITEA-2005 already uses. An **incremental
  addition**, not a near-rewrite; ELITEA-2005's own test body and assertions are untouched.
- **Extension shape**: add a **new test function** to the same file
  (`test_pipeline_entry_point_trigger_types_persist.py`), reusing the `pipeline_with_llm_id`
  fixture, `_navigate_to_canvas`, `add_node()`, `get_entrypoint_node_id()`, and
  `get_trigger_type_value()` (all already proven by ELITEA-2005's own test in the same file), plus
  two new page-object additions this extension itself requires (a node-scoped Trigger-count method
  and an Information-section Trigger-row locator — see § Concrete Handles). Does not modify
  ELITEA-2005's existing test body.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline with multiple nodes exists where the first-added node is the entry point — satisfied
  by `pipeline_with_llm_id` (single LLM node, "LLM 1", entry point by construction) plus two nodes
  added live via the canvas "+" menu (Code, Printer) — mirrors the case's own example
  ("LLM → Code → Printer"). **Do not use the multi-node `create_pipeline_with_nodes()` helper**
  for the seed — same seeding gotcha ELITEA-2005's AFS already documents (a hand-built multi-node
  pipeline loads dirty; irrelevant to this case's assertions but avoided for consistency with the
  covering spec's own precondition).

## Test Data
| Field | Value |
|-------|-------|
| (none required) | — matches the case's own Test Data table |

## Test Steps

1. Use the `pipeline_with_llm_id` fixture (single LLM node, "LLM 1", connected to END). Navigate
   to the pipeline detail page and wait for the canvas.
   - **Verify**: `get_entrypoint_node_id() == "LLM 1"`; the LLM node's own card (scoped via
     `RF_NODE_TESTID`) contains exactly one Trigger control (`get_trigger_control_count_for_node`
     — new method, see § Concrete Handles) — confirmed live this session.
2. Add a Code node via the canvas "+" menu (unconnected — connections are irrelevant to this
   case's observable).
   - **Verify**: `get_entrypoint_node_id()` is UNCHANGED (still `"LLM 1"`) — adding a node never
     transfers the entry point (confirmed via source read of `NodeCardHeader.jsx`'s
     `menuItems`: entry-point transfer only happens via the explicit "Make entrypoint" action).
     The Code node's OWN card contains ZERO Trigger controls
     (`get_trigger_control_count_for_node(code_node_id) == 0`) — confirmed live this session via a
     full DOM dump of the Code node's card: it renders CODE/Input/Output/Interrupt fields but no
     "Trigger" label or combobox at all, unlike the LLM node's card.
3. Add a Printer node too (now LLM → Code → Printer are all present, matching the case's example
   verbatim), also unconnected.
   - **Verify**: the Printer node's OWN card ALSO contains ZERO Trigger controls
     (`get_trigger_control_count_for_node(printer_node_id) == 0`) — confirmed live this session.
4. With all 3 nodes now on canvas, re-verify the LLM entry node's card STILL contains exactly one
   Trigger control, and that the page-wide `trigger_select` count is exactly 1 across the whole
   canvas (i.e., the two non-entry nodes contribute zero).
   - **Verify**: `get_trigger_control_count_for_node(llm_node_id) == 1`;
     `pipeline_page.trigger_select.count() == 1` — confirmed live.
5. Read the Information section's "Trigger:" row and the entry node's own Trigger select value;
   verify they name the same trigger type.
   - **Verify**: `pipeline_page.information_trigger_row` becomes visible (waiting for the
     `useGetPipelineTriggerQuery` GET to settle — same async-population characteristic
     ELITEA-2005's AFS already documents for the node-level combobox, confirmed live this session
     to apply to the Information section's row too: it does not render on the very first paint),
     and its text equals `f"Trigger:{entry_node_trigger_value}"` where
     `entry_node_trigger_value == pipeline_page.get_trigger_type_value()` (`"Chat Message"` by
     default) — see the CLARIFICATION below for the exact (no-space) text shape.

## Expected Results
- The Trigger control renders ONLY inside the entry point node's own card — confirmed absent from
  every non-entry node's card, for at least 2 simultaneous non-entry node types (Code, Printer),
  while the entry point itself keeps exactly one Trigger control throughout.
- The Information section's "Trigger:" row always names the SAME trigger type currently shown on
  the entry point node's own Trigger control.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: pipeline with multiple nodes, LLM entry point | setup exists | step 1 | step 1: `get_entrypoint_node_id()` | asserted |
| 1 Open a pipeline with multiple nodes (LLM → Code → Printer) | Canvas displayed with all nodes | steps 1–3 | steps 1–3: node presence via `wait_for_node_on_canvas` | asserted |
| 2 Click on the entry point node | Entry point node configuration panel opens | step 1 | step 1 | asserted — **CLARIFICATION: no click is needed/performed.** Confirmed live via source read (`NodeCard.jsx`): every node card renders fully expanded by default (`isExpanded` initial state `true`); a click on the card header actually TOGGLES expand/collapse (it would risk COLLAPSING an already-expanded card, hiding the very field this step wants to observe) rather than "opening" anything. The case's intent (the entry node's fields, including Trigger, are visible) is true and asserted without a click — same non-click pattern ELITEA-2005's own merged test already uses for the identical node. |
| 3 Verify "Trigger" dropdown is visible at the top of node config panel | Trigger dropdown is present | step 1 | step 1: `get_trigger_control_count_for_node(llm_node_id) == 1` | asserted |
| 4 Click on a non-entry-point node (e.g., Code node) | Code node configuration panel opens | step 2 | step 2 | asserted — same no-click CLARIFICATION as row 2 (Code node's card is also expanded by default; no click needed to observe its field set) |
| 5 Verify "Trigger" dropdown is NOT shown for non-entry nodes | Trigger dropdown absent from non-entry node panels | steps 2–4 | step 2: Code node count==0; step 3: Printer node count==0 (case only names one non-entry node — added a SECOND node type, Printer, to strengthen the "ANY non-entry node" claim per Axis 2 below); step 4: LLM's own count stays 1 while both siblings are present | asserted |
| 6 Verify Information section in left panel shows "Trigger: Chat Message" matching entry node's selection | Information section correctly displays the active trigger type | step 5 | step 5: `information_trigger_row` text vs `get_trigger_type_value()` | asserted — **CLARIFICATION: the DOM's actual text content has NO space between the label and value** (`"Trigger:Chat Message"`, not `"Trigger: Chat Message"`) — confirmed live via `element.textContent` (the visual gap is CSS `flex gap`, not a text character). The observable the case cares about (the section correctly displays the active trigger type) is true and asserted against the live-contract string, per the reverse-masking guard. |
| Expected Final State: Trigger control exclusive to entry point node; non-entry nodes show none; Information section reflects current trigger type | — | steps 1–5 | steps 1–5 | asserted |
| Pass/Fail: all steps complete without errors; Trigger dropdown only on entry node, absent on all others, Information section matches | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Added a SECOND non-entry node type (Printer, step 3) alongside the case's own named example
  (Code, step 2) — *added because the case's Expected Final State claims "non-entry nodes do not
  show a Trigger dropdown" as a general rule, not specific to one node type; ELITEA-2005's own
  step 9 already established (via source read of `NodeCard.jsx`) that the Trigger control's
  presence is driven purely by the `isEntrypoint` prop, unconditional on node type — this
  extension adds a second live data point (not just the architectural argument) so the "ANY
  non-entry node" claim rests on two independent observations, not one.*
- Step 4 explicitly re-checks the LLM entry node's OWN Trigger-control count AFTER both siblings
  are added — *added so the test doesn't just prove "Code/Printer have none" in isolation, but
  also that the entry node's own control survives unaffected by its non-entry siblings coexisting
  on the same canvas (guards against a hypothetical regression where adding sibling nodes could
  somehow duplicate/hide the entry node's own control).*
- Step 5's Information-section wait strategy (wait for the row to become visible, don't read
  immediately) is added per the SAME async-population characteristic ELITEA-2005's own AFS
  documents for the node-level Trigger combobox (`useGetPipelineTriggerQuery` not always settled
  synchronously with page load) — confirmed live this session that the Information section's own
  "Trigger:" row is subject to the identical gap (absent on the very first DOM read of a freshly
  loaded/reloaded page, present ~1–2s later).
- No console-error assertion was in the original case text; added across all steps — standard
  practice per this project's `test-case-analysis` skill; zero console errors observed this
  session.

## Gap Assertions (what ELITEA-2005's covering test does NOT already prove — for the implementer)

1. **Direct per-node absence check on a FIXED entry point** — ELITEA-2005's `count() == 1` check
   (its step 9) is a side effect of TRANSFERRING the entry point to a different node, not a direct
   inspection of a specific non-entry node's own card while the original entry point stays put.
   This extension scopes the check to each node's own `RF_NODE_TESTID` container
   (`get_trigger_control_count_for_node`, new method) — a stronger, more literal proof of the
   case's own wording ("not on any other node in the pipeline").
2. **Two simultaneous non-entry nodes, not one at a time** — ELITEA-2005 only ever has 2 nodes on
   canvas at once (the current entry point + one candidate). This extension has 3 (1 entry + 2
   non-entry) simultaneously, closer to the case's own "LLM → Code → Printer" example.
3. **The Information section's "Trigger:" row** — never asserted anywhere in the merged suite.
   This extension is the first to touch `agent-information-section`'s pipeline-specific Trigger
   row (previously-untested content of an already-testid'd, already-page-object'd accordion).

## Cleanup

1. All nodes were added directly on the `pipeline_with_llm_id` fixture's own pipeline, never
   Saved — `PipelineAPI.delete_pipeline()` (the fixture's own teardown) removes the whole pipeline
   regardless of any unsaved canvas edits. No separate cleanup needed.
2. This session's own live exploration (adding LLM/Code nodes to a pre-existing throwaway pipeline,
   `FullDetailsPipe_probe2`, id `6754`) was never Saved and was discarded by reloading the page
   (confirmed via the resulting "Trigger:Chat Message" Information-section read matching the
   pipeline's pre-existing default state) — no residue left on that pipeline either.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Trigger control scoped to a specific node | `PipelineDetailPage.get_trigger_control_count_for_node(node_id)` — **new page-object method**, chains `RF_NODE_TESTID.format(node_id)` (pre-existing #579-sanctioned ReactFlow container) with a new class constant `TRIGGER_SELECT_TESTID = '[data-testid="pipeline-entry-point-trigger-select"]'` (same testid the pre-existing page-wide `trigger_select` field already uses) | No new EliteaUI testid needed — reuses `pipeline-entry-point-trigger-select`, already on `main` (`EliteaAI/EliteaUI@b43fbce0`, per ELITEA-2005's AFS) |
| Information section's "Trigger:" row | `PipelineDetailPage.information_trigger_row` — **new `LocatorDescriptor`**, testid `information-trigger-row` | **New testid, added THIS session** via `add-data-testid`: `ApplicationInformation.jsx` (shared with the Agent detail page's Information section) had NO testid on the Trigger row's wrapping `<Box>` — confirmed via source read (only the two `CopyToClipboardButton`s in that accordion carry `data-testid`, the Trigger/Timezone/Webhook-type/Last-run rows are bare `<Box><Typography/><Typography/></Box>` pairs). Named generically (`information-trigger-row`, not `agent-information-trigger-row` / `pipeline-information-trigger-row`) per the shared-component naming ruling (`.agents/testing.md` § Locator policy) — same style as the pre-existing generic `copy-id`/`copy-version-id` testids in the same component. Committed + pushed to `EliteaAI/EliteaUI`'s `automation/testids` (`28dbc5e4`); confirmed live via HMR after the edit (`element.textContent === "Trigger:Chat Message"`). |
| Entry point node (generic) | `RF_NODE_TESTID = '[data-testid="rf__node-{}"]'` — pre-existing class constant | Third-party ReactFlow wrapper, #579-sanctioned, already the project's established per-node scoping pattern (`fill_printer_node_value_for_node`, etc.) |
| "Make entrypoint" / current entry point / add node | `make_node_entrypoint()` / `get_entrypoint_node_id()` / `add_node()` — all pre-existing, confirmed still correct live | none needed |

## Network Behavior

- `GET ${ELITEA_API_BASE}/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/
  {pipeline_id}/trigger` — same endpoint ELITEA-2005's AFS documents for the node-level combobox;
  confirmed this session that `ApplicationInformation.jsx`'s Information-section Trigger row reads
  from the SAME `useGetPipelineTriggerQuery` hook (not a second/different endpoint) — one shared
  data source drives both the node-level control and the Information section's display.
- Adding Code/Printer nodes fires no network request (unsaved canvas edits are purely client-side,
  same as documented elsewhere in `_surface.md` for other node-add cases).

## Known Defects Found During Exploration

**None.** The case's Objective is fully confirmed live, exactly as written (modulo the two
CLARIFICATIONs above, neither of which is a defect): the Trigger control is exclusive to whichever
node is currently the entry point, absent from every other node regardless of type, and the
Information section's Trigger row always mirrors the entry node's current selection. Zero console
errors observed. Zero failed (≥400) network requests observed.

## Blocked Steps

None. All 6 case steps were executed to completion against the live local environment (LLM entry
node + Code + Printer non-entry nodes, plus the Information section cross-check).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`). This
  case requires ONE `add-data-testid` addition: `information-trigger-row` on
  `ApplicationInformation.jsx`'s Trigger-row `<Box>` (see § Concrete Handles) — everything else
  reuses pre-existing testids.
- Use `pipeline_with_llm_id` (existing fixture) as the seed, exactly as ELITEA-2005's own test in
  the same file does.
- New `PipelineDetailPage` additions needed: `TRIGGER_SELECT_TESTID` class constant,
  `get_trigger_control_count_for_node(node_id)` method, `information_trigger_row`
  `LocatorDescriptor`. None of ELITEA-2005's/ELITEA-2008's existing methods need modification.
- Wait strategy: wait for `information_trigger_row` to become visible before reading its text
  (Playwright web-first `expect(...).to_be_visible()`/`to_have_text()`), never an immediate read —
  same async-population characteristic already documented for the node-level combobox.
- Suggested pytest markers: `@pytest.mark.p2`, `@pytest.mark.pipelines`, `@pytest.mark.regression`
  — matches the covering spec's existing `pytestmark`.
- Test-data fixture: `pipeline_with_llm_id` (existing, shared with the covering spec's own test
  function in the same file). No new fixture needed.
