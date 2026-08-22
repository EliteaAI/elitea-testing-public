---
name: Vite serves a stale module after editing EliteaUI src on OneDrive
description: A freshly added testid can be missing from the DOM because the dev server never picked the file change up
type: project
aliases: [testid missing after edit, HMR not updating, stale vite module]
tags: [area/eliteaui, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## Symptom

Edit `../EliteaUI/src/**.jsx` to add a testid, `page.goto()` the app, and the
new testid is absent from the DOM. Twice in a row (2026-08-22, ELITEA-1973).
The edit IS on disk — the dev server is serving a stale transform (OneDrive's
file watcher misses the change).

## Diagnose before doubting the edit

```js
// in the page
const r = await fetch('/src/%5Bfsd%5D/path/File.jsx?t=' + Date.now());
(await r.text()).includes('my-new-testid')
```
(`[fsd]` must be percent-encoded.) If the served module lacks the string, it
is the watcher, not your edit.

## Fix

`touch` the edited file(s), then an in-page `location.reload()` (a fresh
`page.goto()` alone was not enough — the browser reused its cached module).
