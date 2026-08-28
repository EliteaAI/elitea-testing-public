---
name: Leaving a just-created chat raises beforeunload — blocks Playwright MCP, not pytest
description: browser_navigate times out at 60s and every later call errors "does not handle the modal state" until browser_handle_dialog runs
type: feedback
aliases: [beforeunload, modal state, browser_handle_dialog, chat navigation timeout]
tags: [area/chat, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

Navigating away from `/chat/<id>` within seconds of sending the first message raises a
`beforeunload` dialog.

- **pytest is unaffected** — Playwright auto-dismisses dialogs when no handler is registered.
- **Playwright MCP blocks.** `browser_navigate` times out at 60 s, and every subsequent tool
  call fails with `Tool "…" does not handle the modal state` until `browser_handle_dialog`
  is called. The page URL still shows the old chat while the title reads
  `Loading http://…/<target>`, which makes it look like a hung SPA rather than a dialog.

Cost one 60 s timeout during the settings-w08 analysis. If an MCP navigation off a chat route
hangs, reach for `browser_handle_dialog(accept=true)` before debugging anything else.
