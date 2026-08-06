# Test Case: Run Details — State Before/After per Node

## Metadata
- **TMS ID**: ELITEA-2452
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case; project convention
  maps medium → `@pytest.mark.p2`, matching the sibling case ELITEA-2450's own AFS)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-06
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed
  envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline with **2+ nodes and 2+ state variables** exists and is open in Flow
  view, where at least one node's execution actually MODIFIES a state variable
  (writes to it via its `output` mapping) and at least one variable is left
  untouched throughout. Satisfied via `PipelineAPI.create_pipeline_with_nodes()`
  (`automation/api/client.py`) — confirmed live this session with a fresh
  2-node pipeline (id 7681, deleted at session end):
  ```yaml
  entry_point: LLM 1
  nodes:
    - id: LLM 1
      type: llm
      output: [messages]        # LLM 1 WRITES to `messages`
      transition: LLM 2
      # ... system/task/chat_history input_mapping (see Test Data)
    - id: LLM 2
      type: llm
      input: [messages]
      output: []                 # LLM 2 writes to NOTHING
      transition: END
  ```
  This pipeline's two DEFAULT state variables (`input`, `messages` — no custom
  variable needed for the base case) already exercise both required
  observables: `messages` is modified by LLM 1 (not by LLM 2); `input` is
  populated once (at the pipeline's entry, during LLM 1's step — see step 6
  clarification below) and never modified again (unchanged at LLM 2).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A 2-node LLM→LLM→END pipeline via `PipelineAPI.create_pipeline_with_nodes()`
  (new fixture recommended — see Automation Hints; no existing fixture has 2+
  nodes). LLM 1: `system` (Fixed) = `"You are a helpful assistant."`, `task`
  (F-String) = `"User asked: {input}"`, `chat_history` (Fixed) = `[]`,
  `output: [messages]`. LLM 2: `system` (Fixed) = `"Reply with just OK."`,
  `task` (F-String) = `"Ack: {messages}"`, `chat_history` (Fixed) = `[]`,
  `input: [messages]`, `output: []`.
- Chat message sent: any short prompt (this session used
  `"Say hello in exactly three words."`) — content is irrelevant to the
  assertions; only "the LLM produced SOME non-empty text" matters.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project
  was "Private" (id 399), matching `.env.test`.

## Test Steps

1. Execute a pipeline with 2+ state variables and 2+ nodes, where one node
   writes to a variable and the other does not (the fixture pipeline above).
   **Expected**: pipeline executes without error; a `"Run 1 details"`
   indicator appears above the Flow canvas (`RunStateNode`, reused
   mechanism from ELITEA-2450), status transitions to `"Completed"`.
   Confirmed live: run completed with timeline `[LLM1 @ 20:15:21, LLM2 @
   20:15:23]`.
2. Open Run Details (click the run's label,
   `[data-testid="pipeline-run-node-label"]` — existing from ELITEA-2450).
   **Expected**: panel opens (`role="dialog"`, `[data-testid="pipeline-run-details-panel"]`).
   Confirmed live. **Default selected timeline step on open is the LAST
   step** (`LLM2` for this 2-node pipeline) — confirmed live via the
   `"Timeline step:"` label reading `LLM2` immediately on open, before any
   stepper click. Source-verified: `RunStateDialog.jsx`'s `selectedStep`
   state initializes to `0`... **actually reads the OPPOSITE on a completed
   run** — see Coverage Map CLARIFICATION for step 3 below; the useEffect at
   `RunStateDialog.jsx:184-189` only auto-advances `selectedStep` while
   `status === InProgress`, but this session observed `LLM2` selected
   immediately for an already-`Completed` run. Confirmed via 2 independent
   live executions (pipeline 7681 and 7682) — both landed on the LAST
   timeline entry on open, not index 0. Automation should NOT assume
   `selectedStep === 0` on open; assert whichever step is highlighted
   (`Timeline step:` text) matches the LAST timeline entry's node id for a
   `Completed` run, or explicitly click the desired step before asserting
   Before/After (this AFS's own steps 3-5 do the latter, which is robust to
   either behavior).
3. Click on a timeline step (node) to select it — click the FIRST step
   (`LLM1`, the one whose node execution wrote to `messages`).
   **Expected**: `"Timeline step:"` label updates to `LLM1`; the States
   section's Before/After values update to reflect this step. Confirmed
   live: clicking the first stepper dot (accessible name = the node id,
   `"LLM1"`, via `StyledTooltip`) updated the label and the state values.
