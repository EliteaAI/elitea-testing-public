---
name: Observe a transient loading state by delaying the REAL response, never by faking one
description: page.route + waitForTimeout + route.continue() is sanctioned timing control; recipe and measured timings for Settings → AI Providers
type: feedback
aliases: [loading state, spinner, throttle, slow connection, timing control, page.route delay]
tags: [area/settings, type/fidelity]
created: 2026-08-24
updated: 2026-08-24
---

## Recipe (sanctioned — `.agents/testing.md` § Fidelity policy)

```python
def handler(route):
    page.wait_for_timeout(DELAY_MS)   # delay the REAL response
    route.continue_()                 # never route.fulfill()
page.route("**/api/v2/configurations/configurations/**", handler)
# ... navigate, assert the loading branch, assert it is replaced by real content ...
page.unroute("**/api/v2/configurations/configurations/**")
```

Arm the route **before** the navigation that triggers the fetch, and always
`unroute` so the delay cannot leak into a sibling test.

## Two gotchas that cost time

1. **A route-chunk/Suspense `role="progressbar"` is NOT the data-loading
   indicator.** On a cold `page.goto` it covers the first ~1.5 s and is gone before
   the data-loading branch appears. Assert the feature's own loading element, not
   any progressbar.
2. **Inside the Playwright-MCP `browser_run_code_unsafe` VM, `setTimeout` does not
   exist** — use `page.waitForTimeout()` inside route handlers when probing live.

## Measured (Settings → AI Providers, 2026-08-24, project 399)

`ConfigurationSection.jsx` renders a per-section `Typography` reading `Loading...`
— **7 of them at once**, no testid (needs `{sectionTestId}-loading`). With a 6 s
delay via direct `goto`: progressbar 0-1.5 s → 7× `Loading...` 2.0-8.5 s → 12
`ai-providers-section-*` testids at 9.0 s. Without a delay the fetch finishes in
well under a second — do not try to race it.
