---
name: Chat participant agent quirks
description: How to add an agent as a chat conversation participant (plus-menu -> Agents -> agent popper); issue #38 skill-bleed defect re-confirmed in this second context; bare agent-detail URL without name= param 404s
type: feedback
---

Discovered while analysing ELITEA-1736 (Interact with Skills from
Conversation, localhost:5173) — the chat-participant variant of ELITEA-1735
(agent-level skill testing):

- **Adding an agent as a chat participant**: click `plus-menu-button` next
  to the chat message input -> a tooltip menu opens with items "Modules" /
  "Agents" / "Pipelines" / "Toolkits" / "MCPs" (plain `role="menuitem"`,
  accessible name = the label) -> click "Agents" -> a "Search agents..."
  popper opens listing every agent by name (own + public), `role="menuitem"`
  each. Clicking one switches the chat composer's Model Selector group to
  show `"Switch Agent" -> {agent name}` and adds an "Agents in this
  conversation" badge (`aria-label="Agents in this conversation"` on a
  wrapping div, no testid) showing the participant count as a button label.
- **CONFIRMED: github.com/EliteaAI/elitea-testing-public/issues/38
  reproduces in this second context too.** The original defect (agent
  auto-invoking skill formatting on a plain, non-`~mention` message) was
  found testing agent-level chat (ELITEA-1735, ~1/3 repro rate). Here,
  testing the SAME skill/agent pairing but via a chat **participant**
  instead, the very first plain message ("Tell me a joke", no mention)
  still got the skill's UPPER CASE robot-joke formatting applied, with a
  `"Skill: <skill-name>"` tag visible in the expandable "Thought for N
  secs" trace confirming autonomous `load_skill`. This means the root
  cause lives in the shared LLM-prompt/skill-injection layer, not in
  either surface's own UI/session code. Do NOT file a new/duplicate bug
  for this — reference #38, note the second context in the AFS.
- **Bare agent-detail URL 404s without the `name=` query param.**
  Navigating directly to `/agents/all/{id}?destTab=configuration` (omitting
  `&name=...`) returns a client-side "Page not found", plus a console 400
  on `GET .../public_application/prompt_lib/{id}` (tries a public-agent
  lookup path first). Always navigate via the Agents list UI (search +
  click the card) or preserve the full URL captured at creation time
  (which includes `&name=...&viewMode=owner`). Low-severity footgun, not
  filed as a defect (easy workaround, not exercised by any case so far).
- **Chat conversation deletion has no type-to-confirm** (unlike agent/skill
  delete): hover the sidebar conversation list item to reveal
  `conversation-menu-menu-button` -> click -> "Delete" menuitem -> a plain
  Cancel/Delete confirmation dialog (`"Are you sure to delete the {name}
  chat? It can't be restored."`) -> click "Delete". No name-matching
  textbox required, unlike the agent/skill delete flows which both use
  `delete-confirm-name-input`'s inner `#name` field.
- Full AFS: `test-specs/skills/l3_interact-with-skills-from-conversation_ELITEA-1736.md`.
