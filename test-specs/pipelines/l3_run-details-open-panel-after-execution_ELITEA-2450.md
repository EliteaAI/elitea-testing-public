# Test Case: Run Details — Open Panel After Execution

## Metadata
- **TMS ID**: ELITEA-2450
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case; project convention
  maps medium → `@pytest.mark.p2`, confirmed via
  `test-specs/pipelines/l3_entry-point-trigger-types-persist_ELITEA-2005.md`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-06
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed
  envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline with a runnable node exists and is open in Flow view — satisfied
  via the existing `pipeline_with_llm_id` fixture (`automation/fixtures/data_fixtures.py`,
  `PipelineAPI.create_pipeline_with_llm_node()` — LLM node connected START→LLM→END)
  + `PipelineDetailPage.navigate(pipeline_id)`. Confirmed live this session: created
  pipeline id 7615 via this exact API call, landed on
  `/pipelines/all/7615?viewMode=owner` in Flow view showing `LLM 1 → END`.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline with one LLM node via the `pipeline_with_llm_id` fixture (already
  exists and is reused unmodified by `automation/tests/ui/pipelines/test_pipeline_execution.py`).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project
  was "Private" (id 399), matching `.env.test`.

## Test Steps

1. Navigate to a pipeline (with a runnable LLM node) in Flow view
   (`pipeline_with_llm_id` fixture + `navigate()`).
   **Expected**: canvas displayed, `LLM 1` node visible, connected to `END`
   (confirmed live).
2. Send a message in the embedded chat
   (`chat_input`/`chat_send_button` — already-existing testids
   `chat-message-input`/`chat-send-button`, already wired as
   `PipelineDetailPage.chat_input`/`chat_send_button`) and wait for the AI
   response to complete (`wait_for_embedded_chat_response()` — already
   exists, used unmodified by `test_pipeline_execution.py`).
   **Expected**: pipeline executes; a run indicator appears **above the Flow
   canvas** (see Coverage Map Axis 1 row 2 — this is NOT inside the embedded
   chat's message list, contrary to the case's literal wording), showing a
   status icon, the label `"Run 1 details"`, and a delete icon. Confirmed
   live: status icon tooltip reads `"Run is completed"`; the run's underlying
   state comes entirely from Socket.IO events (`useRunEvent.hooks.js`) — no
   dedicated REST GET backs it, so the test must wait on this DOM element,
   not poll an endpoint.
3. Click the run's `"Run 1 details"` label to open the Run Details panel.
   **Expected**: a `role="dialog"` modal opens (`RunStateDialog.jsx`).
   Confirmed live.
4. Verify the panel header shows `"Run 1 details"` (N = the run number).
   **Expected — confirmed live, exact text match**: header reads literally
   `"Run 1 details"` (not just `"Run 1"` — the case's own wording is exactly
   right here).
5. Verify a `"Completed"` green badge appears next to the header.
   **Expected — confirmed live, exact match**: a pill-shaped badge reading
   `"Completed"`, green outline/text (`RunStatus` component, styled per
   `data.status === FlowEditorConstants.PipelineStatus.Completed`).
6. Verify a trash (delete) icon button is present in the panel header.
   **Expected — confirmed live**: present, positioned right after the
   `"Completed"` badge. Source-verified (`RunStateDialog.jsx`): this is the
   `Delete` branch of a status-conditional render — a pipeline caught
   `InProgress` would show a `Stop` icon here instead of `Delete`; this test
   only exercises the `Completed` path (matches the case).
7. Verify an expand/fullscreen-style control is present in the header area.
   **Expected — CONFIRMED LIVE, but with a case-text CLARIFICATION on what
   it actually is (see Coverage Map + Known Defects Found During
   Exploration below).** The header's second icon button (after the trash
   icon) is a **Close** button (`CollapseIcon` — a "compress to corners"
   glyph that closes the dialog), not a distinct "expand to fullscreen"
   toggle — the dialog is already sized responsively (90% of the editor
   viewport) the moment it opens, so there is no "restore" affordance to
   pair with it. A genuine `FullscreenOutlinedIcon` expand control DOES
   exist live, but it is scoped to each States row's Before/After value box
   (`StateItemViewHeader`), not the panel header. This AFS asserts what is
   actually present: header = [status badge, delete icon, close icon];
   per-state-value expand icons live inside the States section (step 8).
