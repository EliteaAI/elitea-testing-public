---
name: Chat ghost-skill-after-participant-removal defect
description: Confirmed defect (issue #51) — removing an Agent chat participant does not clear its skill from the ~mention popper; remove control is hover-revealed on the participants popper row
type: feedback
---

Discovered while analysing ELITEA-1793 (Ghost skill not shown after Agent
participant removed, localhost:5173):

- **Remove-participant handle discovered**: click the "Agents in this
  conversation" badge (`getByRole('button', { name: <count> })`, wrapped in
  `div[aria-label="Agents in this conversation"]`, no testid) → opens a small
  popper headed `"Agents"` listing each participant (name + version). **Hover**
  the participant row to reveal `button "Edit agent"` / `button "Remove
  agent"` — both absent from the accessibility tree until hovered (same
  hover-reveal pattern as the agent-detail Skills card's remove control,
  see `agent_skill_card_remove_control_quirks.md`). Clicking "Remove agent"
  opens a confirm dialog (`heading "Remove agent?"`, body `"Are you sure to
  remove the {name} agent from chat?"`, Cancel/Remove) — no type-to-confirm,
  unlike agent/skill entity delete.
- **CONFIRMED DEFECT (filed as
  github.com/EliteaAI/elitea-testing-public/issues/51, 2/2 repro,
  independent second attempt after a full page reload)**: after removing an
  agent participant (composer correctly reverts to default model, "Agents in
  this conversation" badge correctly disappears from the DOM entirely),
  re-typing `~` in the chat input STILL shows the removed agent's skill in
  the "Mention skill" popper — identical to the pre-removal state. A control
  check (fresh page load, `~` typed with NO participant ever added) correctly
  shows the empty state `"No skills attached to this agent"`, proving the
  mention list IS scoped to participants when never populated — it's
  specifically the *remove* transition that fails to invalidate the stale
  list. No network call fires on typing `~` in either state (client-side
  only), which points root cause at a stale memo/cached skill-list keyed off
  "current participant agents" that updates on add but not on remove.
- **Not the same as issue #38** (agent auto-invokes skill formatting on a
  plain non-mention message, ~1/3 intermittent rate, LLM-prompt-layer root
  cause). This is a pure UI suggestion-list staleness bug, 2/2 deterministic,
  never got as far as sending a message.
- Full AFS: `test-specs/skills/l3_ghost-skill-not-shown-after-agent-participant-removed_ELITEA-1793.md`.
