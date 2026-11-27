# Test Case: Switch chats during an agent run, come back during the run and after it ends

## Metadata
- **TMS ID**: ELITEA-4953
- **Linked Story**: EliteaAI/elitea_issues#7385 (known issue elitea_issues#7763, OPEN)
- **Priority**: l1 (TMS `critical`)
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed), 2026-11-27, headless Playwright scripted probes
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation

> Classification note (declared improvisation, `.agents/testing.md` § Analysis-time entry): steps 4-5 hit the
> OPEN known issue #7763 deterministically (restored/late chips lose the tool name). Everything else passes live.
> Implementer: write the tool-name assertion as the CORRECT expected behaviour ("<toolkit>: <tool>") inside
> `expect.soft()`/soft-failure aggregation with `# Known defect: elitea_issues#7763`; all other assertions are hard.

## Fixtures (do NOT exist on a fresh env; created by me on DEV, ids below, but the test must be self-provisioning)
Source files: `../onetest-ai-tm-Elitea/test-data/chat-runs-continue/` (`postman-echo-delay.openapi.yaml`, `jsonplaceholder.openapi.yaml`, `r7385-longrunner.instructions.md`).
Provisioning verified via API (token auth, `AgentAPI([])`/`ToolkitAPI([])`/`ConversationAPI([])` work with empty cookies + `ELITEA_API_TOKEN`):
1. `ToolkitAPI.create_toolkit(name, desc, "openapi", {"spec": <yaml text>, "selected_tools": ["waitSeconds"], "openapi_configuration": {"private": True, "elitea_title": ""}})` for "Postman Echo delay" (DEV id 919) and "JSONPlaceholder" (`["getPost","getUser"]`, id 920). Both 201.
2. `AgentAPI.create_agent_full({... "type":"interface", versions:[{name:"base", instructions:<longrunner md>, llm_settings: _default_llm_settings() with reasoning_effort "low", agent_type:"openai", meta:{step_limit:25}, tools:[] ...}]})` -> "R7385LongRunner" (DEV id 4994, version 5146).
3. Link each toolkit: `PATCH {base}/elitea_core/tool/prompt_lib/{pid}/{toolkit_id}` json `{entity_id: agent_id, entity_version_id: version_id, entity_type:"agent", has_relation:true, selected_tools:[...]}` -> 201.
4. Conversations A and B: `conversation_api.create_conversation(name)` (name max 32 chars). B stays empty/idle. A is created fresh so no clearing is needed (else `DELETE .../elitea_core/messages/prompt_lib/{pid}/{conv}` -> 204).
Unique-name the agent/toolkits per run (`autotest_`+suffix) and delete in teardown; the participant picker search then uses that name.

## Test Data
- Message in A: `The word is SMK1.`; expected final answer first line `RUN-DONE SMK1`.
- Run length ~35-40 s on DEV (observed "Thought for 35 secs"); tool order: waitSeconds(10.2s), getPost, waitSeconds, getUser, waitSeconds.

