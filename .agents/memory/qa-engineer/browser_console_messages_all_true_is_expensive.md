---
name: browser_console_messages all=true dumps the whole session into context
description: One call returned ~25k tokens of React stack traces; always filter and cap the side-channel check
type: feedback
aliases: [console messages expensive, all true console dump, side channel check cost]
tags: [area/playwright-mcp, type/context-economy]
created: 2026-08-24
updated: 2026-08-24
---

## What happened

Doing the mandatory side-channel check at the end of the ELITEA-1935/1936
analysis, I called `browser_console_messages` with `level: "error"` **and
`all: true`**.

`all: true` means "since the beginning of the session", not "since the last
navigation". After ~40 minutes of live exploration that was 69 messages, most
of them full React component stack traces — a single tool result of roughly
25k tokens, which then rode along on every subsequent turn.

## The rule

The side-channel check is still mandatory. But scope it:

- **Default to `all: false`** (the default) — errors since the last navigation
  are what the step you just executed actually produced.
- If a session-wide sweep is genuinely needed, write it to disk with the
  `filename` parameter and `grep` it, rather than returning it inline.
- On this project most of what comes back is known noise anyway: the #291
  `unique "key" prop` warning, `dev.elitea.ai/socket.io` `ERR_INTERNET_DISCONNECTED`,
  localhost `socket.io` 500s, and Vite-HMR `toastHandlers of useContext is
  undefined` remounts. None of those are attributable to the flow under test —
  attribute an error to your case only if it names your toolkit/resource id.

Related: [[playwright_mcp_browser_type_is_fill]]
