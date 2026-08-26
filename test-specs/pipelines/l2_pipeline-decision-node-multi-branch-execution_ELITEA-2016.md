# Test Case: Pipeline with Multiple Branches (Decision Node) — Routing Execution

## Metadata
- **TMS ID**: ELITEA-2016
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-08
- **Status**: ready-for-automation

## Relationship to ELITEA-2034 (sibling, already merged to `automation/base`)

`test-specs/pipelines/l2_pipeline-decision-node-configuration_ELITEA-2034.md` +
`automation/tests/ui/pipelines/test_pipeline_decision_node_configuration.py` already cover
Decision-node **field configuration** (Input/Description/DECISION OUTPUTS chips via
drag-connect) and **edge persistence to its own DECISION OUTPUTS targets** — but its target
nodes are bare Printer nodes never wired to `END`, no `default_output` edge is created, and
**no pipeline execution/routing is exercised at all** (its own AFS Coverage Map explicitly
scopes this out). ELITEA-2016's distinguishing content is exactly that gap: connecting the
branches through to `END`, wiring `default_output`, and — the part with zero prior
coverage anywhere in this suite — **actually sending a message and verifying the Decision
node's LLM classification routes execution to the correct branch.** The setup delta is large
enough (new END-wiring, new execution assertions, a different and non-obvious entry-point
requirement — see below) that this is a fresh spec, not an extension of 2034's file, per
SKILL.md's "near-rewrite" boundary call. Reuse 2034's confirmed Decision-node handles/quirks
(cited below) rather than rediscovering them.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard
  Keycloak login via `${TEST_USER}`).
- A project exists with access to the Pipelines feature (`${ELITEA_PROJECT_ID}`).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- An empty pipeline via the `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`,
  `PipelineAPI`-backed create/delete).
- Three Printer nodes, added to the canvas and renamed to `bug_responder` /
  `feature_responder` / `question_responder` — chosen as lightweight, already-automated
  branch targets whose distinct PRINTER **Value** field content becomes the test's
  observable "which branch fired" signal (see Automation Hints — **Value**, not **Final
  Message**, is what the chat response actually renders).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project was
  "Private" (id 399), matching `.env.test`.

## Test Steps

**IMPORTANT — node creation ORDER is load-bearing and must be step 1, exactly as the case's
own step 1 implies ("Create a pipeline **with a Decision node**").** See the entry-point
CLARIFICATION below — this is not cosmetic.

