---
name: Agent Instructions tilde-mention quirks
description: Instructions-field "~" mention flow is a separate entry point from the embedded-chat mention flow; Control+a/Delete unreliable on the Instructions textarea, use .clear()
type: feedback
---

## Two distinct "~"-mention entry points on the Agent detail page

`AgentDetailPage` has TWO separate "~" mention flows that both render the
same "Mention skill" popper component but target different input fields —
do not conflate them:

1. **Embedded chat input** (`data-testid="chat-message-input"`) —
   `send_chat_message_with_mention(skill_name, prompt)`. Covered by
   ELITEA-1735/1736 (`test_skill_agent_interaction.py` /
   `test_skill_conversation_interaction.py`).
2. **Instructions accordion field** (`data-testid="agent-instructions-input"`,
   inherited from `AgentFormPage.instructions_input`) —
   `type_tilde_in_instructions()` / `get_instructions_mention_item(name)` /
   `select_skill_from_instructions_mention(name)` / `clear_instructions_field()`.
   Added for ELITEA-1791 (`test_agent_instructions_tilde_mention.py`).

Both mention panels are scoped to only the agent's currently attached
skills, driven by a client-side filter over data the page already holds
(the `GET application_skills/prompt_lib/{project}/{agent_id}` fetch made
when the Skills accordion first loads) — no additional network request
fires when typing `~` or re-triggering it. Wait on
`page.get_by_text("Mention skill", exact=True)` becoming visible, never a
network-idle wait.

Selecting a mention item inserts `~<skill-name>` as **plain text**, with a
**trailing space** appended (so typing can continue immediately) — the
trailing space is real, harmless UX, not a defect. Strip before asserting
equality: `inserted.strip() == f"~{skill_name}"`.

## `clear_instructions_field()` — use `.clear()`, not Control+a/Delete

Manual `press("Control+a")` + `press("Delete")` on the Instructions
textarea was unreliable in this exploration: only the leading `~` character
was removed, leaving the rest of the text (`~automated-test-explainer` →
`automated-test-explainer `, tilde gone, everything else intact). Switched
to Playwright's `Locator.clear()` (the same MUI-field-clearing call already
used throughout `AgentFormPage.fill_form()` for every other field), which
reliably empties the field and still fires React's `onChange` — unlike
`fill()` with a non-empty value, `.clear()` is not subject to the
"MUI fields need press_sequentially" rule (`.claude/rules/mui-patterns.md`).

## SkillAPI has no create_skill method (as of ELITEA-1791)

`SkillAPI` (automation/api/client.py) only has `list_skills()` and
`delete_skill()` — no create/attach endpoints. Every skills test (1735,
1738, 1739, 1789, 1790, 1791) creates skills via the UI (`_create_skill`
helper, duplicated per-file) and attaches via
`AgentDetailPage.attach_skill()`; only cleanup goes through the API. If a
future case needs `skill_api.create_skill()` / `agent_api.attach_skill()`,
that's a framework-scale addition — escalate rather than adding ad hoc.

## Looking up a pre-existing skill instead of assuming by name

When a case needs "any pre-existing skill" (not one this test creates),
look it up via `skill_api.list_skills()` filtered by excluding this test's
own naming prefix — never assume a specific skill name (e.g.
`automated-test-explainer`) exists in every environment. Same convention
established in ELITEA-1790's cleanup notes; reused for ELITEA-1791's
"Skill A" with a create-if-missing fallback.
