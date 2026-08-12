---
name: Nested agent accordion always has a wrapper chip
description: chat-answer-nested-agent-accordion-details-{name} always contains a bare-agent-name chat-answer-tool-chip regardless of skill/tool use — never assert to_have_count(0) on it
type: feedback
---

`AgentDetailPage.get_nested_agent_accordion_details(agent_name)`'s DOM
(`chat-answer-nested-agent-accordion-details-{agent_name}`) is NOT empty for
a sub-agent with no skills/tools attached. It ALWAYS additionally renders the
delegation wrapper's own "called this agent as a tool" chip — bare agent
name text, sharing the `chat-answer-tool-chip` testid — independent of
whether the sub-agent invoked anything. Confirmed live (ELITEA-2608) and by
source read: `EliteaUI/src/components/Chat/ApplicationThinkView.jsx` (a
sub-agent's `block.actions` includes the wrapper Tool action, not just its
inner chips) + `ActionView.jsx`'s `buildTitle()` (bare agent name when
`loadedSkillName` is null). Same pattern
`test_nested_agent_with_mcp_tool_output.py` (ELITEA-1951) already documented
for an MCP-tool case ("two chips share this testid... the parent's own
'called this agent as a tool' chip... DOM-first").

**Never assert `expect(details.locator(CHAT_ANSWER_TOOL_CHIP_SELECTOR)).to_have_count(0)`**
to prove "no skill/tool used" — it will fail deterministically (actual
count 1, not 0). Use `AgentDetailPage.get_nested_agent_tool_chip_texts(agent_name)`
and assert `not any(text.startswith("Skill: ") for text in texts)` (or the
analogous `toolkit_name`-filtered check for MCP tool calls) instead — the
same technique the isolation test's own Part-A assertion already uses.

Case this bit: ELITEA-2608 (`test_subagent_skills_isolation.py`) — AFS's own
step 13/15 "confirmed live: zero chat-answer-tool-chip elements" claim was
wrong; amended in the AFS's Implementer Amendment section.