1. Create a pipeline; add a Decision node via the canvas "+" button → "Decision"
   (`add_node("Decision")`) **before adding any other node**.
   - **Verify**: node appears on canvas (`wait_for_node_on_canvas("decision")` → non-empty
     id, `Decision 1`); `get_entrypoint_node_id() == "Decision 1"` (confirms the Decision
     node is the pipeline's entry point — see CLARIFICATION).
2. Add three Printer nodes via the canvas "+" button → "Printer" (`add_node("Printer")` ×3),
   repositioning each with `move_node_by_flow_offset()` between adds (ELITEA-2047 gotcha —
   default add position overlaps the previous node; ELITEA-2016 — offsets are FLOW-space,
   not screen px, so the layout no longer drifts with the zoom), then rename them via `edit_node_name(node_id,
   new_name)` to `bug_responder`, `feature_responder`, `question_responder`.
   - **Verify**: `get_node_ids()` includes `Decision 1`, `bug_responder`, `feature_responder`,
     `question_responder`, `END`.
3. Configure the Decision node:
   - Select `input` in the **Input** combobox (`select_decision_node_input_variables(["input"])`)
     — **REQUIRED, not optional** despite the case text never mentioning it (see
     CLARIFICATION — without it, classification silently fails).
   - Fill **Description** with the classification prompt: `Classify this input into one
     category: - bug_responder: reports a defect - feature_responder: requests new
     functionality - question_responder: asks a question` (`fill_decision_node_description(...)`).
   - Add all three DECISION OUTPUTS by dragging from the Decision node's `Output` handle
     (`data-handleid="nodes"`) to each renamed target (`connect_nodes("Decision 1",
     "bug_responder", source_handle="nodes")`, then `feature_responder`, then
     `question_responder`) — same drag-connect-only mechanism ELITEA-2034 already
     documented (NOT a typeable chip field).
   - **Verify**: `is_decision_node_output_chip_present(...)` is `True` for all three names;
     `edge_exists("Decision 1", "bug_responder")` etc. are all `True` immediately (before Save).
4. Connect the remaining edges (case step 4 — "edges from Output **and Default output**
   handles"):
   - Each branch node → `END`: `connect_nodes("bug_responder", "END")`, then
     `feature_responder`, then `question_responder` (default/only bottom handle, no
     `source_handle` argument needed).
   - Decision's `Default output` handle → `END`: `connect_nodes("Decision 1", "END",
     source_handle="default_output")` — REQUIRED per the platform's own authoring docs
     ("Router and Decision nodes must declare `default_output`" — `elitea-pipeline` skill,
     `SKILL.md` — every execution path must reach `END`, including the case where the LLM
     classification doesn't match any DECISION OUTPUTS value).
   - **Verify**: `get_edge_count() == 7`; `edge_testid_present(...)` true for all 7 pairs
     (see Concrete Handles for the exact pre-save testid strings).
5. Save (`agent-save-button`) and reload at the pipeline's canonical URL
   (`/pipelines/all/{id}?destTab=configuration&viewMode=owner`).
   - **Verify** (after a real `page.reload()`, not just an API read): `entry_point:
     Decision 1` in the YAML view; all 3 DECISION OUTPUTS chips + all 7 edges persist
     (**edge testid SHAPE CHANGES across the reload** — see Concrete Handles, this is the
     single most important gotcha, already flagged once by ELITEA-2034 and reconfirmed
     here with the exact strings for this case's edges); both Printer-node fields
     (`printer_node_value`) persist per-node.
6. Execute: send a message matching one DECISION OUTPUTS category via the embedded chat
   (`send_message_in_embedded_chat(...)`, `wait_for_embedded_chat_response(...)`,
   `get_embedded_chat_last_message()`) and verify the correct branch's distinguishing text
   appears in the response.
   - **Verify**: for an input like *"The application crashes when I click the save button,
     this is clearly a defect."*, the last chat message equals (or contains)
     `bug_responder`'s PRINTER **Value** field content — confirmed live, exact string match
     observed (`BUG_BRANCH_REACHED`).
   - **CLARIFICATION (multi-turn continuation — automation hint, not a defect):** a
     Printer node with `transition: END` "pauses for acknowledgement" per the platform's
     own docs. Confirmed live: sending a SECOND, differently-classified message in the
     **same** chat conversation does NOT re-invoke the Decision node — the run resumes at
     the SAME branch node from turn 1 (`Run details` dialog's Timeline step literally reads
     `bug_responder_reset` for the second turn, using the SAME classification result). A
     test that wants to prove **differential** routing (a second category → a different
     branch) MUST clear the chat / start a fresh conversation between messages
     (`clear the chat` button, `[aria-label="clear the chat"]`) — confirmed live: after
     clearing, a feature-request input correctly routed to `feature_responder`
     (`FEATURE_BRANCH_REACHED`).

## Expected Results
- The Decision node, created first, is the pipeline's `entry_point` (no other UI action can
  set this for a Decision node — see CLARIFICATION).
- All three branch nodes are wired as DECISION OUTPUTS (Decision → each, via the `nodes`
  handle) AND all four terminal edges exist (`bug_responder`/`feature_responder`/
  `question_responder` → `END`, plus Decision's `default_output` → `END`) — 7 edges total,
  all surviving save + reload (with the documented testid-shape change).
- Sending a message whose content matches one DECISION OUTPUTS category causes the pipeline
  to execute through to that specific branch and no other — confirmed by the branch's own
  distinguishing PRINTER **Value** text appearing as the final chat response, for at least
  two different categories in two separate conversations.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in, project with Pipelines access | setup exists | Preconditions | fixture/env | asserted |
| 1 Create pipeline with a Decision node | Decision node appears on canvas | step 1 | step 1: node count + id + `get_entrypoint_node_id()` | asserted — **CLARIFICATION: the case's own literal step-1 ordering (Decision created before anything else) is not cosmetic — it's the ONLY way to make Decision the pipeline's entry point. See note below.** |
| 2 Add three nodes (LLM or Code) as branch targets | three branch nodes added | step 2 | step 2: `get_node_ids()` | asserted — Printer chosen over LLM/Code as a lightweight, already-automated node type with a directly-observable output string; any node type satisfies the case's own "(e.g., LLM or Code)" wording |
| 3 Decision: set Description + add all 3 node names to DECISION OUTPUTS | Decision configured with prompt + outputs | step 3 | step 3: chips present + edges exist | asserted — **CLARIFICATION: the case text never mentions an Input variable, but the Decision node's Input combobox must include the built-in `input` state var or the underlying LLM tool-call silently fails (`content: '{}'`, `tool_calls: []`) and the pipeline completes at the Decision node without ever executing a branch. Confirmed live via 3 repeated runs: WITHOUT `input` wired → always `{}`; WITH it wired → correct branch every time.** |
| 4 Connect Decision → each branch → END (edges from Output and Default output handles) | edges connect Decision to all branches and each branch to END | step 4 | step 4: `get_edge_count()==7` + `edge_testid_present()` per pair | asserted — the case's own step-4 wording ("edges from Output **and** Default output handles") already anticipates the `default_output → END` edge; no case-text drift here |
| 5 Save and verify edges + DECISION OUTPUTS persist after reload | all present after reload | step 5 | step 5: YAML `entry_point`, chips, edges (post-reload testid shape), printer Values | asserted |
| 6 Execute with input matching one category — verify correct branch responds | execution routes correctly | step 6 | step 6: chat response text == branch's Value | asserted |
| Expected Final State: Decision classifies + routes correctly; edges/config persist | — | steps 5–6 | steps 5–6 | asserted |
| Pass/Fail: all steps complete without errors; correct branch selected; no lost config | — | all steps | all steps | asserted |

**CLARIFICATION — Decision-node entry-point mechanism (new, not covered by ELITEA-2034,
which never made its Decision node the entry point):** confirmed via source
(`EliteaUI/src/[fsd]/features/pipelines/flow-editor/ui/nodes/BaseNode/NodeCardHeader.jsx`,
the node header's `menuItems`) that the "Make entrypoint" menu action is **unconditionally
excluded for Decision (and legacy Condition) node types** — Router and every other node
type retain it. The ONLY way to make a Decision node the entry point via the UI is for it
to be the FIRST node added to the pipeline (entry_point auto-sets to the first node's id at
creation time). Filed as
[EliteaAI/elitea-testing-public#1347](https://github.com/EliteaAI/elitea-testing-public/issues/1347)
(bug, not blocking this case — the case's own step order sidesteps it). The AFS's step 1
preserves the case's literal ordering for exactly this reason — **do not reorder steps 1–2
in the implementation.**

### Axis 2 — Analyst additions

- step 5 asserts the exact pre-save vs post-reload edge-testid SHAPE CHANGE with this
  session's concrete strings (not just "edges persist") — *added: this is the single most
  fragile part of any Decision-node edge assertion (already flagged once by ELITEA-2034);
  restating it here with THIS case's own edges closes the risk of the implementer
  hand-rolling a wrong-shape assertion from scratch.*
- step 6 asserts a SECOND, differently-classified message only after clearing the chat —
  *added: live-confirmed multi-turn continuation resumes at the previously-selected branch
  instead of re-classifying; omitting this would make a differential-routing assertion
  flaky/wrong 100% of the time, not just occasionally.*
- step 3 asserts the Input-variable requirement with a concrete pass/fail signature (`{}`
  vs correct branch) — *added: this is not asserted anywhere else in the suite; without it
  a future case could silently ship a Decision node that never routes.*

## Cleanup
1. Delete the test pipeline via `PipelineAPI` (fixture teardown) or UI "Delete pipeline"
   action.

## Concrete Handles (discovered during exploration)

All Decision/Printer node fields below are **existing** `LocatorDescriptor` fields in
`automation/pages/pipeline_detail_page.py` (from ELITEA-2034/2039) — no new testids needed
for this case's node-configuration surface. Two existing helper methods need a **scoping
fix** before this case can call them (see below) since this is the first case with THREE
simultaneous Printer nodes.

| Element | Locator / Method | Provenance | Notes |
|---|---|---|---|
| Decision entry-point check | `get_entrypoint_node_id()` (reads YAML `entry_point`) | existing, on-main ✓ | Use this instead of `make_node_entrypoint()` — the latter has NO effect on a Decision node (issue #1347) |
| Decision Input select | `decision_node_input_select` / `select_decision_node_input_variables(["input"])` | ELITEA-2034, on-main ✓ | Page-wide field — fine here, only one Decision node on canvas |
| Decision Description | `decision_node_description_input` / `fill_decision_node_description()` | ELITEA-2034, on-main ✓ | |
| Decision Output handle (`nodes`) | `decision_node_output_handle` (`pipeline-decision-node-output-handle`) | ELITEA-2034, on-main ✓ | `connect_nodes(decision_id, target_id, source_handle="nodes")` |
| Decision Default output handle | `decision_node_default_output_handle` (`pipeline-decision-node-default-output-handle`) | ELITEA-2034, on-main ✓ | `connect_nodes(decision_id, "END", source_handle="default_output")` — NOT exercised by ELITEA-2034; first live confirmation of this handle actually wiring here |
| DECISION OUTPUTS chip | `DECISION_NODE_OUTPUT_CHIP` template / `is_decision_node_output_chip_present()` | ELITEA-2034, on-main ✓ | |
| Printer Value field | `printer_node_value` (`pipeline-printer-node-value`) / `fill_printer_node_value()` / `get_printer_node_value()` | ELITEA-2039, on-main ✓ | **SCOPING GAP — implementer action required.** Class docstring at `pipeline_detail_page.py:600-608` states this field is "page-wide (not scoped to a specific node container) — correct as long as a test only has a single Printer node on canvas." This case has THREE. Either add a `node_id` param to `fill_printer_node_value`/`get_printer_node_value` that scopes via `self.page.locator(f'[data-id="{node_id}"] [data-testid="pipeline-printer-node-value"]')`, or add sibling scoped methods. Do NOT call the existing unscoped methods as-is against a multi-Printer canvas — first-match ambiguity. |
| Printer Final Message field | `printer_node_final_message_input` | ELITEA-2039, on-main ✓ | Same scoping gap as Value — **this case does not need Final Message at all** (see Automation Hints: it is NOT what renders in chat), so the implementer can skip wiring it and avoid the scoping fix for this field entirely. |
| Embedded chat send/wait/read | `send_message_in_embedded_chat()` / `wait_for_embedded_chat_response()` / `get_embedded_chat_last_message()` | `test_pipeline_execution.py` pattern, on-main ✓ | Reuse verbatim — same pattern proven for LLM-node pipelines |
| Clear chat | `[aria-label="clear the chat"]` | confirmed live, this session | No existing page-object method — add one (`clear_chat()`) if a second-category assertion is implemented |
| Edge existence (pre-save) | `EDGE_TESTID` template / `edge_testid_present()` / `get_edge_locator()` | ELITEA-2032/2034, on-main ✓ | Pre-save testids observed THIS session: `rf__edge-xy-edge__Decision 1nodes-bug_respondertarget`, `rf__edge-xy-edge__Decision 1default_output-ENDtarget`, `rf__edge-xy-edge__bug_respondersource-ENDtarget` |
| Edge existence (post-reload) | same methods | ELITEA-2034's documented shape change, reconfirmed this session | Post-reload testids observed THIS session: `rf__edge-xy-edge__Decision 1---bug_responder` (nodes-handle edges drop the `nodes`/`target` suffixes), `rf__edge-xy-edge__Decision 1default_output---END` (keeps `default_output`, drops `target`), `rf__edge-xy-edge__bug_responder---EliteAPipelineEnd` (branch→END edges use the literal internal id `EliteAPipelineEnd` for the END node post-reload, not `END`) |

## Network Behavior
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — Save, 201 Created
  (observed live, same pattern as every other pipeline-node AFS in this suite).
- Chat execution runs over WebSocket/Socket.IO (`/socket.io/...`), not a plain REST predict
  call visible in the network tab — matches `.agents/testing.md`'s "AI responses arrive
  over WebSocket ~2s after send" note. Use `wait_for_embedded_chat_response()`'s condition
  wait, never a fixed sleep.
- The in-page `GET /api/v2/elitea_core/conversation/prompt_lib/{project}/{conversation_id}`
  call (used by the "Run details" dialog to show per-node timeline/state) **redirects to a
  `dev.elitea.ai` OIDC login and fails with a CORS error on localhost** (confirmed live,
  console error captured). This does not block the case — the same information is fully
  readable from the "Run details" dialog's own rendered DOM (Timeline step / States /
  Messages panels), which populates independently of that failed background fetch — but a
  test relying on that specific REST endpoint directly (rather than the dialog UI) would be
  blocked on localhost. Noting for any future Run-details-focused case (ELITEA-2450/2452/2453).

## Known Defects Found During Exploration
- **[MINOR]** Decision node cannot be made the pipeline entry point via the node header's
  "Make entrypoint" menu action (unconditionally excluded for Decision/Condition types,
  unlike Router) — filed as
  [EliteaAI/elitea-testing-public#1347](https://github.com/EliteaAI/elitea-testing-public/issues/1347).
  Not blocking this case (see CLARIFICATION above); the AFS's step-1 ordering is the
  documented workaround.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, page object `automation/pages/pipeline_detail_page.py`
  (`PipelineDetailPage`) — extend, don't duplicate. Reuse `pipeline_id` fixture for an empty
  starting pipeline.
- **Printer "Final Message" is NOT what appears in the chat response — "Value" is.**
  Confirmed live via a first failed attempt: setting only Final Message produced a
  `content: '{}'` chat response even after correct routing; setting the PRINTER section's
  **Value** field (Type=Fixed, plain text) produced the expected distinguishing text.
  Per the platform's own `elitea-pipeline` skill docs, `input_mapping.printer.value` is the
  field that's actually printed; `final_message` is a separate, unrelated field (semantics
  not otherwise exercised by this case).
- **The Decision node's Input combobox MUST include the built-in `input` variable for
  classification to work at all** — this is the single most important setup step this AFS
  adds beyond the case text (see CLARIFICATION). Skipping it doesn't error; it silently
  produces an unrouted, "completed" pipeline run.
- Reuse `test_pipeline_execution.py`'s `_execute_pipeline()` helper pattern
  (`send_message_in_embedded_chat` → `wait_for_embedded_chat_response` →
  `get_embedded_chat_last_message`) rather than re-deriving embedded-chat interaction.
- `PIPELINE_EXECUTION_TIMEOUT = 90_000` ms (from `test_pipeline_execution.py`) is a
  reasonable default — observed live executions completed in ~3-6s ("Thought for 3 secs"),
  well under that ceiling.
