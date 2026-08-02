# Chat-interface surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Chat surface (`/chat`).
Not a substitute for execution — verify a handle as you use it. One writer at
a time; last confirmed by: qa-engineer analyst, ELITEA-2181 run, 2026-08-02.

## Streaming / in-progress response widget (ELITEA-2181)
- The "loading indicator" shown between Send and content-arrival is
  `RotatingMessages.jsx` — text-cycling placeholder ("Waking the agent…", …),
  NOT a `CircularProgress` spinner. No testid.
- Once content starts, a "Thought for `<n>` secs" accordion
  (`ApplicationThinkView.jsx` → `ActionView.jsx`) carries the model-name chip
  AND the "Pause scroll"/"Resume scroll" toggle — both scoped to that
  accordion, not the message bubble or page level. Neither has a testid.
  Clicking the toggle flips its own label (confirmed) — that's the stable
  automation signal, not a scrollTop delta (only proves out when the
  conversation's content genuinely overflows the viewport).
- Message action icons (Read-out/speaker, Copy, Regenerate, Delete) only
  render **on hover** over the message block. Confirmed testids:
  `chat-read-out-button`, `chat-delete-button` (both on `main`). Copy has
  NO testid but does get an MUI-auto-injected `aria-label="Copy to
  clipboard"` (its `StyledTooltip` wraps the `IconButton` directly).
  **Regenerate has NEITHER testid NOR aria-label** — its `StyledTooltip`
  wraps a bare `<Box>`, breaking MUI's auto aria-label injection. The page
  object's existing `copy_message_button`/`regenerate_button`
  `LocatorDescriptor`s reference stale, nonexistent testids
  (`message-copy-button`/`message-regenerate-button`) — pre-existing tech
  debt (not introduced by ELITEA-2181), still functioning today only via
  their `fallback=` role/aria-label lookups. Don't reuse those dead names
  when adding real testids — follow the live sibling convention instead
  (`chat-copy-button`/`chat-regenerate-button`).
- The last message's `Answer` block carries a **same-element,
  state-conditional testid** (`ApplicationAnswer.jsx:640`):
  `data-testid={isLastMessage ? 'skill-test-last-response' :
  'chat-answer-content'}` — pre-existing tech debt (not this case's
  anti-pattern to fix). For any single-exchange test the value will be
  `skill-test-last-response` (misleadingly named — unrelated to Skills).
  Scope through the parent `chat-message-item` container instead of either
  literal string.
- This environment's default chat participant answered "write a poem"
  requests by invoking a file-writing TOOL (visible via "I'll create this
  poem in a file for you." + an artifact reference), not a plain text
  completion — full generation took 34–54s across 4 live runs. Don't assume
  a short prompt like this completes quickly; size waits ≥90s.

## "+ Create New Agent" canvas + Build with AI (ELITEA-1920/2166)
- `ChatPage.open_create_new_agent_canvas()` (plus_menu_button → hover
  agents_menuitem → click agents-create-new-button) opens `AgentCanvasPage`,
  which renders the SAME `CreateAgentForm.jsx` as `/agents/create` — including
  its conditional `GenerateAgentButton` (`generate-agent-open-button`,
  entityType !== 'pipeline'). Build-with-AI works identically inside the
  canvas as on the standalone create page (same testids, same network
  contract) — confirmed live, ELITEA-1920.
- **Completion wiring differs by host page.** `/agents/create`'s
  `onAgentCreated` auto-navigates to `/agents/all/{id}` (ELITEA-1909). The
  chat canvas's `onAgentCreated` is `src/hooks/chat/useAgentCreation.js`
  instead: it adds the created agent as a chat participant
  (`addNewParticipants`) and auto-activates it — URL stays on
  `/chat?edited_participant_id={id}`, NO navigation away. Don't reuse
  ELITEA-1909's "wait for /agents/all navigation" pattern here; wait on
  `AgentCanvasPage.title` (switches to the agent's name post-creation) or the
  Participants popover instead.
- Participants panel: `ChatPage.open_participants_popover(timeout, section="agents")`
  (pre-existing, ELITEA-2166) — reuse directly, don't re-derive.
- Composer shows `"Editing..."` (not the agent name) while that agent's own
  canvas/editor is still open — a transient state, already documented +
  clarified (issue EliteaAI/elitea-testing-public#709). Don't mistake it for
  a broken participant-name display.

## Fragility note — `switch_project()` to an already-active project
In a from-scratch `sync_playwright` script (no pytest fixture chain),
calling `ChatPage.switch_project(<already-active-project-id>)` was observed
once to leave the composer stuck behind a permanent `MuiCircularProgress`
loading overlay that then blocks `plus-menu-button` clicks entirely (30s
timeout, `<div class="MuiBox-root css-1qkypnf">` intercepts pointer events).
Skipping the redundant switch (project was already correct) avoided it
entirely. Not reproduced through the normal pytest fixture chain — flagging
as a possible transit-path fragility for a from-scratch driver, not filed as
a product defect (never observed via the real test suite's own fixtures).
