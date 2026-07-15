# Test Case: Agent execution — instructions field alone does not prevent execution (name+description sufficient)

## Metadata
- **TMS ID**: ELITEA-1897
- **Linked Story**: none
- **Priority**: l2 (source case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaAI/EliteaUI `automation/testids` → DEV backend, project `Private` id `399`)
- **User set**: `${TEST_USER}` (localhost `auth_state` skip-login via `VITE_DEV_TOKEN`, user `project_user_659`)
- **Analyst**: qa-engineer (agent), 2026-07-15
- **Status**: defect-found (blocked on an already-filed, unresolved regression — see § Known Defects)

## Preconditions
- User is logged in to the Elitea platform (satisfied automatically on localhost via `auth_state`/`VITE_DEV_TOKEN` — no Keycloak login step needed in this environment).

## Test Data
### reuse-existing
- None required — the case is entirely self-contained (creates its own agent).

### generate-per-test (in test setup, cleaned up in its own teardown)
- Agent name: `autotest_ELITEA1897_confirm` (or `f"autotest_{request.node.name}"[:32]` per the project's existing naming convention, see `agent_with_toolkit_instructions` fixture in `tests/ui/chat/test_agent_with_toolkit_chat.py`)
- Agent description: free text, e.g. "Agent for ELITEA-1897 — name+description+instructions execution check"
- Agent instructions: free text that does NOT reference tools/toolkits — case intent is to prove a *plain* instructions field doesn't block execution, so keep instructions toolkit-free (unlike the existing `agent_with_toolkit_instructions` fixture, which exists specifically to force tool use)
- Test message: `"Reply with: CONFIRMED"` (literal, per TMS case Test Data table)
- Expected response substring: `"CONFIRMED"` (case-sensitive per case; recommend `.upper()` containment check to avoid false negatives from incidental casing)

## Test Steps

**BLOCKED before step 1 completes** — see § Known Defects Found During Exploration.
Steps below are the case's intended flow; steps 2–4 could not be executed live
because step 1 (agent creation) 400s on save, both via the UI form and via the
API fixture path (`AgentAPI.create_agent()`) that existing tests use to bypass
the UI form. This is a defect in the product/test-client default `llm_settings`
payload, not a locator or case-authoring problem.

1. Navigate to `${BASE_URL}/agents/create`
   - **Verify**: "New Agent" tab/form is shown
2. Fill Name (`agent-name-input`), Description (`agent-description-input`), Instructions (`agent-instructions-input`)
3. Click Save (`agent-save-button`)
   - **Verify** (per case): agent created successfully, lands on `/agents/all/{id}`
   - **OBSERVED (2026-07-15, live)**: Save does NOT navigate away. `POST /api/v2/elitea_core/applications/prompt_lib/399` → **400 Bad Request**:
     `{"type": "value_error", "loc": ["versions", 0, "llm_settings"], "msg": "Value error, temperature is not allowed together with a reasoning_effort (other than 'none') — reasoning models reject a custom temperature"}`.
     A toast/alert surfaces the same message to the user; the form does not clear or recover; retry reproduces the identical error (deterministic, not intermittent).
4. In the embedded chat panel (`chat-message-input` / `chat-send-button`), send `"Reply with: CONFIRMED"`
   - **NOT REACHED** — no agent exists to navigate to.
5. Verify the agent responds with a message containing `"CONFIRMED"` (`chat-message-item` / `skill-test-last-response` testids)
   - **NOT REACHED**
6. Verify no error state / "waking the agent" spinner hangs indefinitely
   - **NOT REACHED** — no dedicated spinner/hang-detection testid or page-object method exists anywhere in `automation/pages/agent_detail_page.py` today (confirmed by full-file review); this assertion has no existing handle to reuse and will need one authored once step 1 is unblocked (see § Automation Hints).

## Expected Results
- Per case: agent created; embedded chat responds with a message containing "CONFIRMED"; no persistent spinner/error state.
- **Actual (observed)**: agent creation itself fails at the API boundary before any chat interaction is possible. See § Known Defects.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | session valid | n/a (auto via `auth_state`) | — | asserted (environment-level, not a test assertion) |
| Step 1: Create agent with Name, Description, Instructions filled | agent created successfully | AFS step 1–3 | step 3 | **blocked** — real defect (#524) prevents save from succeeding via UI form; confirmed live 2026-07-15, deterministic (100% repro, 3/3 including the pre-existing filed report's 2/2) |
| Step 2: Send "Reply with: CONFIRMED" in embedded chat | message submitted | AFS step 4 | — | blocked *(unreachable — no agent to chat with)* |
| Step 3: Verify agent responds with message containing "CONFIRMED" | response contains "CONFIRMED" | AFS step 5 | — | blocked *(unreachable)* |
| Step 4: Verify no error state / hanging "waking the agent" spinner | no persistent spinner/error | AFS step 6 | — | blocked *(unreachable; also no existing handle — see Automation Hints)* |
| Objective (description): agent w/ Name+Description+Instructions executes via embedded chat without hanging | as above | AFS steps 4–6 | — | blocked |

### Axis 2 — Analyst additions

- Confirmed the defect is **not** limited to the raw `/agents/create` UI form — it also breaks `automation/api/client.py::AgentAPI.create_agent()`, the API convenience method the existing test suite's `agent_id` fixture (and several other fixtures, e.g. `agent_with_toolkit_instructions`) uses to provision agents. Ran two unrelated existing tests (`test_agent_detail_page_loads`, `test_agent_instructions_field`) that depend on the `agent_id` fixture — both error at setup with the identical 400. *Added: this widens the defect's blast radius far beyond ELITEA-1897 and is the reason this AFS is `defect-found`/`blocked` rather than merely noting a local repro — every agent-dependent fixture in the suite is currently broken, which the implementer needs to know before attempting ANY agent-creation-dependent automation, not just this case.*
- No other assertions added beyond the case — automation of steps 4–6 could not begin.

## Cleanup
- No agent was successfully created (Save 400s before an agent ID exists), so there is nothing to delete from this analysis run.
- **Recommendation for the eventual implementer**: once the defect is fixed, follow the project's existing pattern (`agent_with_toolkit_instructions` fixture in `tests/ui/chat/test_agent_with_toolkit_chat.py`, or the plain `agent_id` fixture) — create per-test via `agent_api.create_agent(...)`, `yield`, then `agent_api.delete_agent(aid)` in a `finally`/fixture-teardown block. Do **not** reuse a shared stable agent for this case: the case's whole point is verifying a *freshly created* agent (with only Name+Description+Instructions, no toolkit) executes without hanging, so a fresh instance per run is load-bearing, not incidental — Hard Rule 10's "prefer reuse" guidance doesn't apply here.

## Concrete Handles (discovered during exploration)

All handles below were directly observed live via Playwright MCP snapshots against `http://localhost:5173/agents/create`; the embedded-chat handles are corroborated by the existing `automation/pages/agent_detail_page.py` page object (already testid-based, no gaps found there).

| Element | Testid (confirmed) | Notes |
|---|---|---|
| Agent Name field | `agent-name-input` | Confirmed live via generated Playwright code (`page.getByTestId('agent-name-input')`) |
| Agent Description field | `agent-description-input` | Confirmed live |
| Agent Instructions field | `agent-instructions-input` | Confirmed live; matches `AgentFormPage.instructions_input` in existing page object |
| Save button (create form) | `agent-save-button` | Confirmed live; disabled until required fields pass validation, enabled once Name+Description+Instructions filled |
| Embedded chat message input | `chat-message-input` | Existing `AgentDetailPage.chat_message_input` — not independently re-verified live (blocked before reaching detail page), but already exercised by 2+ merged specs (`test_agent_with_github_toolkit.py`, `test_agent_management.py`) |
| Embedded chat send button | `chat-send-button` | Existing `AgentDetailPage.chat_send_button` — same caveat as above |
| Embedded chat message list / items | `chat-message-list`, `chat-message-item` | Existing `AgentDetailPage._embedded_chat_messages()` |
| Last AI response text (non-last message) | `chat-answer-content` | Existing `get_last_chat_message()` |
| Last AI response text (last message specifically) | `skill-test-last-response` | Existing `get_last_chat_response_text()` — **prefer this one** for the case's step 3 assertion, since it's the message actually asserted on |
| "No hang / no error state" spinner or loading indicator | **none found** | No `data-testid` for a loading/spinner/"waking the agent" state exists anywhere in `agent_detail_page.py` or its templates as explored. **Gap**: if the implementer needs a positive assertion (not just "response arrived within timeout"), this needs `add-data-testid` on whatever loading indicator EliteaUI renders during a pending agent response (likely a `CircularProgress`/skeleton in `ApplicationAnswer.jsx` or the chat input's disabled/pending state) — flagging per this project's "missing testid ⇒ add it, don't rung down" rule. In the interim, "response text is non-empty and stable within `AI_RESPONSE_TIMEOUT`, no timeout exception raised" is an acceptable stand-in per project convention (`wait_for_chat_response`'s existing content-stability polling already encodes this implicitly). |

## Network Behavior
- `POST /api/v2/elitea_core/applications/prompt_lib/399` — agent creation. **Currently returns 400** for any Name+Description(+Instructions)-only payload where the resolved default model (`eu.anthropic.claude-sonnet-4-5-20250929-v1:0`, `supports_reasoning: true`) receives a non-null `temperature` alongside a non-`"none"` `reasoning_effort` in `versions[0].llm_settings` — see `GET /api/v2/configurations/models/399?include_shared=true` for the model's `supports_reasoning` flag. Confirmed via both the UI form's own payload construction and `AgentAPI.create_agent()`'s hard-coded `{"temperature": 0.6, "reasoning_effort": "medium"}` defaults (`automation/api/client.py` ~L386-390).
- Once unblocked: expect the standard embedded-chat WebSocket flow (~2s delay per project convention) for the "Reply with: CONFIRMED" turn — no toolkit call expected (plain instructions, no toolkit attached), so this should be a simple LLM turn with no tool-execution round trip, unlike the toolkit-chat specs' `TOOLKIT_EXECUTION_TIMEOUT` (120s) — `AI_RESPONSE_TIMEOUT` (30s per existing module constants) should be sufficient once the defect is fixed.

## Known Defects Found During Exploration

- **[CRITICAL/BLOCKING]** Agent creation fails with 400 on the default create form/API payload: `temperature` set alongside a non-`"none"` `reasoning_effort` for a `supports_reasoning: true` default model. **Already filed**: [EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524) (filed same day, prior to this analysis, by a different case — ELITEA-1889). Re-confirmed independently live for this case (Name+Description+Instructions, matching this case's exact preconditions) and additionally confirmed the same defect breaks the `agent_id`/`agent_api.create_agent()` fixture path used across the whole existing agent test suite — **added a corroborating comment to #524** with this fixture-level finding (see issue comment, 2026-07-15). No new issue filed (dedup — same root cause, same tracked ticket).
- This is a **blocking** defect per the project's no-masking policy (`.agents/profile.md` § Bug filing: "blocking defect → natural fail + blocked") — not isolated/soft-assertable, since it prevents the case's very first step from completing at all.

## Blocked Steps

- **All of steps 2–4** (send message, verify "CONFIRMED" response, verify no hang/error state) are blocked because step 1 (create agent) cannot complete — `POST .../applications/prompt_lib/{project}` 400s deterministically for both the UI create-form path and the `AgentAPI.create_agent()` fixture path. Unblock condition: EliteaAI/elitea-testing-public#524 is fixed (backend accepts a valid default `llm_settings` for reasoning-capable default models, or the UI/API client stops sending an incompatible default `temperature`+`reasoning_effort` combination).
- Once unblocked, no further blockers are anticipated: the embedded-chat send/wait/assert mechanics are already proven working code paths (`send_chat_message`, `wait_for_chat_response`, `get_last_chat_response_text` in `automation/pages/agent_detail_page.py`), exercised by 2 already-merged specs (`tests/ui/agents/test_agent_with_github_toolkit.py`, `tests/ui/chat/test_agent_with_toolkit_chat.py`). The only net-new work once unblocked is: (a) a toolkit-free agent-creation fixture/inline setup (existing fixtures all attach a toolkit or require one), and (b) the "no hang / no error state" positive assertion, which currently has no dedicated handle (see Concrete Handles gap above).

## Automation Hints

- Framework: Playwright + pytest, confirmed from `.agents/testing.md`.
- Once unblocked, this case is a strong candidate to **extend** `tests/ui/agents/test_agent_management.py::TestCreateAgent::test_create_agent_via_ui` (creates an agent via the UI form with Name+Description+Instructions already) by appending an embedded-chat send/verify block — rather than writing a wholly separate spec — since steps 1–3 (create via UI, all three fields) are identical to that test's existing steps 1–4. Alternatively, a small new test in `tests/ui/agents/test_agent_management.py` (or a new `TestAgentExecution` class) using the plain `agent_id`/API-created agent (no toolkit) + `send_chat_message("Reply with: CONFIRMED")` + `wait_for_chat_response()` + `get_last_chat_response_text()` containment assertion is equally valid and avoids coupling this case's assertions to the create-form test's unrelated concerns (list-page verification, cleanup timing). **Recommend the latter** (new focused test) given the create-form test's finally-block cleanup already has a distinct responsibility.
- Do not reuse `agent_with_toolkit_instructions` (chat toolkit fixture) or the GitHub-toolkit fixtures — this case explicitly wants a **plain**, toolkit-free agent, since its point is proving instructions alone (no tool coupling) still executes.
- Re-verify all Concrete Handles above live once #524 is fixed — they were captured from the create form's initial render only; the post-fix payload/response shape may differ.
