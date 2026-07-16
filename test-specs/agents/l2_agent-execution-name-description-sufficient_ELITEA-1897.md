# Test Case: Agent execution — instructions field alone does not prevent execution (name+description sufficient)

## Metadata
- **TMS ID**: ELITEA-1897
- **Linked Story**: none
- **Priority**: l2 (source case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaAI/EliteaUI `automation/testids` → DEV backend, project `Private` id `399`)
- **User set**: `${TEST_USER}` (localhost `auth_state` skip-login via `VITE_DEV_TOKEN`, user `project_user_659`)
- **Analyst**: qa-engineer (agent), 2026-07-15; **re-verification pass**: qa-engineer (agent), 2026-07-16
- **Status**: **ready-for-automation** — re-executed end-to-end live on 2026-07-16 after #524 was confirmed fixed. All 4 case steps completed with no blockers. No new defects found. (Was `defect-found`/blocked on 2026-07-15; #524 is now closed-by-fix.)

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

**RE-EXECUTED END-TO-END LIVE 2026-07-16** — all 6 sub-steps below completed with
no blockers, now that #524 is fixed. (The 2026-07-15 pass below is preserved as
history; the 2026-07-16 OBSERVED lines are the current ground truth.)

1. Navigate to `${BASE_URL}/agents/create`
   - **Verify**: "New Agent" tab/form is shown
   - **OBSERVED (2026-07-16, live)**: form loads, "New Agent" tab selected, all fields present as before.
2. Fill Name (`agent-name-input`), Description (`agent-description-input`), Instructions (`agent-instructions-input`)
   - **OBSERVED (2026-07-16, live)**: all three testids confirmed present and fillable via `page.getByTestId(...)`. Filled with `autotest_ELITEA1897_confirm` / description / plain toolkit-free instructions text.
3. Click Save (`agent-save-button`)
   - **Verify** (per case): agent created successfully, lands on `/agents/all/{id}`
   - **OBSERVED (2026-07-15, live, historical — superseded)**: Save did NOT navigate away. `POST /api/v2/elitea_core/applications/prompt_lib/399` → **400 Bad Request**:
     `{"type": "value_error", "loc": ["versions", 0, "llm_settings"], "msg": "Value error, temperature is not allowed together with a reasoning_effort (other than 'none') — reasoning models reject a custom temperature"}`.
   - **OBSERVED (2026-07-16, live, current)**: Save button enabled once all three required fields were filled; click navigated immediately to `/agents/all/4903?destTab=configuration&name=autotest_ELITEA1897_confirm&viewMode=owner`. Network: `POST /api/v2/elitea_core/applications/prompt_lib/399` → **201 Created** (was 400). **#524 confirmed fixed** — bug is gone, not intermittently avoided; standard UI create-form flow now works with the platform's default model/llm_settings combination.
4. In the embedded chat panel (`chat-message-input`), send `"Reply with: CONFIRMED"` (Enter submits, equivalent to `chat-send-button`)
   - **OBSERVED (2026-07-16, live)**: message typed and submitted via `page.getByTestId('chat-message-input').fill(...)` + `.press('Enter')`. Message appears immediately in the chat list as a "Test Bot to autotest_ELITEA1897_confirm" turn.
5. Verify the agent responds with a message containing `"CONFIRMED"` (`chat-message-item` / `skill-test-last-response` testids)
   - **OBSERVED (2026-07-16, live)**: response arrived ~15s after send (well within the existing `AI_RESPONSE_TIMEOUT`=30s constant; "Thought for 3 secs" shown in the UI, model `Anthropic Claude 4.5 Sonnet`). Response text: exactly `"CONFIRMED"` — case assertion satisfied.
6. Verify no error state / "waking the agent" spinner hangs indefinitely
   - **OBSERVED (2026-07-16, live)**: no persistent spinner — chat input textbox returned to an active/enabled state, response rendered with normal action icons (Read out / Copy / Regenerate / Delete), 0 console errors (checked both `warning` and `error` levels), no error toast. No hang.

