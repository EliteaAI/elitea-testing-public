---
name: Delay a single request in Playwright sync API by holding the Route, not sleeping
description: time.sleep() inside a sync-API route handler freezes the test body too — hold the Route and continue_() it from the test
type: feedback
aliases: [route delay, slow connection, throttled connection, loading state, page.route sleep, transient state]
tags: [area/playwright, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

To observe a transient state (a loading placeholder, a spinner, a skeleton) the
established in-repo pattern is `page.route(glob, handler)` where the handler does
`time.sleep(N); route.continue_()` (`tests/ui/artifacts/test_artifacts_download_*_zip.py`).

That works there only because those tests delay MANY requests in sequence. For a
**single** request it does not: Playwright's sync API runs route handlers on the same
OS thread as the test body, so the sleeping handler freezes the test body too. The
test resumes at the same instant the response lands — racing the very re-render it
came to observe. Symptom: the transient element is genuinely rendered (it shows in
the failure's aria snapshot) yet the locator times out.

## The pattern that works — hold and release

```python
held_routes: list[Route] = []

def _hold(route: Route) -> None:
    held_routes.append(route)          # never answered here

page.route(GLOB, _hold)
page.goto(url, wait_until="domcontentloaded")
# ... assert the transient state, with the request still in flight ...
for route in held_routes:
    route.continue_()                  # released from the TEST BODY
held_routes.clear()
# ... assert the loaded state ...
# finally: release anything still held + page.unroute(GLOB, _hold)
```

Deterministic (the window is the test's own progress, not a guessed constant) and
the same fidelity class as the sleep version: the product's own request is
`continue_()`d, never `fulfill()`ed — timing control per `.agents/testing.md`
§ Fidelity policy.

## Two companions

- **`BasePage.navigate()` is unusable while a request is held** — it waits for
  `networkidle`, unreachable by construction (30 s dead wait). Use
  `page.goto(f"{settings.app_base_url}{PATH}", wait_until="domcontentloaded")`.
- Always release in a `finally` and `page.unroute(...)`, or the held request leaks
  into the next test.

First established: ELITEA-2251 (Settings → AI Providers loading state), 2026-08-24.

Related: [[elitea_ui_prettier_forces_jsx_tag_reflow_when_adding_a_testid]]
