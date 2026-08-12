# Test Case: Run Details — Timeline Steps Display

## Metadata
- **TMS ID**: ELITEA-2451
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case; project convention
  maps medium → `@pytest.mark.p2`, matching the sibling cases ELITEA-2450/2452/2453)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-09 (batch pipelines-remaining, wave-07)
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A pipeline with **3+ nodes, all plain (non-structured-output) types**, exists and
  is open in Flow view. Confirmed live this session with a fresh 3-node LLM chain
  (pipeline id 8767, `afs_2451_probe2`, deleted at session end) via
  `PipelineAPI.create_pipeline_with_nodes()`:
  ```yaml
  entry_point: LLM 1
  nodes:
    - id: LLM 1
      type: llm
      output: [messages]
      transition: LLM 2
      # system: "You are a helpful assistant.", task: "Say hello in exactly three words." (fixed)
    - id: LLM 2
      type: llm
      input: [messages]
      output: []
      transition: LLM 3
      # system: "Reply with just OK.", task: "Ack: {messages}" (fstring)
    - id: LLM 3
      type: llm
      input: []
      output: []
      transition: END
      # system: "Reply with just DONE.", task: "final ack" (fixed)
  ```
  **Deliberately NOT the `structured_output: true` shape** — see Known Defects/
  Automation Hints below: a structured-output LLM node renders TWO timeline entries
  per execution (confirmed by the ELITEA-2453 sibling AFS), which would break this
  case's own step-8 "entries == executed nodes" assertion. A plain multi-LLM chain
  keeps the 1:1 correspondence this case needs.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A 3-node LLM→LLM→LLM→END pipeline via `PipelineAPI.create_pipeline_with_nodes()`
  (the YAML above — no existing fixture has exactly 3 plain nodes; see Automation
  Hints for a recommended new fixture).
- Chat message sent: any short prompt (this session used
  `"Say hello in exactly three words."`) — content is irrelevant to the assertions;
  only "the pipeline runs to completion, producing exactly 3 timeline entries" matters.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project
  was "Private" (id 399), matching `.env.test`.

## Test Steps

1. Execute a pipeline with 3+ nodes (the fixture pipeline above).
   **Expected**: pipeline executes without error; a `"Run 1 details"` indicator
   appears above the Flow canvas (`pipeline-run-node-label`, reused unmodified
   from ELITEA-2450), status transitions to `"Completed"`. Confirmed live:
   run completed with 3 nodes executed (`LLM 1`, `LLM 2`, `LLM 3`).
2. Open Run Details (`pipeline-run-node-label` click →
   `open_run_details_panel()`, reused unmodified from ELITEA-2450).
   **Expected**: panel opens (`role="dialog"`, `pipeline-run-details-panel`).
   Confirmed live.
3. Verify each executed node appears as a timeline entry (steps 4–6 below detail
   what each entry must show).
   **Expected**: exactly one timeline-step dot per executed node. Confirmed live:
   3 dots present (`pipeline-run-details-timeline-step-0/1/2`), one per executed
   `LLM 1`/`LLM 2`/`LLM 3` node.
4. Green dot indicator (successful execution).
   **Expected — confirmed live via screenshot AND source
   (`ProcessStepIcon.jsx`)**: every dot renders filled with `palette.status.published`
   (green) — the color is driven by a SINGLE run-level flag
   (`isError = data.status === PipelineStatus.Error`), passed identically to every
   step's `ProcessStepIcon`, not computed per-step. For a `Completed` run (this
   case's own precondition), all N dots are green; there is no per-step
   success/failure color — the run-level status IS the color signal. Confirmed
   live: all 3 dots rendered green, connected by a green `StepConnector` line.
5. Node name (on hover) matching the node id from the pipeline.
   **Expected — confirmed live, WITH a mechanism clarification**: hovering a
   timeline-step dot shows a small popup with the node's id — e.g. hovering the
   middle dot showed `"LLM2"` (screenshot:
   `test-results/screenshots/ELITEA-2451-step-hover-tooltip.png`). The id
   renders **without the YAML id's space** (`"LLM 2"` → `"LLM2"`) — same
   space-stripping behavior already documented for the Timeline label in
   ELITEA-2450's AFS. Mechanism: the dot (`ProcessStepIcon.jsx`'s outer `Box`,
   already carrying the `pipeline-run-details-timeline-step-{index}` testid) is
   wrapped in a `StyledTooltip` with `title={step.id}` — MUI's Tooltip surfaces
   this as a static `aria-label` HTML attribute on the trigger element itself
   (confirmed via `outerHTML` read: `aria-label="LLM1"` on the dot, alongside
   `data-mui-internal-clone-element="true"`), present even before a real
   mouse-hover event fires (accessibility snapshot showed the name
   immediately on panel open — same technique already documented in role
   memory,
   `artifacts_bucket_search_testid_gaps_and_tooltip_aria_label_technique.md`,
   for a different MUI Tooltip call site). A real `browser_hover` on the dot
   additionally rendered the VISUAL popup on top of it (screenshot above).
   Automation reads `get_attribute("aria-label")` on the
   EXISTING per-index testid locator — no new handle needed for this
   assertion; a real `.hover()` call is still exercised for behavioral fidelity
   with the case's literal "on hover" wording, but the assertion itself doesn't
   need the popup to be visually rendered.
