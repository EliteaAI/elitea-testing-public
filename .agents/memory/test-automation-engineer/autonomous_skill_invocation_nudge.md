---
name: Autonomous skill invocation needs nudged description + agent instructions
description: Attaching a skill isn't enough for autonomous invocation — skill description and agent instructions must nudge the model
type: feedback
---

Attaching a skill to an agent does NOT guarantee the model will autonomously
`load_skill` it on a given prompt, even with a matching test prompt. Two
fields must actively nudge the decision, confirmed live (ELITEA-2610, first
implementation attempt failed with a plain generic response, no
`chat-answer-tool-chip`, no marker tag — the skill was simply never invoked):

- **Skill `description`**: generic prose ("... — version selection
  behaviour") is not enough. Use an explicit trigger condition, e.g.
  `"Use this skill for EVERY user question, no matter the topic."` (or, for a
  conditional trigger, `"Use this skill ONLY when the user explicitly asks to
  X."` — the pattern already established in `test_skill_agent_interaction.py`
  SKILL_3_DESCRIPTION for ELITEA-2607).
- **Agent `instructions`**: `"Answer the user's question directly"` actively
  discourages tool/skill use. Use `"You are a helpful assistant. Use your
  skills when appropriate."` — the exact phrase already used by the merged
  ELITEA-2607/2609 tests.

Separately: a literal fenced code block (`` ``` ``) does NOT survive
`AgentDetailPage.get_last_chat_response_text()`'s `text_content()` extraction
— the markdown renderer converts it to `<pre><code>`, stripping the backtick
characters from the extracted text. If a test needs to assert "the response
contains a code example," don't check for `` "```" `` — ask the model (via
skill instructions) to prefix the code example with a literal marker tag
(e.g. `[CODE-EXAMPLE]`) instead, same mechanism as any other deterministic
marker-tag assertion.
