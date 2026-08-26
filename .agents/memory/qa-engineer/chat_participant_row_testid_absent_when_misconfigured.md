---
name: Misconfigured chat participant has no chat-participant-row testid
description: A warned/misconfigured chat participant renders via the attention branch with no row testid — assertions read it as missing
type: feedback
aliases: [chat-participant-row, participant warning icon, MCP disconnected participant, participant row missing]
tags: [area/chat, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

`[data-testid="chat-participant-row-{uniqueId}"]` renders **only for a NON-misconfigured**
chat participant. A participant carrying a misconfiguration warning renders through a
different (attention) branch, exposing `[data-testid="chat-participant-warning-icon"]` and
**no row testid at all**.

So a locator-count assertion on `chat-participant-row-*` reports a warned participant as
**absent**, even when it is plainly visible in the PARTICIPANTS panel.

## Where this bites today

`mcp_toolkit_with_tools` (a *healthy* public `mcp.deepwiki.com` MCP, 3 real tools, no OAuth)
is falsely flagged "Server is disconnected! Reconnect it to use." —
EliteaAI/elitea-testing-public#687, re-confirmed 4/4 on 2026-08-27. Any test asserting
"the MCP appears in the MCPS section" via the row testid fails for a reason that has nothing
to do with participant membership.

When counting participants, prefer `PARTICIPANT_ROW_PREFIX` **plus**
`PARTICIPANT_WARNING_ICON`, or the collapsed `chat-participants-badge-{section}` badges,
rather than assuming every participant owns a row testid.

Related: [[agent_pipeline_second_participant_add_silently_dropped]]