8. Verify the panel contains a Timeline step section and a States section.
   **Expected — confirmed live** (amended during ELITEA-2450 implementation
   fix round 1: the ALL-CAPS "TIMELINE STEP"/"STATES" wording below was this
   AFS's own paraphrase, not the literal rendered text — source-verified
   against `RunStateDialog.jsx:277` (`Timeline step:`) and `:452` (`States`),
   both sentence case): a `"Timeline step:"` label immediately followed by
   the node id with no separator (renders `Timeline step:LLM1` for this
   pipeline's single-node run — confirmed live) followed by a stepper (one
   filled circle + timestamp per timeline entry — one entry, `18:45:09`, for
   this single-node pipeline); then a `"States"` section header followed by
   one accordion row per pipeline state variable
   (`input`, `messages` for this pipeline), each expandable to show
   Before/After value boxes with their own per-value expand icons.

## Expected Final State
The Run Details panel is open and displays: header `"Run N details"`,
`"Completed"` status badge, delete icon, close icon, a Timeline step section,
and a States section — all confirmed live and asserted above.

## Coverage Map

### Axis 1 — Case elements → live behavior

| Case element | Expected result (case text) | Covered by (this AFS) | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Create and execute a pipeline | Operation completes; state updates, confirmation shown | Step 1 (navigate to `pipeline_with_llm_id`) + Step 2 (send message, wait for response) | Steps 1–2 | covered |
| Step 2: Click the run "in chat history" to open Run Details | Action completes without error | Step 3 (click `"Run 1 details"` label) | Step 3 | **covered, with CLARIFICATION** — the click target is a `RunStateNode` element rendered above the Flow canvas, not inside the embedded chat's message list. Filed: `EliteaAI/elitea-testing-public#1268`. |
| Step 3: "Verify Run Details panel shows:" (section intro, no standalone assertion) | Condition holds as described | N/A — introduces steps 4–8 | — | covered (via steps 4–8) |
| Step 4: Header "Run N details" | Action completes without error | Step 4 | Step 4 | covered — exact text match |
| Step 5: "Completed" green badge next to header | Action completes without error | Step 5 | Step 5 | covered — exact match |
| Step 6: Trash (delete) icon button | Action completes without error | Step 6 | Step 6 | covered |
| Step 7: Expand/fullscreen button | Action completes without error | Step 7 | Step 7 | **covered, with CLARIFICATION** — header's second icon is a Close button, not a fullscreen toggle; the genuine expand/fullscreen controls are per-state-value, inside the States section. Filed: `EliteaAI/elitea-testing-public#1268`. |
| Step 8: Panel contains TIMELINE STEP section and STATES section | Condition holds as described | Step 8 | Step 8 | **covered, with CLARIFICATION** — case text is ALL-CAPS ("TIMELINE STEP"/"STATES"); confirmed-live text is sentence case (`"Timeline step:"` / `"States"`, source-verified against `RunStateDialog.jsx:277`/`:452`); the assertions check the sentence-case literal text, not the case's paraphrase. |

### Axis 2 — Assertions beyond the case

