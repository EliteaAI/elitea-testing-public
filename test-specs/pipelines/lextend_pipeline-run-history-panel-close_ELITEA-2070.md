# Test Case: Pipeline — Run History Panel (open, view, detail, close)

## Metadata
- **TMS ID**: ELITEA-2070
- **Linked Story**: none
- **Priority**: l2 (high, as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: localhost dev auth (`auth_state` / `VITE_DEV_TOKEN`) — no explicit
  `${TEST_USER}` needed
- **Analyst**: qa-engineer (analyst slot), batch `pipelines-remaining-w7`
- **Status**: extend-existing

## Repair amendment — 2026-09-09 (FIX card #2063, red on DEV)

> **Everything below this section that describes a Run History *panel* with an `X`
> close button is SUPERSEDED by this amendment.** The product changed; the case's
> observable did not. Sections § Test Steps step 4, § Concrete Handles (close-button
> row), § Network Behavior and § Coverage Map row 7 are re-stated here and this
> version wins.

**Environment explored for the repair:** BOTH `https://dev.elitea.ai/app` (the card's
declared environment, harness-driven) and `http://localhost:5173` — behaviour is
**identical on both**; the earlier "passes on localhost" premise is stale.

**What changed in the product.** `EliteaAI/EliteaUI` commit `90e20a03`
(*feat: [EL-6537] Integrate Agent and Pipeline Run History into Breadcrumb
Navigation*, on `main` 2026-09-07, and an ancestor of `origin/automation/testids`)
turned the inline Run History panel into a **dedicated route**:

- `src/pages/Pipelines/Components/ConfigurationTab.jsx:359` now wires
  `onShowHistory={applicationId ? goToRunHistory : undefined}` — clicking
  `pipeline-history-tab` **navigates** to `/pipelines/:tab/:agentId/history`
  (`src/routes.js:29`) instead of flipping a local `showHistory` state.
- That route renders `src/[fsd]/pages/shared/RunHistoryPage.jsx`, which does **not**
  pass an `onClose` prop to `RunHistoryContainer`.
- `RunHistoryContainer.jsx:164` renders the close button only inside
  `{onClose && (...)}` — so `run-history-close-button` **never mounts** on the
  Agent or Pipeline surface any more (the testid still exists in the source; it is
  unreachable). No caller anywhere in `src/` passes `onClose`.

**The replacement affordance** is the breadcrumb header the new page renders:
`Pipelines / <pipeline name> / Run History` — clicking the `<pipeline name>` crumb
returns to the pipeline detail view. Verified live on localhost 2026-09-09:

| Observation | Value (live) |
|---|---|
| URL on pipeline detail | `…/pipelines/all/10369?viewMode=owner&name=…` |
| URL after clicking `pipeline-history-tab` | `…/pipelines/all/10369/history?viewMode=owner&name=…` |
| `run-history-close-button` count on that view | **0** (DEV and localhost) |
| `chat-message-input` / `pipeline-history-tab` count while History is open | **0 / 0** (different route) |
| breadcrumb link crumbs (`breadcrumb-item`) | `['Pipelines', '<pipeline name>']` |
| breadcrumb current (`breadcrumb-current`) | `'Run History'` |
| URL after clicking the last `breadcrumb-item` | back to `…/pipelines/all/10369?viewMode=owner&name=…` |
| after return | `chat-message-input` visible, `pipeline-history-tab` visible, `run-history-list-item` count = **0** |
| conversation requests fired by the return | **none** (`/conversation(s)/prompt_lib` zero hits) |
| console errors across the whole flow | **none** |

### Amended step 4 (the case's step 7 — "Close run history panel / Panel closes")

Click the **last `breadcrumb-item`** (the pipeline-name crumb; the trail is
`Pipelines / <name> / Run History`, only the last entry is `breadcrumb-current`).
**Expected:** the Run History view is left — `run-history-list-item` count returns to
0 — and the pipeline detail view is restored (`chat-message-input` and
`pipeline-history-tab` visible again), with no `conversation(s)/prompt_lib` re-fetch.

### Amended § Concrete Handles rows

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| ~~Run History panel close (X)~~ | **REMOVED — no longer rendered** (`RunHistoryContainer.jsx:164` `{onClose && …}`, no caller passes `onClose`) | testid string still on `origin/main`, but unreachable at runtime | n/a |
| Breadcrumb link crumbs (return affordance) | class constant `'[data-testid="breadcrumb-item"]'`, positional `.last` (= the pipeline-name crumb) | **on-main ✓** (`git fetch origin` + `git grep` 2026-09-09: `breadcrumb-item` YES on `origin/main` and `origin/automation/testids`) — `BreadcrumbItem.jsx:30` | none — testid only |
| Breadcrumb current crumb (Run-History-view marker) | class constant `'[data-testid="breadcrumb-current"]'` (text `Run History`) | **on-main ✓** — `BreadcrumbItem.jsx:17` | none — testid only |

No new testid is needed for this repair.

### Amended § Network Behavior

- Opening Run History now also **auto-selects the newest run** (`RunHistoryContainer.jsx:93-96`,
  added by `84025881` *fix: [EL-6391] select the latest run when Run History opens*,
  2026-08-26). Live capture on DEV, immediately after the list rendered:
  `GET /elitea_core/conversations/prompt_lib/399?source=pipeline&…`,
  `GET /elitea_core/conversation/prompt_lib/399/9947`,
  `GET /elitea_core/message_traces/prompt_lib/399/9947?...` — i.e. the conversation
  **detail** GET fires on OPEN, before any row is clicked.
- Consequence for `select_run_history_item(0)`: row 0 already carries
  `data-selected="true"` before the click, and **clicking it fires zero requests**
  (verified live). The endpoint itself is unchanged
  (`/elitea_core/conversation/prompt_lib/{projectId}/{conversationId}` GET,
  `runHistoryApi.js:42`), so the page object's `expect_response` *predicate* is still
  correct — but the *event* it waits for is no longer caused by the click. It only
  passes when the auto-select's own GET happens to land inside the expectation
  window. Wait on selection state + rendered message content instead.
- Returning via the breadcrumb re-fires only the pipeline-detail view-population
  requests (`toolkits`, `index_types`) — **no** `conversation(s)/prompt_lib` refetch.
  The original durable claim survives verbatim.

### Amended § Coverage Map row 7

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 7 Close run history panel | Panel closes | **amended step 4** — leave the Run History route via the pipeline-name breadcrumb crumb | new test's own step | asserted (new) |

The case text says only *"Close run history panel"* / *"Panel closes"* — it never
names an `X` button, so the observable is unchanged and this is **not** case-text
drift on step 7.

### Implementer note — 2026-09-09 (repair shipped, FIX card #2063)

- Step 3's `is_run_history_item_selected(NEWEST_RUN_INDEX)` assertion was **removed**
  from the test: post-`84025881` row 0 is auto-selected on open, so asserting
  `data-selected="true"` on it after clicking it is tautological. The step's real
  observable (the run's own message rendered in the detail pane) is unchanged.
- `select_run_history_item()`'s `expect_response` wrapper was replaced by a state wait
  (`data-selected="true"` on the clicked row + first `chat-message-item` visible), per
  the amended § Network Behavior above. Both values are still produced by the system.
- `PipelineDetailPage.run_history_close_button` (`LocatorDescriptor`) was **deleted** —
  the testid is unreachable at runtime and it had exactly one caller.
- Verified green on BOTH environments, whole file (both this test and ELITEA-2011's):
  localhost 2/2, DEV (`https://dev.elitea.ai/app`) 2/2, zero reruns each. Step 2's wording (*"Run history panel opens"*) is now a page rather
than a panel — cosmetic drift, observable preserved; optional TMS clarification, not
blocking.

### Observation (not asserted, not filed)

Returning from Run History leaves the embedded chat **empty** (`chat-message-item`
count 0) — the live conversation is not restored by plain back-navigation; the
product offers an explicit *restore conversation* affordance in the row menu
(`run-history-menu-menu-button` → `handleRestoreConversation`). Under the old inline
panel the in-memory conversation survived a close. Reads as intended-by-design for a
route change; the case asserts nothing about it, so no assertion is added.

## Covering Spec (dedup / extension proof)

- **Covering spec**: `automation/tests/ui/pipelines/test_pipeline_run_history_view_executions.py`
  (`TestPipelineRunHistoryViewExecutions.test_run_history_panel_lists_and_shows_execution_details`,
  TMS ELITEA-2011), AFS `test-specs/pipelines/l2_pipeline-run-history-panel-view-executions_ELITEA-2011.md`
  — **merged onto this batch's trunk `tests/batch-pipelines-remaining-w7`** (commit `30041066`),
  not yet on `origin/automation/base`. Per the merged-target rule this qualifies `extend-existing`
  (not `already-covered`, which would require a merge to `origin/automation/base`).
- **Behavioural overlap**: ELITEA-2011's test already builds and proves the exact precondition +
  first 6 observables ELITEA-2070 also describes on the same `PipelineDetailPage` surface, same
  shared `ViewRunHistoryButton.jsx` / `RunHistoryContainer.jsx` / `RunHistoryList` /
  `RunHistoryChat` stack:
  1. Open a pipeline that has been executed before → `pipeline_with_llm_id` fixture + `navigate()`.
  2. Click "view run history" icon in the chat panel header → `open_run_history()`
     (`pipeline-history-tab`).
  3. Run history panel opens → asserted (panel content present).
  4. Verify panel is visible → same click, same assertion.
  5. Shows list of past executions with timestamps → `get_run_history_item_texts()` regex-matched
     against `dd-MM-yyyy, hh:mm AM/PM`.
  6. Click a specific execution entry → execution details displayed (input message + output
     response) → `select_run_history_item()` + `get_run_history_chat_messages_text()`.

  Confirmed live this session on a **different, real-data probe pipeline**
  (`AutoTest_Pipeline_probe_2020`, id `8056`, project `399`) — not a re-run of ELITEA-2011's own
  fixture-backed test, but an independent live check that the same shared component behaves
  identically outside the disposable-pipeline fixture path: sent one embedded-chat message
  (`ELITEA-2070 probe message`), opened Run History, saw exactly one row
  (`09-08-2026, 01:05 PM` / `base` / `1.42 s`), clicked it, saw the Test Bot's message + the
  pipeline's response rendered in the same panel. Zero console errors throughout.

- **The gap**: ELITEA-2011's test never clicks the close (`X`) button — it leaves the Run History
  panel open at the end of its last `allure.step`. ELITEA-2070's own case text adds this as an
  explicit numbered step (step 7: "Close run history panel" / "Panel closes") that ELITEA-2011
  does not assert. **This is the entire gap** — everything else in ELITEA-2070's steps 1–6 is a
  strict subset of what ELITEA-2011 already proves on the identical shared component and page
  object methods.
- **Extension shape**: add a **new test function** to the same file
  (`test_pipeline_run_history_view_executions.py`), reusing the `pipeline_with_llm_id` fixture and
  the same `open_run_history()` / `get_run_history_item_count()` / `select_run_history_item()` /
  `get_run_history_chat_messages_text()` helpers ELITEA-2011 already proved — plus ONE new
  page-object method, `close_run_history()`, and ONE new testid (see § Concrete Handles — none
  exists yet; ELITEA-2011 explicitly declined to request one since its own steps never touched the
  close button). Does not modify ELITEA-2011's existing test body.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard
  Keycloak login via `${TEST_USER}`).
- A pipeline that has been executed at least once is open — satisfied via the existing
  `pipeline_with_llm_id` fixture, identical to ELITEA-2011.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline with one LLM node via the `pipeline_with_llm_id` fixture (already exists, already
  used unmodified by ELITEA-2011's own test and `test_pipeline_execution.py`).
- One message sent through the embedded chat (case only requires "executed at least once" — no
  need for ELITEA-2011's 2-entry Clear-the-chat dance, since this extension's own new assertion
  (close) doesn't depend on entry count).

## Test Steps

1. Navigate to a pipeline with a runnable LLM node (`pipeline_with_llm_id` fixture +
   `PipelineDetailPage.navigate(pipeline_id)`), send one message via
   `send_message_in_embedded_chat()`, and wait for the AI response
   (`wait_for_embedded_chat_response()`).
   **Expected**: one execution now exists server-side. *(Covered by ELITEA-2011's own steps 1–2 —
   not re-asserted here beyond confirming a response arrived; this extension's own new
   observable is step 4 below.)*
2. Click the "view run history" icon button (`pipeline-history-tab` / `open_run_history()`).
   **Expected**: Run History panel opens, replacing the Configuration form + embedded chat.
   *(Covered by ELITEA-2011's steps 3–4 — reused verbatim, not re-asserted.)*
3. Click the one execution entry.
   **Expected**: the row shows `data-selected="true"` and the right-hand content renders that
   execution's message + response. *(Covered by ELITEA-2011's step 6 — reused verbatim.)*
4. Click the close (`X`) button (`aria-label="close run history"` — see § Concrete Handles for
   the new testid this step requires).
   **Expected — confirmed live this session, twice (once on an empty-history pipeline, once after
   selecting a populated entry)**: the Run History panel is removed from the DOM and the
   Configuration form + embedded chat (`chat-message-input`, `pipeline-history-tab` again visible)
   is restored. Zero network requests fire on close (purely client-side `onClose` state flip,
   confirmed via source read of `RunHistoryContainer.jsx:74-91`).

## Expected Final State
The Run History panel — already proven reachable and functional by ELITEA-2011 — also closes
correctly via its `X` button, returning the pipeline detail view to the Configuration form +
embedded chat with no residual state or network side effects.

## Pass/Fail Criteria
**Pass**: steps 1–3 pass exactly as ELITEA-2011 already proves; step 4 (close) removes the panel
and restores the chat/config view.
**Fail**: close button missing, unresponsive, or panel/DOM state doesn't revert (e.g.
`chat-message-input` stays absent, or a stale History header remains).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step / covering spec) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline that has been executed before | Pipeline loaded | ELITEA-2011 step 1 (reused) | covering spec | asserted (covering spec) |
| 2 Click "view run history" button | Run history panel opens | ELITEA-2011 steps 3–4 (reused) | covering spec | asserted (covering spec) |
| 3 Verify run history panel opens | Panel visible | ELITEA-2011 step 4 (reused) | covering spec | asserted (covering spec) *(case's own steps 2+3 are one observable, same decomposition ELITEA-2011 already documents for its own steps 3+4)* |
| 4 Verify list of past executions with timestamps | Executions listed with timestamps | ELITEA-2011 step 5 (reused) | covering spec | asserted (covering spec) |
| 5 Click a specific execution entry | Execution details displayed | ELITEA-2011 step 6 (reused) | covering spec | asserted (covering spec) |
| 6 Verify execution details shown (input message, output, status) | Message + response visible | ELITEA-2011 step 6 (reused) | covering spec | asserted (covering spec) *(see Axis 2 — "status" is case-text drift, not asserted as a distinct field)* |
| 7 Close run history panel | Panel closes | **this AFS's step 4 — THE GAP** | new test's own step | asserted (new) |

### Axis 2 — Analyst additions
- **Case-text drift, non-blocking (reverse-masking guard)**: the case's own step 6 expected result
  says execution details show "input message, output response, **and status**." Confirmed live
  this session (both the ELITEA-2011 covering spec's own exploration and this session's own probe
  on `AutoTest_Pipeline_probe_2020`): the Run History detail panel renders the message + response
  content only — there is no separate labelled "status" field anywhere in the row or the detail
  view. An errored execution's response IS visually and textually distinguishable (this session's
  probe pipeline had no nodes configured and its response read `"Pipeline has no nodes to execute.
  Please add at least one node to the pipeline before running it."` with an "Error debugging info"
  disclosure) — so status is inferable from the response content, not exposed as its own element.
  Treat as case-text drift, not a defect: assert message + response content (already proven by the
  covering spec), do not add an assertion for a distinct "status" element that doesn't exist.
  Filed as case-text clarification — see § Known Defects Found During Exploration.
- Zero console errors confirmed live this session across the whole close-flow probe (open →
  populated-entry select → close), on top of ELITEA-2011's own zero-console-errors assertion for
  steps 1–6.
- The close button's behavior was confirmed live in **two** states — an empty Run History (zero
  entries) and a populated one with a selected entry — to make sure `onClose` isn't gated on
  selection state. Both closed cleanly. *Added: the case text doesn't specify whether "close" must
  happen from a particular sub-state; confirming both removes an implicit assumption.*

## Cleanup
1. Pipeline deleted automatically by the `pipeline_with_llm_id` fixture's teardown
   (`pipeline_api.delete_pipeline(pid)`), identical to ELITEA-2011.
2. This session's live probe reused the pre-existing `AutoTest_Pipeline_probe_2020` pipeline
   (id `8056`) — left it with one extra Run History entry (an errored "no nodes" execution from the
   probe message); this is a shared, disposable probe pipeline already accumulating such entries
   from prior sessions (ELITEA-2062's digest entry), so no separate cleanup performed.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| Everything in steps 1–3 | Reuses `PipelineDetailPage`'s existing `chat_input`, `chat_send_button`, `history_tab`, `RUN_HISTORY_LIST_ITEM_SELECTOR`, `RUN_HISTORY_LIST_ITEM_SELECTED_SELECTOR`, `CHAT_MESSAGE_ITEM_SELECTOR` | Identical to ELITEA-2011's own PROVENANCE table — not re-verified here beyond the live probe above | none — testid only |
| Run History panel close (`X`) button | **`testid needed: run-history-close-button`** — no testid exists today, `aria-label="close run history"` only (`RunHistoryContainer.jsx:77-84`, `../EliteaUI/src/[fsd]/entities/run-history/ui/RunHistoryContainer.jsx`). Naming follows the existing shared-component precedent (`run-history-list-item` carries no `pipeline-`/`agent-` prefix because `RunHistoryContainer`/`RunHistoryList` are shared entities serving both the Agent and Pipeline surfaces — same reasoning applies to the close button, which is the SAME `IconButton` regardless of which surface passed `onClose`). | **needs-adding** — confirmed via `git fetch origin` + `git grep -- "close run history" origin/main -- src/` → hit only on the bare `aria-label` string, no `data-testid`; same on `origin/automation/testids`. Neither ELITEA-2011 (Pipeline) nor ELITEA-1877/#1093 (Agent) requested it because neither case's own steps clicked it — ELITEA-2070 is the first dispatched case whose steps do. |

**PROVENANCE freshness:** verified via `cd ../EliteaUI && git fetch origin` + `git grep` against
`origin/main` and `origin/automation/testids`, 2026-08-09.

## Network Behavior
- **Amended during implementation (test run, 2026-08-09)** — the `onClose` handler
  itself (`RunHistoryContainer.jsx:74-91`) is confirmed a pure client-side state
  flip with no fetch call inline. But closing the panel also **unmounts** it and
  **remounts** the Configuration form, which independently re-fires its own
  view-population requests (`upload_icon`, `tags`, `tools` ×2, `toolkits`,
  `applications` ×2, `index_types` — all `prompt_lib/{project}` scoped) as a normal
  consequence of remounting — this is unrelated to Run History and not a defect.
  A blanket "zero network requests on close" assertion is therefore too broad and
  was corrected in the implemented test to the precise, durable claim: closing
  does **not** re-fetch the conversations list (`conversation(s)/prompt_lib`) —
  confirmed zero hits live, matching the intuition that already-loaded/discarded
  Run History data has no reason to be re-read on close.
- Steps 1–3's traffic is identical to ELITEA-2011's own § Network Behavior (`GET
  .../conversations/prompt_lib/...?source=pipeline...` on panel open, `GET
  .../conversation/prompt_lib/{project}/{conversationId}` on row click) — not re-documented here.

## Known Defects Found During Exploration

**No product defects found.** The close button works correctly on the Pipeline surface (same fix
already confirmed for the Agent surface, `EliteaAI/elitea-testing-public#1093`) — confirmed live
twice this session (empty-history and populated-history states).

**Case-text drift (clarification, not a bug)** — case step 6's expected result names a "status"
element that doesn't exist as a distinct UI element in the Run History detail view (see Axis 2
above). Per `.agents/profile.md` § Bug filing, filing as a lightweight `question`-labelled
clarification issue in `EliteaAI/elitea-testing-public`, strict-per-bug, linking ELITEA-2070 and
noting "Found while working #<ELITEA-2070 tracking issue>" — filed by whichever agent owns this
case's tracker card (the analyst slot doesn't have this case's issue number at analysis time; the
finding is recorded here and in the Run Report / findings[] for the orchestrator to file per the
seeded routing).

