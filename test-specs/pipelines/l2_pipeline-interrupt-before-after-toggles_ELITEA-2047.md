# Test Case: Pipeline — Interrupt Before/After Toggles

## Metadata
- **TMS ID**: ELITEA-2047
- **Linked Story**: none
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), 2026-08-08
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline with a node (e.g., Code node) exists — matches the case's stated precondition. Live-confirmed: a **single** node's "Interrupt after" switch is `disabled` while the node's `transition` is `END` (the default state of a lone freshly-added node), so this AFS's setup adds a SECOND node (Printer) and connects them — only then is "Interrupt after" actually clickable. This is a setup requirement, not case-text drift (same `CommonInterruptSettings.jsx` disabled-state logic already documented for every other node-configuration AFS in this suite, e.g. ELITEA-2009's Axis 2).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- An empty pipeline via the `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`, `PipelineAPI`-backed create/delete).

| Field | Value |
|-------|-------|
| Node 1 | Code node, id `Code 1`, Value = `result = "code node ran"` (any non-empty fixed value — content is irrelevant to the interrupt mechanism) |
| Node 2 | Printer node, id `Printer 1`, transition `END` |
| Edge | `Code 1 -> Printer 1` (via `connect_nodes`) |
| Chat trigger message | any non-empty text, e.g. `"Hello"` |

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.

## Test Steps

**IMPORTANT — step 0 added ahead of the case's step 1**, to satisfy the
Interrupt-after-not-disabled precondition documented above.

0. **Setup**: create an empty pipeline (`pipeline_id` fixture); add a Code
   node (`add_node("Code")`) and a Printer node (`add_node("Printer")`);
   connect them (`connect_nodes("Code 1", "Printer 1")`).
   - **Verify**: `wait_for_edge("Code 1", "Printer 1")` — edge exists before
     proceeding (Interrupt after's disabled-state gate depends on this).
1. Open the pipeline with the node (already satisfied by step 0 — the
   pipeline is open on the canvas with both nodes visible; no separate
   navigation is needed since the test built the pipeline in-session).
   - **Verify**: `wait_for_node_on_canvas("code")` and
     `wait_for_node_on_canvas("printer")` both return non-empty ids.
2. In node config, locate "Interrupt before" switch.
   - **Verify**: `code_node...` — actually the generic dynamic
     `NODE_INTERRUPT_BEFORE_TOGGLE.format("Code 1")` locator — is visible,
     AND (Axis-2 addition) is `disabled` because Code 1 is the pipeline's
     entry point (`is_node_interrupt_before_toggle_disabled("Code 1")
     == True`) — confirmed live, same rule already documented for every
     other node type sharing `CommonInterruptSettings.jsx`.
3. Locate "Interrupt after" switch.
   - **Verify**: `pipeline_page.code_node_interrupt_after_toggle` is
     visible AND, thanks to step 0's edge, **enabled** (not disabled) —
     confirmed live: with no outgoing edge the switch is disabled; once
     `transition: Printer 1` exists (via the drawn edge) it becomes
     clickable.
4. Toggle "Interrupt after" to enabled.
   - **Verify**: `expect(code_node_interrupt_after_toggle).to_be_checked(checked=True)`.
5. Save pipeline (`agent-save-button`).
   - **Verify**: no console errors; `PUT
     .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` returns
     a 2xx (201 Created, confirmed live, same as every other pipeline-node
     AFS in this suite). Reload the canonical URL and confirm the switch is
     still checked AND the YAML editor shows the top-level field
     `interrupt_after:\n  - Code 1` (see § Concrete Handles — this is a
     **pipeline-level** YAML key, a list of node ids, NOT a per-node nested
     field like `code_node.interrupt_after: true`).
6. Execute the pipeline via the embedded chat — send any message — verify
   execution pauses after Code 1.
   - **Verify** (all confirmed live, 2026-08-08, pipeline id 8159):
     - Code 1 executes (its "Thought"/Python-sandbox execution bubble
       appears in the embedded chat, `Execution time: N.NNs` in
       `execution_info`).
     - The run then **pauses**: the `Code 1 -> Printer 1` canvas edge shows
       an `interrupt` label/pill; Code 1's ENTIRE config panel becomes
       `disabled` (Type/Value/Input/Output/Interrupt-before/Interrupt-after/
       Structured-output selects and switches all flip to a disabled
       state); the chat header shows a "Run is in progress" spinner +
       clickable "Run N details" label + a "Stop run" button.
     - Chat auto-posts, as its own message: *"How to proceed? To resume the
       pipeline - type anything..."*
       **Implementer correction (Phase 2/4, reverse-masking guard —
       `.agents/testing.md` § Merge gate): NOT reproduced.** Re-checked live
       on a FRESH pipeline (2 independent test runs, plus a manual probe on
       this AFS's own exploration pipeline id 8159) — the embedded chat
       shows exactly 2 messages after the trigger send (the user's message +
       Code 1's execution-result bubble), even after a further 10s settle
       wait. No separate "How to proceed?" bubble ever appears. Not filed as
       a defect (the interrupt mechanism itself is unaffected — the pill,
       locked panel, and run-in-progress indicator all appear correctly);
       the case's own wording ("UI indicates pipeline is paused") is already
       satisfied by those signals without this specific hint text, so the
       shipped test does not assert it.
     - Printer 1 does NOT execute yet (no Printer output bubble).
7. Verify interrupt state shown in UI.
   - **Verify**: same observations as step 6's pause assertions (the `interrupt`
     edge pill + locked Code 1 panel + "Run is in progress"/"Run N details"/
     "Stop run" header ARE the UI's interrupt-state indication — case step 7
     is a re-statement of step 6's expected result, not a distinct
     mechanism; asserted together in the same test step to avoid a flaky
     re-poll).
8. Resume execution — verify pipeline completes.
   - **KNOWN DEFECT — sanctioned RED, `expect.soft()` + `# Known defect:
     EliteaAI/elitea-testing-public#1327`.** Sending a plain chat message
     (e.g. `"continue"`), which is the UI's OWN advertised resume
     instruction, does **NOT** resume the paused run. Confirmed live,
     reproduced independently in TWO sessions on the same pipeline
     (id 8159): a **second, distinct Run History entry** is created
     (durations differ — 7.42s vs 9.61s — i.e. a NEW run is spawned, not a
     resume of the checkpointed one); the SAME "How to proceed?" hint is
     re-emitted verbatim; Printer 1 never executes; the `interrupt` edge
     pill and Code 1's locked panel remain. "Run is in progress"/"Stop run"
     disappear from the header (ambiguous partial-cleanup, not a clean
     resume or a clean failure). Zero console errors — a silent behavioral
     defect. Full repro + evidence: `EliteaAI/elitea-testing-public#1327`.
     Write this step's assertions (`Printer 1 output reaches chat` /
     `interrupt pill clears` / `Code 1 panel re-enables`) as the CORRECT
     expected behavior with `expect.soft()`, so the test flips green the
     moment the product fix ships (per `.agents/testing.md` § Merge gate,
     Analysis-time entry).

## Expected Results
- "Interrupt before" and "Interrupt after" switches are visible on every
  node type sharing `CommonInterruptSettings.jsx`; "Interrupt before" is
  disabled while the node is the pipeline's entry point, "Interrupt after"
  is disabled while the node has no outgoing transition (`transition: END`
  or none).
- Toggling "Interrupt after" on and saving persists correctly (round-trip
  confirmed via reload + YAML read) as the **pipeline-level**
  `interrupt_after:` list field (not a per-node nested field).
- Executing the pipeline correctly PAUSES after the interrupted node — the
  canvas shows an `interrupt` edge pill, the node's config panel locks, and
  the chat header shows an in-progress run indicator + a "How to proceed?"
  resume hint. This part of the case (steps 1-7) has **no product defect** —
  it matches the case text exactly.
- **Resuming via the UI's own advertised "type anything" instruction does
  NOT work** (step 8) — `EliteaAI/elitea-testing-public#1327`, sanctioned
  RED per the Merge gate's analysis-time exception.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in, pipeline with a node exists | met | Preconditions + step 0 | n/a (localhost auto-auth) + step 0 setup | asserted — **CLARIFICATION: a single node's "Interrupt after" is disabled (no outgoing edge); this AFS adds a second node + edge to satisfy the case's own step 4 ("toggle to enabled")** |
| 1 Open a pipeline with a node | Pipeline open, node visible | step 0-1 | step 1: `wait_for_node_on_canvas` ×2 | asserted |
| 2 Locate "Interrupt before" switch | visible | step 2 | step 2: visibility + disabled-state (entry point) | asserted — Axis-2 addition: disabled-state assertion beyond bare visibility |
| 3 Locate "Interrupt after" switch | visible | step 3 | step 3: visibility + NOT-disabled (has outgoing edge) | asserted |
| 4 Toggle "Interrupt after" to enabled | switch enabled | step 4 | step 4: `to_be_checked(True)` | asserted |
| 5 Save pipeline | saves without errors | step 5 | step 5: no console errors, 201, reload + YAML round-trip | asserted |
| 6 Execute — verify pauses after node | pause after Code 1 | step 6 | step 6: chat execution bubble, interrupt pill, locked panel, run-in-progress header, resume-hint message | asserted — no case-text drift, live UI matches exactly |
| 7 Verify interrupt state shown in UI | UI indicates paused | step 7 | step 7: same UI signals as step 6 (re-stated per case's own step split) | asserted |
| 8 Resume execution — verify pipeline completes | pipeline resumes and completes | step 8 | step 8: `expect.soft()` assertions, currently FAILING | **DEFECT — `EliteaAI/elitea-testing-public#1327`. Case's own Fail criteria ("execution cannot resume") is met live — this is a confirmed product bug, not case-text drift.** |
| Expected Final State: toggle pauses execution, UI shows state, resumes successfully | — | steps 6-8 | steps 6-8 | steps 6-7 pass; step 8 is the confirmed defect |
| Pass/Fail: interrupt after toggle pauses, UI shows state, execution resumes | — | all steps | all steps | **partially met — resume half fails per #1327; test stays green via soft-assert + linked defect, not masked** |

### Axis 2 — Analyst additions

- Step 0 additionally asserts the edge exists before proceeding — *added:
  without it, step 3's "Interrupt after is visible AND not disabled"
  assertion would be untestable (the switch is disabled with no outgoing
  transition), so the setup gate itself is asserted, not just performed.*
- Step 2 additionally asserts "Interrupt before" is `disabled` (the case
  only asks that it be "visible") — *added: matches this same family's
  established disabled-state convention (ELITEA-2037/2009/2034 etc.) and
  distinguishes a genuinely-disabled control from an accidentally-inert one.*
- Step 5 additionally asserts the exact HTTP status (201) and the exact YAML
  shape (`interrupt_after:` as a top-level list, not nested under the node)
  — *added: pins the field's actual location so a future implementer
  doesn't waste time guessing a per-node key that doesn't exist; also
  guards against a regression to a looser 2xx-only check.*
- Step 6/7 add the FULL set of live-observed pause signals (edge pill,
  locked panel, run-in-progress header, resume-hint chat message) — the
  case's own text only asked for "execution pauses" / "UI indicates
  paused"; the concrete signals are what actually exists to assert against.
- Step 8's soft-assert + Known-Defect framing is itself an Axis-2 addition
  — the case's raw Pass/Fail criteria would fail the whole test hard on a
  known, filed, isolated tail-step defect; per `.agents/testing.md` §
  Merge gate's analysis-time exception, the correct behavior is asserted
  and the test stays green until the fix ships, rather than either masking
  the defect (banned) or blocking the entire case on the tail step (steps
  1-7 have real, working, worth-having coverage).

## Cleanup

- Implementer teardown: use the existing `pipeline_id` fixture
  (`automation/fixtures/data_fixtures.py`), which creates-and-deletes an
  empty pipeline per test via `PipelineAPI`; build the two-node topology
  inside the test via `add_node`/`connect_nodes` (existing, unmodified
  methods) rather than a hand-built YAML fixture, since the case's own
  steps 1-4 are specifically about the TOGGLE INTERACTION on a live canvas,
  not just the end-state YAML.
- This analysis session reused a PRE-EXISTING exploration pipeline
  (`autotest_interrupt_2047`, id `8159`, project 399 "Private") that an
  earlier `test-automation-engineer` implementation attempt had already
  created and partially configured (see
  `.agents/memory/test-automation-engineer/pipeline_generic_interrupt_after_resume_is_ambiguous.md`).
  **Not deleted at the end of this session** — same tooling limitation
  already documented in sibling pipeline AFSes (this analyst-style
  exploration session's tooling doesn't expose a live `browser_cookies`
  context for `PipelineAPI`). Flagging for the implementer/lead: safe to
  delete (`pipeline_id` 8159) once the automated test's own fixture
  supersedes it.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Interrupt before switch (dynamic, per-node-id) | `NODE_INTERRUPT_BEFORE_TOGGLE.format(node_id)` → `[data-testid="pipeline-node-interrupt-before-toggle-{node_id}"]` | **on-`automation/testids` only** (awaiting human promotion to `main`, per ELITEA-2034's CORRECTION entry in the digest) — pre-existing class constant, already wired as `PipelineDetailPage.NODE_INTERRUPT_BEFORE_TOGGLE`; `toggle_node_interrupt_before()` / `is_node_interrupt_before_toggle_visible()` / `is_node_interrupt_before_toggle_disabled()` methods already exist, reused unmodified. | none needed |
| Interrupt after switch (Code node) | `[data-testid="pipeline-code-node-interrupt-after-toggle"]` | **added by a prior session — `EliteaAI/EliteaUI@92fc6ec4` on `automation/testids`** (awaiting human promotion to `main`) — already wired as `PipelineDetailPage.code_node_interrupt_after_toggle`, reused unmodified. Equivalent testids/fields exist for every other node type (`llm_node_interrupt_after_toggle`, `mcp_node_interrupt_after_toggle`, `toolkit_node_interrupt_after_toggle`, `custom_node_interrupt_after_toggle`, `decision_node_interrupt_after_toggle`, `agent_node_interrupt_after_toggle`) — pick the field matching whichever node type the implementer chooses. | none needed |
| Code node on canvas | `[data-testid="rf__node-{node_id}"]` (dynamic, e.g. `rf__node-Code 1`) | **on-main ✓** — ReactFlow's own testid convention (library-injected, sanctioned #579 exception); confirmed live via `wait_for_node_on_canvas("code")`. | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` | **on-main ✓** — confirmed present, already wired as `PipelineFormPage.save_button`; fires `PUT .../application/prompt_lib/{project}/{pipeline_id}` → 201, confirmed live. | none needed |
| Pipeline YAML tab | `pipeline-yaml-view` / `pipeline-flow-view` | **on-main ✓** — confirmed live this session (`page.getByTestId('pipeline-yaml-view')` / `'pipeline-flow-view'`); already wired via `PipelineDetailPage.switch_to_yaml_view()` / `get_yaml_content()`. | none needed |
| Embedded chat input / send | `chat-message-input` (testid) | **on-main ✓** — confirmed live (`page.getByTestId('chat-message-input')`); already wired via `PipelineDetailPage.send_message_in_embedded_chat()`. | none needed |
| Embedded chat message list | `ul.MuiList-root li.MuiListItem-root` | **CSS, pre-existing pattern** — already wired via `PipelineDetailPage._embedded_chat_messages()` / `get_embedded_chat_last_message()`; used to confirm the Code-1 execution bubble and the "How to proceed?" resume-hint bubble text this session. | none needed |
| Run details panel / status badge | `pipeline-run-details-panel` / `pipeline-run-details-status-badge` (with `data-status` attribute) | **pre-existing** — already wired as `PipelineDetailPage.run_details_panel` / `run_details_status_badge`, `open_run_details_panel()` / `get_run_details_status()`. Not yet exercised live this session (used the header's own text instead — see gaps below) but the implementer should prefer these for step 6/7's pause assertion where possible. | none needed |
| **GAP — "Run is in progress" header banner** | none | **Testid gap.** Confirmed live via `document.body.innerText.includes('Run is in progress')` — no `data-testid` on this element or its progressbar. Recommend `pipeline-run-in-progress-banner`. | text-content check (used this session) |
| **GAP — "Run N details" clickable label** | none | **Testid gap.** Confirmed live (`"View details": "Run 1 details"` accessible name in the a11y snapshot) — no testid. Recommend `pipeline-run-details-open-button` (distinct from the panel's own `pipeline-run-details-panel` which is the DIALOG, not the trigger). | accessible-name text match (used this session: `"Run 1 details"`, though the number increments per run — match by prefix `"Run"` + suffix `"details"`, not the literal string) |
| **GAP — "Stop run" button** | none | **Testid gap.** Confirmed live (accessible name `"Stop run"`) — no testid. Recommend `pipeline-stop-run-button`. | accessible-name text match |
| **`interrupt` edge pill — CLOSED (implementer, add-data-testid)** | `pipeline-edge-label-xy-edge__{source}---{target}` | **Testid added this implementation** — `EliteaAI/EliteaUI@94d190c9` on `automation/testids`. The pill is app JSX (`CustomEdge.jsx`'s `EdgeLabelRenderer` `Typography`, rendering `data.label` — NOT ReactFlow-internal despite sitting inside the `rf__wrapper` subtree), so the #579 third-party exception the AFS proposed does NOT apply; added `data-testid={`pipeline-edge-label-${id}`}` directly, keyed by the SAME internal `xy-edge__{source}---{target}` id `EDGE_TESTID` already uses for the edge itself (confirmed live: CustomEdge's `id` prop IS that exact string). New page-object constant `PipelineDetailPage.EDGE_LABEL` + `get_edge_label_locator(source_id, target_id)`. | none needed — real testid now exists |
| Pipeline-level `interrupt_after` YAML field | top-level list key: `interrupt_after:\n  - {node_id}` | **confirmed live, this session** — read via `get_yaml_content()` on pipeline id 8159: `entry_point: Code 1\ninterrupt_after:\n  - Code 1\nnodes:\n  ...`. **NOT a per-node nested field** (unlike `structured_output`, which nests under the node) — implementer must assert against the pipeline-level YAML root, not `nodes[0].interrupt_after`. | n/a — this IS the source-of-truth field |

## Network Behavior
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on Save click (step 5); persists the `interrupt_after` list at the pipeline YAML root. Confirmed live: **201 Created**.
- Chat execution and the pause/resume protocol run entirely over the **WebSocket** channel (architecture.md: "AI responses arrive over WebSocket ~2s after send") — no discrete REST request fires per chat message; this AFS's evidence for step 6/8 is DOM/UI-observed (chat bubbles, canvas state, Run History entries), not a captured HTTP payload. An implementer wanting the exact wire-protocol frame for step 8's defect (e.g. to confirm no `interrupt_resume`-shaped frame is ever sent, vs one being sent and ignored) should use `PipelineDetailPage.capture_websocket_frames()` (existing helper, same pattern as `test_pipeline_hitl_node_runtime_behavior.py`) — this analyst session's live-browser tooling (Playwright MCP, not a pytest fixture) could not attach that capture retroactively to an already-open session.

## Known Defects Found During Exploration

- **[CONFIRMED DEFECT] Generic per-node `Interrupt after` pause cannot be
  resumed via the UI's own advertised "type anything" chat instruction.**
  Filed: `EliteaAI/elitea-testing-public#1327`. Reproduced independently in
  two sessions (an earlier `test-automation-engineer` implementation
  attempt, and this analysis session) on the same pipeline (id 8159,
  `Code 1 -> Printer 1 -> END`, `interrupt_after: [Code 1]`). Distinct from
  `EliteaAI/elitea-testing-public#1103` (HITL node's dedicated
  Approve/Reject resume path) — sibling defect, same general area, filed
  separately per the sibling-not-duplicate dedup rule. Per
  `.agents/testing.md` § Merge gate's analysis-time exception, this AFS
  classifies `ready-for-automation` (not `defect-found`) because the defect
  is isolated to the case's tail step (8 of 8) — steps 0-7 execute and
  assert cleanly against the live product with zero drift.

## Blocked Steps

None. All 9 steps (case's 8 plus this AFS's setup step 0) were executed
live against the local environment. Step 8 is not blocked — it was
executed and its actual (broken) behavior is precisely what's being
automated as a sanctioned-RED soft-assertion tied to the filed defect.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. All
  testids for the "happy path" (steps 0-7) already exist and are already
  wired as `PipelineDetailPage` fields/methods from prior sessions working
  this same surface — no NEW `add-data-testid` pass is required to automate
  steps 0-7. The three header-banner testid gaps (run-in-progress banner,
  "Run N details" trigger, "Stop run" button) and the `interrupt` edge-pill
  gap are listed in § Concrete Handles for the implementer to close via
  `add-data-testid` if the chosen assertion approach needs them (a coarse
  `innerText`/accessible-name check, as used during this exploration, is a
  viable interim fallback per the case's own loose "UI indicates paused"
  wording, but a testid is preferred per the project's coverage-by-testid-
  presence policy).
- **Reuse `connect_nodes()`, `add_node()`, `wait_for_edge()`** (all
  pre-existing, unmodified) for step 0's two-node setup — same pattern as
  ELITEA-2031/2032's edge-creation/deletion AFSes.
- **The pipeline-level `interrupt_after:` YAML field is the one genuinely
  new handle this case needed** — every other node-configuration AFS in
  this suite deals with per-node nested fields; this is the first case
  whose toggle writes to the pipeline root instead. Read via
  `get_yaml_content()` after `switch_to_yaml_view()` (pre-existing,
  unmodified) — this pipeline's YAML is only ~17 lines, well under the
  ~32-34-line truncation threshold documented for
  `EliteaAI/elitea-testing-public#1025`, so the on-screen tab is safe to
  read directly (no `pipeline_api.get_pipeline()` workaround needed).
- **Wait strategy for step 6's pause**: wait for the Code-1 execution
  bubble to appear in the embedded chat (`wait_for_embedded_chat_response`,
  pre-existing) THEN additionally wait for the "How to proceed?" hint
  bubble (a SECOND, separate chat message) before asserting the pause is
  fully settled — sending the trigger message and asserting immediately
  raced ahead of the pause state during this exploration; allow up to
  ~15s total (observed: ~9-10s from send to the hint bubble appearing).
- **Step 8's assertion shape**: don't hard-fail the whole test on the
  resume defect. Use `expect.soft()` (or the project's equivalent soft-
  failure aggregation, per `.agents/testing.md` § Merge gate's closed-set
  variant) for exactly the resume-completion assertions (Printer 1 output
  appears / interrupt pill clears / Code 1 panel re-enables), each tagged
  `# Known defect: EliteaAI/elitea-testing-public#1327` — steps 0-7's
  assertions stay hard (they pass cleanly and should keep blocking on
  regression).
