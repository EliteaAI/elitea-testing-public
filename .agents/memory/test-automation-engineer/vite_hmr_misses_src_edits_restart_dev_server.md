---
name: Vite dev server can serve a stale module after a src/ edit (OneDrive watcher miss)
description: A freshly added testid resolving to count=0 may be a missed HMR reload, not a bad JSX edit — curl the transformed module, then restart npm run dev
type: feedback
aliases: [hmr miss, testid count 0, stale vite module, dev server restart]
tags: [area/elitea-ui, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## Symptom

ELITEA-1844 (2026-08-22): two testids were committed on `automation/testids`
(`delete-confirm-close-button`, `delete-confirm-entity-name`) in
`src/[fsd]/shared/ui/modal/DeleteEntityModal.jsx`, but both locators resolved
to **count=0** in a live run against `localhost:5173` — while every
pre-existing testid in the SAME file resolved fine. The JSX edit was correct.

## Cause + check + fix

The Vite file watcher had not picked up the change (the repos live on
OneDrive — the known "many file ops are slow/unreliable" hazard). The dev
server was serving its cached transform of the old file.

One-command check before doubting the edit — fetch the transformed module
straight from Vite and grep it:

```bash
curl -s "http://localhost:5173/src/%5Bfsd%5D/shared/ui/modal/DeleteEntityModal.jsx" | grep -c "<new-testid>"
```

`0` there (while an old testid in the same file greps `>0`) proves it is a
serving problem, not a JSX problem. Fix: kill the `vite` + `npm run dev`
processes and restart (`nohup npm run dev > /tmp/vite-dev.log 2>&1 &`, ~12s to
ready). After the restart both testids grepped and resolved immediately.

Related: [[artifacts_delete_flow_implementer_race_and_locator_override]]
