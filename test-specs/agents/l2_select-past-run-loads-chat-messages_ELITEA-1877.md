# Test Case: Selecting a past run from history loads its messages in the chat panel

## Metadata
- **TMS ID**: ELITEA-1877
- **Linked Story**: none
- **Priority**: l2 (high)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`)
- **User set**: none — localhost `auth_state` bypass (`VITE_DEV_TOKEN`), no login required
- **Analyst**: qa-engineer (Sage), 2026-07-24
- **Status**: ready-for-automation

## Preconditions
- User is on `${BASE_URL}` (localhost auth bypass — no explicit login step).
- An agent exists with **at least 2 distinct run history entries** ("run" =
  one conversation against that agent's embedded chat). This is **not**
  guaranteed by seed data — the existing `agent_id` pytest fixture
  (`automation/fixtures/data_fixtures.py:79`) creates a fresh agent via API
  and deletes it on teardown; the 2 distinct runs must then be created as a
  **setup step inside the test** (see Test Steps 1–2). Confirmed live: the
  fixture-created (or any existing) agent starts with an empty run history —
  there is no "at least 2 runs" seed data anywhere in the app to reuse.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Agent: `agent_id` fixture (`automation/fixtures/data_fixtures.py:79`) — fresh
  agent created via `AgentAPI`, deleted in teardown. Default model
  (Anthropic Claude 4.5 Sonnet in the explored env) is fine — no toolkit/model
  dependency in this case.
- Run 1 message: unique string per test run, e.g.
  `f"Run 1 marker {uuid4().hex[:8]}"` — must differ textually from Run 2's
  message so the assertion in Step 6/7 cannot pass by coincidence.
- Run 2 message: a second, textually-distinct unique string, e.g.
  `f"Run 2 marker {uuid4().hex[:8]}"`.
- No cleanup needed beyond the `agent_id` fixture's own teardown (deleting the
  agent removes its conversations/run history with it).

## Test Steps
1. Navigate to the agent detail page: `AgentDetailPage.navigate(agent_id)`
   (→ `/agents/all/{agent_id}?viewMode=owner` — **note:** the bare path
   without `?viewMode=owner` 404s locally, "Page not found"; the existing
   `navigate()` helper already appends it correctly — do not regress this).
   - **Verify**: page loads (`information_section` visible, Name field
     populated) — existing `wait_for_page_load()` already does this.
2. **Setup — create 2 distinct runs** (not a case step, but required to meet
   the case's precondition; document as setup, not as a numbered case step):
   a. `send_chat_message(RUN_1_MESSAGE)` → `wait_for_chat_response(initial_count=get_chat_message_count())`.
   b. `clear_embedded_chat()` (existing method — confirmed live: this starts
      a **brand-new** conversation while preserving the previous one in Run
      History; it does NOT delete/overwrite the prior run).
   c. `send_chat_message(RUN_2_MESSAGE)` → `wait_for_chat_response(...)`.
   - **Verify**: both responses received (message + AI reply visible for each,
     confirmed via `get_chat_message_count()` / delete-button presence).
3. Click the "View run history" button (`pipeline-history-tab` testid).
   - **Verify**: the Run History panel opens (heading "Run History" text
     visible; the embedded chat/config form area is replaced by the panel).
4. Verify the Run History list shows **at least 2 entries**.
   - **Verify**: row count ≥ 2 (once the testid gap below is closed —
     `page.locator(RUN_HISTORY_ITEM_ANY_SELECTOR).count() >= 2`).
5. Click the **older** (non-most-recent) row — i.e. the row corresponding to
   Run 1, NOT the row for the run that was active when Step 3 was performed
   (Run 2).
   - **Verify**: that row carries `data-selected="true"`; the other row
     carries `data-selected="false"` (once the testid/attribute gap below is
     closed).
6. Verify the chat panel (right pane, inside the Run History view) shows the
   messages from the selected (Run 1) session.
   - **Verify**: `chat_message_list` / `chat_message_item` content contains
     `RUN_1_MESSAGE` (the user message) and an AI reply — NOT `RUN_2_MESSAGE`.
7. Verify this loaded content is **distinct** from the run that was active
   immediately before opening history (Run 2).
   - **Verify**: the text captured in Step 6 does not equal/contain the text
     captured from the live chat panel in Step 2c (Run 2's message + reply).

## Expected Results
- Run History panel opens via the `pipeline-history-tab` button and lists
  both runs (Step 2's two conversations), newest first.
- Clicking the older (Run 1) row highlights that row specifically (and only
  that row).
- The chat panel updates to show Run 1's user message and AI reply.
- Run 1's content is textually distinct from Run 2's content (which was the
  active/current conversation before history was opened).
- No console errors during any of the above (confirmed: `get-console` showed
  only routine `debug`/`info` entries, no `error` level).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: agent with ≥2 run history entries | entries exist to select from | AFS step 2 (setup) | step 2: 2 responses received | asserted *(decomposed into setup, not a numbered case step)* |
| 1 Navigate to an agent with ≥2 run history entries | agent detail page loads | AFS step 1 | step 1: `information_section` visible | asserted |
| 2 Open the run history panel | panel opens, ≥2 entries listed | AFS steps 3–4 | step 3: "Run History" heading visible; step 4: row count ≥ 2 | asserted |
| 3 Click a specific past run entry (not most recent) | entry is highlighted | AFS step 5 | step 5: `data-selected="true"` on clicked row | asserted *(testid gap — see Concrete Handles)* |
| 4 Chat panel updates to show messages from selected run | messages for that run appear | AFS step 6 | step 6: `chat_message_item` contains Run 1 text | asserted |
| 5 Displayed messages match the historical session's content | content correctness | AFS step 6 | step 6: exact marker-string match | asserted |
| 6 Distinct from current/active run | loaded messages differ from active run | AFS step 7 | step 7: Run 1 text ≠ Run 2 text | asserted |

### Axis 2 — Analyst additions

- AFS step 5 additionally asserts the **non-clicked row stays unselected**
  (`data-selected="false"`) — *added: this is the natural counterpart of "the
  selected run entry is highlighted" and catches a class of bug (e.g. the
  wrong row lighting up) that "is the clicked row highlighted" alone would
  miss. See the debugging note below — this exact failure mode was reproduced
  once with an ambiguous test-tooling selector and ruled out as a tooling
  artifact, not a product bug, but the assertion is cheap insurance regardless.*
- No console-error assertion added beyond the case — *observed clean
  (`get-console` had no `error`-level entries) during exploration; not adding
  a dedicated assertion since the case doesn't call for it and existing
  suite-wide conventions don't universally assert this per-test.*

## Cleanup
1. `agent_id` fixture teardown deletes the fixture-created agent (and with it
   both conversations/runs) — no manual cleanup needed.

## Concrete Handles (discovered during exploration)

**Locator policy for this project is testid-only — no role/label/text/CSS
ladder** (`.agents/role-overrides.md`, `.agents/testing.md` § Locator policy).
Handles below follow that policy; state is a `data-*` attribute filter, never
a state-dependent testid.

| Element | Testid (existing) | PROVENANCE | Notes |
|---|---|---|---|
| "View run history" button | `pipeline-history-tab` | on-main ✓ (pre-existing; verify at implementation time — see note) | `ViewRunHistoryButton.jsx:27` — **shared component** used identically by Agent/Pipeline/Toolkit/MCP "history" entry points; the value is a leftover from the Pipelines context (misleading in the Agent case) but functionally fine to reuse as-is. This is pre-existing tech debt (not touched/added by this case) — not a new finding, out of scope to rename here. |
| Embedded chat message list (also serves as the Run-History chat pane — mutually exclusive mount) | `chat-message-list` / `chat-message-item` | on-main ✓ (already in `agent_detail_page.py:171-172` as `chat_message_list`/`chat_message_item`) | `RunHistoryChat.jsx` reuses the SAME shared `ChatMessageList` component the live embedded chat uses. `ConfigurationTab.jsx` renders `RunHistoryContainer` and `ConfigurationRightContent` **mutually exclusively** (`{showHistory && <RunHistoryContainer/>} {!showHistory && <ConfigurationRightContent/>}`), so only one `[data-testid="chat-message-list"]` is ever mounted at a time — the existing `chat_message_list` LocatorDescriptor and `_embedded_chat_messages()` helper work unchanged while the history panel is open. **No gap here.** |
| Chat send button / input (setup only) | `chat-message-input`, `chat-send-button` | on-main ✓ (`agent_detail_page.py:171-176`) | Reused via existing `send_chat_message()` method — no gap. |
| Clear chat button (setup only) | `chat-clear-button` | on-main ✓ (`agent_detail_page.py:180`) | Reused via existing `clear_embedded_chat()` method — no gap. |
| Run History panel heading (Step 3's own "panel opened" assertion — `RunHistoryContainer.jsx`'s `<Typography>Run History</Typography>`) | `testid needed: run-history-panel-heading` | needs-adding *(implementer finding — this AFS's own Coverage Map names "heading visible" as Step 3's assertion technique, but the Concrete Handles table above didn't carry a testid for it — a gap in this AFS, not a technique change)* | **Amendment (implementer exploration, `docs(afs)` commit):** added via `add-data-testid` on `EliteaAI/EliteaUI`'s `automation/testids` (EliteaAI/EliteaUI@1a684045). Static testid, not dynamic — the panel renders exactly one heading. `AgentDetailPage.run_history_panel_heading` field + `open_run_history_panel()` method wait on it. |

| Element | Testid (needed) | State attribute (needed) | PROVENANCE |
|---|---|---|---|
| Run History list row (`RunHistoryListItem.jsx`'s outer clickable `<Box onClick={() => onItemSelect(item.id)}>`, lines 141–144) | `testid needed: run-history-item-{id}` (dynamic, keyed by `item.id` — the conversation id) | `data-selected="true"/"false"` (reflecting `selectedItem === item.id`) | **needs-adding** — grepped the entire `entities/run-history/` tree (`ui/RunHistoryContainer.jsx`, `ui/RunHistoryChat.jsx`, `ui/RunHistoryList/*.jsx`): **zero `data-testid` attributes anywhere.** Confirmed live: the only way I could disambiguate the two rows was a raw MUI-emotion-generated class (`.css-1o16zsr`), which is **shared by both unselected rows** (same computed `sx`) and therefore NOT usable as a stable per-row handle — see debugging note below. This is a genuine, blocking testid gap for Steps 5–7; route via `add-data-testid` on `EliteaAI/EliteaUI`'s `automation/testids` per the dual-target flow. Suggested class-level pattern (per `.agents/testing.md` § Locator policy, "Dynamic (runtime-parameterized) testids"): `RUN_HISTORY_ITEM = '[data-testid="run-history-item-{}"]'` on the page object, `.format(conversation_id)` at the call site — naming is deliberately **generic** (`run-history-item`, not `agent-run-history-item`) because `RunHistoryListItem` is a shared cross-feature entity component (also used by Pipelines/Toolkits/MCP), per the "shared components never hardcode feature-scoped testids" rule. |

**Debugging note — a false alarm, documented so it isn't re-litigated:** my
first live attempt to click the older row used `page.locator('.css-1o16zsr')`
(no testid existed yet, so I improvised a raw CSS handle purely to explore
behavior — never for the shipped locator). That class turned out to be
**shared by both unselected rows** (identical computed MUI `sx`), so
`querySelector`/Playwright's implicit "first match" landed on the **newer**
row instead of the older one I intended, and post-click evidence appeared to
(misleadingly) confirm the click — because by then the newer row's class had
changed (no longer matching `.css-1o16zsr`), leaving only the older row
visible under that selector. Net effect: it LOOKED like clicking the older
row highlighted the newer one instead — a plausible-looking product bug. I
re-ran the exact same interaction with an unambiguous selector
(`.css-1o16zsr:nth-of-type(2)`, confirmed unique before clicking) in the same
live session, and the **feature behaved correctly**: the clicked (older) row
highlighted, and only that row. Verdict: tooling/selector-ambiguity artifact,
not a product defect — no ticket filed. This is exactly why the AFS's
Concrete Handles section asks for a real per-row testid: the ambiguity that
fooled my own probing here is the same ambiguity that would make a shipped
test flaky/wrong without one.

## Network Behavior
- Opening the panel fires `RunHistoryApi.useLazyGetRunHistoryListQuery` (list
  of runs); clicking a row fires `useLazyGetRunHistoryDetailsQuery`
  (conversation detail for that run) — confirmed via source
  (`RunHistoryContainer.jsx`, `RunHistoryChat.jsx`). Could not capture the
  actual request/response pair via the CDP tooling used this session (network
  buffer was empty/evicted across navigations — a tooling limitation, not a
  product observation); the UI-level evidence (distinct, correct message
  content per run, confirmed by screenshot across 2 clean toggles) is
  sufficient and was not blocked by this gap. Implementer: if a network wait
  is needed, `wait_for_response` matching the conversation-details endpoint
  is the natural condition (never a fixed sleep, per `.agents/testing.md`).
- **Amendment (implementer exploration, R1):** the LIST endpoint wait matters
  too, not just the details one. A first automation attempt that opened the
  panel and read row count right after `run_history_panel_heading` became
  visible observed **0 rows** (confirmed via failure screenshot: the panel
  showed `RunHistoryListItem`'s own `useMock`/`Skeleton` loading placeholders,
  not real rows) — the heading is static markup that renders independent of
  `useLazyGetRunHistoryListQuery`'s async resolution, so it's not proof the
  list itself has loaded. Fix: `open_run_history_panel()` wraps the button
  click in `page.expect_response` for the PLURAL list endpoint
  (`/elitea_core/conversations/prompt_lib/`, GET) before returning, and
  `get_run_history_item_count()` additionally waits for the first row's
  visibility before counting. Root cause: infrastructure (a wait-condition
  gap in this AFS's own network-behavior guidance, not a product defect) —
  fixed in R1, test green thereafter.

## Known Defects Found During Exploration
None found. The one anomaly encountered (a row appearing to highlight
incorrectly) was reproduced from a clean, isolated re-test to be a
test-tooling selector-ambiguity artifact, not a product defect — see the
debugging note above. Feature behavior for both directions of switching
(older→newer, newer→older) was confirmed correct via unambiguous selectors.

## Blocked Steps
None. Full case executed end-to-end against the live local app.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`); implement in
  `automation/pages/agent_detail_page.py` (extend — do not create a new page
  object; the embedded chat + run history panel are already part of
  `AgentDetailPage`'s surface) and a new test file under
  `automation/tests/ui/agents/`.
- Reuse `agent_id` fixture (`automation/fixtures/data_fixtures.py:79`) for
  test-data setup/teardown.
- Reuse existing methods: `navigate()`, `send_chat_message()`,
  `wait_for_chat_response()`, `clear_embedded_chat()`, `get_chat_message_count()`,
  `_embedded_chat_messages()`.
- New page-object additions needed: a `run_history_button` LocatorDescriptor
  (`testid="pipeline-history-tab"` — reuse existing testid, new field on this
  class since `AgentDetailPage` doesn't have one yet), a `RUN_HISTORY_ITEM`
  class-constant template (`'[data-testid="run-history-item-{}"]'`, once
  `add-data-testid` lands it), and a state-filtered variant for the
  "selected" assertion (`'[data-testid="run-history-item-{}"][data-selected="true"]'`).
- **Unrelated observation, not part of this case's scope** (no action
  needed, noting for the record only): `AgentDetailPage.verify_tabs_visible()`
  (`agent_detail_page.py:473-479`) references `self.configuration_tab` /
  `self.history_tab`, neither of which is defined anywhere on `AgentDetailPage`
  or its `AgentFormPage`/`BasePage` parents (those two locators exist only on
  `PipelineDetailPage`/`ToolkitDetailPage`). The method appears to be
  dead/copy-pasted code — no test in `automation/tests/` calls it (confirmed
  via `grep -rln "verify_tabs_visible" automation/tests/` → no hits) — so it
  doesn't affect this case or any currently-running suite. Flagging only so
  it isn't mistaken for something this case's implementation should wire up
  (the Agent page's actual "history" mechanism is the toggle panel this AFS
  covers, not a Configuration/History tab pair).
