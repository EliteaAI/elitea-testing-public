# Test Case: Send in a new chat and switch to another chat at once

## Metadata
- **TMS ID**: ELITEA-4956
- **Linked Story**: EliteaAI/elitea_issues#7385
- **Priority**: l1 (TMS `critical`)
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed), 2026-11-27, headless scripted pytest/Playwright probes (2 full live runs)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation
- **Neighbour reused**: `automation/tests/ui/chat/test_chat_leave_and_return_running_agent.py` (ELITEA-4953, on main) — fixtures `long_runner_agent`, conversation B creation, `ChatPage.get_conversation_running_icon`, `start_recording_delete_requests`. Different observable (new, not-yet-created chat; race on Send) so NOT already-covered / extend.

## Fixtures
Same self-provisioning as ELITEA-4953 (`test-data/chat-runs-continue/` openapi + longrunner instructions; agent `autotest_runner_<sfx>`, two toolkits, linked). The 4953 fixtures live inside the 4953 spec file, not `automation/fixtures/` (rule: fixtures belong in `fixtures/`); the implementer should move/share `long_runner_agent` into `automation/fixtures/` (flag to lead) rather than import from a test module.
Only conversation **B** (idle, API-created `autotest_idle_B_<sfx>`) is pre-created. The target chat is created BY THE UI (New chat). Cleanup: delete B, the agent, toolkits, and the UI-created chat (found by id diff / API list; delete via `ConversationAPI.delete_conversation`).

