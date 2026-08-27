---
name: Vite serves a STALE transform after a JSX edit on the OneDrive checkout
description: A new data-testid can be absent from the DOM purely because Vite's watcher missed the file change — restart the dev server, don't re-debug the wiring
type: project
aliases: [vite stale, testid not rendering, HMR not picking up, dev server cache]
tags: [area/eliteaui, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## What happens

Editing JSX under `../EliteaUI/src` and reloading `localhost:5173` can show the
**pre-edit** DOM: a freshly added `data-testid` is simply absent. `touch`-ing the
file does **not** invalidate it either. The checkout lives on OneDrive, and Vite's
file watcher misses the change, so it keeps serving its cached transform.

## How to tell it apart from a wiring mistake in one command

Ask the dev server what it is actually serving (URL-encode the `[fsd]` brackets):

```bash
curl -s "http://localhost:5173/src/%5Bfsd%5D/features/settings/ui/secrets/SecretsTable.jsx" \
  | grep -c "secrets-pagination-prev-button"
```

`0` while the file on disk clearly contains the string ⇒ stale transform, not a
wiring bug. `1` ⇒ the JSX is being served and any absence is a real wiring problem
(wrong prop name, prop not forwarded, component not rendered).

## Fix

Restart the dev server (`kill` the `npm run dev` + `vite` PIDs, then `npm run dev`
again, ~25 s). HMR alone will not recover it.

Cost of not knowing this: an entire debugging detour re-reading correct component
source looking for a bug that was not there (settings-w05, 2026-08-27).


