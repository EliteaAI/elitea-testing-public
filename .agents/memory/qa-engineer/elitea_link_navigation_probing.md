---
name: Probing Elitea in-app link navigation (new tab + project switch)
description: Two waits that make or break any "click a link, check where it lands" analysis in Elitea
type: feedback
aliases: [target blank elitea, project switch url, popup wait elitea, notification link]
tags: [area/ui, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## Links inside notifications (and similar surfaces) are `target="_blank"`

They open a NEW TAB. `page.wait_for_url()` on the original page hangs forever. Use
`page.expect_popup()` / `context.expect_page()` and assert on the popup `Page`.

## Elitea URLs with a `/{projectId}` prefix rewrite themselves after load

`/{projectId}/chat?conversation=5883` is consumed by the project switcher and becomes
`/chat/5883?name=Hello`. Reading the URL after `domcontentloaded` gives the PRE-switch
value and produces a false verdict. Settle on the final shape first:

```js
await p.waitForFunction(() => /\/chat\/\d+/.test(location.pathname), null, {timeout: 25000});
```

Cost one wasted probe round on 2026-08-26 (12 conversations all reported "fine" while
still mid-redirect; two of them were actually dead).

## RTK-Query caches search terms — a repeated query fires NO request

Re-typing a term already fetched this session serves from cache, so
`wait_for_response(... "search=")` times out. Wait on the rendered row count instead.
Same root cause as the already-documented "clearing the search field issues no request".

Related: [[project_briefing]]
