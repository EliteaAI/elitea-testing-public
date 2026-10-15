---
name: Sandbox APP_PREFIX gap and Playwright MCP browser gap are independent, both self-triage-able
description: missing APP_PREFIX=/app gives a 404 that LOOKS like a timeout; a broken MCP browser binary doesn't block a direct playwright.sync_api script — check both before escalating or dispatching
type: feedback
---

## What happened (issue #2440, ELITEA-2310, this session)

Two separate sandbox gaps, hit back to back, neither a repo defect:

1. **No `automation/.env.test` + no `APP_PREFIX` in the shell env** →
   `settings.app_base_url` silently resolves to `https://dev.elitea.ai` with
   NO `/app` prefix (`config.py`'s `app_prefix` default is `""`). The DEV
   backend serves a client-rendered 404 page at HTTP 200 for that bare URL —
   so `AnalyticsPage.navigate()`'s `expect_response(...)` wrapper around the
   analytics-fetch GET times out (`Timeout 15000ms exceeded while waiting for
   event "response"`), because the SPA never mounts the route that would fire
   that request. The pytest failure LOOKS like a backend/network timeout; it
   is a client-side routing miss from a missing env var. One `export
   APP_PREFIX=/app` (or set it in a created `.env.test`) before anything
   else, confirmed via `settings.app_base_url` directly in a one-liner,
   fixes it instantly — don't chase a phantom timeout.
   (test-automation-engineer independently hit and logged the identical
   pattern same day: `sandbox_missing_env_test_app_prefix_404.md`.)

2. **Playwright MCP's own browser launch can be broken** (`Error:
   async initializeServer: Chromium distribution 'chrome' is not found at
   /opt/google/chrome/chrome`) while a **direct `playwright.sync_api` script**
   in the same sandbox launches Chromium fine via `.venv`'s own installed
   browser (once `PLAYWRIGHT_BROWSERS_PATH` points at a usable install — see
   `sandbox_playwright_browser_revision_mismatch_readonly_cache.md` for that
   half). These are independent failure surfaces — MCP shells out to a
   hardcoded CDP-launch path, pytest/your own script uses the pip package's
   own browser resolution. **Don't let an MCP tool error block live-DEV
   triage** — fall back to a short inline Python script
   (`sync_playwright() as p: ... p.chromium.launch(headless=True)`) using the
   same `api_auth.get_playwright_storage_state()` the fixtures use, dump
   whatever DOM state you need (`query_selector_all`, `get_attribute`,
   `text_content`), and you have the same ground truth MCP would have given
   you.

## Rule going forward

At the start of any live-DEV triage in a fresh sandbox: (a) confirm
`settings.app_base_url` actually contains `/app` before trusting any
navigation-related failure's surface symptom (timeout, 404, blank page all
look different but share this one root cause); (b) if the Playwright MCP
tool errors on launch, don't treat it as a hard blocker — write a 15-line
inline script using the project's own `api_auth`/`config` modules and
`playwright.sync_api` directly. Both checks cost under a minute and prevent
chasing the wrong layer.