## Blocked Steps
None. All 7 case steps were executed to completion against the live local environment (pipeline
id 8056, `AutoTest_Pipeline_probe_2020`, this session; steps 1-6 additionally already proven by
the ELITEA-2011 covering spec against `pipeline_with_llm_id`-fixture pipelines).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **One new testid required**: `run-history-close-button` on the `RunHistoryContainer.jsx` close
  `IconButton` (`../EliteaUI/src/[fsd]/entities/run-history/ui/RunHistoryContainer.jsx:77-84`).
  Since this is a shared component consumed by both the Agent and Pipeline surfaces, adding it
  here automatically also gives `AgentDetailPage` a close handle for free — but do NOT add a
  method there unless a dispatched Agent-surface case actually calls it (locator-policy scope
  discipline: testids go only where a dispatched case's steps touch them; the Agent-surface
  `run_history_open_button`'s own comment already documents "no close locator/method exists on
  purpose" for exactly this reason — this AFS does not change that for the Agent page object).
- **Add to `PipelineDetailPage`**: `close_run_history()` — click the new
  `run-history-close-button`, then wait for `chat_input` (or `history_tab`) to be visible again as
  the completion signal (poll, not a fixed sleep, per `.claude/rules/ui-tests.md`).
- **Extend, don't duplicate**: add the new test function to
  `test_pipeline_run_history_view_executions.py`, reusing `pipeline_with_llm_id` +
  `open_run_history()` + `select_run_history_item()` — no need to replicate ELITEA-2011's 2-entry
  `Clear the chat` dance; one entry is enough to prove close works from a "detail selected" state.
- **Sibling-case resolution**: this AFS is the resolution of the "sibling case flag" ELITEA-2011's
  own AFS raised in its Automation Hints — confirmed here as `extend-existing` against ELITEA-2011
  now that ELITEA-2011 is merged onto this batch's trunk (merged-target rule satisfied).
- `_surface.md` updated this session: the existing "Run History panel — Pipeline surface" section
  now notes the close button's testid gap is filled by ELITEA-2070 (not ELITEA-2011), and that the
  sibling-case flag is resolved.
