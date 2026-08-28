---
name: Vite dev server serves stale modules on the OneDrive clone
description: New testids invisible in the browser though present on disk — the watcher misses edits; only a dev-server restart fixes it
type: feedback
aliases: [HMR not working, testid not found, stale module, dev server]
tags: [area/environment, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

Editing `../EliteaUI/src/**` did not reach the running dev server (2026-08-28): the browser kept
rendering the pre-edit component, and `curl` of the module URL returned the OLD transform for BOTH
the plain URL and a `?t=<epoch>` cache-buster, even after `touch`. The clone lives on OneDrive, so
chokidar's watcher can miss events.

**Diagnosis in one command** (before doubting the testid name or the JSX):

```bash
curl -s "http://localhost:5173/src/%5Bfsd%5D/features/.../File.jsx" | grep -c "<the-testid>"
```

0 with the testid present on disk ⇒ it is the watcher, not your edit. **Restart the dev server**
(`kill` the vite pid, `npm run dev` again); nothing else worked. Cost ~15 minutes when mistaken for
a wrong testid.

Related: [[mui_datetimepicker_automation]]
