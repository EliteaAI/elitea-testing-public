---
name: Vite serves a STALE module after editing EliteaUI src (OneDrive path)
description: A just-added testid missing from the DOM is usually a dead file watcher, not bad JSX — curl the served module, then restart the dev server
type: feedback
aliases: [testid not appearing, HMR not firing, stale vite transform, dev server restart]
tags: [area/eliteaui, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## Symptom

Edit `../EliteaUI/src/**/*.jsx`, reload `localhost:5173`, the new `data-testid` is absent.
The file on disk is correct. `touch`ing the file does not help. Vite's watcher does not fire
for the OneDrive-backed clone path, so the dev server keeps serving the cached transform.

## Diagnosis in one command (do this BEFORE re-reading the JSX)

```bash
curl -s -g "http://localhost:5173/src/[fsd]/path/To.jsx" | grep '<the-testid>'
```

Absent from the served module ⇒ watcher problem, not a JSX problem.

## Fix

Restart the dev server (`pkill -f 'EliteaUI/node_modules/.bin/vite'` then `npm run dev`,
~25 s). Cost of not knowing this: two implement-verify cycles on ELITEA-2385/2386.

Related: [[mui_v7_switch_input_testid]]
