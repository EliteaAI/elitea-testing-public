---
name: Nested agent / tool invocation needs a fully-specified chat message
description: Vague prompts silently skip tool/sub-agent calls (normal LLM behavior, not #1127); chip-vs-accordion shape depends on whether the invoked agent itself calls a tool.
type: project
---

Confirmed twice now, on two different surfaces (chat-interface direct-toolkit-call,
ELITEA-2211/2215; agents nested-agent-with-MCP, ELITEA-1951): whether an agent
actually invokes a configured tool (or a nested sub-agent invokes ITS OWN
configured tool) is entirely a function of how specific the driving chat message
is — not flaky infrastructure, not a platform bug.

- A vague message ("Please help me with this task.") → the model just answers
  conversationally, ZERO tool/sub-agent invocation. Normal LLM judgment given
  ambiguous input.
- A message that names the target (sub-agent / tool) but omits a REQUIRED
  parameter → the outer call may fire (e.g. parent invokes the sub-agent) but
  the inner one silently doesn't (sub-agent skips its own tool, answers
  generically) — no error, no visible sign anything went wrong.
- Only a message naming every entity AND every required parameter explicitly
  reliably produces the full chain, repeatably (3/3 in the ELITEA-1951 run,
  after 2 failed vaguer attempts).

**Do not confuse this with #1127** (chat-interface: a tool-call *intent*
leaking as raw visible text instead of invoking the backend tool — a real,
separately-filed, non-deterministic platform defect). The message-specificity
gap above never produces malformed/leaked text — every non-invoking response
is a normal, well-formed conversational reply. It is a **test-design**
concern (write a fully-specified test message), not a product defect to file.

**Bonus, agent-nesting-specific (ELITEA-1951):** the chat UI's own choice
between a flat `chat-answer-tool-chip` and an expandable nested accordion for
a sub-agent invocation depends on whether the sub-agent ITSELF made a further
tool call during that turn — confirmed across 2 otherwise-identical runs.
Don't hardcode either shape; check for the nested accordion first, fall back
to the chip.

When writing an AFS/test for ANY agent/sub-agent tool-invocation flow: always
use a message that names the target and every required parameter explicitly —
never rely on the model inferring missing detail, even if the case text itself
is vague.