## Test Steps (live-observed)
1. Open A (`/chat/<A>`), close the platform banner (`platform-banner-close`; it intercepts clicks), add the agent as participant (plus-menu -> Agents -> search -> pick; see `ChatPage.add_agent_participant` or the testid below), send message.
   - Verify: ~2 s later `chat-list-item-running-icon` count 1 (A's row), `chat-inject-button` (Stop) present, `chat-answer-tool-chip` >=1 by ~4 s.
2. After the first chip, click B's row `chat-conversation-item-<B>`.
   - Verify: URL becomes `/chat/<B>`, B is empty (0 `chat-message-item`), `[role=dialog]` count 0, recorded `DELETE` requests == 0 (page.on("request") filter on method DELETE / url contains `/task`). Observed 0 DELETE, 0 dialogs.
3. In the list, A's row `chat-conversation-item-<A>` contains `chat-list-item-running-icon` with `aria-label="Generating…"` (the tooltip is that label; hovering renders no `[role=tooltip]` in headless, so assert the aria-label).
4. ~8 s later click A's row again (still running).
   - Observed on return (t~21 s): `chat-answer-tool-chip` 2 inside `chat-answer-thought-accordion`; "Agent is running…" bubble visible (text; a `progressbar` span + the string, no testid). Chip text: `Postman Echo delay · 10.2s`, `JSONPlaceholder: getPost · 120ms` — i.e. NO tool name on restored/earlier chips (#7763) and later chips (`Postman Echo delay · 10.1s`) too. Row spinner still present.
   - **Stop button NOT found after return**: `chat-inject-button` count 0 and no Stop-like button in the composer footer (screenshot-confirmed: composer shows "Reply to R7385LongRunner..." with no Stop). Case expects Stop. Only DIRECT live (no-leave) run shows `chat-inject-button`. Treat as a second symptom of the same area; assert Stop soft with `# Known defect` pointing at #7763 and flag to lead (see findings) - not independently filed as it needs a human decision whether it belongs to #7763.
5. Stay in A: chips grow live (2 at 21 s, 3 at 27 s, final 5 at ~39 s, and running icon gone at ~39 s). Late steps DO appear before the final answer (case "Fail" clause "only with the final answer" did not reproduce on DEV today; chip names do not appear until the end: at 39 s all 5 read `<Toolkit>: <tool>`).
   - Final: message text ends `RUN-DONE SMK1` (second line `Post 3 "ea molestias quasi exercitationem repellat qui ipsa sit aut" was written by Leanne Graham (Sincere@april.biz).`), tool chips 5.
6. Click B then A. Final answer present, `chat-list-item-running-icon` count 0 on A's row, no "Agent is running…". **The accordion is collapsed after re-open**: 0 `chat-answer-tool-chip` until you click the accordion header button (`[data-testid=chat-answer-thought-accordion] button` first; the Paper itself is not the click target). Expanded -> 5 chips: `Postman Echo delay: waitSeconds · 10.2s`, `JSONPlaceholder: getPost`, `...: waitSeconds`, `JSONPlaceholder: getUser`, `...: waitSeconds`.
7. API oracle `GET {api_base}/elitea_core/message_traces/prompt_lib/{pid}/{A}` -> 200 `{total, rows}`; rows = 6, NOT 5: 5 `kind=="tool_call"` (`tool_name` waitSeconds, getPost, waitSeconds, getUser, waitSeconds, in order) + 1 `kind=="thinking_step"` (`step_type` ChatGeneration). Assert on the filtered tool_call rows == UI chips in order (case text "5 traces" is case-text drift: filter by kind).
   - Also: `GET .../conversation/prompt_lib/{pid}/{A}` -> message_groups; final group `is_streaming:false`; `GET .../conversations/prompt_lib/{pid}?limit=100` -> row `has_running_task` False after end (and mid-run it should be True; I did not poll it mid-run - verify when implementing).

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Conversation row | 1 | `[data-testid="chat-conversation-item-{id}"]` (`ChatPage.CONVERSATION_ITEM`) | - | testid on DEV ✓ |
| Row running spinner | 1 | `chat-list-item-running-icon`, `aria-label="Generating…"` | - | testid on DEV ✓ (span, scope under the row) |
| Stop / inject button | 1 | `chat-inject-button` (existing `ChatPage.chat_inject_button`) | - | testid on DEV ✓ (present only in a never-left run; absent after return) |
| Tool chip | 1 | `chat-answer-tool-chip` (text `<toolkit>: <tool> · <dur>`) | - | testid on DEV ✓ |
| Chip duration | 1 | `chat-answer-chip-duration` | - | testid on DEV ✓ |
| Thought accordion | 1 | `chat-answer-thought-accordion` (Paper); toggle = its inner `button` (`aria-expanded` on the button) | - | testid on DEV ✓; header button ladder: css `[data-testid=chat-answer-thought-accordion] button` unique (first) |
| Model chip | 1 | `chat-answer-model-chip` | - | testid on DEV ✓ |
| "Agent is running…" indicator | 3/text | text "Agent is running" (only one in page) with MUI `progressbar` | `chat-agent-running-indicator` | ladder - no testid on DEV; unique text on the page |
| Platform banner close | 1 | `platform-banner-close` | - | testid on DEV ✓ |
| Agent in participant picker | 1 | `agents-menu-item-agent-<pid>-<agent_id>`; search `get_by_placeholder("Search agents...")`; `plus-menu-button`, menuitem "Agents" | - | testid on DEV ✓ |
| Message item / input | 1 | `chat-message-item`, `chat-message-input`, `chat-message-list` | - | testid on DEV ✓ |

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 | run starts, first tool step | step 1 | chip>=1, running icon | covered |
| Step 2 | B opens at once, no dialog, no DELETE /task | step 2 | request listener, dialog count | covered |
| Step 3 | row spinner "Generating…" | step 3 | aria-label | covered (tooltip -> aria-label) |
| Step 4 | steps with tool names, Stop, "Agent is running…" | step 4 | chips, text | partial: tool names + Stop soft (#7763) |
| Step 5 | live steps, running-step spinner, RUN-DONE SMK1 | step 5 | chip growth poll, final text | covered; running-step spinner not asserted (no stable handle observed; not identified) -> clarification |
| Step 6 | final answer, 5 steps, no spinner | step 6 | expand accordion, chips==5, icon 0 | covered |
| Step 7 | 5 traces == UI | step 7 | API tool_call rows | covered with kind filter (case drift: 6 rows incl. thinking_step) |
| Axis 2 extra | `has_running_task` false at end, `is_streaming` false | step 7 | API | grounded in case Notes oracle |

## Known Defects
- elitea_issues#7763 (OPEN): restored/late chips lack tool name until the run ends. Reproduced 3/3 today. No new issue filed.
- Possible additional symptom: Stop absent after return (see step 4); unfiled, lead decides.

## Notes for the implementer
- Run ~40 s; give the test a 90 s ceiling. Navigate between chats ONLY by clicking list rows (never `goto`).
- `chat-list-item-running-icon` is attached/detached with the run; poll with `wait_for(state="detached")` at the end.
- Close `platform-banner-close` before any click on the page; it blocks pointer events.
- Use `ConversationAPI([])` style token auth for the API oracle, or the cookie-based fixtures; cleanup agent, toolkits, A, B in teardown.