## Expected Results
- Per case: agent created; embedded chat responds with a message containing "CONFIRMED"; no persistent spinner/error state.
- **Actual (observed 2026-07-16)**: matches expected exactly. Agent created (id 4903), embedded chat responded with the literal text "CONFIRMED", no error/hang state observed. Case **PASSES**.
- (2026-07-15 historical actual, superseded: agent creation failed at the API boundary before any chat interaction was possible — see #524, now fixed.)

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | session valid | n/a (auto via `auth_state`) | — | asserted (environment-level, not a test assertion) |
| Step 1: Create agent with Name, Description, Instructions filled | agent created successfully | AFS step 1–3 | step 3 | **covered** — re-verified live 2026-07-16: `POST .../applications/prompt_lib/399` → 201, navigation to `/agents/all/4903`, deterministic (not intermittent — single clean attempt, no retries needed) |
| Step 2: Send "Reply with: CONFIRMED" in embedded chat | message submitted | AFS step 4 | step 4 | covered — message appears in chat list turn |
| Step 3: Verify agent responds with message containing "CONFIRMED" | response contains "CONFIRMED" | AFS step 5 | step 5 | covered — response text observed as exactly `"CONFIRMED"`, arrived ~15s post-send |
| Step 4: Verify no error state / hanging "waking the agent" spinner | no persistent spinner/error | AFS step 6 | step 6 | covered — no spinner/error observed; input re-enabled, 0 console errors; **no dedicated positive-assertion handle exists** (see Concrete Handles gap, unchanged) — implementer should assert on response-arrived + no-console-error + no-timeout as the stand-in, per existing `wait_for_chat_response` convention |
| Objective (description): agent w/ Name+Description+Instructions executes via embedded chat without hanging | as above | AFS steps 4–6 | steps 4–6 | covered |

### Axis 2 — Analyst additions

- Re-ran the exact repro from the 2026-07-15 blocked pass (Name+Description+Instructions, plain, no toolkit) — **#524 no longer reproduces**: `POST /api/v2/elitea_core/applications/prompt_lib/399` now returns 201 with the platform's current default model/`llm_settings` combination for the create-form path. This closes the blast-radius concern raised in the prior pass (the `agent_id`/`AgentAPI.create_agent()` fixture path was not independently re-exercised in this pass since the case only requires the UI form path, but the same backend validation is what changed, so that path is expected fixed too — flag for the implementer to spot-check on first use rather than assume).
- No assertions added beyond the case's 4 steps. Cleanup (delete) verified via UI flow — `DELETE /api/v2/elitea_core/application/prompt_lib/399/4903` → 204.

## Cleanup
- **Agent created during this pass (id 4903, name `autotest_ELITEA1897_confirm`) was deleted** via the UI Delete flow (table-view row → "more" action menu → Delete → typed exact name to confirm → Delete). Verified via network: `DELETE /api/v2/elitea_core/application/prompt_lib/399/4903` → **204 No Content**. Nothing left behind from this analysis run.
- **Recommendation for the implementer (confirmed, not just a suggestion)**: create per-test via `agent_api.create_agent(...)` (existing `automation/api/client.py::AgentAPI`), `yield`, then `agent_api.delete_agent(aid)` in a `finally`/fixture-teardown block — same pattern as `agent_with_toolkit_instructions`/`agent_id` fixtures, but **without attaching a toolkit** (plain instructions only). Do **not** reuse a shared stable agent for this case: the case's whole point is verifying a *freshly created* agent (Name+Description+Instructions only, no toolkit) executes without hanging, so a fresh instance per run is load-bearing, not incidental — Hard Rule 10's "prefer reuse" guidance doesn't apply here. This was re-confirmed by manually exercising the create→chat→delete lifecycle live in this pass with no friction.

## Concrete Handles (discovered during exploration)

All handles below were directly observed live via Playwright MCP against `http://localhost:5173/agents/create` and the resulting `/agents/all/{id}` detail page, **re-verified against the current live DOM on 2026-07-16 (post-#524-fix)** — all still accurate, no drift since the 2026-07-15 pass.

| Element | Testid (confirmed) | Notes |
|---|---|---|
| Agent Name field | `agent-name-input` | Re-confirmed live 2026-07-16 (`page.getByTestId('agent-name-input').fill(...)`) |
| Agent Description field | `agent-description-input` | Re-confirmed live 2026-07-16 |
| Agent Instructions field | `agent-instructions-input` | Re-confirmed live 2026-07-16; matches `AgentFormPage.instructions_input` in existing page object |
| Save button (create form) | `agent-save-button` | Re-confirmed live 2026-07-16; disabled until required fields pass validation, enabled once Name+Description+Instructions filled; click now succeeds (201, navigates to `/agents/all/{id}`) |
| Embedded chat message input | `chat-message-input` | **Independently re-verified live 2026-07-16** (previously blocked, now confirmed): `page.getByTestId('chat-message-input').fill(...)` + `.press('Enter')` submits the turn correctly. Matches `AgentDetailPage.chat_message_input`. |
| Embedded chat send button | `chat-send-button` | Not separately exercised this pass — Enter-to-submit was used instead and worked; existing `AgentDetailPage.chat_send_button` should be equally valid (same existing page-object method used by 2 merged specs) |
| Embedded chat message list / items | `chat-message-list`, `chat-message-item` | Confirmed live 2026-07-16 — chat turns render as list items with sender name, timestamp, content |
| Last AI response text (non-last message) | `chat-answer-content` | Not independently re-exercised (only one AI turn occurred); existing `get_last_chat_message()` unchanged |
| Last AI response text (last message specifically) | `skill-test-last-response` | Not independently re-exercised via testid lookup this pass (verified via accessibility snapshot text instead — response text confirmed exactly `"CONFIRMED"`); **still recommended** for the case's step 3 assertion per existing `get_last_chat_response_text()` |
| "No hang / no error state" spinner or loading indicator | **still none found** | Re-confirmed 2026-07-16: no dedicated loading/spinner/"waking the agent" testid exists. The response rendered directly (with a "Thought for N secs" collapsible header) with no observable intermediate spinner state to assert against. **Gap unchanged** — implementer should use "response arrived within `AI_RESPONSE_TIMEOUT`, 0 console errors, no timeout exception" as the stand-in per existing `wait_for_chat_response` convention; file `add-data-testid` work separately if a positive spinner-absence assertion becomes a hard requirement. |

## Network Behavior
- `POST /api/v2/elitea_core/applications/prompt_lib/399` — agent creation. **RE-VERIFIED 2026-07-16: now returns 201 Created** for the same Name+Description+Instructions-only payload that 400'd on 2026-07-15. #524's root cause (temperature + reasoning_effort conflict on the default reasoning-capable model) is resolved — confirmed via direct network inspection during this live pass (`page.getByTestId(...)`-driven form fill + Save click), not just re-reading the ticket.
- Embedded-chat WebSocket flow: send → response arrived in **~15s** (well under the existing `AI_RESPONSE_TIMEOUT`=30s constant), UI showed "Thought for 3 secs", model `Anthropic Claude 4.5 Sonnet`. No toolkit call involved (plain instructions, no toolkit attached) — a simple LLM turn, no tool-execution round trip, confirming the AFS's prior expectation.
- `DELETE /api/v2/elitea_core/application/prompt_lib/399/4903` — cleanup delete. **204 No Content.**

## Known Defects Found During Exploration

- **#524 — CONFIRMED FIXED, re-verified independently in this pass.** Agent creation via the UI create-form (Name+Description+Instructions, exact same repro as the 2026-07-15 blocked pass) now succeeds: `POST .../applications/prompt_lib/399` → 201 (was 400), navigates to `/agents/all/{id}` as expected. No new defects were found during this re-execution — end-to-end flow (create → chat → confirm response → delete) completed cleanly with 0 console errors and no unexpected network failures.
- No new GitHub issue filed — nothing new to report; #524 stays as the historical record of the now-resolved blocker. Per dispatch: this pass's job was re-verification, not a fresh defect hunt, and none surfaced.

## Blocked Steps

- **None.** All 6 sub-steps (form load, fill, save, send message, verify response, verify no-hang) completed live with no blockers as of 2026-07-16. (Historical: 2026-07-15 pass had all of steps 2–4 blocked on #524; that blocker is resolved — see Known Defects above.)

## Automation Hints

- Framework: Playwright + pytest, confirmed from `.agents/testing.md`.
- **Verified: no existing spec fully covers this case's observable.** Checked both AFS-named candidates live during this pass:
  - `tests/ui/agents/test_agent_management.py::TestCreateAgent::test_create_agent_via_ui` — creates an agent via the UI form with Name+Description+Instructions and verifies detail-page navigation + list-page presence, but **does not touch the embedded chat at all** (no send, no response assertion). Confirmed by reading the full test body (lines 113–182) — it stops at "Verify agent appears in the list" and cleans up. Not a covering spec for this case's core observable (chat execution).
  - `tests/ui/agents/test_agent_with_github_toolkit.py::test_add_toolkit_to_agent` — does send a chat message and assert on the response, but the whole point of that fixture is a **toolkit-attached** agent whose response is expected to mention "branch" (GitHub toolkit output) — a categorically different observable from this case's plain-instructions "CONFIRMED" echo, and it depends on `github_toolkit`/`GIT_HUB_TOKEN` test data this case doesn't need. Not a covering or reasonably-extendable spec (attaching a toolkit here would violate the case's explicit intent of proving toolkit-free instructions alone are sufficient).
  - **Conclusion: `ready-for-automation` (fresh implementation), not `extend-existing`.** Neither candidate's gap is "a small number of missing assertions" — `test_create_agent_via_ui` is missing the entire chat-execution half of the case, and `test_agent_with_github_toolkit` tests a fundamentally different (toolkit-coupled) code path. Per the skill's own boundary rule ("if the gap is large enough that the extension would be a near-rewrite... treat as ready-for-automation"), this is squarely fresh-implementation territory.
- **Recommended implementation shape**: a new focused test (e.g. `TestAgentExecution::test_agent_executes_with_name_description_instructions_only` in `tests/ui/agents/test_agent_management.py`, or a new file if the class doesn't fit) using `agent_api.create_agent(...)` (plain, no toolkit) → `yield` → `agent_api.delete_agent(aid)` in teardown, then `send_chat_message("Reply with: CONFIRMED")` → `wait_for_chat_response()` → assert `"CONFIRMED" in get_last_chat_response_text().upper()` (case-insensitive per AFS Test Data recommendation) → assert 0 console errors / no timeout raised as the no-hang stand-in.
- Do not reuse `agent_with_toolkit_instructions` (chat toolkit fixture) or the GitHub-toolkit fixtures — this case explicitly wants a **plain**, toolkit-free agent, since its point is proving instructions alone (no tool coupling) still executes.
- All Concrete Handles above are now confirmed against the current (post-fix) live DOM — no further re-verification needed before implementation.
