---
name: OAuth authorize popup reports about:blank until it settles
description: page.expect_popup() hands back a popup whose url is about:blank; wait_for_url before judging the provider
type: feedback
aliases: [oauth popup url, about:blank popup, McpAuthModal authorize popup, authorize url assertion]
tags: [area/credentials, area/oauth, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

`McpAuthModal.onAuthorize` calls `window.open('about:blank', '_blank', …)` **first**
and assigns `location` afterwards. So the page object returned by
`page.expect_popup()` reports `url == "about:blank"` with an empty body — and stays
that way for seconds. A run that reads `popup.url` (or `document.body.innerText`)
right after the click, or even after a `sleep(4)`, records "the provider returned
nothing" and can wrongly conclude the provider 404'd.

```python
with page.expect_popup() as popup_info:
    modal.authorize_button.click()
popup = popup_info.value
popup.wait_for_url(re.compile(r"login\.microsoftonline\.com"), timeout=20_000)
assert "scope=Invalid.Scope.xyz" in popup.url   # only now is this meaningful
```

## Second half — the authorize URL's SHAPE depends on discovery

Same flow, two credentials, measured 2026-08-26 on localhost:5173:

- `oauth_discovery_endpoint = …/placeholder-tenant` (discovery fails) → synthetic
  `{endpoint}/v2.0/oauth2/authorize?…&scope=<field verbatim>` → HTTP 404, blank popup.
- `oauth_discovery_endpoint = …/common` (discovery succeeds) → Microsoft's canonical
  `/common/oauth2/v2.0/authorize` **plus `nonce`** and an `openid `-prefixed scope →
  the real "Sign in to your account" page.

Never hardcode the path; assert the host from the credential's own endpoint value, and
pin specs to the placeholder tenant when determinism matters.

Related: [[project_briefing]]
