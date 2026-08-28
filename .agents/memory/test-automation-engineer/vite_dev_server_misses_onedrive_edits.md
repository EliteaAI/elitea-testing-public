---
name: Vite dev server misses edits on the OneDrive checkout
description: New testids can be absent from localhost:5173 although the JSX is correct — the watcher missed the change; curl the module, then restart npm run dev
type: project
aliases: [HMR lag, testid not found, stale vite transform, dev server restart, element(s) not found]
tags: [area/ui-automation, type/environment]
created: 2026-08-29
updated: 2026-08-29
---

## Symptom

A pytest run fails with `element(s) not found ... waiting for get_by_test_id("<brand-new-testid>")`
even though the JSX on disk carries the attribute and the change is committed and pushed.

## Diagnosis (2 seconds, do this before touching the locator)

```bash
curl -s "http://localhost:5173/src/%5Bfsd%5D/.../Component.jsx" | grep -c "<the-testid>"
```

`0` means the dev server is serving a **pre-edit transform** — Vite's file watcher missed
the change. The repos sit on OneDrive, whose fs events are unreliable; `touch`-ing the
files did **not** wake the watcher.

## Fix

Restart the dev server (`kill` the `vite`/`npm run dev` pids, `nohup npm run dev &`, wait
~25 s, re-`curl`). Verified 2026-08-29 on ELITEA-2372/2373/2387: 3 specs failed on 9 missing
testids before the restart, 3/3 green immediately after, no code change.

This is the sharper form of the "HMR lag — re-run, don't change the locator" note in
`test-specs/settings-user-profile/_surface/profile-and-drawer.md`: a re-run does NOT help
when the watcher is asleep; a restart does.

Related: [[project_briefing]]
