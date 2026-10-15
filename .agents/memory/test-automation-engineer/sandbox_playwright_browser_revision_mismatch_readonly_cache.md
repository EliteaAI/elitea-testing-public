---
name: Sandbox Playwright browser revision mismatch, read-only /opt/ms-playwright
description: /opt/ms-playwright can be read-only and ship an older chromium revision than the installed playwright pip package expects — fix with a user-writable PLAYWRIGHT_BROWSERS_PATH dir of symlinks pointing the expected revision name at the installed one, not a reinstall
type: feedback
---

## The trap

In some sandbox flavors, `playwright.sync_api`'s `chromium.launch()` fails with
`BrowserType.launch: Executable doesn't exist at
/opt/ms-playwright/chromium_headless_shell-1248/...` even though
`/opt/ms-playwright/` exists and has `chromium-1243`/`chromium_headless_shell-1243`
installed — the installed `playwright` pip package (e.g. 1.64.0) expects revision
`1248` (per its own `browsers.json`), one or two revisions ahead of what the image
shipped. `playwright install chromium` (plain, or via `python -m playwright
install`) looks like the fix but **times out / silently no-ops** downloading the
newer revision (no network egress to the CDN in some sandboxes), and even a
successful plain `playwright install` **cannot write to `/opt/ms-playwright`** —
it's root-owned read-only in this flavor (`ln -s` there fails with `Permission
denied` even as the `factory` user).

## The fix

Don't fight the install. The already-installed `1243` binaries work fine when
launched with an explicit `executable_path=` — so make the *expected* revision
name resolve to the *installed* one, in a directory you can actually write to:

```bash
mkdir -p /opt/work_dir/.pw-browsers
ln -s /opt/ms-playwright/chromium-1243 /opt/work_dir/.pw-browsers/chromium-1248
ln -s /opt/ms-playwright/chromium_headless_shell-1243 /opt/work_dir/.pw-browsers/chromium_headless_shell-1248
ln -s /opt/ms-playwright/ffmpeg-1011 /opt/work_dir/.pw-browsers/ffmpeg-1013
export PLAYWRIGHT_BROWSERS_PATH=/opt/work_dir/.pw-browsers
```

Verify the exact revision numbers both sides expect before symlinking — read the
error message for what's missing, and
`cat .venv/lib/python3.13/site-packages/playwright/driver/package/browsers.json`
for what the installed pip package wants. Confirm with a real launch + navigation
(`browser.new_page().goto("https://example.com")`), not just a successful
`launch()` call — a stale/mismatched binary can still launch and then fail oddly
on navigation.

Set `PLAYWRIGHT_BROWSERS_PATH` in every shell that runs Playwright for the rest
of the session (pytest invocations included) — it's a sandbox-env-only fix,
nothing in the repo changes, nothing is committed.

## Also: the venv's own `python -m pip` can be absent

`.venv/bin/python -m pip` → `No module named pip`, even though the venv has every
package installed (checked via `python -c "import playwright, pytest, allure..."`
— all present). Don't `python3 -m venv .venv` + reinstall from scratch assuming the
venv is broken (per `[[sandbox_missing_env_test_app_prefix_404]]`'s update) —
check `pip list`/direct imports FIRST. In this flavor the venv was fully
provisioned; only pip's own entrypoint was stripped, which has zero effect on
running tests.

Related: [[sandbox_missing_env_test_app_prefix_404]], [[dev_env_run_harness_and_goto_flake]]
