# Test Case: Chat – Remove Agent from Conversation Clears Conversation Starters

## Metadata
- **TMS ID**: ELITEA-2178
- **Linked Story**: none
- **Priority**: l2 (medium — per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `Private` (`${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster dispatch with ELITEA-2177, ELITEA-2465
- **Status**: `ready-for-automation` — all 7 case steps reproduced live
  end-to-end: added an agent with conversation starters to a conversation,
  expanded the PARTICIPANTS panel's Agents section, hovered the participant
  row to reveal its "Remove agent" icon, clicked it, confirmed the "Remove
  agent?" modal's exact text (one case-text wording drift — see below),
  clicked Remove, and confirmed the agent chip + starters disappeared, the
  default LLM was restored in the composer, and the prior conversation
  history (a pre-existing exchange) remained intact. Zero console errors
  beyond the project's standing sanctioned `secrets 403` noise, zero
  unexpected 4xx/5xx.

## Dedup check (why this is fresh work)
`ChatPage.remove_agent_participant(agent_id)` already exists and is used by
several tests (`test_ghost_skill_after_agent_removed.py`,
`test_team_users_mention_and_remove_participants.py`'s sibling
`open_remove_user_dialog()` mechanism) — but **none of them assert
conversation-starter clearing or default-LLM restoration**; they check
skill-ghosting and user-removal-dialog behavior respectively. Confirmed via
`grep -n "remove_agent_participant\|conversation_starter\|default.*llm" automation/tests/ui/skills/test_ghost_skill_after_agent_removed.py automation/tests/ui/chat/test_team_users_mention_and_remove_participants.py`
— zero hits for starter/LLM assertions in either file. This case's own
observable (starters + default LLM, specifically as a POST-removal side
effect) is fresh coverage riding an existing, reusable removal mechanism.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A conversation with an agent that has conversation starters already added
  as a participant exists (this AFS's own precondition — reuse the
  add-agent flow from ELITEA-2177's AFS, or set up independently per the
  Test Data below).

## Test Data

### Case-text drift (CLARIFICATION, not a defect)
Same as ELITEA-2177/ELITEA-2465: **"Claude B" does not exist** in this
environment. Use any starters-bearing agent — this run used the pre-existing
Catalog agent **"StarterComposer"** (a Public agent already carrying 4
configured starters, no test-data setup needed for the removal flow itself)
as well as a disposable agent created the same way as ELITEA-2177's AFS.
Either works; a disposable agent is preferred for test isolation (no shared
fixture agent state to protect).

### Second case-text drift (CLARIFICATION, not a defect) — modal wording
The case's expected modal text is **"Are you sure to remove the Claude B
agent from conversation?"**. The live modal reads:
**"Are you sure to remove the `{agent-name}` agent from `chat`?"** — literal
word difference **"conversation" → "chat"** (confirmed live, screenshot
evidence: `Remove agent?` dialog body). Assert the live wording pattern
(`f"Are you sure to remove the {agent_name} agent from chat?"`), not the
case's literal "from conversation" text — this is the live product's correct,
current copy; the case text is stale. Do not file as a defect
(reverse-masking guard, `.agents/testing.md` § Classify findings).

## Test Steps
1. Verify agent (with starters) is in the conversation with starters
   visible.
   - **Verify — PASSES.** Precondition setup (adding the agent) is itself
     verified the same way as ELITEA-2177's AFS step 1: agent chip
     (`chat-switch-participant-button`) + conversation starter tile(s)
     (`chat-conversation-starter-tile`) both visible before proceeding.
2. In the PARTICIPANTS panel's AGENTS section, hover over the trash bin icon
   next to the agent.
   - **Verify — PASSES.** Expanding the participants popover
     (`chat-participants-badge-agents` → `chat-participants-badge-button`)
     shows the "Agents" heading + the participant row
     (`chat-participant-row-{unique_id}`, dynamic —
     `application_{agent_id}_{project_id}` per the existing
     `remove_agent_participant()` implementation's documented derivation).
     Hovering the row reveals a hover-only icon-button pair: "View settings"
     and **"Remove agent"** (confirmed live via accessibility snapshot's
     accessible names — the row is hover-reveal, matching the same UX idiom
     already documented for the agent-detail Skills card's remove control,
     `.agents/memory/qa-engineer/agent_skill_card_remove_control_quirks.md`).
     Case text says "trash bin icon" / tooltip "Remove agent" — confirmed the
     accessible name IS literally "Remove agent" (case's expectation matches
     exactly, no drift here).
3. Click the trash bin icon.
   - **Verify — PASSES.** Clicking `chat-participant-remove-button`
     (scoped inside the hovered row) opens the "Remove agent?" confirmation
     dialog.
4. Verify modal text: "Are you sure to remove the Claude B agent from
   conversation?"
   - **Verify — PASSES, with the case-text drift noted above.** Live text:
     `"Are you sure to remove the {agent-name} agent from chat?"` — see
     § Test Data drift note. Assert against the live "from chat" wording.
5. Click Remove.
   - **Verify — PASSES.** Modal closes; the AGENTS section is removed from
     PARTICIPANTS (confirmed live: `chat-participants-badge-agents` badge
     disappears entirely from the composer's participant-badge row — the
     badge is only rendered when the agents list is non-empty); the default
     LLM is restored in the composer (confirmed live: model-selector reverted
     from the agent's model context back to the conversation's plain default
     model, e.g. "GPT-5.4"/"Anthropic Claude 4.5 Sonnet" per project —
     exact model name is environment/project-dependent, assert
     `model-selector-name` is visible and non-empty again, not a hardcoded
     literal). `DELETE`/participant-removal network call succeeds (confirmed
     via the existing `remove_agent_participant()`'s `wait_for_network()`
     call, no error).
6. Verify conversation starters no longer displayed.
   - **Verify — PASSES.** Zero `chat-conversation-starter-tile` elements
     remain in the DOM (confirmed live via screenshot: the composer area
     between the message list and the input field is empty where the tiles
     previously rendered).
7. Verify conversation history intact.
   - **Verify — PASSES.** All messages present before the agent was added
     (the conversation's own prior exchange) remain visible and unchanged
     after removal (confirmed live via reload: message list identical to its
     pre-add-agent state).

## Expected Results
- Removing an agent participant clears its conversation-starter tiles
  entirely (zero remaining), restores the conversation's default LLM in the
  composer, removes the Agents section from the PARTICIPANTS panel, and
  leaves the conversation's prior message history untouched.
- The "Remove agent?" confirmation dialog's live wording is
  "...agent from **chat**?" (not "...from conversation?" as the case text
  states — CLARIFICATION, live product is correct/current).

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: conversation with a starters-bearing agent already added | Setup reachable | Step 1 (verifies the precondition itself, matching case's own step 1 wording) | agent chip + starter tiles visible | asserted |
| Step 1: verify agent in conversation with starters visible | Agent chip and starters shown | Step 1 | testid visibility checks | asserted |
| Step 2: hover trash bin icon | 'Remove agent' tooltip appears | Step 2 | hover-reveal icon's accessible name == "Remove agent" | asserted |
| Step 3: click trash bin icon | 'Remove agent?' modal appears | Step 3 | dialog heading text | asserted |
| Step 4: verify modal text | Modal text correct | Step 4 | dialog body text | asserted *(clarified — live says "from chat", case says "from conversation"; assert live wording)* |
| Step 5: click Remove | Modal closes; AGENTS section removed; default LLM restored | Step 5 | dialog gone, `chat-participants-badge-agents` absent, `model-selector-name` shows default again | asserted |
| Step 6: starters no longer displayed | Starters gone | Step 6 | zero `chat-conversation-starter-tile` elements | asserted |
| Step 7: conversation history intact | Previous messages still visible | Step 7 | message list unchanged vs pre-removal snapshot | asserted |
| Pass criterion: "all steps complete without errors" | No errors | Steps 1-7 | console error check (secrets-403 excluded) | asserted |
| Fail criterion: "starters remain or LLM not restored" | n/a (negative condition) | Steps 5-6 | zero-tile assertion (step 6) + default-LLM assertion (step 5) directly cover the negative | asserted |

### Axis 2 — observables asserted beyond the case text

- Zero console errors / zero unexpected 4xx-5xx across the add → remove
  cycle — silent-error discipline per project convention.
- Network call underlying the removal succeeds (200-range), not just that
  the UI visually updated — *added: catches a case where the DOM update is
  optimistic/client-only and the removal never actually persisted server-side
  (would silently re-appear on reload).*
- Re-verify starters absence AND participant-list absence survive a full page
  reload, not just the immediate post-click DOM state — *added: the same
  "confirm via reload, not just live DOM" discipline already established for
  ELITEA-1886's Save-persistence proof point; guards against a
  client-state-only removal that reverts on refresh.*

## Cleanup
1. If a disposable agent was used: delete it via
   `AgentAPI.delete_agent(agent_id)` after the test (it was already removed
   as a participant by the test's own steps 5-7, so this is pure agent
   cleanup, not conversation cleanup).
2. If the pre-existing "StarterComposer" Catalog agent was used instead:
   nothing to delete (it is a shared fixture agent, not test-owned) — the
   test's own removal steps already restore the conversation to a
   no-agent-participant state, which IS the conversation's correct
   post-test state.
3. No message-history cleanup needed — this case never sends a message, only
   adds/removes a participant.

## Concrete Handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Status |
|---|---|---|
| Participants panel "Agents" badge / popover trigger | `chat-participants-badge-agents` + `chat-participants-badge-button` (`PARTICIPANTS_BADGE.format("agents")`) | pre-existing |
| Participant row (dynamic) | `chat-participant-row-{unique_id}` where `unique_id = application_{agent_id}_{project_id}` (`ChatPage.PARTICIPANT_ROW`) | pre-existing |
| Row's hover-reveal "Remove agent" button | `chat-participant-remove-button` (`ChatPage.PARTICIPANT_REMOVE_BUTTON`), scoped inside the row | pre-existing |
| "Remove agent?" confirmation dialog | Shared `Dialog` component (`components/mui.py` `Dialog.wait_for()` / `Dialog.click_button()`) — confirmed live, buttons "Cancel"/"Remove" | pre-existing |
| Dialog confirm button (via shared Dialog helper) | `delete-confirm-button` (confirmed live via `getByTestId` resolution) | pre-existing |
| Default LLM label (post-removal) | `model-selector-name` (`ChatPage.model_selector_name`) | pre-existing |
| Conversation starter tile (absence check) | `chat-conversation-starter-tile` (`ChatPage.CHAT_STARTER_TILE`) — asserted via `to_have_count(0)` post-removal | pre-existing |

## Network Behavior
- Participant-removal call (fired by `remove_agent_participant()`'s existing
  `wait_for_network()` — implementer: confirm the exact endpoint/method at
  implementation time via a network capture; the existing helper already
  waits on it correctly, no new discovery needed for THIS case) succeeds
  before the modal closes.
- No `POST .../conversations/...` call in this case — no message is ever
  sent.

## Known Defects Found During Exploration
No functional product defect. One case-text wording drift (§ Test Data,
"from conversation" → live "from chat" — CLARIFICATION, not filed as a
defect per the reverse-masking guard). The same `reasoning_effort: "none"`
participants-add gotcha documented in ELITEA-2177's AFS applies to this
case's OWN precondition setup (adding the agent) if a disposable agent with
that field set is used — omit the field per that AFS's Test Data guidance.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, `.agents/testing.md`).
- Reuse `ChatPage.remove_agent_participant(agent_id)` as-is for steps 2-5 —
  it already implements the hover → click-remove → confirm-dialog sequence
  matching this case's steps exactly, including the residual-hover
  mouse-reset gotcha documented in its own docstring. The implementer only
  needs to ADD the case's own assertions (modal text, starters-gone,
  default-LLM-restored, history-intact) around the existing call — not
  reimplement the removal mechanism.
- Precondition setup (step 1) can reuse ELITEA-2177's AFS's disposable-agent
  fixture + `add_agent_participant()` call directly.
- Wait strategy: after clicking Remove, wait for the dialog to close AND for
  `chat-participants-badge-agents` to be absent (or the network response) —
  don't assert starters-gone before the removal's own network round-trip
  settles, per the project's no-sleep convention.
- Consider structuring this as a page-object-level helper
  (`ChatPage.assert_agent_removal_clears_starters_and_restores_llm()` or
  similar) if a future sibling case needs the same post-removal assertion
  bundle — not required for THIS case alone, just a forward-looking note.
