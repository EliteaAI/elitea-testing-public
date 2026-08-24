---
name: Vite dev server serves a STALE transform after a testid edit
description: A new testid resolving 0 times is usually the dev server's transform cache, not your edit — verify with an un-cache-busted GET before doubting the JSX
type: project
aliases: [stale testid, HMR not picking up, testid not found, vite cache, node_modules/.vite]
tags: [area/eliteaui, type/gotcha]
created: 2026-08-22
updated: 2026-08-24
---

## Symptom

You add a `data-testid` under `../EliteaUI/src`, the dev server is running, and
the new testid resolves **0 times** in a fresh Playwright run. `touch`-ing the
file and reloading the page does not help (the remedy `_surface.md` recorded
for an earlier, milder version of this).

## Diagnose before doubting the edit

```bash
grep -c '<new-testid>' "src/[fsd]/.../File.jsx"                               # is it in the file?
curl -s http://localhost:5173/src/%5Bfsd%5D/.../File.jsx        | grep -c ...  # what the BROWSER gets
curl -s "http://localhost:5173/src/%5Bfsd%5D/.../File.jsx?t=$(date +%s)" | grep -c ...
```

The tell: the **cache-busted** URL returns the new text while the **plain** one
returns the old. The browser requests the plain form, so it runs stale code —
a `?t=` probe from inside the page (`page.evaluate(fetch…)`) will LIE to you in
the opposite direction if you only try that one.

## Fix

```bash
kill <vite pids>; rm -rf node_modules/.vite; nohup npm run dev > /tmp/eliteaui-dev.log 2>&1 &
```

Then re-verify with the **plain** curl before re-running the spec. Cost 3 turns
on ELITEA-1970 (2026-08-22) on this OneDrive-backed clone, where fs events are
unreliable.

## Milder variant — the SERVER is fine, the OPEN PAGE is stale (2026-08-24, ELITEA-2237)

Same symptom, cheaper cause and cheaper fix. If the **cache-busted** curl returns
the new text, the dev server does NOT need restarting — a long-lived browser page
(a live Playwright-MCP exploration session opened before the edit) is holding the
old module, and a plain re-`goto` of the SAME url does not dislodge it.

Fix: navigate with a throwaway query — `/onboarding?r=1`. Cost 4 turns before
reaching for it.

Decision rule, one probe:

| cache-busted curl | plain curl | cause | fix |
|---|---|---|---|
| new | new | the open page only | re-navigate with `?r=<anything>` |
| new | old | server transform cache | kill vite + `rm -rf node_modules/.vite` (above) |
| old | old | the edit never reached the server | `touch` the file / check you edited the right clone |

Never bites pytest runs — each test opens a fresh context.

Related: [[project_briefing]]
