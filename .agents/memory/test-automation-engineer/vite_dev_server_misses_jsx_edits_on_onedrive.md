---
name: Vite dev server misses JSX edits on OneDrive — touch the file to force HMR
description: A new testid can be committed and still absent from localhost:5173 — the fs watch event never fires; touch forces it
type: feedback
aliases: [testid not found, HMR not updating, dev server stale module, add-data-testid didn't work, OneDrive watcher]
tags: [area/eliteaui, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## Symptom

You add a `data-testid` under `../EliteaUI/src`, save, commit, push — and the
locator still resolves to **0 elements** on `http://localhost:5173`. The
element itself renders fine (its text is findable); only the attribute is
missing. Easy to misread as "the prop isn't passed through" or "the component
doesn't accept `data-testid`", and to start editing the shared component.

## Cause

The repos live on OneDrive, whose virtual filesystem does not reliably deliver
the fs watch event Vite depends on. The dev server keeps serving the
**pre-edit transformed module** indefinitely — HMR never fires, and nothing
reports an error. Confirmed 2026-08-23 (ELITEA-1818/1819), cost ~15 min.

## Check + fix (both cheap)

```bash
# 1. Is the running dev server actually serving your edit?
curl -s "http://localhost:5173/src/<path>.jsx" | grep -c "<your-testid>"   # 0 = stale

# 2. Force the watcher — HMR updates within seconds
touch ../EliteaUI/src/<path>.jsx
```

Make the `curl` grep the FIRST move after any `add-data-testid` edit, before
running a spec against the new handle. A dev-server restart also works but
costs minutes.

Related: [[testids_live_only_on_automation_testids_branch]]
