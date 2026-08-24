---
name: Toolkit/MCP Run History row == one conversation, not one run
description: Two Run Test clicks in one Test-panel mount produce ONE history row; remount the Test route between runs to get two.
type: feedback
aliases: [run history rows, toolkit run history, mcp run history, two runs one row, activeConversation]
tags: [area/toolkits, area/mcp, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The fact

On the toolkit / MCP Test surface (`/mcps/all/{id}/test`), a **Run History row
is one conversation**, not one Run Test click.
`useToolkitChat.executeRunTool` creates a conversation only when
`!activeConversation`, so every run inside a single mount of the Test panel
appends to the SAME conversation and Run History shows **one** row.

Measured during ELITEA-1940 (2026-08-24): the first implementation clicked Run
Test twice in place; `expect(rows).to_have_count(2)` polled 24× and saw 1.

## What to do instead

Leave and re-enter the Test route between runs — detail page ->
`toolkit-test-button` -> re-select the tool -> Run. That remounts the panel,
clears `activeConversation`, and produces a second row. It is also what a real
user doing two separate test sessions does.

Corollary: the Results list APPENDS within a mount
(`setChatHistory(prev => [...prev, ...])`), so
`ToolkitTestSettingsPage.wait_for_tool_result()` (reads `.last`) can return the
PREVIOUS run's already-completed ✅ if a second run starts in the same mount.

Same surface, same session: `test-specs/mcp/_surface.md` § Run History carries
the cross-role version of this.
