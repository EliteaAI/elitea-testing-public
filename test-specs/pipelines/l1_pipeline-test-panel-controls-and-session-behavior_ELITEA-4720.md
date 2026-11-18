# Test Case: Pipeline — Test Pipeline Panel Controls and Session Behavior

## Metadata
- **TMS ID**: ELITEA-4720 (priority: high -> l1 per dispatch naming of the 4714 sibling; authored `high`)
- **Linked Story**: EliteaAI/elitea_issues#7155 (epic 7093)
- **Environment Explored**: DEV `https://dev.elitea.ai/app`, scripted Python Playwright probes (headless, viewport 1600x1400, storage state from `dev_storage_state.py`). UI source cross-checked on `EliteaUI origin/main` (fetched).
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), 2026-11-18
- **Status**: ready-for-automation
- **surface_key**: pipelines-test-panel

## Preconditions
- Saved pipeline `LLM 1` (entry, task = f-string `{input}`) -> END. Reuse fixture `pipeline_with_fstring_llm_id` (`fixtures/data_fixtures.py`, auto-deleted) — a fixed empty task also runs, but f-string gives a real answer to the poem prompt. Run takes ~1.4 s for `Hello`, ~5 s for the poem (long enough to close the panel mid-run; the `running` highlight appeared ~2 s after Enter).
- Banners on DEV (`platform-banner-center` dialog, then `platform-banner-corner`) intercept clicks ~6 s after load: close via `platform-banner-close`/corner button, or (probe) remove `[data-testid^=platform-banner]`. Existing page-object dismissal helpers apply.

## Test Data
Message 1 `Hello`; Message 2 `Write a short poem about pipelines`; unsaved edit = **edit the LLM node's System field** (`pipeline-llm-node-system-value`), NOT the pipeline Description (see Clarification C1).

## Test Steps (executed live 2026-11-18; every step observed)
1. Open `/pipelines/all/<id>?viewMode=owner`. `pipeline-test-panel` NOT visible (stays mounted, hidden); `pipeline-test-button` visible + enabled (inner button `to_be_enabled`). Canvas full width.
2. Click `pipeline-test-button`. `pipeline-test-panel` visible (width **373 px** default, x=1203, right side). Inside: `chat-message-input`, `model-selector-button` (name text e.g. "Anthropic Claude Haiku 5.5"), `pipeline-test-panel-controls` with `pipeline-history-tab`, `chat-clear-button`, `pipeline-test-panel-close`. `pipeline-test-button` NOT visible while open (replaced by controls). Resize handle `pipeline-test-panel-resize-handle` (24 px wide, aria "Resize test panel"). Context pill appears only once a conversation exists (absent on a fresh panel).
3. Click `chat-message-input`, type `Hello`, Enter (or `chat-send-button`, aria "send your question"). Within ~2 s `[data-testid="pipeline-node-card-LLM 1"][data-status="running"]` count 1 (poll — transient; attribute absent otherwise). Then `chat-message-item` x2 (user "Hello" + answer), `chat-answer-model-chip` ("... (LLM1) · 1.4s"), `skill-test-last-response` text "Hello! How can I help you today?" (LLM wording varies — assert non-empty).
4. `context-budget-pill` (aria "Context management 0%") text **"0%"** (case says e.g. "1%" — value depends on tokens; assert regex `^\d+%$`).
5. Click the pill -> `context-budget-popover` (MuiPopper) containing `context-budget-tokens` ("24 of 269 280 tokens"), `context-budget-messages-count` ("2"), `context-budget-summaries-count` ("0"), `context-budget-percentage`, `context-budget-edit-button` ("Edit" action, icon-only testid), plus window-mode selector (`context-window-mode-*`) and usage totals. Escape closes it (popover count 0).
6. Hover `pipeline-history-tab` -> `[role=tooltip]` text exactly "Run History". Click -> URL `/pipelines/all/<id>/history?viewMode=owner&name=...`; `run-history-list-item` count >= 1 (3 on the shared probe pipeline; own fresh pipeline -> 1). Run History is a ROUTE, not an inline panel (same as ELITEA-2070 amendment). Return with browser back (`page.go_back()`) or breadcrumb (`breadcrumb-item` = pipeline name): lands on detail with the **panel CLOSED** (not restored open) and the `pipeline-test-button` shown; after re-opening the panel the chat is EMPTY (`chat-message-item` 0) — the in-memory conversation does not survive a route round-trip (observed 2/2). Plan for it: do the Run History check LAST-OF-SESSION or re-send; do not carry the conversation across it (see Clarification C2).
7. With panel open, edit the node System text (click `pipeline-node-card-LLM 1` via JS click if intercepted; `pipeline-llm-node-system-value` textarea). `agent-save-button` becomes enabled. Click `pipeline-test-panel-close`: panel hidden, `pipeline-test-button` visible and **enabled** (also verified with the Description edit — same). 7a: click `pipeline-test-button`: panel opens with the SAME conversation (2 items) — within one route session.
8. Type a message in `chat-message-input`; `chat-send-button` is **disabled** (`is_disabled()` True, `aria-disabled` null — native disabled). `hover(force=True)` shows `[role=tooltip]` "Save the pipeline to test the latest changes." (source `testPanel.constants.js` UNSAVED_CHANGES_HINT, passed as `sendBlockedReason`). Pressing Enter sends nothing (message count unchanged).
9. Click `agent-save-button` (JS click if banner intercepts): Save becomes disabled, `chat-send-button` enabled. Send `Hello` (input retained text) -> 2 new `chat-message-item`, response appears.
10. Send `Write a short poem about pipelines`; poll for `[data-status="running"]` (count 1), click `pipeline-test-panel-close` while running: panel hidden, `pipeline-test-button` visible, `data-status="running"` count still **1** immediately after close; it clears by ~6 s (run finished).
11. Click `pipeline-test-button`: panel shows the same conversation incl. completed poem (observed 2 items, poem text present). Assert the answer is non-empty / contains multiple lines; the run completed while the panel was closed.
12. Drag `pipeline-test-panel-resize-handle` leftwards ~150 px with real mouse (move to handle centre, down, move steps=10, up): panel width 373 -> **492 px**. Persistence is `localStorage["pipelineTestPanelWidth:<pipelineId>"]`. `page.reload()`, wait, dismiss banners, open the panel: width **492** retained. Cleanup: remove that localStorage key (context is isolated per test anyway) — default width is otherwise 373.
13. With >=1 exchange in the panel (`chat-clear-button` is **disabled** on an empty conversation, enabled once messages exist), click `chat-clear-button`: `chat-message-item` 0, `context-budget-pill` disappears (count 0), clear button disabled again.
Side channels: console errors 0 in all probes; no failing requests observed.

