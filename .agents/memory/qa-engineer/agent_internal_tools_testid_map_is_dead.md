---
name: Agent internal-tools testid map is dead
description: INTERNAL_TOOL_TESTIDS maps to internal-tool-* which does not exist; agent tool lookup silently degrades to case-sensitive text
type: reference
aliases: [INTERNAL_TOOL_TESTIDS, get_tool_testid, AGENT_INTERNAL_TOOLS, agent-canvas-tools-toggle, get_available_tools]
tags: [area/agents, type/tech-debt]
created: 2026-09-09
updated: 2026-09-09
---

## The dead map

`automation/pages/internal_tools.py`'s `INTERNAL_TOOL_TESTIDS` / `get_tool_testid()`
produce `internal-tool-<slug>` (e.g. `internal-tool-python-sandbox`).
**`git grep "internal-tool-" origin/main -- src/` returns 0 hits.** The attribute the
product actually renders is `agent-canvas-tools-toggle-<name>`
(`AgentInternalToolSwitch.jsx:108`). So the map has never matched anything.

## Why that is worse than a red test

`AgentDetailPage._get_tool_switch_locator()` tries the testid, gets `count() == 0`,
and falls through to `page.locator(f'text="{tool.value}"')` — Playwright's quoted
text selector is **exact and case-sensitive**. `AGENT_INTERNAL_TOOLS` still carries
`"Image creation"` and `"Python sandbox"` while the UI renders `Image Creation` and
`Python Sandbox`, so those two simply never match.

`get_available_tools()` *filters* by that same lookup and returns only what it found,
and `test_agent_toggle_tool_enum_api` asserts merely `len(available_tools) > 0` and
uses `available_tools[0]`. **The test stays green while silently covering fewer tools
than it claims.** Coverage loss with no signal — the reason to fix it is not a red.

Also incomplete: `AGENT_INTERNAL_TOOLS` has 8 entries but the agent surface renders
11 (the chat 10 plus `Attachments`); `Agent & Pipeline Builder`, `Skill Builder` and
`Project Context Builder` are absent from the enum entirely.

Related: [[chat_modules_panel_handles]]
