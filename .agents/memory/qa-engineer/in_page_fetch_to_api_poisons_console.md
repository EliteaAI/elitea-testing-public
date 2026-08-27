---
name: An ad-hoc in-page fetch() to the Elitea API emits two console errors
description: page.evaluate(fetch('/api/v2/...')) lacks the app's auth headers, redirects to OIDC, and CORS-fails — looks exactly like a product defect
type: feedback
aliases: [console errors, CORS, forward-auth, auth_oidc, fetch from evaluate, ERR_FAILED, false console error]
tags: [area/tooling, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

Reading the API from inside the page during exploration —
`page.evaluate(() => fetch('/api/v2/auth/token/'))` — does **not** inherit the app's
RTK-Query auth headers on localhost. The dev proxy redirects the request to
`https://dev.elitea.ai/forward-auth/auth_oidc/login?target_to=...`, which is then blocked
by CORS, emitting **two console errors**:

```
Access to fetch at 'https://dev.elitea.ai/forward-auth/auth_oidc/login?...'
  (redirected from 'http://localhost:5173/api/v2/auth/token/') ... blocked by CORS policy
Failed to load resource: net::ERR_FAILED
```

They are indistinguishable from a product defect to a "no console errors" assertion, and
they persist in the console for the rest of the session — so a later step's console check
inherits them. Cost me a re-read of the console log to clear the page's name (the surface
was 0-error otherwise).

**Do instead:** capture the app's *own* request via `page.expect_response(...)` and read
its body. That is also the honest shape — the value comes from the system's real call, not
a hand-rolled one.
