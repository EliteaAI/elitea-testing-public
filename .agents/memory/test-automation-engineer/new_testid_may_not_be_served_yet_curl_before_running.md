---
name: A just-added testid can be missing from the DOM on the very next run — curl the dev server first
description: Verify a freshly-committed EliteaUI testid is actually served by :5173 before running the spec that needs it
type: feedback
aliases: [testid not found, dev server stale, vite hmr stale testid, waiting for get_by_test_id, add-data-testid then red]
tags: [area/eliteaui, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## What happened

ELITEA-1833 (2026-08-21). Added `artifacts-resolve-duplicates-close-button` to
`../EliteaUI` on `automation/testids` (prop-only `closeButtonTestId` on the shared
`Modal.BaseModal`), committed and pushed. The very next pytest run still saw a DOM
without it — `Locator.click: Timeout 10000ms exceeded` with a call log containing ONLY
`- waiting for get_by_test_id("artifacts-resolve-duplicates-close-button")` and **no**
`locator resolved to …` line, i.e. the element never attached. It failed that way twice
(pytest-rerunfailures burned its own reruns on it too).

Nothing was wrong with the code. A `curl` of the module off the dev server afterwards
showed the edit being served correctly, and the identical, unchanged spec then passed
first try, and again in a combined 2-spec run.

## The cheap guard

One command, before running any spec that depends on a testid you just added:

```bash
curl -s "http://localhost:5173/src/<path/to/edited>.jsx" | grep -c "<the-testid>"
```

Non-zero -> run the spec. Zero -> the dev server has not picked the edit up yet; do not
spend a ~60 s red run plus reruns discovering that.

## How to read the symptom

`- waiting for get_by_test_id(...)` with **no** following `locator resolved to …` means
NEVER ATTACHED — suspect the testid isn't in the served bundle. If the log DOES say
`locator resolved to <button …>` and then times out, that is a different problem
(visibility, overlay, actionability) and this note does not apply.