4. In the STATES section, verify all pipeline state variables appear as
   expandable accordion rows.
   **Expected**: one row per state variable — confirmed live: `input`,
   `messages` (2 rows for this pipeline's default variables; a
   custom-variable pipeline would show 3+). The FIRST row (`input`, list
   index 0) is auto-expanded on render (`defaultExpanded={!index}`,
   source-verified `RunStateDialog.jsx:482`); subsequent rows start
   collapsed and require a click to expand.
5. Click the expand (accordion header) control on the `messages` row (index
   1, starts collapsed).
   **Expected**: row expands, revealing a Before/After sub-view. Confirmed
   live (clicked the `messages` accordion header — the row's own
   `paragraph` text acts as the click target inside a `role="button"`
   `heading`).
6. Verify two columns/boxes appear: `"Before"` (value entering the node) and
   `"After"` (value leaving the node).
   **Expected — confirmed live, exact match**: both `messages` and `input`
   rows show a `"Before"` label + value box and an `"After"` label + value
   box side by side (`StateItemView` component). For `LLM1` (the FIRST
   executed step): `input` Before = `""`, After = `"Say hello in exactly
   three words."` — **CLARIFICATION**: the case's step 8 implies the node
   ITSELF must have written the value for Before≠After to occur, but
   `input` is never referenced in LLM 1's `input`/`output` mapping (both
   empty/unset for this variable) — its value transition happens because
   `input` is the pipeline's chat-message variable, populated automatically
   at pipeline entry, concurrently with the first node's execution, not
   because LLM 1 explicitly wrote to it. Both the case's step 7 and step 8
   are satisfiable using DEFAULT variables without a custom one, but the
   causal story for `input`'s "modification" at the first node is "entry
   population", not "node output mapping" — noted here so the implementer
   doesn't over-claim "LLM 1's output mapping caused this" in a comment.
7. For a variable NOT modified by the selected node, verify Before and After
   show the same value — select the `LLM2` timeline step
   (`input` is not referenced by LLM 2 at all).
   **Expected — confirmed live, exact match**: at step `LLM2`, `input`
   Before = After = `"Say hello in exactly three words."` (both quote the
   identical string). This is the case's step 7 satisfied cleanly, using a
   NON-FIRST timeline step (see Known Defects below for why the FIRST step
   is NOT a safe choice for this assertion when a variable carries a
   non-empty pre-existing value).
8. For a variable modified by the selected node, verify After differs from
   Before — select the `LLM1` timeline step, `messages` row.
   **Expected — confirmed live, exact match**: at step `LLM1`, `messages`
   Before = `""` (empty — no prior run history), After = a JSON-encoded
   array of 2 LangChain message objects (`"[...content='User asked: Say
   hello...' ...]"`, `"...content='Hello to you!' ..."`) — i.e. LLM 1's
   `output: [messages]` mapping wrote the LLM's response into the variable,
   confirmed differing values.
