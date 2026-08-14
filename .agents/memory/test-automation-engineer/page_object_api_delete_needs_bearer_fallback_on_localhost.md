---
name: Page-object API delete needs Bearer fallback on localhost
description: self.page.request calls only send cookies; localhost has none — add settings.elitea_api_token fallback or get silent 400s
type: feedback
---

If a page-object method makes a raw REST call via `self.page.request`
(e.g. a `DELETE ... via API` cleanup fallback bypassing a broken UI path),
it must NOT rely on browser-context cookies alone for auth.

On **localhost** (this project's primary test target), the EliteaUI dev
server authenticates via `VITE_DEV_TOKEN`, not real Keycloak session
cookies — `self.page.context.cookies()` is empty for the API domain
(`dev.elitea.ai`), so a cookie-only request 400s silently (an HTML error
page, not a JSON error body). This is exactly why the existing
cookie-based API clients (`ConversationAPI`, `AgentAPI`, … in
`api/client.py`) all fall back to `Authorization: Bearer
<settings.elitea_api_token>` whenever `browser_cookies` is empty
(`fixtures/api_fixtures.py`'s `_browser_cookies` fixture returns `[]` on
localhost specifically so this fallback fires).

Pattern to replicate in a page-object method:
```python
headers = {}
if not self.page.context.cookies() and settings.elitea_api_token:
    headers["Authorization"] = f"Bearer {settings.elitea_api_token}"
response = self.page.request.delete(url, headers=headers, timeout=timeout)
```

Caught this via ground-truth verification (independent API GET after the
call, not just "no exception raised") on ELITEA-2459's `#1309` fix
(`ChatPage.delete_folder_via_api()`) — the cookie-only first version
returned no exception path issue itself, but the response was a 400 my
own `response.ok` check DID catch; still, always verify a new API-cleanup
method actually removes the entity via an independent read, not just that
it didn't raise.
