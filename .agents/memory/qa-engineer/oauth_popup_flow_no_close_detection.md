---
name: OAuth popup flow — no close detection, 5-minute silent Authorizing
description: Elitea's OAuth dialog only learns of failure via a callback redirect; killing the popup buys 5 min of silence — plan specs around it
type: project
aliases: [oauth popup, McpAuthModal, Configuration OAuth, authorization timed out, mcp-auth-callback]
tags: [area/credentials, area/mcp, type/product-behaviour]
created: 2026-08-24
updated: 2026-08-24
---

## The mechanism

`McpAuthModal.onAuthorize` opens a popup and runs the whole handshake inside it.
The parent learns the outcome ONLY through `createAuthorizationMonitor`
(`mcpAuthWindow.helpers.js`): postMessage / BroadcastChannel / localStorage from
`/mcp-auth-callback`, plus a **5-minute** `setTimeout` fallback.

Consequences, all measured live 2026-08-24 (ELITEA-1984):

- **No `authWindow.closed` poll.** Close the popup → dialog sits on `Authorizing…`
  for 300 s, then shows the generic `Authorization timed out. Please try again.`
  Never a cancellation message. Filed as **#1713**. Cancel still works throughout.
- **A provider that errors out never redirects back**, so Elitea's error path
  (`data.error_description` in the dialog) is unreachable without a REAL registered
  OAuth app + tenant. Placeholder tenant ⇒ the authorize URL answers a bare
  **HTTP 404, empty body** — no error page to observe either.
- Therefore any "failed OAuth" case is **blocked on test data**, not on tooling.
  Simulating the callback would be a terminal substitution.

## Practical rules for specs on this surface

- `page.expect_popup()` — the parent makes **zero** API requests on Authorize.
- Assert the popup's **URL parameters** (client_id, redirect_uri, state, scope) —
  that is the honest, provider-independent observable, and it proves a user-edited
  scope is carried through.
- Never wait on a post-popup message: budget >5 min or skip it.
- `Authorize` label flips to `Authorizing…` — assert `to_be_disabled()`, not text.

Related: [[project_briefing]]