9. Click the expand/fullscreen button on a Before or After value box —
   verify the long value displays in full.
   **Expected — confirmed live, exact match**: clicking the fullscreen icon
   (`FullscreenOutlinedIcon`, `StateItemViewHeader`'s `IconButton`) next to
   either the `messages` row's Before or After value opens a SECOND,
   separate `role="dialog"` modal (`PipelineStateViewModal.jsx`) with a
   heading showing the variable name and the FULL, unclipped
   `JSON.stringify`'d value as body text, plus its own close (X) icon.
   Confirmed live: clicked the After-value expand icon for `messages`;
   modal opened showing the complete 2-message JSON array (matches the
   truncated-in-the-row content exactly, just not clipped by the row's
   `maxHeight: 7.9375rem` / `overflow: auto` CSS). **CLARIFICATION (see
   Known Defects)**: the modal's heading shows ONLY the variable name
   (`"messages"`), not which direction (Before/After) was expanded — this
   AFS does not require the implementer to assert a Before/After
   distinction in the modal, only that the FULL value text is present and
   matches the row's own (un-clipped) value.

## Expected Final State
The Run Details panel, opened on a 2+-node, 2+-variable pipeline run, shows
per-variable accordion rows in the STATES section; selecting a timeline step
updates each row's Before/After values; an unmodified variable shows
identical Before/After at a given step, a modified variable shows differing
values; each value's fullscreen icon opens a modal showing the complete,
unclipped value.

## Coverage Map

### Axis 1 — Case elements → live behavior

| Case element | Expected result (case text) | Covered by (this AFS) | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Execute a pipeline with 2+ state variables and 2+ nodes | Completes without error | Step 1 (fixture pipeline: LLM 1→LLM 2→END, `input`/`messages`) | Step 1 | covered |
| Step 2: Open Run Details | Panel loads | Step 2 | Step 2 | covered — **NOTE**: default-selected timeline step on open is the LAST step, not necessarily the first; see step 2's expected-result note. Not asserted as a case requirement (case doesn't specify default selection), but documented so the implementer doesn't assume index 0. |
| Step 3: Click a timeline step to select it | Control responds; next state shown | Step 3 (click `LLM1`) | Step 3 | covered |
| Step 4: STATES section shows all pipeline state variables as expandable rows | Action completes, UI state shown | Step 4 | Step 4 | covered |
| Step 5: Click expand button on a state variable row | Control responds | Step 5 (`messages` row) | Step 5 | covered |
| Step 6: Two columns Before/After appear | Condition holds | Step 6 | Step 6 | covered — **CLARIFICATION**: `input`'s "modification" at the first node comes from pipeline-entry population, not the node's own output mapping (see step 6 note); doesn't contradict the case, just documents causality precisely for the implementer. |
| Step 7: Unmodified variable — Before = After | Action completes | Step 7 (`input` @ `LLM2`) | Step 7 | covered |
| Step 8: Modified variable — After ≠ Before | Action completes | Step 8 (`messages` @ `LLM1`) | Step 8 | covered |
| Step 9: Expand/fullscreen button — long value displays in full | Control responds | Step 9 (`messages` After value @ `LLM1`) | Step 9 | covered — **CLARIFICATION**: fullscreen modal heading doesn't distinguish Before vs After (case doesn't require it either — not a defect against case text). |

### Axis 2 — Assertions beyond the case

