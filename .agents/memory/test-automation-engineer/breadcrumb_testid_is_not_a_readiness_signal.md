---
name: Breadcrumb testid is not a readiness signal
description: A *-detail-title testid may be a breadcrumb rendered from route params — it mounts instantly, before the page's data loads
type: feedback
---

# A `*-detail-title` testid can be a BREADCRUMB — not a load-complete gate

Confirmed 2026-08-27 (ELITEA-1140 / #1816, toolkit Test-route repair).

Replacing a `wait_for_timeout(2000)` after a `page.goto()` with
`expect(detail_title).to_be_visible()` looks like the textbook sleep→condition-wait
fix. It is **not equivalent** when the title testid comes from the breadcrumb bar.

`toolkit-detail-title` is declared in
`EliteaUI/src/[fsd]/shared/lib/constants/breadcrumb.constants.js`, **not** on the
page's own heading. The breadcrumb renders from **route params**, so it is visible
the instant the SPA route resolves — long before the entity's data has loaded and
the form's action bar has mounted.

**Symptom this produced:** the readiness assertion passed instantly, and the *next*
step (`ToolkitDetailPage.open_test_surface()`, which waits 10 s for
`toolkit-test-button`) then lost the race on a freshly API-created toolkit —
1 flake in the first 2-param invocation, `allure` status `broken`, invisible in the
pytest tail because rerunfailures passed it on the rerun.

**How to check before trusting a title testid:**

```bash
grep -rn "<the-title-testid>" ../EliteaUI/src/
```

A hit in `breadcrumb.constants.js` (or any route/nav constants file) means it is a
route-derived handle. Treat it as *"we are on the right route"*, never as
*"the page has loaded"*.

**The fix that is NOT a longer timeout on a bad signal:** wait on the control the
next step actually needs (`.agents/testing.md` § #1847 — wait on the element the
caller needs, not on network silence), with a **page-load-scale** budget rather
than a UI-interaction-scale one. Here: passing a 30 s budget into
`open_test_surface()` at the call site — additive, not a change to the shared
page-object default, so the sibling caller is untouched.

Result: 2 consecutive clean invocations, `reruns.json == {}`, and wall clock
*halved* (79.6 s → 43.3 s) because the wasted 10 s timeout + full rerun disappeared.
