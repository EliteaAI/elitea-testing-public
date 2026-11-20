# Test Case: Agent test chat — Copy markdown / Copy text icons visible, clickable, confirmed by toast

## Metadata
- **TMS ID**: ELITEA-4755
- **Linked Story**: EliteaAI/elitea_issues#5838 (EL-5838 copy split)
- **Priority**: l1 (source: critical)
- **Environment Explored**: DEV https://dev.elitea.ai/app (live, 2026-11-20), headless pytest scratch probe via existing page objects
- **Status**: ready-for-automation

## Preconditions
- Authenticated (`auth_state`). A disposable agent created per-test via `agent_api.create_agent(name, desc, "You are a helpful assistant. Reply only with: PONG")` (same pattern as ELITEA-1874). Case's "Fairy Tale File Creator" is just an example ("any existing agent").
- Cleanup: `agent_api.delete_agent(id)` in `finally`.

## Test Data
- Request: `PING` (deterministic reply PONG; case allows any request).

## Test Steps
1. `AgentDetailPage.navigate(agent_id)` (opens `?viewMode=owner`). Verify `information_section` visible and `test_agent_button` visible/enabled.
2. `open_test_agent_panel()`. Verify `test_agent_panel`, `chat_message_input` visible.
3. `send_chat_message("PING")` + `wait_for_chat_response(initial_count=...)`. Verify response non-empty.
4. Verify on the last AI response: `chat-copy-markdown-button` and `chat-copy-text-button` both visible (observed visible w/o hover after completion).
5. Hover markdown icon -> tooltip text `Copy markdown` (observed `[role=tooltip]` = "Copy markdown").
6. Click it -> `toast-alert` (data-severity=info) + `toast-message` text `Markdown copied to clipboard.`. Toast auto-dismisses within ~6s (wait it out / wait toast hidden before step 8 so step 8 asserts the NEW toast).
7. Hover text icon -> tooltip `Copy text`.
8. Click it -> `toast-message` text `Text copied to clipboard.`.

## Expected Results
As case. Exact toast strings above (case text matches live; no drift).

## Coverage Map
**Axis 1**
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 open agent, Test Agent button visible | config page, button visible | step 1 | button visible | asserted |
| 2 click Test Agent | panel opens w/ input | step 2 | panel+input visible | asserted (welcome message not asserted: not a stated copy-feature observable; see Axis 2 note) |
| 3 send request | response generated | step 3 | response text non-empty | asserted |
| 4 icons visible | both visible | step 4 | is_visible x2 | asserted |
| 5 hover M | tooltip Copy markdown | step 5 | tooltip text | asserted |
| 6 click M | toast Markdown copied to clipboard. | step 6 | toast-message text | asserted |
| 7 hover copy | tooltip Copy text | step 7 | tooltip text | asserted |
| 8 click copy | toast Text copied to clipboard. | step 8 | toast-message text | asserted |
**Axis 2**: "clickable" -> `is_enabled()` before each click (grounded: Pass criteria "visible and clickable"). Welcome message: analyst did not verify it live in this run; optional, omit.

## Concrete Handles (verified live on DEV)
| Element | Rung | Handle | suggested_testid | Provenance |
|---|---|---|---|---|
| Test Agent button | testid | `AgentDetailPage.test_agent_button` | - | existing, reused |
| Test panel / input | testid | `test_agent_panel`, `chat_message_input` (`chat-message-input`) | - | existing |
| Copy markdown icon | testid | `chat-copy-markdown-button` (`ChatPage.copy_markdown_action_button`) | - | testid on DEV ✓ |
| Copy text icon | testid | `chat-copy-text-button` (`ChatPage.copy_text_action_button`) | - | testid on DEV ✓ |
| Toast | testid | `toast-alert`, `toast-message` (`AgentDetailPage.toast_alert/toast_message`) | - | testid on DEV ✓ |
| Tooltip | role | `role=tooltip` (MUI popper) — no testid; scope by role, read text | `chat-copy-tooltip` | ladder — unique while hovering |

Use `.last` / scope to the last AI message item (several messages may carry the buttons); scope via existing last-AI-message accessor, not positional picks of siblings. Check whether `ChatPage` copy descriptors work on `AgentDetailPage` (the scratch probe used raw page locators for these; implementer must declare/reuse class-level fields on AgentDetailPage).

## Network / Side channels
Clipboard write is client-side; toast is the observable (don't read clipboard — headless permissions). No console errors checked in probe beyond none surfaced.

## Known Defects
None.

## Blocked Steps
None.

## Automation Hints
- Page object: AgentDetailPage; add class-level copy_markdown/copy_text/tooltip fields (or reuse ChatPage descriptors via scope). Marker pair: tms ELITEA-4755 + allure.issue.
- Transit gotcha (flag): in this analysis environment `automation/.env.test` was absent so `APP_PREFIX` defaulted to "" -> `navigate()` hit `/agents/...` -> 404 "Page Not Found" (existing ELITEA-1874 spec failed for that reason). Setting `APP_PREFIX=/app` fixed it. Environment issue, not a product regression.
- Wait for the first toast to dismiss before clicking the second icon.
