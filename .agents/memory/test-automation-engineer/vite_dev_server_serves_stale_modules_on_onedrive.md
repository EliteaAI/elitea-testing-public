---
name: Vite dev server serves stale modules on this OneDrive checkout
description: A newly added testid can be committed and still absent from localhost:5173 — restart the dev server, don't debug the test
type: project
aliases: [stale testid, HMR not firing, testid not found after add-data-testid, vite cache, dev server restart]
tags: [area/ui-localhost, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## Symptom

A testid added to `../EliteaUI/src` (committed + pushed on `automation/testids`)
is **not in the DOM** the pytest run sees. The failure reads exactly like
"the testid was never added": `element(s) not found`, and the aria snapshot shows
the element's *text* present with no testid on it.

## Cause

Vite's dev server never saw the file change. The three repos sit on OneDrive,
whose filesystem does not deliver reliable fs-watch events, so HMR never fires and
Vite keeps serving the **pre-edit transform** from its module graph. `touch`-ing
the file does **not** help.

## The 10-second check, before touching the test

```bash
curl -s 'http://localhost:5173/src/%5Bfsd%5D/<path>/<File>.jsx' | grep -c '<the-testid>'
```

(`[fsd]` must be percent-encoded.) `0` ⇒ the server is stale, the test is fine.

## Fix

**Restart the dev server** — that is the only thing that worked:

```bash
ps aux | grep -i vite            # find the `npm run dev` + `node .../vite` pids
kill <npm-pid> <vite-pid>
cd ../EliteaUI && nohup npm run dev > /tmp/elitea-ui-dev.log 2>&1 &
```

~20 s to be serving again. Confirmed 2026-08-27 (ELITEA-2287): cost one rerun.

Related: [[[surface digest] test-specs/settings-personal-tokens/_surface.md]]