6. Timestamp in HH:MM:SS format.
   **Expected — confirmed live, exact format match**: each timeline entry shows
   a timestamp directly under its dot in `HH:mm:ss` (e.g. `13:32:19`, `13:32:20`,
   `13:32:21` for this session's 3-node run) — source-verified,
   `RunStateDialog.jsx:289`: `format(new Date(step.created_at), 'HH:mm:ss')`.
   **This Typography element has NO existing testid** (see Concrete Handles —
   needs-adding).
7. Verify nodes appear in execution order (top to bottom = first to last).
   **Expected — CONFIRMED LIVE, but with a case-text CLARIFICATION on the
   axis** (filed:
   `EliteaAI/elitea-testing-public#1375`): the Timeline is a plain MUI
   `Stepper` with no `orientation="vertical"` override — it renders
   **horizontally, left to right**, not stacked top to bottom. Confirmed via
   a bounding-box read of all 3 dots after the completed run:

   | Step | x | y |
   |---|---|---|
   | LLM1 @ 13:32:19 | 371 | 303 |
   | LLM2 @ 13:32:20 | 852 | 302 |
   | LLM3 @ 13:32:21 | 1336 | 303 |

   Y stays constant (~302–303px, i.e. one visual row) while X increases
   monotonically with execution order and DOM order (`data.timeline.map`
   renders in array order = execution order, confirmed via the ascending
   timestamps above). The case's underlying intent — first-executed appears
   first in the visual reading order — DOES hold; only the described axis
   (top-to-bottom vs left-to-right) is wrong. This AFS asserts execution
   order via **DOM/index order correlated with ascending timestamps**
   (robust to the axis, and to any future layout change), not via absolute
   pixel Y-coordinates.
8. Verify total timeline entries match the number of nodes that executed.
   **Expected — confirmed live**: exactly 3 timeline-step dots
   (`pipeline-run-details-timeline-step-0`, `-1`, `-2`) for the 3 executed
   nodes (`LLM 1`, `LLM 2`, `LLM 3`). **Automation caveat (see Known Defects)**:
   this 1:1 correspondence does NOT hold for a `structured_output: true` LLM
   node, which the ELITEA-2453 sibling AFS found renders TWO timeline entries
   per execution — this case's fixture deliberately avoids structured output
   to keep the assertion meaningful.

## Expected Final State
The Run Details panel is open, showing exactly one timeline-step entry per
executed node (3 for this case's fixture), each with a green dot, a
hover-revealed node-id tooltip, and an `HH:mm:ss` timestamp, laid out in
execution order (left to right, confirmed live) — all asserted above.

## Coverage Map

### Axis 1 — Case elements → live behavior

| Case element | Expected result (case text) | Covered by (this AFS) | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Execute a pipeline with 3+ nodes | Action completes without error | Step 1 (3-node LLM chain fixture, send message, wait for response) | Step 1 | covered |
| Step 2: Open Run Details | Target page/section loads successfully | Step 2 (`open_run_details_panel()`, reused from ELITEA-2450) | Step 2 | covered |
| Step 3: "Verify each executed node appears as a timeline entry with:" (section intro) | Condition holds as described | N/A — introduces steps 4–6 | — | covered (via steps 4–6) |
| Step 4: Green dot indicator (successful execution) | Action completes without error | Step 4 | Step 4 | **covered, with mechanism note** — color is a single run-level flag applied uniformly to every step, not computed per-step; asserting the run's `Completed` status (existing `pipeline-run-details-status-badge`'s `data-status`) is the ground truth the dot color derives from |
| Step 5: Node name (on hover) matching the node id from the pipeline | Action completes without error | Step 5 | Step 5 | **covered, with mechanism note** — node id renders space-stripped (`"LLM 2"` → `"LLM2"`), same as ELITEA-2450's Timeline-label finding; read via the dot's `aria-label` attribute, real `.hover()` also exercised |
| Step 6: Timestamp in HH:MM:SS format | Action completes without error | Step 6 | Step 6 | covered — exact format match (`HH:mm:ss`) |
| Step 7: Verify nodes appear in execution order (top to bottom = first to last) | Condition holds as described | Step 7 | Step 7 | **covered, with CLARIFICATION** — layout is left-to-right, not top-to-bottom; filed `EliteaAI/elitea-testing-public#1375`. Execution-order semantic itself holds and is asserted via DOM-index/timestamp correlation. |
| Step 8: Verify total timeline entries match the number of nodes that executed | Condition holds as described | Step 8 | Step 8 | covered — 3 entries for 3 executed nodes, with an automation caveat about structured-output nodes (see Known Defects) |

### Axis 2 — Assertions beyond the case

| Extra observable | Grounded reason |
|---|---|
| Zero unexpected console errors during navigate→execute→open-panel, EXCEPT the known `EliteaAI/elitea-testing-public#1267` Stepper prop-leak warning | `.agents/testing.md` "check console even when UI looks fine" discipline; the same known, filed, deterministic warning fires for this pipeline too (confirmed live — identical stack trace through `RunStateDialog.jsx`'s `Stepper`/`ProcessConnector`) — scope the assertion to exclude that one known signature, don't swallow console-checking entirely. |
| Timeline entries' order matches the entries' own ascending timestamps | Directly proves "execution order" independent of any visual axis — a stronger, more future-proof assertion than reading pixel positions, and it's what step 7's actual intent (not its literal axis wording) requires. |

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Run node label / Run Details panel / header / status badge / timeline section / states section | Reuse unmodified: `pipeline-run-node-label`, `pipeline-run-details-panel`, `pipeline-run-details-header`, `pipeline-run-details-status-badge` (+`data-status`), `pipeline-run-details-timeline-section` | **on-`main`** — added by ELITEA-2450, already merged. Already wired as `PipelineDetailPage` fields/methods (`open_run_details_panel()`, `get_run_details_status()`, etc.) | none needed |
| Timeline-step dot (per index) | `RUN_DETAILS_TIMELINE_STEP.format(index)` → `[data-testid="pipeline-run-details-timeline-step-{}"]` | **on-`main`** — added by ELITEA-2452, already merged (`PipelineDetailPage.select_run_details_timeline_step()` already uses it). This case reads the SAME element's `aria-label` attribute (node id, for step 5) and `data-status` attribute (green/error, for step 4 — **needs-adding**, see below) rather than clicking it. | none needed |
| Timeline-step dot `data-status` (green/error signal) | Same testid as above, NEW attribute: `data-status="{data.status === Error ? 'error' : 'completed'}"` mirroring the existing `isError` prop already passed into `ProcessStepIcon` | **needs-adding.** Source: `ProcessStepIcon.jsx` — the `isError` boolean already exists as a prop (drives `innerBox`/`outerBox` color), just isn't exposed as a DOM attribute. Mirrors the exact `pipeline-run-details-status-badge`'s `data-status` pattern (`.agents/testing.md` "testid = stable identity; state via `data-*`" ruling) — avoids any CSS-color-literal assertion. | interim only, exploration-only: `to_have_css("background-color", "rgb(...)")` on the SAME testid locator (fragile to theme changes — do not ship; used only to visually confirm "green" this session, screenshot above) |
| Timeline-step dot `aria-label` attribute (hover node-id) | Same testid as above — `get_attribute("aria-label")`, no new handle | **on-`main`**, pre-existing MUI `Tooltip` mechanism (confirmed via `outerHTML` read: `aria-label="LLM1"` static on the dot; NOT `title` — reading an ATTRIBUTE of an already-testid-located element, not using it AS a locator) | none needed |
| Per-step timestamp (`HH:mm:ss` text, sibling of the dot inside the same `Step`) | `testid needed: pipeline-run-details-timeline-timestamp-{index}` (dynamic, UPPER_CASE template constant: `RUN_DETAILS_TIMELINE_TIMESTAMP = '[data-testid="pipeline-run-details-timeline-timestamp-{}"]'`) | **needs-adding.** Source: `RunStateDialog.jsx:285-290` — the `Typography` rendering `format(new Date(step.created_at), 'HH:mm:ss')` has zero testid/aria-label; it is a plain sibling of `ProcessStepIcon` inside each `Step`. Use `index` (already the same index the dot's testid uses) so the two stay correlated 1:1. | none needed |
| Timeline entry count (total dots) | NEW UPPER_CASE prefix constant: `RUN_DETAILS_TIMELINE_STEP_PREFIX = '[data-testid^="pipeline-run-details-timeline-step-"]'`, `.count()` on it | **No new testid needed** — same mechanism as the pre-existing `CHAT_ATTACHMENT_CHIP_PREFIX` precedent (`pipeline_detail_page.py`), just a new prefix-selector constant over the ALREADY-EXISTING per-index dot testid. Confirmed live: exactly 3 matches for a 3-node completed run. | none needed |

## Network Behavior
Same as ELITEA-2450/2452/2453: pipeline execution and all Run Details data
(timeline, states) arrive entirely over Socket.IO (`useRunEvent.hooks.js`) — no
dedicated REST endpoint returns run/timeline/state data. Not re-verified via
`browser_network_requests` this session (established, unchanged pattern across
all four sibling AFS's); automation must wait on the DOM
(`wait_for_embedded_chat_response()`), never poll an endpoint for timeline data.

## Known Defects Found During Exploration

**No new product bug.** The already-filed `EliteaAI/elitea-testing-public#1267`
(Timeline Stepper prop-leak console warning) reproduces identically for this
case's 3-node pipeline too (same stack trace through `RunStateDialog.jsx`'s
`Stepper`/`ProcessConnector`) — same known signature, not a new occurrence to file.

**One case-text CLARIFICATION filed**: `EliteaAI/elitea-testing-public#1375` —
covers step 7's "top to bottom" wording; live layout is left-to-right. Dedup
checked against the existing `question`/`bug` issue list before filing (keyword
search on "timeline"/"2451"/"top to bottom") — no existing issue covered this,
so it's a new, non-duplicate filing.

**Cross-reference (not re-verified live this session, informational only)**:
the ELITEA-2453 sibling AFS found that a `structured_output: true` LLM node
produces TWO timeline entries per execution instead of one — this case's own
step 8 assertion ("entries == executed nodes") would be FALSE against that
fixture shape. This AFS's precondition explicitly avoids structured output for
exactly this reason; the implementer must not swap in a structured-output
fixture without re-deriving the expected entry count.

## Blocked Steps

None. All 8 case steps were executed to completion against the live local
environment (pipeline id 8767, `afs_2451_probe2`, deleted at session end;
an earlier probe pipeline, id 8766, `afs_2451_probe`, used a Printer node
that paused mid-run awaiting acknowledgement — deleted, not reused, since it
never reached `Completed` status needed for this case).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **Testid gaps this case needs before implementation**: run `add-data-testid`
  for exactly 2 changes in `RunStateDialog.jsx`/`ProcessStepIcon.jsx`:
  1. Add `data-status` to `ProcessStepIcon.jsx`'s outer `Box` (already has the
     `pipeline-run-details-timeline-step-{index}` testid) mirroring the
     existing `isError` prop — `"error"` or `"completed"`.
  2. Add `data-testid="pipeline-run-details-timeline-timestamp-{index}"` to
     the sibling `Typography` rendering the `HH:mm:ss` timestamp
     (`RunStateDialog.jsx:285-290`).
  No new testid is needed for the dot itself, the hover node-id (read via
  existing `aria-label` attribute), or the entry count (new prefix-selector
  constant over the existing per-index testid) — see Concrete Handles.
- **Recommended new fixture**: no existing fixture provides exactly "3+ plain
  (non-structured-output) nodes, all `Completed`". Add a
  `build_three_llm_chain_nodes()` helper (mirrors the existing
  `_llm_node_dict()`/`build_delete_node_pipeline_nodes()` pattern in
  `automation/fixtures/data_fixtures.py`) using the exact YAML proven live in
  this AFS's Preconditions section, plus a `pipeline_three_llm_chain` fixture
  wrapping it (create via `PipelineAPI.create_pipeline_with_nodes()`, delete
  in teardown) — same shape as `pipeline_llm_code_end`/`hitl_runtime_pipeline`.
- **Reuse `send_message_in_embedded_chat()` + `wait_for_embedded_chat_response()`
  + `open_run_details_panel()`** — all already exist and are green
  (`test_pipeline_execution.py`, `test_pipeline_run_details_panel.py`). No new
  execution/open-panel code needed.
- **Do NOT assert dot color via a literal CSS color value** — use the new
  `data-status` attribute (mirrors the `pipeline-run-details-status-badge`
  pattern) instead; this keeps the assertion theme-change-proof and consistent
  with the project's "testid = identity, state = data-*" locator ruling.
- **Order assertion**: iterate `RUN_DETAILS_TIMELINE_STEP_PREFIX` matches in DOM
  order, read each entry's timestamp (parse `HH:mm:ss`), and assert the
  sequence is non-decreasing — this proves "execution order" without relying on
  the (clarified-wrong) top-to-bottom axis or on brittle pixel coordinates.
- `_surface.md` updated this session with a new subsection on the Timeline
  Stepper's per-step handles (dot aria-label attribute, needed timestamp testid,
  needed data-status attribute, count-prefix constant) under the existing
  Run Details panel entry.
