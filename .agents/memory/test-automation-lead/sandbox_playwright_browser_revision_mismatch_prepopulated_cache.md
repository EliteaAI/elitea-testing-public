---
name: Sandbox Playwright browser revision mismatch — check for a pre-populated cache before symlinking
description: /opt/ms-playwright had chromium rev 1243 but the venv's playwright-core wanted 1248 — before building the symlink workaround, check /opt/work_dir/.cache/ms-playwright (or similar sibling cache dirs); it may already have the right revision
type: feedback
---

## What happened (issue #2441/ELITEA-2284, 2026-10-15)

Same root cause as `test-automation-engineer`'s
`sandbox_playwright_browser_revision_mismatch_readonly_cache.md`: pytest's
`browser = p.chromium.launch(...)` failed with `BrowserType.launch:
Executable doesn't exist at
/opt/ms-playwright/chromium_headless_shell-1248/...` because
`PLAYWRIGHT_BROWSERS_PATH` defaulted to `/opt/ms-playwright`, which only had
revision `1243` installed, while the venv's `playwright-core` (`1.64.0-beta`)
wants `1248`.

**Before reaching for that entry's symlink-farm fix, `ls` nearby cache
directories first** — in this sandbox flavor, `/opt/work_dir/.cache/ms-playwright`
already existed with `chromium-1248` / `chromium_headless_shell-1248` /
`ffmpeg-1013` pre-installed (likely populated by an earlier
`playwright install` that *did* have egress, or baked into the image at a
different path than the default). One line fixed it with no symlinks and no
network call:

```bash
export PLAYWRIGHT_BROWSERS_PATH=/opt/work_dir/.cache/ms-playwright
```

Confirmed by actually running pytest end-to-end against DEV afterward (not
just a bare `launch()` smoke check).

## Rule going forward

On `BrowserType.launch: Executable doesn't exist at /opt/ms-playwright/...`:
1. `cat .venv/lib/python3.13/site-packages/playwright/driver/package/browsers.json`
   (or wherever the venv's playwright-core lives) to confirm the exact
   revision wanted.
2. `find / -maxdepth 4 -iname "*ms-playwright*" -o -iname "*playwright*" -type d 2>/dev/null`
   (scoped, not full-root) to see if a sibling cache already has that
   revision installed somewhere else on the box.
3. Only if nothing matches, fall back to the symlink-farm workaround in
   `test-automation-engineer`'s `sandbox_playwright_browser_revision_mismatch_readonly_cache.md`.

Also hit the sibling `APP_PREFIX` env-var gap in the same session
(`sandbox_app_prefix_and_mcp_browser_can_both_be_broken_independently.md`) —
both are independent, both self-triage-able in under a minute, neither is a
repo defect worth escalating.

Related: [[sandbox_app_prefix_and_mcp_browser_can_both_be_broken_independently]]
