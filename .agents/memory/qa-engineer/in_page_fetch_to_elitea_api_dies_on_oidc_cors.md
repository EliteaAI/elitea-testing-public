---
name: In-page fetch to the Elitea API dies on OIDC/CORS
description: page.evaluate + fetch('/api/v2/...') is redirected to forward-auth and blocked by CORS — use the suite's APIClient for any API probe or precondition
type: feedback
aliases: [in-page fetch, browser fetch api, evaluate fetch, forward-auth CORS, api probe from page]
tags: [area/api, area/analysis, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The gotcha

During live analysis it is tempting to read an API value with
`browser_evaluate(() => fetch('/api/v2/...', {credentials:'include'}))`. **It never works on
localhost:5173.** The request is same-origin, but the dev proxy forwards it and the backend
redirects to `https://dev.elitea.ai/forward-auth/auth_oidc/login?target_to=…`, which carries no
`Access-Control-Allow-Origin` — the fetch fails with a bare `TypeError: Failed to fetch`.

The app's own requests to the same URL succeed because they carry a Bearer token the page context
does not reproduce for an ad-hoc `fetch`.

## What to do instead

- **Read the value the product already fetched**: `browser_network_requests` (filtered) shows the
  real call, and in a spec `page.expect_response(...)` gives you the body. That is also the
  fidelity-compliant oracle (`.agents/testing.md` § How to test a NONDETERMINISTIC producer).
- **For an API precondition**, use the suite's `automation/api/` `APIClient` (Bearer from
  `.env.test`), never `page.evaluate` + `fetch`.

## Second-order trap

The failed probes leave `CORS policy` / `net::ERR_FAILED` **errors in the browser console log**.
When reviewing the side channel afterwards, don't mistake your own probe wreckage for product
errors — check the URL: `forward-auth/auth_oidc/login` means it was yours.

Cost when rediscovered: ~3 turns (2026-08-24, ELITEA-2234 analysis).

Related: [[first_visit_tour_prompt_blocks_the_sidebar]]
