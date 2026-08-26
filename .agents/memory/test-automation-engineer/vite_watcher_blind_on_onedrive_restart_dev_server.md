---
name: Vite watcher is blind on this OneDrive checkout — restart the dev server after JSX edits
description: New testids can be on disk yet not served; restart vite and verify with curl, never trust the DOM
type: feedback
aliases: [testid not appearing, HMR not working, add-data-testid no effect, vite stale module, dev server restart]
tags: [area/testids, area/eliteaui, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## Symptom

You add a `data-testid` under `../EliteaUI/src`, the file on disk clearly has it, and the
browser still cannot find it — after HMR, after `location.reload(true)`, and after
`touch`ing the file. Every locator times out and it looks like your JSX edit was wrong.

## Cause

The repos sit on OneDrive (`.agents/profile.md` § Additional notes). Vite's file watcher
does not reliably see writes there, so the dev server keeps serving its **cached
transform** of the pre-edit module. The DOM is downstream of that, so the DOM is not the
ground truth — the served module is.

## Fix + the one-command check

```bash
# ground truth: does the SERVED module contain the new testid?
curl -s "http://localhost:5173/src/%5Bfsd%5D/path/to/File.jsx" | grep -c "my-new-testid"
# 0 while the file on disk has it  ⇒  the watcher missed it
pkill -f "node .*node_modules/.bin/vite"
cd ../EliteaUI && nohup npm run dev > /tmp/eliteaui-dev.log 2>&1 &
# ~25 s to "VITE ... ready in"; then re-navigate
```

Run that `curl` **before** concluding a testid "didn't work" — it separates "my JSX is
wrong" from "the server never saw my JSX", which are hours apart in debugging cost.
Confirmed 2026-08-26 during ELITEA-2266/2267/2276 (13 testids, none served until restart;
all 13 rendered immediately after).

Related: [[mui_switch_testid_must_reach_the_input_not_the_root]]
