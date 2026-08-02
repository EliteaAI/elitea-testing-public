# Test Case: Selecting a past run from history loads its messages in the chat panel

## Metadata
- **TMS ID**: ELITEA-1877
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: localhost dev auth (`auth_state` / `VITE_DEV_TOKEN`) — no explicit `${TEST_USER}` needed
- **Analyst**: qa-engineer (analyst slot), batch `approved-top10`
- **Status**: ready-for-automation

## Preconditions
- User is on the Agent detail page's Configuration tab (`/agents/all/{id}?viewMode=owner`).
- (No pre-existing run-history data required — the test creates its own disposable
  agent and generates exactly two distinct run-history entries itself; see § Test Data.)

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Dedicated disposable agent via `agent_api.create_agent_full(...)`. **Amended at
  implementation time (2026-08-02):** the original draft mirrored
  `test_agent_llm_selector_anthropic_models.py`'s `_build_dedicated_agent_payload`
  (`reasoning_effort: "none"`, omit `temperature`) — but that pattern is documented
  (test-automation-engineer memory `reasoning_effort_none_breaks_embedded_chat.md`,
  confirmed in `test_agent_management.py`'s `_build_execution_agent_payload` docstring,
  ELITEA-1897/#560) to 500 the `POST .../conversations/prompt_lib/{project}` call
  whenever the agent actually opens the embedded chat — which THIS case's own steps 2
  and 3-6 require (two chat messages + Run History). Use
  `reasoning_effort: "low"` instead (avoids both the open #524 creation-400 and the
  #560 chat-500, and stays within a normal 30s response wait — `"medium"` is safe but
  too slow). Omit `temperature` and the model fields (`model_name`/`model_project_id`)
  entirely, letting the backend apply its own valid default — same shape as
  `_build_execution_agent_payload` in `test_agent_management.py`.
- Two distinct chat messages sent through the embedded chat panel, each producing its
  own server-side conversation (run-history entry):
  - Message A (older run): e.g. `f"first-run-{uuid4().hex[:6]}"`
  - Message B (newer / "current active" run): e.g. `f"second-run-{uuid4().hex[:6]}"`
  - **Mechanism confirmed live + code-confirmed (`ChatBox.jsx` `onClickClearChat`,
    `isAgentsPage` branch):** sending Message A creates conversation A server-side.
    Clicking **Clear chat** (`chat_clear_button`) does **not** wipe conversation A — it
    starts a fresh **local, unsaved** conversation object (`isNew: true`, no id yet) as
    the new active conversation. Sending Message B then persists that as conversation B.
    Conversation A therefore survives, unmodified, as its own Run History row alongside
    the now-active conversation B — this is what gives the test two *distinct* runs
    without needing two agents or two browser sessions.
  - **Verify live once at implementation time**, don't assume from this note alone:
    whether a conversation needs at least one message exchange before it appears in the
    Run History list (all conversations observed during exploration already had
    `message_groups_count >= 1` — none were empty), i.e. always send the message before
    opening History.

## Test Steps
1. Create the disposable agent via `agent_api.create_agent_full(...)`; navigate to its
   detail page (`AgentDetailPage.navigate(agent_id)`).
   - **Verify**: page loads (`wait_for_page_load()` — INFORMATION section + populated
     Name field).
2. Send Message A via `send_chat_message("first-run-...")`; wait for the AI response
   (`wait_for_chat_response`). Click **Clear chat**
   (`clear_embedded_chat()`/`chat_clear_button`). Send Message B via
   `send_chat_message("second-run-...")`; wait for the AI response.
   - **Verify**: the embedded chat's last message (`chat-message-item`, last) reflects
     Message B's exchange — this is the "current/active run" content the test will
     later prove the historical run is *distinct from* (case step 6).
3. Click the **Run History** button (`pipeline-history-tab`) in the embedded chat
   panel's top controls.
   - **Verify**: the Configuration form + embedded chat are replaced by the Run History
     view; `run-history-list-item` count is `>= 2` (both conversations A and B are
     listed — case step 2's "at least 2 entries").
4. Click the run-history entry that is **not** the most recent — with the list's
   default sort (`Date`, descending — confirmed in `RunHistoryList.jsx`
   `useRunHistorySorting(SORT_TYPES.DATE)`), that is index `1`:
   `page.locator('[data-testid="run-history-list-item"]').nth(1).click()`.
   - **Verify**: that same element now carries `data-selected="true"`
     (`[data-testid="run-history-list-item"][data-selected="true"]` resolves to exactly
     one element, and it is the clicked one) — case step 3's "highlighted".
5. Read the messages rendered in the right-hand panel
   (`chat-message-list` → `chat-message-item` items, same shared `ChatMessageList`
   component the main embedded chat uses — **confirmed live**: it renders correctly
   scoped inside the Run History panel, no new testid needed for message content).
   - **Verify**: the text matches Message A (the older run) — case steps 4 + 5.
6. Compare the Run History panel's message text against Message B (captured in step 2).
   - **Verify**: they differ — case step 6 ("distinct from the current/active run").

## Expected Results
- The Run History view lists at least 2 entries once two distinct conversations exist
  for the agent.
- Clicking a non-most-recent entry visibly selects it (`data-selected="true"`) and loads
  that conversation's messages — not the current/active conversation's — into the
  right-hand chat panel via the standard `chat-message-list`/`chat-message-item` handles.
- The loaded historical messages are textually distinct from the current/active run's
  messages.
- No console errors during the flow.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to an agent with ≥2 distinct run history entries | Agent detail page loads | steps 1–2 | `step 1`: page load wait; `step 2`: two conversations created | asserted *(decomposed — case precondition is generated by the test, not found pre-existing)* |
| 2 Open the run history panel | Panel opens with ≥2 entries | step 3 | `step 3`: `run-history-list-item` count ≥ 2 | asserted |
| 3 Click a specific past run entry (not the most recent) | Entry is highlighted | step 4 | `step 4`: `data-selected="true"` on the clicked element | asserted |
| 4 Chat panel updates to show messages from the selected run | Displays messages from selected historical session | step 5 | `step 5`: `chat-message-item` text | asserted |
| 5 Messages match the content from that historical session | Displayed messages correspond to the selected past run | step 5 | `step 5`: exact text match against Message A | asserted |
| 6 Distinct from the current/active run | Loaded messages differ from current/active run content | step 6 | `step 6`: Message A text ≠ Message B text | asserted |

**Axis 2 — Analyst additions**
- `step 3` asserts the Run History button (`pipeline-history-tab`) fully unmounts the
  Configuration form + main embedded chat (verified live: after opening History, that
  same testid throws a Playwright `TimeoutError` on a second click — the control is
  gone from the DOM) — *added: this is why the test must not try to "close" Run History
  via the same button; see § Known Defects. Not a case requirement, but the implementer
  needs to know the button won't be there to click again.*
- **Amended at implementation time (2026-08-02):** `§ Expected Results` already stated
  "No console errors during the flow" but this row was missing from Axis 2 — added the
  standard project-wide console-error/warning listener (same pattern as
  `test_agent_llm_selector_anthropic_models.py`) asserted at the end of the flow.

## Cleanup
1. Delete the disposable agent via `agent_api.delete_agent(agent_id)` (also deletes its
   conversations server-side, consistent with the pattern in
   `test_agent_llm_selector_anthropic_models.py`).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| Embedded chat: message input | `LocatorDescriptor(testid="chat-message-input")` — `chat_message_input` field, already on `AgentDetailPage` | on-main ✓ (pre-existing, reused as-is) | none — testid only |
| Embedded chat: send button | `LocatorDescriptor(testid="chat-send-button")` — `chat_send_button`, already on `AgentDetailPage` | on-main ✓ (pre-existing) | none |
| Embedded chat: clear button | `LocatorDescriptor(testid="chat-clear-button")` — `chat_clear_button`, already on `AgentDetailPage` | on-main ✓ (pre-existing) | none |
| Embedded chat: message list / items | `chat_message_list` (`chat-message-list`) + `CHAT_MESSAGE_ITEM_SELECTOR` (`[data-testid="chat-message-item"]`), already on `AgentDetailPage` | on-main ✓ (pre-existing) | none |
| Run History open button | `LocatorDescriptor(testid="pipeline-history-tab")` — **testid needed on `AgentDetailPage`** (field doesn't exist yet there; testid itself is pre-existing on the shared `ViewRunHistoryButton.jsx`, `src/[fsd]/shared/ui/button/ViewRunHistoryButton.jsx:28`) | on-main ✓ (testid exists in EliteaUI; page-object field is new) | none — testid only |
| Run history list item (row) | **testid needed**: `data-testid="run-history-list-item"` on `RunHistoryListItem.jsx`'s outer `Box` (`src/[fsd]/entities/run-history/ui/RunHistoryList/RunHistoryListItem.jsx`, the `Box sx={[styles.listItem, ...]}` around line 148) — same literal testid on every row (rows are positionally distinguished, default sort = Date desc, so `.nth(1)` = "not the most recent") | needs-adding | none — testid only |
| Run history list item: selected state | **testid needed**: `data-selected={selectedItem === item.id}` on the same `Box` as the row testid (state-as-attribute, not a state-dependent testid — per `.agents/testing.md` § Locator policy) | needs-adding | none |
| Selected run's chat panel (message list / items) | Reuses `chat-message-list` / `chat-message-item` — `RunHistoryChat.jsx` renders the same shared `ChatMessageList` component. **Confirmed live**: both testids render correctly inside the Run History panel with no extra scoping needed (main embedded chat is unmounted while History is open, so there's only one instance on the page at a time) | on-main ✓ (pre-existing, reused as-is — no new testid) | none |

**PROVENANCE freshness:** verified via `cd ../EliteaUI && git fetch origin` +
`git grep` against `origin/main` (all "on-main ✓" rows above), 2026-08-02.

## Network Behavior
- `GET /elitea_core/conversations/prompt_lib/{projectId}?source=agent&entity_name=application&entity_meta_id={agentId}&entity_meta_project_id={projectId}&limit=20&offset=0`
  — fires when the Run History button is clicked; `response.total` / `response.rows[].id`
  give the entry count and ids (useful as a tie-breaker if the UI count assertion is flaky).
- `GET /elitea_core/conversation/prompt_lib/{projectId}/{conversationId}` — fires when a
  row is clicked; its `message_groups` become the `chat-message-item`s rendered in the
  Run History chat panel.

## Known Defects Found During Exploration
- **[MINOR]** Filed as `EliteaAI/elitea-testing-public#1093` — the Run History view has
  no way to close/exit once opened (the button that opens it, `pipeline-history-tab`,
  unmounts along with the Configuration form when History opens; `RunHistoryContainer`
  accepts an `onClose` prop but never wires it to any rendered element — confirmed both
  by source read and live, a second click on `pipeline-history-tab` times out because
  the element is gone). **Does not block this case** — ELITEA-1877's own steps only
  require opening History and selecting a run, never closing it. Flagged for the
  implementer/reviewer as context, not a blocker.

## Blocked Steps
- none

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: extend `AgentDetailPage` (`automation/pages/agent_detail_page.py`) — it
  already has everything for the embedded-chat half of this case
  (`send_chat_message`, `clear_embedded_chat`, `wait_for_chat_response`,
  `_embedded_chat_messages`/`CHAT_MESSAGE_ITEM_SELECTOR`). Add the Run History locators
  + a small set of new methods (`open_run_history()`, `get_run_history_item_count()`,
  `select_run_history_item(index)`, `get_run_history_chat_messages()`) alongside the
  existing "Embedded chat (right panel)" section — same class, don't create a new page
  object for this (it's the same page, same tab, one more UI mode).
- Disposable-agent fixture: mirror `_build_dedicated_agent_payload` from
  `test_agent_llm_selector_anthropic_models.py` (`reasoning_effort: "none"`, no
  `temperature` — #524 workaround already documented in
  `test-specs/agents/_surface.md`).
- Wait strategy: after clicking `pipeline-history-tab`, wait for
  `run-history-list-item` count to stabilize (`page.wait_for_function` or a
  `expect(...).to_have_count(...)` poll) rather than a fixed timeout — the list fetch
  (`GET .../conversations/prompt_lib/...`) is a real network round trip.
- `wait_for_chat_response` (existing method) already handles the AI-reply WebSocket
  delay for both Message A and Message B.
