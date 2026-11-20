# Test Case: Agent test chat — USER message Copy markdown / Copy text icons visible, clickable, confirmed by toast

## Metadata
- **TMS ID**: ELITEA-4760
- **Linked Story**: EliteaAI/elitea_issues#5838 (EL-5838 copy split); manual source ELITEA-4754
- **Priority**: l1 (source: high)
- **Environment Explored**: DEV https://dev.elitea.ai/app (live, 2026-11-20), scratch pytest probe via existing page objects (Playwright MCP browser unavailable in sandbox: no chrome), `APP_PREFIX=/app`
- **Status**: ready-for-automation

## Neighbour check (not coverage)
ELITEA-4755 (`tests/ui/agents/test_agent_test_chat_copy_icons.py`, merged) asserts the icons under the **AI response** (`chat-copy-*-button`, `AgentDetailPage._last_response_copy_icon`). 4760's observable is the icons under the **user's own message** — different component (`UserMessage.jsx`), different testids. Not covered: own test (may live in the same file/class, reusing its structure). Case allows "agent or skill"; automate the agent path (same transit as 4755).

## Preconditions
- Authenticated (`auth_state`). Disposable agent via `agent_api.create_agent(name, desc, "You are a helpful assistant. Reply only with: PONG")`; `agent_api.delete_agent(id)` in `finally`. Case's "Bugs & Features project" is an example; default project works.

## Test Data
- Message: `Create a fairy tale about a dragon.` (case text; reply content irrelevant, PONG).

## Test Steps
1. `AgentDetailPage.navigate(agent_id)`; `test_agent_button` visible. `open_test_agent_panel()`; `test_agent_panel` + `chat_message_input` visible.
2. `send_chat_message(msg)` + `wait_for_chat_response(initial_count=...)`. Verify the user message text appears in the panel (the chat-message-item holding the user bubble; see Handles) — observed with sender "AA" avatar/timestamp; timestamp/sender not separately probed (assert text only, or omit).
3. Both `user-message-copy-markdown-button` and `user-message-copy-text-button` visible and enabled (observed visible without hover after response completed; count 1 each in panel).
4. Hover markdown icon -> `[role=tooltip]` text `Copy markdown`. Click -> `toast-message` `Markdown copied to clipboard.` (`toast-alert` data-severity=info). Wait `toast-message` count 0 (<=20s).
5. Hover text icon -> tooltip `Copy text`. Click -> toast `Text copied to clipboard.`.

## Expected Results
As case. Toast strings and tooltips confirmed live; no case-text drift.

## Coverage Map
**Axis 1**
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 open agent, Test Agent | panel opens | step 1 | button/panel/input visible | asserted |
| 2 send message | user message appears (sender+timestamp) | step 2 | user message text visible | asserted (text); sender/timestamp not probed — out-of-scope of the copy observable, see Axis 2 |
| 3 icons visible | both visible | step 3 | visible x2 | asserted |
| 4 click Copy markdown | clickable + toast Markdown copied to clipboard. | step 4 | enabled + toast text | asserted |
| 5 click Copy text | clickable + toast Text copied to clipboard. | step 5 | enabled + toast text | asserted |
| Precondition skill alternative / Bugs & Features project | - | - | - | out-of-scope: agent path, default project |
**Axis 2**: tooltips (aria-label + MUI tooltip, same as 4755/4757 pattern) — grounded in case's icon names. `is_enabled` grounded in "clickable". Nothing else.

## Concrete Handles (verified live on DEV)
| Element | Rung | Handle | suggested_testid | Provenance |
|---|---|---|---|---|
| Test Agent button / panel / input | testid | `AgentDetailPage.test_agent_button`, `test_agent_panel`, `chat_message_input` | - | existing |
| User copy markdown | testid | `user-message-copy-markdown-button` (`ChatPage.user_copy_markdown_action_button` exists; AgentDetailPage needs its own class-level field) | - | testid on DEV ✓ (count 1 in panel; UserMessage.jsx:248 on origin/main) |
| User copy text | testid | `user-message-copy-text-button` (NO descriptor exists anywhere in pages/ — implementer adds) | - | testid on DEV ✓ (UserMessage.jsx:266) |
| Toast | testid | `toast-alert`, `toast-message` (`AgentDetailPage.toast_alert/toast_message`) | - | testid on DEV ✓ |
| Tooltip | role | `AgentDetailPage.open_tooltips` `.last` | `chat-copy-tooltip` | ladder (existing) |
| User message container | testid | ancestor chain: button > `div.actionButtons` > div > `li[data-testid=chat-message-item]` > `ul[chat-message-list]` | - | testid on DEV ✓ (use `chat-message-item` if scoping is needed; icons are unique to user bubble so `.last`/direct scoping to panel works since AI uses different `chat-copy-*` testids) |

Tip: since user-message ids differ from the AI ones, each is unique in the panel after one exchange; don't pick siblings positionally.

## Network / Side channels
Clipboard write is client-side; toast is the observable (do not read clipboard). No console errors observed.

## Known Defects
None.

## Blocked Steps
None.

## Automation Hints
- Page object: add class-level `user_copy_markdown_button` / `user_copy_text_button` to AgentDetailPage (parallel to `chat_copy_*_button` ~agent_detail_page.py:3116) plus click/hover helpers (generalise `_last_response_copy_icon`). Marker pair tms ELITEA-4760 + allure.issue.
- Wait for the first toast to dismiss before clicking the second icon.
- Env gotcha as 4755: need `APP_PREFIX=/app` if `.env.test` absent.
