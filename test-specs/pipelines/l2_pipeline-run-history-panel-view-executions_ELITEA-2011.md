# Test Case: Pipeline Run History — View Executions

## Metadata
- **TMS ID**: ELITEA-2011
- **Linked Story**: none
- **Priority**: l2 (high, as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: localhost dev auth (`auth_state` / `VITE_DEV_TOKEN`) — no explicit
  `${TEST_USER}` needed
- **Analyst**: qa-engineer (analyst slot), batch `pipelines-remaining` wave-07
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A pipeline with a runnable LLM node exists — satisfied via the existing
  `pipeline_with_llm_id` fixture (`automation/fixtures/data_fixtures.py`,
  `PipelineAPI.create_pipeline_with_llm_node()`), reused unmodified.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline with one LLM node via the `pipeline_with_llm_id` fixture (already
  exists, already used unmodified by `automation/tests/ui/pipelines/test_pipeline_execution.py`).
- Two distinct messages sent through the embedded chat, each producing its own
  server-side conversation (a run-history entry) — satisfies the case's "execute
  2-3 times" with the minimum that proves the observable (≥ 2 entries, same
  convention as the sibling agent-surface case ELITEA-1877):
  - Message A (older run): e.g. `f"first-run-{uuid4().hex[:6]}"`
  - Message B (newer/current-active run): e.g. `f"second-run-{uuid4().hex[:6]}"`
  - **Mechanism confirmed live this session** (pipeline id 8759, `autotest_test_probe_run_history`):
    sending Message A creates conversation A server-side. Clicking the embedded
    chat's **Clear the chat** button (`chat-clear-button`) starts a fresh, local,
    unsaved conversation as the new active one — conversation A survives unmodified
    as its own Run History row. Sending Message B then persists conversation B.
    Identical mechanism to ELITEA-1877 (Agent surface) — same shared `ChatBox`
    component, `ChatPanel.jsx` also passes `isAgentsPage={true}`.

## Test Steps

1. Navigate to a pipeline with a runnable LLM node (`pipeline_with_llm_id` fixture +
   `PipelineDetailPage.navigate(pipeline_id)`).
   **Expected**: canvas displayed, embedded chat panel visible on the right.
   Confirmed live (pipeline id 8759).
2. Send Message A via `send_message_in_embedded_chat()`; wait for the AI response
   (`wait_for_embedded_chat_response()`). Click the embedded chat's **Clear the
   chat** button (`chat-clear-button` — see § Known Defects / Automation Hints,
   the EXISTING `clear_embedded_chat()` helper is broken and must not be used
   as-is). Send Message B; wait for its AI response.
   **Expected**: two distinct executions now exist server-side. Confirmed live:
   `RUN_HISTORY_ITEM_COUNT=2` after this sequence (pipeline id 8759).
