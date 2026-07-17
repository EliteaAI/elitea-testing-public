# Test Case: Welcome message is shown as agent bubble before first user message

## Metadata
- **TMS ID**: ELITEA-1885
- **Linked Story**: none
- **Priority**: l2 (medium — per case frontmatter/header, both agree)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend `https://dev.elitea.ai`), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end against the live
  system, all 6 steps verified, feature under test (welcome message rendered as an
  agent bubble in the embedded chat panel before any user message) has **no
  functional defect**. All required testids already exist — no `add-data-testid`
  work needed. One noteworthy **live-product behavior not stated in the case
  text**: the welcome message renders in the embedded chat panel **live, as soon
  as it is typed into the field** — it does not wait for Save. This is not a
  defect (Save still persists it for reload/reopen, which is what the case's
  pass criterion actually requires), but the implementer should assert
  post-Save/post-reload, not rely on the pre-Save live-preview render as the
  proof point. See Coverage Map Axis 2 and Automation Hints.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- An existing agent is available in the current project.
- **Test-data setup**: use `AgentAPI.create_agent_full()` with the
  `reasoning_effort: "none"` / no-`temperature` payload shape (same workaround
  documented in `test-specs/agents/lcritical_edit-agent-instructions-verify-persistence_ELITEA-1872.md`
  and `l3_remove-variable-verify-removal-persists_ELITEA-1884.md` — the plain
  `agent_id` fixture / `AgentAPI.create_agent()` 400s against DEV, tracked as
  [#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)).
  Confirmed live this run (agent id `5009`, deleted at teardown):
  ```python
  payload = {
      "name": f"autotest_{request.node.name}"[:32],
      "description": f"Auto-created for test {request.node.name}",
      "type": "interface",
      "versions": [{
          "name": "base",
          "tags": [],
          "instructions": "You are a test agent.",
          "variables": [],
          "tools": [],
          "llm_settings": {
              "max_tokens": -1,
              "reasoning_effort": "none",
              "model_name": settings.default_model_name,
              "model_project_id": settings.default_model_project_id,
          },
          "conversation_starters": [],
          "agent_type": "openai",
          "welcome_message": "",
          "meta": {"step_limit": 25},
      }],
  }
  agent = agent_api.create_agent_full(payload)
  ```

## Test Data

### Literal values
| Field | Value |
|-------|-------|
| Welcome message | `Welcome! I am your test assistant. How can I help you today?` |

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner`.
   - **Verify — PASSES.** Agent detail page loads (`Page Title: Agent:
     <name> - Private`). The embedded chat panel is already present on the
     page — no separate "open chat" action is needed for the agent detail
     route (the case's step 4 alternative "open the embedded chat panel" is
     therefore a no-op here; the panel is always mounted). Chat message list
     (`chat-message-list`) is empty pre-welcome-message.
2. Click into `agent-welcome-message-input` and type (via `press_sequentially`,
   per the project's MUI React-onChange convention) the welcome message:
   `Welcome! I am your test assistant. How can I help you today?`
   - **Verify — PASSES.** Field value updates immediately; character counter
     (`agent-welcome-message-counter`) shows `708 characters left`. **Also
     observed (Axis 2):** the embedded chat panel's message list
     immediately renders one `chat-message-item` containing the typed text,
     styled as an agent bubble (see Step 6 below) — this happens on every
     keystroke, before Save. Not itself the case's pass criterion (see
     Metadata note) but useful context for the implementer.
3. Click `agent-save-button` (plain Save) and wait for network idle.
   - **Verify — PASSES.** `PUT
     /api/v2/elitea_core/application/prompt_lib/399/{agent_id}` returns
     `201 Created`. Zero console errors, zero console warnings.
4. Full-navigation reload (`page.goto`, not an SPA route change) to
   `${BASE_URL}/agents/all/{agent_id}?viewMode=owner` — this both re-verifies
   persistence (case's Save-then-reopen intent) and gives a clean, pristine
   "before any user message" state (no synthetic input carried over from
   Step 2's live-preview render).
   - **Verify — PASSES.** Page reloads fully; `GET
     /api/v2/elitea_core/application/prompt_lib/399/{agent_id}` → `200 OK`.
     The embedded chat panel re-renders.
5. Verify the welcome message is displayed before any user message is sent.
   - **Verify — PASSES.** Exactly **one** `chat-message-item` is present in
     `chat-message-list` post-reload — the welcome message — and its text
     (`.innerText`) contains the exact literal
     `Welcome! I am your test assistant. How can I help you today?`. No user
     message precedes or follows it (message count == 1).
6. Verify the welcome message appears as an agent bubble (not a user bubble).
   - **Verify — PASSES.** The single `chat-message-item` is rendered via
     `ApplicationAnswer.jsx` (agent path), confirmed via its child testids —
     it contains `chat-read-out-button` (agent-only: TTS read-out) and
     `skill-test-last-response` (the agent-answer-content variant used when
     the message is the last/only one in the list — see Concrete Handles
     below for the `chat-answer-content` vs `skill-test-last-response`
     state-ternary quirk), and does **not** contain
     `chat-message-delete-button` (user-message-only per `UserMessage.jsx`).
     Visually (screenshot evidence): left-aligned bubble with the agent's
     name (`autotest_1885_welcome`) and avatar icon in the header row —
     the same layout as any other agent response, distinct from the
     right-aligned, avatar-less user-message layout.

## Expected Results
- Welcome message text persists across Save and full-page reload.
- Exactly one message renders in the embedded chat panel before any user
  message is sent, and it is that welcome message.
- The message renders through the agent-message code path (`ApplicationAnswer`),
  never the user-message code path (`UserMessage`).
- No console errors or warnings at any step.
- `PUT .../application/prompt_lib/{project}/{agent_id}` returns `201`.

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture (localhost `VITE_DEV_TOKEN`) | n/a (fixture-level) | asserted |
| Precondition: existing agent available | Agent detail page reachable | Test-data setup (`create_agent_full()` workaround) | agent created, id returned | asserted (via documented workaround) |
| Step 1: navigate to agent detail page | Page loads | Step 1 | page title, empty `chat-message-list` pre-message | asserted |
| Step 2: set welcome message text | Field displays the text | Step 2 | `agent-welcome-message-input.input_value()` | asserted |
| Step 3: click Save | Save completes successfully | Step 3 | PUT response `201`, zero console errors/warnings | asserted |
| Step 4: open embedded chat panel / start new chat | Chat panel opens | Step 1 + Step 4 | panel always mounted on agent detail route (no separate open action exists here — see Step 1 note); Step 4's full reload re-confirms a pristine load | asserted *(no-op-by-design — panel isn't a togglable element on this route)* |
| Step 5: welcome message visible before any user message | Text visible, no prior user messages | Step 5 | `chat-message-list` message count == 1, text equals literal | asserted |
| Step 6: welcome message appears as agent bubble (not user bubble) | Agent-styled rendering | Step 6 | child testids `chat-read-out-button` + `skill-test-last-response` present, `chat-message-delete-button` absent; screenshot (left-aligned, agent avatar/name) | asserted |
| Pass criterion: "all steps complete without errors" | No errors at any step | Steps 1-6 | console error/warning check at each step (all zero) | asserted |
| Fail criterion: "welcome message absent / after user input / user-styled" | n/a (negative condition) | Steps 5-6 | count==1 assertion (absent-or-after-input would fail it) + agent-path testid assertion (user-styled would fail it) | asserted |

### Axis 2 — observables asserted beyond the case text

| Observable | Why asserted |
|---|---|
| Welcome message renders live in the chat preview on every keystroke, before Save | Discovered during exploration — not itself the case's pass criterion (which is about the *saved* state), but documented so the implementer doesn't mistake the pre-Save live-preview render for the persisted-state proof and assert too early |
| Zero console errors AND zero console warnings at Save and at post-reload load | Silent-error check per project convention (`test-case-analysis` § Anti-patterns); clean both times this run |
| Message rendered via the agent code path specifically (`chat-read-out-button` + `skill-test-last-response` present, `chat-message-delete-button` absent), not just "looks left-aligned" | The case's step 6 says "e.g. on the left side or with agent avatar" (illustrative, not prescriptive) — a testid-based code-path assertion is a stronger, more stable signal than a visual/positional one and satisfies the project's testid-only locator policy |
| Exact message count == 1 (not just "welcome message is present") | The case's Fail criterion explicitly calls out "appears after user input" as a failure — a bare presence check wouldn't catch a welcome message that shows up *behind* an accidental prior message; asserting count==1 closes that gap |
| Full-page reload (not SPA navigation) before the pre-first-message check | Guards against synthetic/session-state carryover from Step 2's live-preview render poisoning the "before any user message" assertion — same pristine-context discipline as the project's reproduction/verification conventions |

## Cleanup
1. Created a disposable agent (`autotest_1885_welcome`, id `5009`) via
   `AgentAPI.create_agent_full()` with the `reasoning_effort: "none"` workaround.
2. Executed all 6 case steps against it (see Test Steps above).
3. Deleted the agent via `AgentAPI.delete_agent(5009)` after verification —
   confirmed via a follow-up `GET` returning `400 No application found with id
   '5009'`. No shared/fixture state was touched or left modified.

**For the implementer:** the automated test must follow the same
create-disposable-agent-then-delete-at-teardown pattern (via a `pytest` fixture
or `try/finally`), matching `TestAgentActions` in
`automation/tests/ui/agents/test_agent_management.py`.

## Concrete Handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Status |
|---|---|---|
| Welcome message input | `agent-welcome-message-input` (`AgentDetailPage`/`AgentFormPage.welcome_message_input`) | pre-existing |
| Welcome message char counter | `agent-welcome-message-counter` | pre-existing |
| Save button | `agent-save-button` | pre-existing |
| Embedded chat message list container | `chat-message-list` (`AgentDetailPage.chat_message_list`) | pre-existing |
| Each message item (user OR agent — shared testid) | `chat-message-item` (`AgentDetailPage.chat_message_item` / `CHAT_MESSAGE_ITEM_SELECTOR`) | pre-existing |
| Agent-only child: TTS read-out button (scoped inside a `chat-message-item`) | `chat-read-out-button` (`ChatPage.read_out_button`) | pre-existing |
| Agent-answer body, non-last message | `chat-answer-content` (`AgentDetailPage.chat_answer_content`) | pre-existing |
| Agent-answer body, when the message is the last (or only) one in the list — **same DOM node, testid swaps** per `ApplicationAnswer.jsx`'s `isLastMessage ? 'skill-test-last-response' : 'chat-answer-content'` ternary | `skill-test-last-response` (`AgentDetailPage.skill_test_last_response`) | pre-existing. **Grandfathered pattern** — pre-dates the 2026-07-16 "testid = stable identity, state via `data-*`" ruling in `.agents/testing.md`; not this case's element to fix (out of scope — only the elements this case *adds* testids to would need the new pattern, and none were added). Implementer note: because a lone welcome message is always the "last" message, assert on `skill-test-last-response`, not `chat-answer-content`, when checking count==1 |
| User-only child (absence check): message delete button | `chat-message-delete-button` (`CHAT_MESSAGE_DELETE_SELECTOR`) | pre-existing — used here as a NEGATIVE assertion (must be absent) to confirm the bubble is not user-rendered |

No new testids were needed — every element this case touches already has a
testid in `AgentDetailPage`/`ChatPage`. No `add-data-testid` work required.

## Network Behavior
- `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` —
  fires on Save click, `201 Created` on success (confirmed this run).
- `GET /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` —
  fires on page load/reload, `200 OK`, returns `version_details.welcome_message`
  which the chat panel reads to seed its initial history
  (`ChatBox.jsx`'s `getInitialChatHistory()` / `getWelcomeMessage()` helpers —
  confirmed via source read, `src/[fsd]/features/chat/lib/helpers/chat.helpers.js`).

## Known Defects Found During Exploration
None found. The feature behaves exactly as the case describes — no
reverse-masking, no functional defect. (See Metadata for the one *documented
behavior nuance*, live-preview-before-Save, which is not a defect.)

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, `.agents/testing.md`).
- Page objects: `AgentDetailPage` (welcome message fields, inherited from
  `AgentFormPage`) + its embedded-chat testids (`chat_message_list`,
  `chat_message_item`, `CHAT_MESSAGE_ITEM_SELECTOR`) already cover everything
  this case needs — no new page-object methods strictly required, though a
  thin helper like `get_last_chat_message_agent_markers()` returning
  `(has_read_out, has_last_response_or_answer_content, has_delete_button)` for
  the scoped-child-testid check (Step 6) would keep the test body clean and is
  a reasonable addition to `AgentDetailPage`.
- Test-data setup: use `AgentAPI.create_agent_full()` with the
  `reasoning_effort: "none"` payload (see Preconditions) — do not use the
  plain `agent_id` fixture (currently blocked by open defect #524, unrelated
  to this case's feature).
- Wait strategy: after Save, wait for network idle (`PUT .../application/...`
  settling) before reload; after reload, wait for `chat-message-list` to be
  visible AND for its first `chat-message-item` child to be visible before
  reading message count/text — do not assert on message count==1 immediately
  on `domcontentloaded` (the panel populates from the `GET .../application/...`
  response, which lands slightly after the shell renders).
- Assertion order: assert count==1 first (Step 5), then assert the
  agent-path child testids within that single item (Step 6) — this ordering
  mirrors the case's own step numbering and keeps failures attributable to
  the right step.
