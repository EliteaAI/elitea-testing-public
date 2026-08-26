# Test Case: Chat – Add agent with conversation starters and use a starter to send message

## Metadata
- **TMS ID**: ELITEA-2465
- **Linked Story**: none
- **Priority**: l1 (high — per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `Private` (`${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster dispatch with ELITEA-2177, ELITEA-2178
- **Status**: `ready-for-automation` — all 15 case steps reproduced live
  end-to-end. Same underlying flow as ELITEA-2177 (add an agent with
  conversation starters to an existing conversation, use a starter to send a
  message), decomposed here into 15 fine-grained verification points instead
  of 6. Zero console errors beyond the project's standing sanctioned
  `secrets 403` noise, zero unexpected 4xx/5xx.

## Dedup check / sibling relationship (why this is a SEPARATE AFS from ELITEA-2177, not a family merge)
Same dedup search as ELITEA-2177's AFS (no existing merged spec covers this
mid-conversation add-agent flow — see that file's Dedup section for the full
grep trail against ELITEA-2369/ELITEA-1886). **This case is NOT merged with
ELITEA-2177 into one family AFS** because the two differ in STEPS, not just
data (test-case-analysis skill § "differ only in data vs differ in steps"):
this case's own text explicitly asserts several observables ELITEA-2177 never
requests —
- Step 2: default LLM shown **before** adding the agent (a precondition
  ELITEA-2177 never checks).
- Step 5: PARTICIPANTS panel's "AGENTS" section explicitly named as a
  standalone verification point.
- Step 12: an explicit "response generation indicator" check, separate from
  the Thinking-accordion check.
- Step 13: LLM model label shown on the response, as its own numbered step
  (ELITEA-2177 folds this into its step 6).
Both cases share the same handles, fixtures, and even test-data shape — an
implementer may reasonably write them as two `test_*` methods in one file
reusing one page object and one disposable-agent fixture — but each AFS
stands alone per the skill's decomposition rule.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- An existing conversation is open, OR a new one is created for the test (the
  case's own step 1 says "open or create a new conversation" — either is
  valid; confirmed live against an existing conversation).
- An agent with configured conversation starters exists in the current
  project (see § Test Data — same disposable-agent setup as ELITEA-2177).

## Test Data

### Case-text notes
No specific agent name/starter text is mandated by this case ("(none
required)" in the case's own Test Data table) — the case's step 3/8 give
"e.g." examples only ("Claude B", "here is your task: Explain Exponential
Backoff"). Use the SAME disposable-agent setup as ELITEA-2177's AFS (§ Test
Data) — reuse the fixture if implemented in the same file/session.

### generate-per-test (in test setup, cleaned up in its own teardown)
Identical to ELITEA-2177's AFS § Test Data — `AgentAPI.create_agent_full()`
with `conversation_starters` populated, `llm_settings.reasoning_effort`
OMITTED (see that AFS's § Known Defects/Gaps for why — the participants-add
endpoint 400s on the literal `"none"` value that agent-creation itself
silently accepts).

## Test Steps
1. Navigate to the Chats section and open or create a new conversation.
   - **Verify — PASSES.** Target page/section loads successfully (confirmed
     live against an existing conversation, `/chat/{id}`).
2. Verify the default LLM is shown in the input bar.
   - **Verify — PASSES.** Composer's model selector shows the project's
     default model name (confirmed live: "Anthropic Claude 4.5 Sonnet" for
     project 399/`Private`; a different default model may render for a
     different project — assert non-empty/model-selector visibility, not a
     hardcoded literal, since the default is environment/project-configurable
     — `model-selector-name` / `model_selector_name` pre-existing testid).
3. Click + and select Agents, then select an agent with conversation starters
   configured (e.g. "Claude B").
   - **Verify — PASSES.** Control responds; agent gets added as a
     participant. **Case-text drift (CLARIFICATION):** "Claude B" does not
     exist in this environment — see ELITEA-2177's AFS § Test Data for the
     same drift note and the disposable-agent substitution.
4. Verify the input bar now shows the agent name and version (e.g.
   "Claude B | base") with a gear icon and X icon.
   - **Verify — PASSES.** Confirmed live via screenshot: composer shows
     `{agent-name} | {version}` as two adjacent chips
     (`chat-switch-participant-button` name text + `chat-version-selector-trigger`
     version text — TWO separate elements, not one combined chip, matching the
     existing ELITEA-2362 finding already documented in
     `test-specs/agent-hub/_surface.md`), a gear/settings icon
     (`chat-participant-settings-button`), and an "X" icon immediately to the
     right of the ButtonGroup (`aria-label="switch to model"`,
     tooltip "Switch to model" — **no `data-testid`, see § Concrete Handles,
     testid needed**).
5. Verify the PARTICIPANTS panel shows the AGENTS section with the selected
   agent.
   - **Verify — PASSES.** Expanding the participants popover
     (`chat-participants-badge-agents` → `chat-participants-badge-button`)
     shows an "Agents" heading + one participant row with the agent's name
     and version (confirmed live).
6. Verify conversation starter buttons are displayed above the message input
   field (maximum 4 starters).
   - **Verify — PASSES.** `chat-conversation-starter-tile` tiles render above
     `chat-message-input`; count ≤ 4 (this environment's disposable agent had
     1-2 configured).
7. Hover over a starter button with truncated text and verify a tooltip shows
   the full text.
   - **Verify — PASSES, same caveat as ELITEA-2177 step 2.** The tooltip is
     conditional on genuine visual truncation (`EllipsisTextWithTooltip`'s
     `clientWidth < scrollWidth` check) — confirmed live with a deliberately
     long (>150 char) starter added for this verification; the short literal
     "here is your task: Explain Exponential Backoff" example does NOT
     truncate at this environment's rendered tile width. Implementer: give
     the disposable agent one starter long enough to force truncation for
     this step.
8. Click on a conversation starter (e.g. "here is your task: Explain
   Exponential Backoff").
   - **Verify — PASSES.** Click handled without error (pre-fill mechanism
     confirmed live and via source, `onSendConversationStarter`).
9. Verify the full starter text is inserted into the message input field and
   is editable.
   - **Verify — PASSES.** `chat-message-input` value equals the clicked
     starter's exact text; field remains a live editable textbox (Send button
     transitions absent→enabled).
10. Click the Send button.
    - **Verify — PASSES.** `chat-send-button` click submits the message.
      `POST .../conversations/prompt_lib/{project}` → `201`.
11. Verify the message is sent and appears in the conversation directed "to
    [Agent Name]".
    - **Verify — PASSES.** Confirmed live: the sent message's header shows
      "{Sender} to {agent-name}" (a "Chat now" affordance on the agent-name
      text — incidental, not this step's assertion).
12. Verify the agent begins processing with a response generation indicator.
    - **Verify — PASSES.** Confirmed live: the `chat-answer-thought-accordion`
      renders in an `[expanded]` state immediately while the response streams
      (e.g. "Thought for less than a second" for a fast response) — this
      accordion IS the processing indicator this environment renders; there
      is no separate spinner/skeleton element distinct from it (confirmed via
      accessibility snapshot at the moment of send — the accordion appears
      before the response body).
13. Verify the LLM model label is shown on the agent's response.
    - **Verify — PASSES.** `chat-answer-model-chip` inside the accordion
      shows the model used (confirmed live: "Anthropic Claude 4.5 Sonnet").
14. Verify a "Thinking" section is visible and expanding during generation.
    - **Verify — PASSES.** Same `chat-answer-thought-accordion` element from
      step 12 — confirmed `[expanded]` state attribute during/immediately
      after generation via live accessibility snapshot (case text's
      "Thinking section" = this project's "Thought for N secs" accordion;
      same case-text-vs-live-label pattern already documented for the
      sibling starters cases, not a new drift worth filing separately).
15. Verify the agent's full response is received and displayed with no
    error.
    - **Verify — PASSES.** Full, contextually-relevant response text renders
      in the message body (confirmed live: a correct one-sentence
      exponential-backoff explanation). Zero console errors beyond sanctioned
      `secrets 403` noise; zero unexpected network 4xx/5xx across the entire
      15-step flow.

## Expected Results
- Same as ELITEA-2177's AFS, at finer granularity: default LLM visible
  pre-add; agent+version chips, gear icon, and X icon all visible post-add;
  PARTICIPANTS panel's Agents section shows the participant; starters render
  (≤4) with truncation-conditional tooltips; clicking a starter pre-fills
  (not auto-sends) an editable field; sending produces a "to {agent}"
  message, a processing/Thinking indicator, an LLM model label, and a full,
  error-free response.

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture | n/a (fixture-level) | asserted |
| Step 1: navigate to Chats, open/create conversation | Page/section loads | Step 1 | conversation page loaded | asserted |
| Step 2: default LLM shown in input bar | Condition holds | Step 2 | `model-selector-name` visible, non-empty | asserted |
| Step 3: click + → Agents → select agent with starters | Control responds | Step 3 | agent added as participant (network 200 + chip render) | asserted *(case-text drift: "Claude B" → disposable agent, clarification)* |
| Step 4: input bar shows agent name+version, gear icon, X icon | Condition holds | Step 4 | agent chip + version chip + gear testid visible; X icon visible via new testid | asserted *(new testid needed for the X icon, see Concrete Handles)* |
| Step 5: PARTICIPANTS panel AGENTS section shows agent | Condition holds | Step 5 | participants popover "Agents" heading + row visible | asserted |
| Step 6: starter buttons shown, max 4 | Condition holds | Step 6 | `chat-conversation-starter-tile` count ≤ 4 | asserted |
| Step 7: hover truncated starter shows tooltip | Action completes, tooltip shown | Step 7 | tooltip visible with full text on a genuinely-truncated starter | asserted *(clarified — truncation-conditional by design)* |
| Step 8: click a conversation starter | Control responds | Step 8 | click succeeds, no error | asserted |
| Step 9: full starter text inserted, editable | Condition holds | Step 9 | `chat-message-input` value equals clicked starter text | asserted |
| Step 10: click Send | Control responds | Step 10 | `POST .../conversations/...` 201 | asserted |
| Step 11: message sent, "to [Agent Name]" | Condition holds | Step 11 | message item header text pattern | asserted |
| Step 12: agent begins processing, generation indicator | Condition holds | Step 12 | `chat-answer-thought-accordion` renders `[expanded]` | asserted |
| Step 13: LLM model label shown on response | Condition holds | Step 13 | `chat-answer-model-chip` visible, non-empty | asserted |
| Step 14: "Thinking" section visible and expanding | Condition holds | Step 14 | same accordion, `[expanded]` state during generation | asserted *(case-text "Thinking" = live "Thought for N secs", not a new drift)* |
| Step 15: full response received, no error | Condition holds | Step 15 | response text non-empty + contextually relevant; zero console/network errors | asserted |
| Pass criterion: "all steps complete without errors" | No errors at any step | Steps 1-15 | console error check (secrets-403 excluded) at each step | asserted |
| Fail criterion: "any expected UI state/validation/side effect not observed" | n/a (negative condition) | Steps 1-15 | per-step assertions above | asserted |

### Axis 2 — observables asserted beyond the case text

- Zero console errors / zero unexpected 4xx-5xx across the whole 15-step
  cycle — silent-error discipline per project convention.
- The response is contextually relevant to the specific starter clicked, not
  a generic/error fallback — *added: rules out a stub/placeholder response
  passing step 15's weaker "no error" wording alone.*
- The agent+version chips are confirmed to be TWO separate adjacent elements
  (not one combined string), matching the existing ELITEA-2362 finding
  already on file — *added: prevents an implementer from writing a single
  combined-text assertion that would break the moment either sub-element's
  copy changes independently.*

## Cleanup
Identical to ELITEA-2177's AFS § Cleanup — delete the sent message pair
(cascading delete via the response's Delete button, confirmed live), delete
the disposable agent via `AgentAPI.delete_agent(agent_id)` (confirmed live:
cleanly drops the chat participant too, composer reverts to the
conversation's original default LLM on reload).

## Concrete Handles (testid-only, per `.agents/testing.md` § Locator policy)

Same handle set as ELITEA-2177's AFS § Concrete Handles — reproduced here for
this AFS's self-containedness; **the "X" icon testid gap is THIS case's own
step 4, so it is restated as a hard requirement, not a nice-to-have:**

| Element | Handle | Status |
|---|---|---|
| Default LLM label (pre-add) | `model-selector-name` (`ChatPage.model_selector_name`) | pre-existing |
| Composer agent chip (name) | `chat-switch-participant-button` | pre-existing |
| Composer version chip | `chat-version-selector-trigger` | pre-existing |
| Composer settings gear icon | `chat-participant-settings-button` | pre-existing |
| **Composer "X" / remove-participant icon (case step 4's own subject)** | **`testid needed`** — `AgentEditorPanel.jsx`'s `IconButton` (`aria-label="switch to model"`, tooltip "Switch to model", lines ~178-192 collapsed-view / ~294-320 full-view — confirmed via source, TWO render branches share the same missing-testid gap) has no `data-testid`. Recommend `chat-switch-to-model-button` (`{section}-{element}-{type}` naming, parallel to the sibling `chat-switch-participant-button`). This case's own step 4 explicitly names "X icon" as something to VERIFY (presence, not necessarily click) — a `ready-for-automation` verdict is contingent on the implementer adding this via `add-data-testid` before writing that assertion, per `.agents/role-overrides.md` § Analyst slot ("Do not soften a testid demand... it is implementer work"). | **needs-adding** |
| Participants panel "Agents" badge / popover | `chat-participants-badge-agents` + `chat-participants-badge-button` | pre-existing |
| Conversation starter tile | `chat-conversation-starter-tile` | pre-existing |
| Message input | `chat-message-input` | pre-existing |
| Send button | `chat-send-button` | pre-existing |
| Thought/reasoning accordion (steps 12 + 14's shared element) | `chat-answer-thought-accordion` | pre-existing |
| Model chip in accordion (step 13) | `chat-answer-model-chip` | pre-existing |

## Network Behavior
Identical to ELITEA-2177's AFS § Network Behavior — same
`POST .../participants/...` (add-agent) and
`POST .../conversations/...` (send) calls, same `reasoning_effort: "none"`
400-gotcha documented there (§ Known Defects/Gaps item 1).

## Known Defects Found During Exploration
No functional product defect in the case's own flow. Same two
analyst-environment gotchas as ELITEA-2177's AFS (`reasoning_effort: "none"`
participants-add 400, and the browser's default-active-project mismatch vs
`${ELITEA_PROJECT_ID}`) — see that AFS's § Known Defects/Gaps for full detail;
not duplicated verbatim here to avoid drift between the two copies.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, `.agents/testing.md`).
- **This AFS and ELITEA-2177's are prime candidates for ONE shared fixture +
  page-object usage across two `test_*` methods in the same file** — the
  disposable-agent creation, the add-agent action, and the starter-click →
  send → response sequence are byte-for-byte identical; only the assertion
  GRANULARITY differs. Implementer's call whether to also share a helper
  method for the common send/response assertions (steps 10-15 here map to
  ELITEA-2177's steps 5-6) — just don't let the file-level sharing collapse
  the two into one test method, since each AFS's Coverage Map must stay
  independently traceable.
- Step 12's "response generation indicator" and step 14's "Thinking section"
  are THE SAME live element (`chat-answer-thought-accordion`) — don't write
  two separate locators expecting two different components; assert the same
  testid's `[expanded]` state (or equivalent `aria-expanded`/`data-expanded`
  attribute — verify exact attribute name at implementation time) for both.
- Add the `chat-switch-to-model-button` testid via `add-data-testid` on
  `AgentEditorPanel.jsx` BEFORE writing step 4's assertion — both the
  collapsed (`disableSwitchToModel`/loading-skeleton) and full render
  branches need it if the implementer wants one consistent locator across
  agent AND pipeline participants (the same panel serves both, confirmed via
  `isPipeline` prop in the surrounding code).