## Expected Results
As the case, with the clarifications below. Hard assertions: panel closed by default / opens with controls; button swap; response present; node `data-status=running` seen during run; pill percent text; popover figures (messages=2, summaries=0, Edit button); tooltip "Run History" + history route lists >=1 item; Test button enabled with unsaved change; send disabled + hint tooltip while node edit unsaved; send works after Save; panel closes mid-run without stopping it and shows the completed answer on reopen; width persists across reload; Clear empties messages.

## Coverage Map

### Axis 1 — Case coverage
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 closed + enabled | panel hidden, full canvas, button enabled | step 1 | panel not visible, button enabled | asserted (full-width = not-visible panel; no pixel check) |
| 2 open | right panel, input, model selector, button replaced | step 2 | panel visible, input + model selector visible, test-button hidden, controls visible | asserted |
| 3 send Hello | user+response, active node highlighted | step 3 | message items, last response non-empty, running attr polled | asserted |
| 4 Context % | percentage | step 4 | pill text regex | asserted (clarification C3: "0%" not "1%") |
| 5 Context popover | tokens, messages, summaries, Edit | step 5 | popover testids visible, messages=2, summaries=0 | asserted |
| 6 Run History | tooltip + lists run | step 6 | tooltip text, route, list item >=1 | asserted |
| 7 unsaved + close | button enabled | step 7 | enabled | asserted (clarification C1 on edit kind) |
| 7a reopen | same conversation | step 7a | message count 2 | asserted |
| 8 hint | hint shown, send blocked | step 8 | disabled + tooltip text + no new message | asserted |
| 9 Save + send | response | step 9 | new messages, send enabled | asserted |
| 10 close mid-run | closed, button shown, node highlighted | step 10 | panel hidden, button visible, running attr | asserted (timing-sensitive, see Risks) |
| 11 reopen | same convo + progress/complete | step 11 | messages incl. poem | asserted |
| 12 width persists | wider after reload | step 12 | width after drag > default; equal after reload (tolerance) | asserted |
| 13 Clear | messages removed | step 13 | message count 0 | asserted |

