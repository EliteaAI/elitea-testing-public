# Test Case: Chat – Create Agent with AI Build – Save Agent, Close Canvas, and Test with Conversation Starters

## Metadata
- **TMS ID**: ELITEA-2074
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Status**: `ready-for-automation`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (dev-token auth on localhost, `auth_state` skips login)
- **Analyst/Implementer**: test-automation-engineer, combined slot (wave-16) — cluster dispatch with ELITEA-2073
- **Tooling**: Playwright MCP server, driving the live localhost surface directly

## Coverage decision — why `ready-for-automation`, not `extend-existing`

The mechanics this case exercises after canvas-close (participant chip,
version chip, starter tiles, click-a-starter-to-populate, Send, AI reply)
are the SAME infrastructure `test_chat_agent_starters_add_remove.py`
(ELITEA-2177/2178/2465, merged) already proves — but that spec's agent is a
**disposable, API-seeded agent with hand-written `conversation_starters`**
(`AgentAPI.create_agent_full()`). This case's own precondition is
qualitatively different: the agent's name, instructions, welcome message
AND conversation starters are **all AI-generated** by the Build-with-AI
flow (ELITEA-2073), so nothing about their exact content is knowable ahead
of a live run — the test must capture what the LLM actually produced and
assert against THAT, not a literal example string, which is a different
implementation shape from the existing spec's fixed-payload approach (see §
Test Data below). Reusing `ChatPage`'s existing starter-tile/participant
methods verbatim, but the precondition-building and the content assertions
are this case's own. **Zero new page-object locators or testids are needed**
(100% reuse of `ChatPage`, `AgentCanvasPage`, `GenerateAgentModalPage`,
`AgentFormPage`).

## Preconditions
- User is logged in (`${TEST_USER}`, `auth_state` skips login on localhost).
- An agent has been generated using "Build with AI" (the case's own stated
  precondition, "following ELITEA-2073") — **the implementation reproduces
  this precondition fresh in its own Setup step** (open canvas → Build with
  AI → prompt `"generate an echo agent"` → Generate → Create Agent), the
  same generate-flow ELITEA-2073's AFS already proves step-by-step,
  reused here as transit to reach THIS case's own subject (save/close/
  starters). This is the correct test-isolation shape — each automated test
  independently establishes its own precondition rather than depending on
  ELITEA-2073's test having run first/leaving state behind.

## Test Data

### Live-captured this session (from the ELITEA-2073 exploration — see that
AFS's own step 12), reused here as this case's Test Data, since the values
are inherent to what Build-with-AI actually generates for the prompt
`"generate an echo agent"`:

- **Generated name**: `"Echo Agent"` (exact, both explorations this
  session).
- **Generated instructions** (350 chars, captured verbatim): *"You are an
  Echo Agent. Your sole purpose is to repeat back exactly what the user
  says to you. When a user sends a message, respond by echoing their
  message back to them. You may add a brief prefix like 'You said:' or
  'Echo:' to make it clear you're echoing, but otherwise preserve their
  exact words. Be friendly and straightforward in your responses."*