| Extra observable | Grounded reason |
|---|---|
| Zero unexpected console errors during navigate→execute→open-panel, EXCEPT the known `EliteaAI/elitea-testing-public#1267` Stepper prop-leak warning | `.agents/testing.md` "check console even when UI looks fine" discipline; a blanket "0 console errors" assertion would be false given the known, filed, deterministic warning — implementer should scope the assertion to exclude/soft-assert that one known signature (see Known Defects below), not swallow console-checking entirely. |
| Close button actually closes the dialog | Confirmed live this session (clicked the close icon, dialog `role="dialog"` node disappeared from a fresh snapshot) — cheap, high-value smoke of the one control this case's own pass/fail criteria imply should work ("panel" being a real, dismissible UI element) without being a separate case. |

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Embedded chat message input | `[data-testid="chat-message-input"]` | **needs re-verification of on-main vs on-`automation/testids` status** (not re-checked this session — already wired as `PipelineDetailPage.chat_input`, reused unmodified from `test_pipeline_execution.py`, which is itself merged and green) | none needed |
| Embedded chat send button | `[data-testid="chat-send-button"]` | same as above — already wired as `PipelineDetailPage.chat_send_button` | none needed |
| Run node clickable label (opens Run Details) | `testid needed: pipeline-run-node-label` | **needs-adding.** Source: `RunStateNode.jsx` — `<Typography onClick={onOpen}>{data.label}</Typography>`, zero testid/aria-label. Confirmed live via full-page snapshot: accessible name is the tooltip text `"View details"`, NOT the visible label text `"Run 1 details"` — do not locate by accessible role/name, it's ambiguous/unstable across i18n and doesn't match what a human reads on screen. | interim only: `text="Run 1 details"` Playwright selector (exploration-only, NOT testid-compliant — used only to reach the panel during this analysis session) |
| Run node delete (outer, on-canvas) icon | `testid needed: pipeline-run-node-delete-button` | **needs-adding.** Source: `RunStateNode.jsx` — conditional `StopIcon`/`DeleteIcon` with no testid; tooltip text `"Delete run"`/`"Stop run"`. Not required by THIS case's assertions (case only requires the delete icon INSIDE the opened panel, step 6) — listed here for completeness/forward reference since a sibling case (ELITEA-2454, "Delete Run from History") will need it. | none needed for this case |
| Run Details panel root (dialog) | `testid needed: pipeline-run-details-panel` | **needs-adding.** Source: `RunStateDialog.jsx` — plain MUI `Dialog`, no testid on `DialogContent`/root `Box`. Recommended scope-anchor for all panel-internal locators below. | interim only: `page.get_by_role("dialog")` (exploration-only; acceptable ONLY as a temporary scope root until the testid is added — do not ship without it, per role-overrides "no raw handle even for scoping") |
| Panel header text ("Run N details") | `testid needed: pipeline-run-details-header` | **needs-adding.** Source: `RunStateDialog.jsx:214-221` — `<Typography>{data.label}</Typography>`, no testid. | none needed |
| Panel status badge ("Completed"/etc.) | `testid needed: pipeline-run-details-status-badge`; state read via a `data-status="{completed\|error\|in_progress\|stopped}"` attribute on the SAME testid (per `.agents/testing.md` "testid = stable identity; state via `data-*`" ruling — do NOT request per-status testid variants) | **needs-adding.** Source: `RunStateDialog.jsx`'s `RunStatus` component — text content IS the status (`{status}` rendered directly), so a `data-status` attribute mirroring `data.status` is the compliant shape, not a testid keyed to the specific status word. | none needed |
| Panel delete/stop icon button | `testid needed: pipeline-run-details-delete-button` (single testid; the Stop-vs-Delete branch is a same-element conditional pair per canon ruling #277 — only one branch renders at a time depending on `data.status`, so ONE testid on whichever `IconButton` is mounted is compliant; no `data-*` state suffix needed since the icon inside, not the testid, encodes which mode) | **needs-adding.** Source: `RunStateDialog.jsx` — `onDelete`/`onStop` `IconButton`s, mutually exclusive branches, neither has a testid. This case only exercises the `Completed` → Delete branch. | none needed |
| Panel close icon button | `testid needed: pipeline-run-details-close-button` | **needs-adding.** Source: `RunStateDialog.jsx` — `onClose` `IconButton` (`CollapseIcon`), no testid. Confirmed live: clicking it removes the `role="dialog"` node from a fresh snapshot. | none needed |
| Timeline step section (label + stepper) | `testid needed: pipeline-run-details-timeline-section` | **needs-adding.** Source: `RunStateDialog.jsx:277` — the `Box` wrapping `"Timeline step:"` (literal, sentence case) + `Stepper`, no testid. Text content renders `Timeline step:LLM1` (label and node id concatenated with no separator) for this pipeline — sufficient for this case's assertion depth; per-step granularity is a sibling case's concern (ELITEA-2451, "Timeline Steps Display" — out of scope here). | none needed |
| States section (header + accordion list) | `testid needed: pipeline-run-details-states-section` | **needs-adding.** Source: `RunStateDialog.jsx:452` — the `Box` wrapping the `"States"` `Typography` (literal, sentence case) + the `variables.map(...)` accordion list, no testid. Per-variable/per-value granularity (Before/After boxes, their own expand icons) is a sibling case's concern (ELITEA-2452, "State Before/After per Node" — out of scope here); this case only needs the section's presence. | none needed |

## Network Behavior
- Pipeline execution and the run's Timeline/States data arrive **entirely
  over Socket.IO** (confirmed via `browser_network_requests`: `socket.io/?EIO=4…`
  polling exchanges around the send/response window; no dedicated REST
  endpoint returns run/timeline/state data — it's derived client-side from
  socket events in `useRunEvent.hooks.js` and held in `FlowEditor`'s local
  state, then threaded down as the `data`/`yamlJsonObject.state` props to
  `RunStateNode`/`RunStateDialog`). Confirms `.agents/testing.md`'s
  "AI responses arrive over WebSocket — use condition waits" note extends to
  this feature: the test must wait on the DOM (`wait_for_embedded_chat_response()`,
  already exists) before the run node becomes clickable, not poll an
  endpoint for "run complete."
- `GET .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — the
  usual page-load fetch (step 1); unrelated to the run itself.

## Known Defects Found During Exploration

**One MINOR product bug found** (does not block the case — panel renders and
functions correctly regardless):

- **Console warning on every panel open**: `RunStateDialog.jsx`'s Timeline
  Stepper leaks a non-boolean prop (likely `last`/`active`/`completed`, MUI
  `Stepper`-injected) onto a raw DOM `<div>` via its custom `ProcessConnector`
  wrapper — same root-cause class as the already-filed
  `EliteaAI/elitea-testing-public#611` (Publish-wizard Stepper icon), but a
  different component/screen, so filed as a sibling, not a duplicate:
  `EliteaAI/elitea-testing-public#1267`. **Automation hint**: do not assert a
  blanket "zero console errors" across navigate→execute→open-panel for this
  flow — either scope the assertion to exclude this one known warning
  signature (`expect.soft()` + `# Known defect: #1267`), or assert
  "zero console errors" only up through step 2 (before the panel opens) and
  handle step 3 onward's known warning explicitly.

**Two case-text CLARIFICATIONS found** (live product is correct; case
wording is stale), both filed together as one issue per the case-level
bundling pattern used elsewhere in this suite (e.g. `#1195`, `#1199`):
`EliteaAI/elitea-testing-public#1268` — covers:
1. Step 2's "click on the run in chat history" — the click target is a
   `RunStateNode` element rendered above the Flow canvas, not inside the
   embedded chat's message list.
2. Step 7's "Expand/fullscreen button" — the header's second icon is a Close
   button, not a distinct fullscreen toggle; genuine expand controls exist
   per-state-value inside the States section instead.

Dedup checked against the existing `[Clarification]`/`[CLARIFICATION]`/`bug`
cluster before filing both (`gh issue list --label bug --state all` /
`--label question`, keyword-matched locally) — no existing issue covered
either the Run Details panel's click-source or its header composition, so
both are new, non-duplicate filings.

## Blocked Steps

None. All 8 case steps were executed to completion against the live local
environment (pipeline id 7615, `afs_2450_probe`).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **Testid gaps this case needs before implementation** — the ENTIRE Run
  Details feature (`RunStateNode.jsx`, `RunStateNodeGroup.jsx`,
  `RunStateDialog.jsx`, all under
  `src/[fsd]/features/pipelines/flow-editor/ui/{nodes,state}/`) has **zero**
  existing testids (confirmed via `grep -rn "data-testid" ...` across all
  three files — no hits). Run `add-data-testid` to add exactly the 6
  testids listed in Concrete Handles above (run-node label, panel root,
  header, status badge + `data-status`, delete button, close button,
  timeline section, states section — 8 total, see table) before writing the
  test; do not add per-run-history-menu or per-state-variable testids in
  this pass — those belong to sibling cases (ELITEA-2451/2452/2453/2454,
  already filed as separate `[Automate]` tickets `#959`/`#960`/`#961`/`#962`
  — out of scope for this AFS).
- **Reuse `pipeline_with_llm_id` + `_execute_pipeline()`-style helpers** from
  `automation/tests/ui/pipelines/test_pipeline_execution.py` — this case's
  steps 1–2 are exactly that fixture + `send_message_in_embedded_chat()` +
  `wait_for_embedded_chat_response()`, all already existing and green. No
  new fixture needed.
- **The run node's accessible name is the TOOLTIP text ("View details"),
  not the visible label ("Run 1 details")** — confirmed live via full-page
  snapshot. This is exactly the kind of trap `_surface.md`'s prior sessions
  flagged for other pipeline controls (`pipeline-state-add-variable-button`'s
  ambiguous accessible name) — never `get_by_role("button", {name: ...})`
  here even as a fallback; use the testid once added.
- **Wait discipline**: the run node only appears/becomes "Completed" after
  `wait_for_embedded_chat_response()` resolves (WebSocket-driven, ~2–5s in
  this session) — do not add a fixed sleep; the existing helper's
  polling-based wait is sufficient and already proven by
  `test_pipeline_execution.py`.
- `_surface.md` updated this session with a new "Run Details panel (RunStateNode/RunStateDialog) — opened after pipeline execution" section covering the click-target location, header composition, the WebSocket-only data source, and the testid gap.