3. Click the "view run history" icon button (`pipeline-history-tab` — same shared
   `ViewRunHistoryButton.jsx` the Agent surface uses; renders as a bare `ClockIcon`
   `IconButton` once `activeConversation.id` is set, matching the case's "icon
   button" wording exactly).
   **Expected**: Run History panel opens, REPLACING the Configuration form +
   embedded chat entirely (not an overlay/modal) — confirmed live via source
   (`ConfigurationTab.jsx`: `{showHistory && <RunHistoryContainer .../>}` /
   `{!showHistory && (...)}`, mutually exclusive).
4. Verify the run history panel opens (same click as step 3 — the case's steps 3
   and 4 describe one observable, not two; see Coverage Map).
   **Expected**: `run-history-list-item` elements are present and the panel header
   reads "Run History". Confirmed live via screenshot.
5. Verify at least 2 execution entries are listed (case: "2-3+").
   **Expected — confirmed live**: `run-history-list-item` count == 2, each row
   showing Date / Version / Duration columns (e.g. `"09-08-2026, 12:44 PM" / "base" /
   "2.26 s"`) — same 3-column shape ELITEA-1876 already documented for the Agent
   surface (case-text says "execution entries", live product's row content is
   Date+Version+Duration, not a message preview — this is consistent with the
   Agent-surface precedent, not a new drift finding for THIS case since ELITEA-2011
   never describes row content, only the click-through detail).
6. Click on one entry (the non-selected one, index 1 with default Date-desc sort)
   — verify it shows the message and response details for that execution.
   **Expected — confirmed live**: the clicked row gets `data-selected="true"`, and
   the right-hand panel renders that conversation's own `chat-message-item`s
   (Test Bot's message text + the AI's response) via the same shared
   `ChatMessageList` component the main embedded chat uses. Screenshot:
   `test-results/screenshots/ELITEA-2011-step-06-history-detail.png` (local capture
   this session: `automation/screenshots/afs_probe_2011_history_detail.png`).

## Expected Final State
The Run History panel is reachable via the `pipeline-history-tab` icon button once
an execution has happened, lists every past execution (Date/Version/Duration
columns) for the pipeline, and clicking any entry loads that specific execution's
message + AI-response content into the right-hand panel — replacing whatever was
previously selected.

## Pass/Fail Criteria
**Pass**: all 6 steps complete without errors; panel opens with ≥ 2 entries; clicking
an entry shows that execution's message + response.
**Fail**: panel doesn't open, shows no/wrong entries, or clicking an entry fails to
load or loads the wrong execution's details.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create a pipeline with LLM node → END | Pipeline created, ready for execution | step 1 | `step 1`: fixture + page load | asserted |
| 2 Execute the pipeline 2-3 times with different messages | Executions complete successfully | step 2 | `step 2`: two AI responses received | asserted *(2 executions used — "at least 2" satisfies "2-3", same convention as ELITEA-1877)* |
| 3 Click the "view run history" icon button | Run history panel opens | step 3 | `step 3`: `pipeline-history-tab` click; panel visible | asserted |
| 4 Verify run history panel opens | Panel visible with execution entries | step 4 | same click as step 3; `run-history-list-item` present | asserted *(decomposed — case's steps 3+4 are one UI action with one observable; kept as separate AFS steps only to preserve 1:1 traceability to the case's own numbering)* |
| 5 Verify at least 2-3 execution entries are listed | Multiple entries displayed | step 5 | `step 5`: `run-history-list-item` count == 2 | asserted |
| 6 Click one entry — verify message + response details | Execution details shown for selected entry | step 6 | `step 6`: `data-selected="true"` + `chat-message-item` content match | asserted |

**Axis 2 — Analyst additions**
- Zero console errors during the whole flow (navigate → execute ×2 → open history →
  select entry) — confirmed live this session (`CONSOLE_ERRORS=[]`). *Added: standard
  project-wide console-error assertion, not explicit in the case text.*
- The history panel REPLACES the Configuration form (not an overlay) — *added: this
  is why the test cannot interact with the Configuration form/canvas while History is
  open, and why `history_tab`/`chat_input` etc. become briefly absent from the DOM.*
- A close (`X`) button IS present and functional (`aria-label="close run history"`)
  and returns the view to the Configuration form + embedded chat — confirmed live
  this session (`CLOSE_BUTTON_COUNT=1`, `HISTORY_PANEL_GONE=True`,
  `CHAT_INPUT_BACK=True` after clicking it). *Added: not required by the case's own
  steps (which never close the panel), but useful teardown/negative-space knowledge
  for the implementer — no new testid requested since the case doesn't touch it
  (locator-policy scope discipline, `.agents/testing.md`).* This also confirms, on
  the Pipeline surface, the same fix already observed on the Agent surface for the
  previously-filed `EliteaAI/elitea-testing-public#1093` ("no UI way to close Run
  History") — a human should verify and close #1093 if not already closed.

## Cleanup
1. Pipeline deleted automatically by the `pipeline_with_llm_id` fixture's teardown
   (`pipeline_api.delete_pipeline(pid)`), which also removes its conversations
   server-side.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| Embedded chat: message input | `LocatorDescriptor(testid="chat-message-input")` — `chat_input` field, already on `PipelineDetailPage` | on-main ✓ (pre-existing, reused as-is) | none — testid only |
| Embedded chat: send button | `LocatorDescriptor(testid="chat-send-button")` — `chat_send_button`, already on `PipelineDetailPage` | on-main ✓ (pre-existing) | none |
| Embedded chat: clear button | `LocatorDescriptor(testid="chat-clear-button")` — `chat_clear_button`, already on `PipelineDetailPage` (field is correct; the `clear_embedded_chat()` METHOD is broken — see Known Defects) | on-main ✓ (pre-existing) | none |
| Embedded chat: message list / items | `CHAT_MESSAGE_ITEM_SELECTOR` (`[data-testid="chat-message-item"]`), already on `PipelineDetailPage` | on-main ✓ (pre-existing) | none |
| Run History open button | `LocatorDescriptor(testid="pipeline-history-tab")` — `history_tab` field, **already exists** on `PipelineDetailPage` (line ~56) | on-main ✓ (pre-existing) | none — testid only (ignore the field's pre-existing `fallback=`; tracked tech debt, not to be extended) |
| Run history list item (row) | `data-testid="run-history-list-item"` — **page-object field needed** on `PipelineDetailPage` (mirror `agent_detail_page.py`'s `RUN_HISTORY_LIST_ITEM_SELECTOR`); same literal testid on every row, positionally distinguished, default sort = Date desc | **on-`automation/testids` only ✓ — NOT yet on `main`** (added during ELITEA-1877's `add-data-testid` work, `EliteaAI/EliteaUI@a5a9d0f5`; awaiting human promotion). Verified via `git fetch origin` + `git grep -- "run-history-list-item" origin/main -- src/` → no hit; `origin/automation/testids` → hit at `RunHistoryListItem.jsx:143`. | none — testid only |
| Run history list item: selected state | `data-selected={selectedItem === item.id}` on the same `Box` as the row testid (state-as-attribute) — **page-object constant needed**: `'[data-testid="run-history-list-item"][data-selected="true"]'` | same commit as above — `automation/testids` only | none |
| Selected run's chat panel (message list / items) | Reuses `CHAT_MESSAGE_ITEM_SELECTOR` — `RunHistoryChat.jsx` renders the same shared `ChatMessageList` component. Confirmed live: renders correctly inside the Run History panel (main embedded chat is unmounted while History is open, so there's only one instance on the page) | on-main ✓ (pre-existing, reused as-is) | none |

**PROVENANCE freshness:** verified via `cd ../EliteaUI && git fetch origin` +
`git grep` against `origin/main` and `origin/automation/testids`, 2026-08-09.

## Network Behavior
- `GET /elitea_core/conversations/prompt_lib/{projectId}?source=pipeline&entity_name=application&entity_meta_id={pipelineId}&entity_meta_project_id={projectId}&limit=20&offset=0`
  (path pattern per `RunHistoryApi` — `source=pipeline` for this surface vs
  `source=agent` on the Agent surface) — fires when `pipeline-history-tab` is
  clicked; gives the entry count/ids.
- `GET /elitea_core/conversation/prompt_lib/{projectId}/{conversationId}` — fires
  when a row is clicked; its `message_groups` become the `chat-message-item`s
  rendered in the Run History chat panel.

## Known Defects Found During Exploration

**No product defects found.** The feature works exactly as the case describes on
the Pipeline surface, using the identical shared component the Agent surface
already proved (ELITEA-1877/#1093-fix).

**One test-suite (automation) defect found — not a product bug, flagged for the
implementer to fix in the same PR, not filed to the tracker (this is our own
page-object code, not an application defect):**
- `PipelineDetailPage.clear_embedded_chat()` (`automation/pages/pipeline_detail_page.py`,
  ~line 6811) clicks a STALE raw locator, `[aria-label="Clear the chat history"]`,
  which matches **zero** elements on the live product — the actual button is
  `ClearChatButton.jsx`, `aria-label="clear the chat"` (lowercase, different
  wording), `data-testid="chat-clear-button"`. The correct `chat_clear_button`
  `LocatorDescriptor` field already exists on the same page object (added for
  ELITEA-2016) — the method just never uses it. Confirmed live twice this session:
  calling the existing method produced only 1 run-history entry after two sent
  messages (silent no-op, both messages landed in the same conversation); replacing
  the click with `self.chat_clear_button.click()` produced the expected 2 entries.
  **This is a dead-code / silent-no-op defect, not a locator-policy violation** (the
  field is already testid-only) — the fix is trivial: change the method body to
  `self.chat_clear_button.click(timeout=timeout)`. The implementer MUST make this
  fix (or call `chat_clear_button` directly) — this case cannot pass with the
  current method.

## Blocked Steps
None. All 6 case steps were executed to completion against the live local
environment (pipeline ids 8757/8758/8759, `autotest_test_probe_run_history`).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **No `add-data-testid` work needed** — every testid this case touches already
  exists (either on `main` or on `automation/testids`, see PROVENANCE table above).
  This case is page-object + test wiring only.
- **Fix `clear_embedded_chat()` first** (see Known Defects) — every later step
  depends on it actually clearing the chat.
- **Add to `PipelineDetailPage`** (mirror `AgentDetailPage`'s existing
  `open_run_history()` / `get_run_history_item_count()` / `select_run_history_item(index)`
  / `get_run_history_chat_messages_text()` methods almost verbatim — same shared
  component, same behavior, confirmed live this session):
  - `RUN_HISTORY_LIST_ITEM_SELECTOR = '[data-testid="run-history-list-item"]'`
  - `RUN_HISTORY_LIST_ITEM_SELECTED_SELECTOR = '[data-testid="run-history-list-item"][data-selected="true"]'`
  - `open_run_history()` — click `self.history_tab` (already exists), wait for
    `RUN_HISTORY_LIST_ITEM_SELECTOR` to render.
  - `get_run_history_item_count()` — count of `RUN_HISTORY_LIST_ITEM_SELECTOR`.
  - `select_run_history_item(index)` — `.nth(index).click()`.
  - `is_run_history_item_selected(index)` — check `data-selected="true"` on that nth
    element.
  - `get_run_history_chat_messages_text()` — reuse `CHAT_MESSAGE_ITEM_SELECTOR` (no
    new selector needed, confirmed live it resolves correctly inside the History
    panel).
- **Reuse `pipeline_with_llm_id` + `_execute_pipeline()`-style helpers** from
  `test_pipeline_execution.py` for steps 1-2 (fixture + `send_message_in_embedded_chat`
  + `wait_for_embedded_chat_response`, all already existing and green).
- **Wait discipline**: after clicking `pipeline-history-tab`, wait for
  `run-history-list-item` count to stabilize (poll/`expect(...).to_have_count(...)`)
  rather than a fixed timeout — the list fetch is a real network round trip
  (confirmed live, this session used a 1.5s explicit wait as a probe convenience
  only; the real test should poll, per `.claude/rules/ui-tests.md`).
- **Sibling case flag for the lead**: `ELITEA-2070` ("Pipeline — Run History
  Panel") in the same wave-07 batch appears to describe the SAME feature
  (view-run-history icon → panel with timestamped entries → click for details →
  close) — its own case text adds "can be closed" as an explicit step, which this
  AFS's Axis-2 addition already covers informationally but ELITEA-2011 itself
  never asserts. Recommend the lead review ELITEA-2070's own case text once
  dispatched; it may be `extend-existing` against whatever spec this AFS produces
  (only once THIS spec is merged — same-batch similarity does not qualify a
  same-batch `extend-existing`/`already-covered` target per the merged-target
  rule), or a near-duplicate worth flagging to the case author. Not decided here —
  out of this AFS's scope since only ELITEA-2011 was dispatched this session.
- `_surface.md` updated this session with a new "Run History panel — Pipeline
  surface" section (mirrors the Agent-surface entry, notes the broken
  `clear_embedded_chat()` helper and the PROVENANCE gap on `run-history-list-item`).
