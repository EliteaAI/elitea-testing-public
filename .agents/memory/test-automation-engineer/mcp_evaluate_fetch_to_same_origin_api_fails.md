---
name: MCP evaluate() fetch to same-origin API fails
description: browser_evaluate-injected fetch() to /api/v2/... throws "Failed to fetch" even for a plain GET — use page.request in real tests, not evaluate, for ad-hoc API calls
type: feedback
---

During live exploration via Playwright MCP (`browser_evaluate`), a `fetch()`
call injected into the page's console context — even a plain `credentials:
'include'` GET to the app's own same-origin `/api/v2/...` path that the app
itself calls successfully via its own network requests — throws
`TypeError: Failed to fetch`. Confirmed on `http://localhost:5173` (EliteaUI
dev server), both for a GET and a DELETE.

This is NOT a problem for real pytest tests: `page.request` (Playwright's
`APIRequestContext`, used by `ChatPage.delete_folder_via_api()` and
sibling `*_via_api()` cleanup methods) is a separate request context that
bypasses whatever blocks the `evaluate()`-injected `fetch()` — it is the
correct tool for both real test assertions and any script/page-object
cleanup helper.

Practical consequence: an MCP exploration session cannot use
`browser_evaluate` + `fetch()` as a quick ad-hoc cleanup shortcut (e.g.
deleting a folder/conversation created purely for manual verification). Use
the UI's own delete flow instead (hover, dot-menu, confirm), or accept that
exploration-only artifacts may need to be left for a later cleanup pass —
note it explicitly rather than silently leaving stray objects unmentioned.