| Extra observable | Grounded reason |
|---|---|
| **KNOWN DEFECT (filed `EliteaAI/elitea-testing-public#1271`)**: at the FIRST timeline step (`selectedStep === 0`), the panel's "Before" value is a hardcoded `''`, NOT the variable's actual pre-run value — confirmed both via source (`RunStateDialog.jsx`'s ternary) and live repro (a pipeline seeded with a non-empty default `seed_var` showed Before=`""`/After=`"PRESET_DEFAULT_VALUE"` for a variable the first node never touched). This AFS's own step 7 assertion (Before=After for an unmodified variable) deliberately uses the SECOND step (`LLM2`), not the first, to avoid tripping this defect — automation must do the same: **never assert step-7-style "unmodified ⇒ Before=After" using the pipeline's FIRST timeline step**, only a later one. | `.agents/testing.md` "no defect masking" — the defect is real, filed, and this AFS routes around it via a legitimate alternate path (a later timeline step) rather than asserting broken behavior as correct or skipping the step. |
| Zero unexpected console errors during navigate→execute→open-panel→select-step→expand-row→fullscreen, EXCEPT the known `EliteaAI/elitea-testing-public#1267` Stepper prop-leak warning (same signature as ELITEA-2450, reproduced again this session) | `.agents/testing.md` "check console even when UI looks fine" discipline; scope the assertion to exclude this one known, filed, deterministic warning signature. |
| Closing the fullscreen value modal returns focus to the underlying Run Details panel (panel stays open, only the value modal closes) | Cheap smoke of the modal's close affordance — the case's own "verify long values display in full" step implies a working modal, and confirming it's dismissible (without accidentally closing the WHOLE Run Details panel) is a natural extension, not a separate case. |

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Run node clickable label (opens panel) | `[data-testid="pipeline-run-node-label"]` | **on-`automation/testids` only** (awaiting human promotion to `main`) — confirmed via fresh `git fetch origin` + `git grep`, added by ELITEA-2450, reused unmodified. | none needed |
| Run Details panel root | `[data-testid="pipeline-run-details-panel"]` | **on-`automation/testids` only** — from ELITEA-2450, reused unmodified. | none needed |
| Timeline step selector (per index) | `testid needed: pipeline-run-details-timeline-step-{index}` (dynamic, UPPER_CASE template constant, e.g. `PIPELINE_RUN_DETAILS_TIMELINE_STEP = '[data-testid="pipeline-run-details-timeline-step-{}"]'`) | **needs-adding.** Source: `RunStateDialog.jsx:404-410` — `ProcessStepIcon`'s outer `Box onClick={onClick}` has zero testid/aria-label; the only existing handle is the `StyledTooltip`'s `title={step.id}` (accessible name = node id — usable as an EXPLORATION-ONLY interim, but per this project's testid-only policy the real locator must be added). Use `index` (already threaded as a prop) rather than node id, since a looped pipeline could revisit the same node id more than once in one timeline. | interim only, exploration-only: `page.get_by_label(node_id)` scoped inside the panel — NOT testid-compliant, do not ship |
| State variable accordion row (name + expand toggle) | `testid needed: pipeline-run-details-state-row-{variable}` (dynamic template) | **needs-adding, LOW-EFFORT** — `BasicAccordion.jsx` (`src/[fsd]/shared/ui/accordion/BasicAccordion.jsx`) ALREADY supports this: `items[].testId` is threaded straight to `StyledAccordionSummary`'s `data-testid` (line 67). `RunStateDialog.jsx`'s `items={[{title: variable, content: ..., testId: ...}]}` (line ~467) just needs one added key: `testId: `pipeline-run-details-state-row-${variable}``. No new plumbing in the shared component — this is the canonical dynamic-testid pattern already in place, just unused by this caller. | none needed |
| Before value box (per variable) | `testid needed: pipeline-run-details-state-value-before-{variable}` (dynamic) | **needs-adding.** Source: `StateItemView`'s `Box sx={styles.valueBox}>{JSON.stringify(valueBefore)}</Box>` (line ~93) — needs a new `beforeTestId`/`afterTestId` prop pair threaded from the caller (`RunStateDialog.jsx`'s `<StateItemView name={variable} .../>` call, line ~471), computed as `pipeline-run-details-state-value-before-${variable}` / `-after-${variable}`. | none needed |
| After value box (per variable) | `testid needed: pipeline-run-details-state-value-after-{variable}` (dynamic) | same as above | none needed |
| Before value's fullscreen/expand icon button | `testid needed: pipeline-run-details-state-expand-before-{variable}` (dynamic) | **needs-adding.** Source: `StateItemViewHeader`'s `IconButton onClick={onFullScreen}` (line ~59) — `StateItemView` calls `StateItemViewHeader` TWICE (once `title="Before"`, once `title="After"`), so each call needs its own `testId` prop threaded through (new prop on `StateItemViewHeader`, e.g. `testId`). | none needed |
| After value's fullscreen/expand icon button | `testid needed: pipeline-run-details-state-expand-after-{variable}` (dynamic) | same as above | none needed |
| Fullscreen value modal root | `testid needed: pipeline-run-details-value-modal` | **needs-adding.** Source: `PipelineStateViewModal.jsx` (`src/components/PipelineStateViewModal.jsx`) — `Dialog`/`DialogContent`, zero testids anywhere in the component. Only consumer is `RunStateDialog.jsx`, so a feature-scoped literal testid is fine (not a cross-feature shared component in practice, despite living under `src/components/`). | interim only, exploration-only: `page.get_by_role("dialog").last` — NOT testid-compliant |
| Fullscreen value modal heading (variable name) | `testid needed: pipeline-run-details-value-modal-header` | **needs-adding.** Source: `DialogTitle` in `PipelineStateViewModal.jsx`, renders `{label}` (the variable name only — see step 9 CLARIFICATION, no Before/After distinction). | none needed |
| Fullscreen value modal close button | `testid needed: pipeline-run-details-value-modal-close-button` | **needs-adding.** Source: `PipelineStateViewModal.jsx`'s `IconButton onClick={onClose}` inside the `DialogTitle`. | none needed |
| Fullscreen value modal content (full value text) | `testid needed: pipeline-run-details-value-modal-content` | **needs-adding.** Source: `DialogContent` rendering `{JSON.stringify(value)}` — this is what step 9 asserts ("long values display in full"). | none needed |

## Network Behavior
- Same as ELITEA-2450: pipeline execution and all Run Details data (timeline,
  per-step state snapshots) arrive entirely over Socket.IO — confirmed via
  `browser_network_requests` on both probe sessions (only
  `socket.io/?EIO=4…` polling exchanges around send/response; no dedicated
  REST endpoint for timeline/state). Selecting a different timeline step or
  expanding a state row/fullscreen modal is **pure client-side re-render**
  from data already delivered — no new network activity on step-select,
  row-expand, or fullscreen-open (confirmed: `browser_network_requests`
  showed no new entries after the initial run-completion exchange, across
  all of steps 3-9 in this session).

## Known Defects Found During Exploration

**One CONFIRMED product defect, filed**: `EliteaAI/elitea-testing-public#1271` —
`RunStateDialog.jsx`'s Before-value computation for the FIRST timeline step
(`selectedStep === 0`) is hardcoded to the literal `''`, never reading the
variable's actual pre-run value (e.g. a non-empty default configured via the
STATE panel). Confirmed via source AND a live repro (pipeline id 7682,
deleted at session end): a `seed_var` with default `'PRESET_DEFAULT_VALUE'`,
untouched by the only node, showed Before=`""`/After=`"PRESET_DEFAULT_VALUE"`
at that node's (first and only) step — a false "modified" read for a variable
the node never wrote to. **Automation impact**: this AFS's step 7 (unmodified
⇒ Before=After) deliberately targets the SECOND timeline step (`LLM2`), not
the first, to avoid the defect; do not "fix" this by using a
non-empty-default-seeded variable at the FIRST step and asserting the (wrong)
observed behavior as correct.

