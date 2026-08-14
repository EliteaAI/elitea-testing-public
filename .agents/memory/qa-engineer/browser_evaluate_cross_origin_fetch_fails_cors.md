---
name: browser_evaluate cross-origin fetch fails CORS
description: page.evaluate()/browser_run_code_unsafe fetch() straight to dev.elitea.ai from localhost:5173 fails CORS — the app always calls same-origin, proxied
type: feedback
---

Tried to shortcut pipeline-fixture setup during ELITEA-2058 analysis by
calling `fetch()` directly against `https://dev.elitea.ai/api/v2/...` from
inside `page.evaluate()`/`browser_run_code_unsafe`, with the browser already
on `http://localhost:5173`. Failed every time with a CORS preflight error:

```
Access to fetch at 'https://dev.elitea.ai/api/v2/elitea_core/applications/prompt_lib/399'
from origin 'http://localhost:5173' has been blocked by CORS policy:
Response to preflight request doesn't pass access control check:
Redirect is not allowed for a preflight request.
```

Root cause: the EliteaUI app's own network calls are ALWAYS same-origin
(`http://localhost:5173/api/v2/...`) — Vite's dev server proxies them
through to the real backend. A raw `fetch()` issued from `page.evaluate()`
bypasses that proxy and hits the backend directly cross-origin, which the
backend's CORS config doesn't allow (compounded by a redirect on the
preflight itself).

**Fix / workaround:** never construct API creation shortcuts via direct
`fetch()` in the browser context. Either (a) drive the UI itself to create
the fixture (Add pipeline → Add node → Save, as ELITEA-2017's AFS did), or
(b) reuse an existing disposable pipeline already in the system read-only
for pure exploration (confirm its node/task shape via the Yaml tab first).
Pytest-side API clients (`api/client.py`) don't hit this — they call the
real `ELITEA_API_BASE` directly over plain `requests`, no browser CORS
policy involved at all; this trap is specific to in-browser JS.
