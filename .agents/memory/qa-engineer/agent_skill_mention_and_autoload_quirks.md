---
name: Agent skill mention and autoload quirks
description: ~mention chat syntax is keyed on real skill name (not literal "skill1"/"skill2"); fill() destroys mention chips; skill attach is auto-saved via PATCH; model autonomously autoloads skills on plain messages (intermittent defect #38)
type: feedback
---

Discovered while analysing ELITEA-1735 (Interact with Skills from Agent,
localhost:5173):

- **Skill invocation syntax is `~<mention>`, not literal `~skill1`/`~skill2`.**
  Typing `~` into the chat input (`chat-message-input`) opens a "Mention
  skill" popper listing attached skills by their *actual* names (ARIA
  `menuitem`, accessible name = skill name). The TMS case's placeholder
  names ("skill1"/"skill2") are generic prose, not literal syntax — this is
  case-text drift, not a product defect (reverse-masking guard: assert the
  live `~<real-skill-name>` contract, not the placeholder text).
- **`fill()` on the chat input destroys an already-inserted mention chip.**
  Playwright's `fill()` replaces the entire textbox value; if you've already
  selected a skill from the mention popper (inserting a `~skill-name` chip),
  a subsequent `fill()` call wipes it out silently — the message sends as
  plain text with no mention, invalidating the test. Always use
  `press_sequentially()` (Playwright) / `type(..., slowly=true)` (MCP) to
  *append* after a mention chip, never `fill()`.
- **Skill attachment to an agent is immediate/auto-saved**, not deferred to
  the agent-level Save button. Clicking a skill in the mention/add popper on
  the agent detail page's Skills accordion fires
  `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}` → `201`
  right away; the page's `Save`/`Save As Version` button stays disabled
  throughout. Don't wait on or assert agent-level Save state after attaching
  a skill.
- **Skills accordion's add-skill button has no `data-testid` and no
  accessible name** in current DOM (icon-only `<button>`, matched only by
  position — first button in the Skills section header). Needs an
  `add-data-testid` pass (e.g. `agent-add-skill-button`) before this can be
  automated cleanly; currently must be role/position-matched.
- **CONFIRMED intermittent defect** (github.com/EliteaAI/elitea-testing-public/issues/38,
  MAJOR): a plain chat message with NO `~mention` sometimes gets BOTH
  attached skills' formatting applied anyway (1/3 repro rate in this run —
  a plain "weather" prompt returned
  `THE_SUN_IS_SHINING_BRIGHTLY_THIS_AFTERNOON.`, all-caps AND
  underscore-delimited, despite zero invocation). Root cause: the model's
  own visible "Thinking" trace (expand "Thought for N secs") shows it's
  instructed to scan `<available_skills>` and autonomously decide whether to
  `load_skill` based on relevance to the message — not strictly gated on the
  `~mention` syntax. This makes plain-message non-invocation a probabilistic
  LLM judgment call, not a deterministic contract. When automating, treat
  this assertion as `expect.soft()` with the ticket linked (isolated defect
  per `.agents/profile.md` § Bug filing), and hard-assert the rest of the
  flow (skill creation, attach, explicit `~mention` invocation for both
  skills) — those reproduced 100% reliably across all attempts.
- Full AFS: `test-specs/skills/l3_interact-with-skills-from-agent_ELITEA-1735.md`.