**One informational note, NOT filed as its own ticket** (doesn't contradict
any case assertion, judgment call left to the lead): the fullscreen value
modal's heading shows only the variable name, not whether the Before or
After value was expanded. Left as a documented AFS note (step 9
CLARIFICATION) rather than a ticket, since the case text never claims the
modal should distinguish direction — flagging in the run's findings for the
lead to decide if worth a UX ticket.

## Blocked Steps

None. All 9 case steps were executed to completion against the live local
environment across two probe pipelines (ids 7681, 7682 — both deleted via
`PipelineAPI.delete_pipeline()` at session end).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **New fixture needed**: no existing fixture builds a 2-node LLM→LLM→END
  pipeline. Recommend `pipeline_with_two_llm_nodes_id` (or similar) in
  `automation/fixtures/data_fixtures.py`, built via
  `PipelineAPI.create_pipeline_with_nodes()` (already exists, generic) with
  the exact node dicts in this AFS's § Test Data — mirrors
  `pipeline_with_llm_id`'s create/yield/delete pattern.
- **Testid gaps this case needs before implementation** — 9 new testids
  total (see Concrete Handles): 1 timeline-step selector (dynamic by
  index), 1 state-row accordion header (dynamic by variable — LOW EFFORT,
  `BasicAccordion` already supports it), 2 value boxes (dynamic,
  before/after × variable), 2 value-expand icon buttons (dynamic,
  before/after × variable), 3 for the fullscreen value modal (root, header,
  close button, content — actually 4, see table). Run `add-data-testid` for
  all before writing the test.
- **Reuse ELITEA-2450's existing testids/methods** unmodified:
  `pipeline-run-node-label`, `pipeline-run-details-panel`,
  `pipeline-run-details-timeline-section`, `pipeline-run-details-states-section`,
  and `PipelineDetailPage.open_run_details_panel()` /
  `wait_for_embedded_chat_response()` / `send_message_in_embedded_chat()`.
- **Do NOT assert `selectedStep === 0` (first timeline step) is selected on
  panel open** — this session observed the LAST step selected immediately
  for a `Completed` run, on 2 independent executions. Explicitly click the
  desired timeline step before asserting Before/After (this AFS's steps 3+5
  already do this).
- **Do NOT use the FIRST timeline step for a "Before=After, unmodified"
  assertion** — hits the known defect `#1271`. Use a later step (this AFS
  uses the SECOND of 2 nodes).
- **Wait discipline**: same as ELITEA-2450 — wait on
  `wait_for_embedded_chat_response()`, never a fixed sleep. Step-select /
  row-expand / fullscreen-open are synchronous client-side re-renders (no
  network wait needed per this session's `browser_network_requests` check),
  but a `expect(locator).to_be_visible()` after each click is still the
  correct wait mechanism (state updates via React, not guaranteed
  synchronous with the click event in a real browser).
- `_surface.md` updated this session — see the Run Details panel section
  amended with the accordion `defaultExpanded={!index}` behavior, the
  `selectedStep` default-selection-on-open observation, the Socket.IO-only
  step-select/expand confirmation, and the `#1271` defect.