## Test Data
- Message: `The word is SMK4.` (the case's `#R7385LongRunner ` prefix is typed as `#<agent name>` and selected from the panel; the typed text does not stay in the message — see Observations). Expected final line `RUN-DONE SMK4`. Run ~35-40 s.

## Test Steps (live-observed)
1. Navigate to `/chat/<B>` (via `ChatPage.navigate_to_chat(conversation_id=B)`, set `APP_PREFIX=/app`), `dismiss_banner_if_present()`. Record the existing `chat-conversation-item-*` ids. Click `sidebar-new-chat-button` (URL `/app/chat?create=1`, greeting + `chat-message-input` visible). Click the input, type `#<agent name>` (press_sequentially); a "SEARCH RESULTS" panel appears with the agent (text = agent name, subtitle "Agent"); click the name (`get_by_text(name, exact=True).last`). Participant is set: `ChatPage.switch_participant_button` count 1 (contains agent name). Click input, type `The word is SMK4.`.
   - Verify: participant = the agent; `chat-send-button` present.
2. Send + switch in ONE browser task: `page.evaluate("(bid)=>{document.querySelector('[data-testid=chat-send-button]').click(); document.querySelector('[data-testid=\"chat-conversation-item-'+bid+'\"]').click()}", B)` — took ~30 ms. After ~2.5 s: URL is `/app/chat/<B>?name=...` (user stays on B, not pulled back to the new chat); 0 `[role=dialog]`; 0 recorded DELETE requests (`start_recording_delete_requests` before send).
3. New row appears in the list (one new `chat-conversation-item-<id>` not in the pre-send id set) containing `chat-list-item-running-icon` with `aria-label="Generating…"` (count 1). Its title is a GENERATED name (observed `Word SMK4.`, and in one run transiently `#autotest_runner_…The word SMK4.`) — do NOT assert the title text; assert the row/spinner only.
4. Wait for `chat-list-item-running-icon` detached (`wait_for(state="detached", timeout=90s)`, observed ~40 s), then click the new row: URL `/app/chat/<id>`; two `chat-message-item`: user message containing `The word is SMK4.` and the agent answer containing `RUN-DONE SMK4` (second line `Post 3 "ea molestias…" was written by Leanne Graham…`).
5. API oracle (hard): `ConversationAPI.get_message_traces(<new id>)["rows"]` -> 5 `kind=="tool_call"` rows (waitSeconds, getPost, waitSeconds, getUser, waitSeconds) + 1 `thinking_step`; `has_running_task(<new id>)` False after the run; `get_message_groups` final `is_streaming` False.

## Observations / gotchas
- **Race**: send and row click must be one JS task (the case Notes say Playwright actionability alone costs ~2 s). Done via `page.evaluate` on the two testid elements (legit here: the case itself prescribes it; these are not raw selectors in a method — declare `chat-send-button` and the `chat-conversation-item-{}` templates via existing ChatPage fields/constants, evaluate on `locator.evaluate("e=>e.click()")` of two locators if possible: `send.evaluate` then `row.evaluate` in a single `page.evaluate`-free way is NOT atomic — keep one `page.evaluate` taking the testids as args, constants from ChatPage).
- Sometimes the run finishes extremely fast with a bad (1st) result when the `#agent` is not selected (agent not participant): the answer was plain "Got it. The word is SMK4." from the default LLM in my first probe (picker click by role=option matched nothing, text typed stayed in the message). **Assert participant set (step 1) before sending** or the run has no tools.
- The platform banner (`platform-banner-close`) can intercept clicks; `dismiss_banner_if_present()` first.
- `.env.test` absent on this host: `APP_PREFIX` defaults to `""` (navigate hits `/chat/..` -> 404). Environment concern only (run with `APP_PREFIX=/app`); pytest-rerunfailures not installed in this venv so `addopts` needed `-o addopts=""` — environment note for lead, not a product matter.
- New chat is created without any dialog; `GET conversation` for the new id works; no console/network errors observed in probes (side channel not exhaustively captured — DELETE count asserted).

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| New chat button | 1 | `sidebar-new-chat-button` (text "New chat"; NOT `sidebar-create-button`, which `ChatPage.click_create_new_conversation` still uses -> 404-prone/stale; implementer to verify and use the new testid) | - | testid on DEV ✓ |
| Message input | 1 | `chat-message-input` | - | testid on DEV ✓ |
| Hash search result row | 2/text | text = agent name, exact, within "SEARCH RESULTS" panel (agent names are unique per run) | `chat-hash-search-result-item-{}` | ladder — no testid on DEV; text unique (autotest_ + uuid) |
| Participant indicator | existing | `ChatPage.switch_participant_button` | - | exists on main |
| Send | 1 | `chat-send-button` | - | testid on DEV ✓ |
| Conversation row | 1 | `[data-testid="chat-conversation-item-{id}"]` | - | testid on DEV ✓ |
| Row spinner | 1 | `chat-list-item-running-icon` `aria-label="Generating…"` | - | testid on DEV ✓ |
| Messages | 1 | `chat-message-item` | - | testid on DEV ✓ |

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition fixtures/agent/B | exist | fixtures | self-provisioned | covered (self-provisioning, case precondition says pre-existing) |
| Precondition DevTools Network open | watch DELETE /task | Step 2 | recorded DELETE requests == [] | covered |
| Step 1 | agent is participant | Step 1 | participant button text | covered |
| Step 2 | B opens, user stays on B | Step 2 | URL stays /chat/<B> after ~2.5 s poll | covered |
| Step 3 | new chat listed, generated name, spinner | Step 3 | new row + aria-label | covered; name NOT asserted (generated, nondeterministic) -> clarification |
| Step 4 | `RUN-DONE SMK4` in new chat with both messages | Step 4 | message texts | covered |
| Pass: chat created & listed w/ spinner; run completes | | Steps 3-5 | | covered |
| Fail: not pulled back / run not lost | | Steps 2, 5 | URL; traces/has_running_task | covered |
| Case Notes: API oracle, DELETE /task | | Step 5 | traces, has_running_task | covered (Axis 2 grounded in case Notes) |
| Case Notes: clear fixture conversations | | n/a | fresh chat each run, no clearing needed | covered by construction |

## Known Defects
None new. (#7763 chip tool-name loss is not in this case's expectations; do not assert chip names mid-run.)

## Notes for the implementer
- 90 s ceiling on the run wait; test total ~70 s.
- Prefer a family-free separate spec file; reuse 4953's agent fixture (relocate into `automation/fixtures/` shared by both).
- Pytest markers: ui, chat, p0, regression; TMS pair `ELITEA-4956` + allure.issue to the case file blob URL.

## Adjustment — class D (teardown hygiene, issue #3050)
No expected-result or step changes. Teardown only:
- `idle_conversation_b` finalizer stops a still-running task (`has_running_task` -> `stop_running_task`) on B and on the UI-created chat(s) before deleting; best-effort, never masks the verdict.
- After the deletes, each created conversation is checked with `has_conversation`; leftovers are logged as warnings only. Agent/toolkit leftovers stay with `_warn_leftovers`.
- The new-chat sweep lists with `limit=100` (`ConversationAPI.list_conversations(limit=None)` gained an optional param; default behaviour unchanged) — the API pages ungrouped chats by 10, so the new chat could be missed.
