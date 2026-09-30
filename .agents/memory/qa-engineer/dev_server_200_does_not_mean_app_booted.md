---
name: Dev server 200 does not mean the app booted
description: A 200 from localhost:5173 only proves vite serves index.html — EliteaUI can render EnvMissingPage with zero testids. Probe a real app element before believing a target is ready.
type: feedback
aliases: [EnvMissingPage, VITE_BASE_URI, VITE_PUBLIC_PROJECT_ID, dev server not booted, target verification]
tags: [area/environment, type/preflight]
created: 2026-09-30
updated: 2026-09-30
---

## The failure mode

ELITEA-2219 analysis (2026-09-30). The dispatch said the target was prepared and
"the server answered `200` after the restart". `curl -s -o /dev/null -w "%{http_code}"
http://localhost:5173/` did return **200** — and the app could not boot at all.
React rendered only `EnvMissingPage`:

```
[Error]
System env missing:
  VITE_BASE_URI
  VITE_PUBLIC_PROJECT_ID
```

`document.querySelectorAll('[data-testid]').length` was **0**. A 200 proves only that
vite is serving `index.html`; the SPA's own env gate runs *after* that.

Cause: `EliteaUI/.env` held 4 of the 12 keys in `.env.example`, and the master
`<workspace>/.env` that the documented architecture symlinks to **did not exist**.

## The check — one line, do it before any live exploration

```python
pg.goto(URL); pg.wait_for_timeout(3000)
assert pg.evaluate("()=>document.querySelectorAll('[data-testid]').length") > 0
```

Or in bash, before launching a browser at all:
`curl -s http://localhost:5173/ | grep -q '<div id="root">'` proves nothing — the shell
always contains it. There is no cheap HTTP-level probe; you must execute the page.

## Details worth keeping

- The gate is `MISSING_ENVS` in `src/common/constants.js` (~line 34), which filters on
  `value === null || value === undefined` — so an **empty string passes**. That is why
  `VITE_BASE_URI=` (empty) is a valid way to satisfy it.
- `VITE_BASE_URI` is **behaviourally inert on localhost**: `src/routes.js:160` is
  `return DEV ? '' : VITE_BASE_URI`, so the dev router base is always `''`, preserving
  `APP_PREFIX=""`. Setting it does not change routing.
- `VITE_PUBLIC_PROJECT_ID` is `1` in this environment (independently recorded in two
  other project files). `PUBLIC_PROJECT_ID = +VITE_PUBLIC_PROJECT_ID`, so when absent it
  becomes `NaN` and you see requests like `configurations/NaN` 404ing.
- `EliteaUI/.env` is **gitignored and untracked**, so repairing it is local provisioning,
  not a repo edit — but say so in the return, because it changes the target the next
  agent inherits.
- `pkill`/`ps` may be absent in this shell. Find vite via
  `for d in /proc/[0-9]*; do tr '\0' ' ' < $d/cmdline | grep -q vite && echo $d; done`,
  and restart detached with `setsid nohup npm run dev > /tmp/vite.log 2>&1 < /dev/null &`
  (a plain `nohup … &` in a loop-killing command block can take the shell down with it).

Related: [[interactive_tours_feature_shared_surface_and_help_center_app_prefix]]