### Axis 2 — Analyst additions
- Step 13: pill gone + clear button disabled after clearing — grounded in `isTestChatClearDisabled` and live observation.
- Step 8: Enter sends nothing — the observable meaning of "sending is blocked".
- Step 2: `pipeline-test-button` hidden while open — the "replaced by panel controls" clause.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Test Pipeline button | 1 | `pipeline-test-button` (`test_pipeline_button`) | — | testid on DEV ✓ |
| Panel | 1 | `pipeline-test-panel` (`test_pipeline_panel`); controls `pipeline-test-panel-controls` | — | testid on DEV ✓ |
| Close | 1 | `pipeline-test-panel-close` | — | testid on DEV ✓ (new field needed) |
| Resize handle | 1 | `pipeline-test-panel-resize-handle` | — | testid on DEV ✓ (new field) |
| Run History icon | 1 | `pipeline-history-tab` (existing `history_tab`-style field, line ~58) | — | testid on DEV ✓ |
| Tooltip | 2 | `role=tooltip` | `pipeline-test-panel-tooltip` (existing field `suggested_testid="pipeline-test-button-tooltip"` at pipeline_detail_page.py:1856 — reuse) | ladder — unique while one hover active |
| Context pill | 1 | `context-budget-pill` | — | testid on DEV ✓ (new field) |
| Context popover | 1 | `context-budget-popover`, `-tokens`, `-messages-count`, `-summaries-count`, `-percentage`, `-edit-button` | — | testid on DEV ✓ (new fields) |
| Clear chat | 1 | `chat-clear-button` (`chat_clear_button`) | — | testid on DEV ✓ |
| Chat input / send / msgs | 1 | `chat-message-input`, `chat-send-button` (`chat_send_button`), `chat-message-item`, `skill-test-last-response` | — | testid on DEV ✓; `chat-input` is a wrapper div (use `chat-message-input`) |
| Model selector | 1 | `model-selector-button` / `model-selector-name` | — | testid on DEV ✓ |
| Running node | 1+attr | `pipeline-node-card-{name}` + `[data-status="running"]` | — | testid on DEV ✓ (state = attribute filter) |
| LLM System | 1 | `pipeline-llm-node-system-value` (`llm_node_system_value`) | — | testid on DEV ✓ |
| Save | 1 | `agent-save-button` | — | testid on DEV ✓ |
| History rows | 1 | `run-history-list-item` | — | testid on DEV ✓ |
Reuse: `PipelineDetailPage.open_test_pipeline_panel`, `clear_chat`, `wait_for_embedded_chat_response`, `open_node_panel_by_card`/`select_node_by_js_click`, `fill_*` node helpers; fixture `pipeline_with_fstring_llm_id`. No existing field for `pipeline-test-panel-close/-resize-handle`, the context pill/popover, the history route round-trip — add as class-level fields. Width read = `bounding_box()['width']` (geometry, not a locator).

## Network Behavior
Send fires the predict via the existing conversation flow (WebSocket answer). Save = PUT application version. Width is client-only localStorage `pipelineTestPanelWidth:<id>`. No 4xx/5xx seen.

## Clarifications (case-text drift, not defects)
- **C1 (Step 7/8):** editing the pipeline **Description** does NOT block sending (Save becomes enabled, but `useIsPipelineYamlCodeDirty` compares the pipeline YAML; description is outside it — send stayed enabled, message went through, 4 items). A **node edit** (LLM System) does block, with the hint. The spec uses a node edit. If the case author intends Description to block, that is a product question (code intent: YAML-dirty gate, `TestPanel.jsx:32-34`).
- **C2 (Step 6/7a):** Run History is a separate route; coming back leaves the panel closed with an EMPTY conversation. Step 7a's "same conversation" holds for close/reopen of the panel, not for a trip to Run History. Page reload also drops the conversation (messages 0 after reload) while width persists.
- **C3 (Step 4):** pill shows "0%" for a short exchange (case example "1%").
- Step 12: persistence mechanism is per-pipeline localStorage; hold the width assertion with tolerance (+-2 px).

## Risks for the implementer
- Step 10 is time-sensitive: the poem run is ~5 s and `running` shows ~2 s after Enter; poll for `data-status=running` then close immediately. If it flakes, use a longer prompt (still the case's text) — do not weaken the "still highlighted after close" assertion.
- Banners intercept clicks; JS-click save/node card as in ELITEA-4719.

## Known Defects Found During Exploration
- none.

## Blocked Steps
- none.
