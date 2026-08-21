---
name: Vite serves stale JSX after an EliteaUI edit (OneDrive checkout)
description: A new testid can be committed, pushed and still invisible in the browser — restart the dev server, don't debug the JSX
type: project
aliases: [stale testid, HMR not working, testid not rendering, vite cache, OneDrive watcher]
tags: [area/eliteaui, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## Symptom

Added `closeButtonTestId` to `ZipDownloadProgressDialog.jsx` (ELITEA-1843), committed +
pushed to `automation/testids`. The live page kept rendering the close button with **no**
`data-testid` — through a full browser reload, not just HMR.

## Diagnosis (2 commands)

```bash
curl -s "http://localhost:5173/src/<path>.jsx" | grep -c <testid>            # 0  ← stale transform
curl -s "http://localhost:5173/src/<path>.jsx?t=$(date +%s)" | grep -c <id>  # 1  ← new code IS on disk
```

The `?t=` cache-buster bypasses Vite's transform cache. Divergence between the two ⇒ Vite's
**file watcher never fired** — the repos live on OneDrive, where fsevents is unreliable.
`touch`ing the file does NOT help.

## Fix

Restart the dev server; then re-verify with the plain (no `?t=`) curl before touching the JSX:

```bash
kill <vite pid>; cd ../EliteaUI && nohup npm run dev > /tmp/eliteaui-dev.log 2>&1 &
```

Cost when missed: ~20 min of "my prop-only testid add must be wrong" — it wasn't.

Related: [[MEMORY]]
