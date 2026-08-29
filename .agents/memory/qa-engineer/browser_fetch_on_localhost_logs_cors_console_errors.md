---
name: browser fetch() on localhost logs CORS console errors
description: Probing the Elitea API with fetch() from browser_evaluate pollutes the very console-error assertion the case makes
type: feedback
aliases: [cors console error, forward-auth 302, api probe from browser]
tags: [area/tooling, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

Calling `fetch('/api/v2/...')` from Playwright MCP `browser_evaluate` on
`http://localhost:5173` does NOT work: the Vite dev proxy 302s to
`https://dev.elitea.ai/forward-auth/auth_oidc/login?target_to=…`, which has no
CORS header, so each attempt logs **two** `console.error`s
(`Access to fetch … blocked by CORS policy` + `Failed to load resource:
net::ERR_FAILED`) and returns `TypeError: Failed to fetch`.

Cost on 2026-08-29 (settings-w10): 6 self-inflicted console errors on a page whose
cases assert "zero console errors" — briefly indistinguishable from a product defect.

**Read API data the honest way instead:** `page.expect_response(...)` around the
navigation/action, or Playwright MCP's `browser_network_requests` filter, or the
suite's own API client with the Bearer token from `config.settings`.