- **Generated conversation starters** (4, this session's run):
  `"Hello, Echo Agent!"`, `"Can you repeat this message?"`,
  `"Test echo functionality"`, `"Echo: Testing 1, 2, 3"`.

### Case-text drift (CLARIFICATION, not filed as a defect — confirmed live)

The case's own Test Data table gives two illustrative starter texts
(`"Echo this: Hello, world!"`, `"Repeat this 3 times: test"`) and Pass
criteria that read them as literal, exact expected strings ("responds by
echoing back exactly 'Hello, world!'", "repeating 'test' exactly 3 times").
**Neither is reproducible as written**, confirmed live this session:

1. **The starters are AI-generated, not user-authorable.** Build-with-AI
   generates its own conversation-starter set from the natural-language
   prompt (`"generate an echo agent"`) — there is no field the case's flow
   ever fills in to force the literal starter text `"Echo this: Hello,
   world!"` to exist. The case's examples are illustrative of *intent*
   ("an echo-behavior starter", "a repeat-count starter"), not a literal
   scriptable value. Confirmed live twice (ELITEA-2073's exploration and
   this case's own Setup) — the generated set is a plausible-but-different
   4-item list each time, never the case's literal strings.
2. **The generated agent's OWN instructions explicitly permit a prefix**
   ("You may add a brief prefix like 'You said:' or 'Echo:'") — and this
   session's live run demonstrated it doing exactly that: sending
   `"Hello, Echo Agent!"` produced the reply `"Echo: Hello, Echo Agent!"`,
   not a bare, prefix-free echo. An exact-equality assertion against the
   sent text (the case's own literal "echoes back exactly" wording) would
   therefore fail on CORRECT, per-spec agent behavior, not a product
   defect — the reverse-masking anti-pattern this project's canon
   specifically warns against (`.agents/testing.md` § reverse-masking
   guard).

**Live-contract resolution (not a scope reduction — the case's own INTENT,
"the agent echoes back what a starter sends," is still fully verified):**
the implementation captures the actually-rendered starter tiles' text at
run time (`ChatPage.click_chat_starter_tile()` already returns the
clicked tile's own text), sends it, and asserts the agent's reply
**contains** that exact sent text (`sent_text in reply_text`) rather than
asserting bare string equality against the case's illustrative literal.
This is satisfiable on every run regardless of which 4 starters get
generated, and it fails honestly if the agent ever stops referencing what
was actually sent to it.

## Test Steps

1. Verify the agent canvas shows the generated "Echo Agent" configuration
   with LLM model displayed.
   - **Verify — PASSES (Setup, reusing ELITEA-2073's own step 12-14
     findings).** `agent-canvas-title` = "Echo Agent";
     `Anthropic Claude 4.5 Sonnet` model shown in the canvas's own Model
     Selector Menu region (confirmed live).
2. Scroll down to view WELCOME MESSAGE and CHAT STARTERS sections.
   - **Verify — PASSES.** Both accordion sections render with populated
     content (Welcome Message textbox non-empty, 4 Starter textboxes
     populated) — confirmed live via full-page snapshot; the composer/
     chat-area ALSO already shows the same 4 starters as clickable tiles
     even before Save/Close (auto-added-as-participant behavior, same
     `useAgentCreation.js` wiring ELITEA-1920/2073 already document).
3. Verify four conversation starter buttons are displayed.
   - **Verify — PASSES, count is data-dependent, not a hardcoded "always
     4".** This run's Build-with-AI draft produced exactly 4 starters,
     matching the case's own expectation, but the count is a property of
     what the LLM generates for this prompt, not a UI guarantee — assert
     `1 <= count <= 4` (same bound `chat_page.py`'s own
     `ChatConversationStarters.jsx` cap documents, and the same assertion
     shape `test_chat_agent_starters_add_remove.py` already uses for the
     analogous check) rather than a bare `== 4`, so the test does not
     false-fail on a future generation that happens to produce fewer.
4. Click the "Save" button in the top right corner of the canvas.
   - **Case-text drift (CLARIFICATION, confirmed live — NOT a defect).**
     `agent-save-button` is **DISABLED** (`.disabled === true`,
     `.discard_button` likewise) immediately after Build-with-AI's
     Create-Agent step, because the entire generated configuration (name,
     instructions, welcome message, starters) was already persisted by
     that single `POST .../applications/prompt_lib/399` call — there is
     nothing dirty left to save. The case's step assumes an active click
     produces a "saved successfully" toast; the live-contract equivalent is
     that Save is CORRECTLY disabled (nothing to persist) and clicking a
     disabled MUI button is a no-op — no toast, no network call. **The
     implementation asserts the disabled state directly** rather than
     force-clicking a disabled control to manufacture a toast that would
     never appear on real product behavior — asserting a fabricated
     "saved" toast here would be reverse-masking the drift, not honoring
     the case's actual intent (that the fully-configured agent ends up
     durably saved, which it already is).
5. Click the X button in the top right corner to close the canvas panel.
   - **Verify — PASSES.** `agent-canvas-close-button` click closes the
     canvas; URL reverts from `/chat?edited_participant_id={id}` to `/chat`
     (confirmed live).
6. Verify "Echo Agent" with version "base" is listed as an active
   participant in the message input area.
   - **Verify — PASSES.** `chat-switch-participant-button` text = "Echo
     Agent"; `chat-version-selector-trigger` text = "base" (confirmed live
     — same two-separate-adjacent-chips shape ELITEA-2362/2465 already
     document).
7. Verify the four conversation starter buttons appear in the main
   conversation area.
   - **Verify — PASSES.** `chat-conversation-starter-tile` tiles (count
     bound 1-4, per step 3's rationale) render in the chat area below the
     greeting, same 4 texts as the canvas's own review-form/Starter fields
     (confirmed live, byte-identical content pre- and post-close).
8. Click on the first conversation starter.
   - **Verify — PASSES (case-text drift — see § Test Data).** Clicking
     PRE-FILLS the message input with the tile's own exact text (does NOT
     auto-send — matches the pre-existing, already-documented behavior
     `ChatPage.click_chat_starter_tile()`'s own docstring and
     ELITEA-2465's AFS both establish); `chat-message-input` value equals
     the clicked tile's returned text. The implementation then clicks Send
     explicitly (same two-step click-then-send sequence every other
     starter-tile case in this suite uses), since the case's own step 8
     ("Starter text is sent as a message") is only reachable via that
     explicit Send click, not the tile click alone.
9. Verify the Echo Agent responds by echoing back the sent text.
   - **Verify — PASSES, via the live-contract resolution (§ Test Data).**
     This session's live run: sent `"Hello, Echo Agent!"` → agent replied
     `"Echo: Hello, Echo Agent!"` — the sent text is contained verbatim in
     the reply, with the agent's own documented `"Echo:"` prefix
     (confirmed live). Asserted as `sent_text in reply_text`, not
     `reply_text == sent_text`.
10. Click on the second conversation starter.
    - **Verify — PASSES.** Same pre-fill mechanism as step 8, confirmed
      live for a second, different tile (`"Can you repeat this message?"`
      this run) in the SAME already-active conversation (starters remain
      clickable after the conversation acquires a real id — confirmed
      live, tile set unchanged post-first-send).
11. Verify the agent responds by repeating the sent text.
    - **Verify — PASSES, via the same live-contract resolution.** This
      session's live run: sent `"Can you repeat this message?"` → agent
      replied `"Echo: . Can you repeat this message?"` — the sent text is
      again contained verbatim in the reply (confirmed live). The case's
      own literal "responds... repeating 'test' exactly 3 times" is a
      DIFFERENT generated-starter's content than what this run actually
      produced (see § Test Data point 1 — no starter this run asked for a
      3x repeat); the implementation verifies the SAME underlying
      capability the case's intent describes (the agent correctly acts on
      the content of whichever starter was actually sent), using the data
      the system actually generated as the oracle, per
      `.agents/testing.md` § "How to test a NONDETERMINISTIC producer
      without substituting it."

## Expected Results
The agent (built via ELITEA-2073's own generate flow) is durably saved
(Save correctly disabled — nothing left dirty), the canvas closes, all
generated conversation starters render in the conversation view, and
clicking each one sends a message the Echo Agent genuinely echoes back
(verbatim, with its own documented `"Echo:"`-style prefix). Both starters
exercised this session produced a correct echo; zero console errors beyond
the pre-existing, already-documented `disableUnderline` baseline noise;
zero unexpected network 4xx/5xx.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Echo Agent generated (following ELITEA-2073) | agent exists | Setup | canvas shows "Echo Agent" post-create | asserted |
| 1 Canvas shows generated config + model | condition holds | step 1 | canvas title + model selector text | asserted |
| 2 Scroll to Welcome/Starters sections, both populated | condition holds | step 2 | textareas non-empty | asserted |
| 3 Four starter buttons displayed | condition holds | step 3 | tile count bound 1-4 (data-dependent, not hardcoded 4) | asserted *(case-text drift — bound, not literal 4, see rationale)* |
| 4 Click Save; agent saved | condition holds | step 4 | `agent-save-button.disabled === true` asserted directly | asserted *(case-text drift, CLARIFICATION — Save correctly disabled, nothing dirty)* |
| 5 Click X; canvas closes | condition holds | step 5 | URL reverts to `/chat` | asserted |
| 6 "Echo Agent \| base" shown as participant | condition holds | step 6 | switch-participant + version-trigger text | asserted |
| 7 Four starters shown in conversation area | condition holds | step 7 | tiles render, same content as canvas | asserted |
| 8 Click first starter; sent as message | condition holds | step 8 | input pre-filled, Send click, message appears | asserted |
| 9 Agent echoes back exactly "Hello, world!" | condition holds | step 9 | `sent_text in reply_text` (live-contract, not literal-string) | asserted *(case-text drift, CLARIFICATION — content + prefix differ from the case's literal example, underlying echo behavior verified)* |
| 10 Click second starter; sent | condition holds | step 10 | input pre-filled, Send click, message appears | asserted |
| 11 Agent repeats "test" exactly 3 times | condition holds | step 11 | `sent_text in reply_text` (live-contract, not literal-string) | asserted *(case-text drift, CLARIFICATION — this run's 2nd generated starter is not a repeat-count prompt; underlying "acts on what was sent" capability verified instead)* |

### Axis 2 — Analyst/implementer additions

- § Test Data documents, with live evidence from TWO independent
  generations (ELITEA-2073's exploration + this case's own Setup), that the
  case's illustrative starter texts and "exactly echoes"/"exactly 3 times"
  wording cannot be literal assertions against an AI-generated agent —
  *added: without this, an implementer would either hardcode a starter
  text that will never actually render (permanent false-fail) or silently
  weaken to a no-op assertion (defect-masking in the other direction).*
- Step 4's disabled-Save finding is asserted directly (`disabled ===
  true`) rather than skipped — *added: turns a would-be silent step-skip
  into a real, positive assertion of the correct product behavior.*
- Steps 9/11 cite `.agents/testing.md`'s nondeterministic-producer guidance
  by name — *added: this AFS's exact drift is the canonical case that
  guidance describes (assert the response as oracle, not a hand-written
  literal), so a future reader can find the general rule from this
  concrete instance.*

## Cleanup
1. The agent built in this case's own Setup (ELITEA-2073's flow, run fresh
   per test-isolation — see § Preconditions) is deleted via
   `AgentAPI.delete_agent()` in the implementation's `finally` block.
2. The conversation acquires a real id once the first starter is sent
   (step 8) — deleted via `ConversationAPI.delete_conversation()` in the
   same `finally` block.

## Concrete Handles (zero new testids — 100% reuse, confirmed live this session)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| Canvas title / model selector | `AgentCanvasPage.title` / canvas's Model Selector Menu region | on-main ✓ | n/a |
| Save / Discard buttons | `AgentCanvasPage` reuses `AgentFormPage`-style `agent-save-button` / `agent-discard-button` (`.agents/testing.md` § ELITEA-2089) | on-main ✓ | n/a |
| Canvas close (X) | `AgentCanvasPage.close_button` (`agent-canvas-close-button`) | on-main ✓ | n/a |
| Participant name/version chips | `ChatPage.switch_participant_button` / `.chat_version_selector_trigger` | on-main ✓ | n/a |
| Conversation starter tiles | `ChatPage.CHAT_STARTER_TILE` / `.get_chat_starter_tiles()` / `.click_chat_starter_tile()` | on-main ✓ | n/a |
| Message input / Send | `ChatPage.message_input` / `.send_button` | on-main ✓ | n/a |
| AI reply text | `ChatPage.wait_for_ai_response()` + `_extract_message_body(messages_container.nth(i))` | on-main ✓ | n/a |
