# Test Case: Leave a running chat for New chat, Agents, browser Back and Artifacts, then see the New response dot

## Metadata
- **TMS ID**: ELITEA-4954
- **Linked Story**: EliteaAI/elitea_issues#7385
- **Priority**: l1 (TMS `critical`)
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed), 2026-11-27, headless scripted pytest probe (live)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation

> Neighbour: ELITEA-4953 (`automation/tests/ui/chat/test_chat_leave_and_return_running_agent.py`, merged to main) shares the
> fixtures (`long_runner_agent`, `two_conversations`), page object and flow. It proves a DIFFERENT observable
> (row-click leave and return, spinner, steps), so this is NOT `already-covered`/`extend-existing`: new spec,
> reusing the fixtures (move the two fixtures to `automation/fixtures/` or import them; implementer decides, see Notes).
> No known defect (#7763 is not hit: no mid-run return to A is asserted; final chips read `<toolkit>: <tool>` after the end).

## Fixtures
Exactly as ELITEA-4953 AFS (self-provisioned: 2 OpenAPI toolkits + R7385LongRunner agent linked, unique `autotest_` names, torn down).
Conversation A: fresh `create_conversation` (no clearing needed). **B is NOT needed** by this case (case text's "idle conversation B" is unused by steps 1-6); do not create it.
Message: `The word is SMK2.`; expected final first line `RUN-DONE SMK2`.
Env note: the run needs `APP_PREFIX=/app` and the API clients need the storage-state cookies (the normal fixtures provide them).

## Test Steps (live-observed, one pass, run ended ~40-45 s after send)
1. Open A (`navigate_to_chat(conversation_id=A)`), `dismiss_banner_if_present()`, `add_agent_participant_by_id`, `expand_participants_panel_via_toggle()`, assert participant row count 1 and `switch_participant_button` has the agent name (REQUIRED: without the wait, send goes to a no-agent chat and no tool chip ever appears), start DELETE recorder + `page.on("dialog")` recorder, `send_message`.
   - Verify: `chat-list-item-running-icon` in A's row count 1; `chat-answer-tool-chip` first visible (~3 s).
2. Click `sidebar-new-chat-button` ("New chat").
   - Observed: URL `/app/chat`, composer `chat-message-input` present and enabled (immediately, ~1 s), 0 dialogs, 0 DELETE, A's row still has the running icon.
3. Open Agents: click `sidebar-explore` then `sidebar-explore-agents` (`a[href=/app/575/agents]`).
   - Observed: URL `/app/agents` at once; 0 dialogs, 0 DELETE, no "Response generation is still in progress" / "Output is still generating" text (body innerText check).
4. `page.go_back()`: lands on `/app/chat/<A>?name=...` (A is reopened, still running). Then click link `Artifacts` (`get_by_role("link", name="Artifacts")`, href `/app/<pid>/artifacts`): URL `/app/artifacts`.
   - Observed: each page opens at once; texts absent; 0 dialogs; 0 DELETE; `dialog` recorder empty. (Back goes to A, not to the New-chat page: assert URL via regex `/chat(/|$)`, not exactly A or exactly empty.)
5. Stay on Artifacts until the run has ended (observed done well inside 55 s from send; poll the API `has_running_task(A)` False with a 90 s ceiling, never a sleep). Then click `sidebar-new-chat-button` (URL `/app/chat`). **On /chat the sidebar is COLLAPSED after arriving from Artifacts** (rows not rendered, 0 `chat-conversation-item-*`): click `sidebar-toggle` (the case's "New chat → chat list") to expand it, in-app only (no goto/reload).
   - Observed: A's row `chat-conversation-item-<A>` contains `[data-testid="chat-list-item-unread-badge"]` with `data-reason="new_response"`, `aria-label="New response"` (hover renders no `[role=tooltip]` in headless; assert aria-label/data-reason). Running icon count 0. While on Agents/Artifacts the sidebar list is not rendered, so badge/icon are only checkable after returning to /chat.
6. Click A's row (`click_conversation_item(A)`).
   - Observed: badge count 0 at once; `RUN-DONE SMK2` in the last message; tool chips 5 after `expand_thought_accordion()` (accordion starts collapsed): `<toolkit>: waitSeconds · 10.3s`, `<toolkit>: getPost`, `waitSeconds`, `getUser`, `waitSeconds`; no streaming indicator. Re-check after New chat + toggle: badge stays 0 ("stays gone").
   - Oracle: `conversation_api.get_message_traces(A)["rows"]` filter `kind=="tool_call"` == [waitSeconds, getPost, waitSeconds, getUser, waitSeconds]; last group `is_streaming` False; `has_running_task(A)` False (mid-run True).

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| New chat button | 1 | `sidebar-new-chat-button` (collapsed sidebar: icon only) | - | testid on DEV ✓ (not yet a ChatPage field; declare `LocatorDescriptor(testid=...)`) |
| Sidebar toggle | 1 | `sidebar-toggle` (`ChatPage.sidebar_toggle`, legacy `fallback=` present - do not copy) | - | testid on DEV ✓ |
| Explore menu trigger | 1 | `sidebar-explore` | - | testid on DEV ✓ (opens `sidebar-explore-menu`) |
| Agents menu entry | 1 | `sidebar-explore-agents` | - | testid on DEV ✓ |
| Artifacts nav link | 2 | role=link name "Artifacts" (href `/app/<pid>/artifacts`) | `sidebar-artifacts-link` | ladder - no testid on DEV; unique in sidebar |
| Conversation row | 1 | `chat-conversation-item-<id>` (`ChatPage.get_conversation_item`) | - | testid on DEV ✓ |
| Running icon | 1 | `chat-list-item-running-icon` (`get_conversation_running_icon`) | - | testid on DEV ✓ |
| New response dot | 1 | `chat-list-item-unread-badge`, `data-reason="new_response"`, `aria-label="New response"`; scope `.within(row)` | - | testid on DEV ✓ (source: ConversationRunIndicator.jsx; `waiting` reason is the other value) |
| Composer | 1 | `chat-message-input` | - | testid on DEV ✓ |
| Dialogs | 2 | `ChatPage.open_dialogs` (role=dialog) | existing | declared |
| Forbidden texts | text | "Response generation is still in progress", "Output is still generating" | - | assert `get_by_text(...)` count 0 via declared descriptors (or body text) |
| Chips / accordion / DELETE recorder | - | existing `answer_tool_chip`, `expand_thought_accordion`, `start_recording_delete_requests` | - | reused from 4953 |

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 | run going | step 1 | running icon, chip, has_running_task True | covered |
| Step 2 | empty chat at once, composer enabled | step 2 | url, composer enabled | covered |
| Step 3 | Agents opens at once | step 3 | url | covered |
| Step 4 | Back + Artifacts open; no dialog/text | step 4 | url, texts, dialogs, DELETE | covered |
| Step 5 | dot with "New response" in A's row | step 5 | badge in row, data-reason, aria-label | covered (tooltip -> aria-label; sidebar must be expanded via toggle) |
| Step 6 | answer, 5 steps, dot gone and stays gone | step 6 | text, chips==5, badge 0 twice | covered |
| Pass: no `DELETE /task` for four navigations | | steps 2-4 | request recorder == [] | covered |
| Precondition: idle conversation B | unused by steps | - | - | out-of-scope (case-text clarification) |
| Axis 2: API oracle | traces, is_streaming, has_running_task | step 6 | API | grounded in case Notes |

## Notes for the implementer
- Spec file suggestion: `automation/tests/ui/chat/test_chat_leave_running_chat_new_response_dot.py`; reuse 4953's fixtures by moving them to `automation/fixtures/` (rule: fixtures not in test files) or minimal import; drop the B fixture.
- Never `goto`/reload after the run starts (the dot is browser-only); no sleeps: wait `has_running_task` False via polling helper, then in-app nav.
- Timing: the run ends ~40-45 s after send; observed ordering is fine because navigation takes ~2 s total. Test ceiling ~120 s.
- Do not wait for badge while on Agents/Artifacts (list not rendered).
- Local env note: this host has no `.env.test`; `APP_PREFIX=/app` and `HEADLESS=true` were passed as shell env.
- TMS file: `chat/chat-runs-continue-in-background/ELITEA-4954_leave-a-running-chat-for-new-chat-agents-browser-back-and-ar.md`.
