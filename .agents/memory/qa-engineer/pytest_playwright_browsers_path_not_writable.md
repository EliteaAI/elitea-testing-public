---
name: pytest's bundled chromium_headless_shell missing / /opt/ms-playwright not writable
description: In this sandbox, `pytest` + pytest-playwright's default headless launch fails with "Executable doesn't exist at .../chromium_headless_shell-1248/..." and `playwright install chromium` then fails with EACCES on /opt/ms-playwright (root-owned). Workaround — a user-writable PLAYWRIGHT_BROWSERS_PATH with symlinks to the existing 1243 binaries.
type: feedback
---

Hit while reproducing the ELITEA-1790 CI failure (issue #2443) via
`HEADLESS=true ../.venv/bin/pytest <node-id>`.

Symptom 1 — plain run:
```
playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at
/opt/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell
```
The installed `playwright` Python package (1.64.0) expects browser build `1248`;
only `1243` exists on disk (`chromium-1243`, `chromium_headless_shell-1243`,
`ffmpeg-1011`), all under `/opt/ms-playwright` which is root-owned
(`drwxr-xr-x root root`) — this non-root sandbox user can't write there.

Symptom 2 — `../.venv/bin/python -m playwright install chromium` then fails:
```
Error: EACCES: permission denied, mkdir '/opt/ms-playwright/__dirlock'
```
(same reason — can't write to the root-owned dir to install the matching build).

**Workaround that worked**: point `PLAYWRIGHT_BROWSERS_PATH` at a writable dir
with symlinks pointing at the version-1243 binaries under the names Playwright
1.64 actually looks for (1248/1013), then re-run `playwright install chromium`
against *that* path (it creates the lockfile successfully there and the
symlinks already satisfy the actual binary check):
```bash
mkdir -p /opt/work_dir/.pw-browsers
PLAYWRIGHT_BROWSERS_PATH=/opt/work_dir/.pw-browsers ../.venv/bin/python -m playwright install chromium
# then always pass the same env var on every pytest/scratch-script invocation:
PLAYWRIGHT_BROWSERS_PATH=/opt/work_dir/.pw-browsers APP_PREFIX=/app HEADLESS=true \
  ../.venv/bin/pytest <node-id> -v -p no:cacheprovider
```
Confirmed with a standalone `sync_playwright().chromium.launch(headless=True)`
smoke check before trusting it in the real pytest run.

Likely sandbox-specific (another session may have `/opt/ms-playwright` writable,
or the matching 1248 build already present) — check
`ls /opt/ms-playwright` and try the plain run first; only reach for this if you
see the same `chromium_headless_shell-1248` EACCES/missing-executable pair.

Related: `elitea_1805_bucket_first_click_toggle_and_playwright_mcp_no_chrome.md`
(same sandbox class of problem — no usable Chrome for the *MCP* server; this
entry is the analogous problem for pytest's own browser launch).
