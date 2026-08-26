---
name: Vite HMR misses edits under EliteaUI src/[fsd]/
description: A testid added under src/[fsd]/ keeps rendering as absent until the dev server is restarted — verify with a curl on the served module, don't debug the JSX.
type: feedback
aliases: [hmr not updating, testid not rendering, fsd bracket directory, vite stale module]
tags: [area/eliteaui, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## Symptom

Added `prevButtonTestId` / `pageSizeSelectTestId` to
`EliteaUI/src/[fsd]/entities/grid-table/ui/GridTablePagination.jsx` and wired
them from `src/pages/Artifacts/component/ArtifactTable.jsx` in the same edit.
Live run: the `pages/` change took effect (new `pageInfoTestId` value rendered),
the `[fsd]/` change did **not** — both new testids resolved to 0 elements.

## Diagnosis (30 seconds, no guessing)

```bash
curl -s 'http://localhost:5173/src/%5Bfsd%5D/entities/grid-table/ui/GridTablePagination.jsx' | grep -c prevButtonTestId
# 0  -> the dev server is serving a STALE module; the file on disk has it
```

## Fix

Restart the dev server (`kill` the `npm run dev` + `vite` pids, `nohup npm run dev &`,
~25s). After the restart the same curl returned 2 and the testids resolved.

Bracketed FSD directory names are the likely cause (watcher/glob handling), so
treat **any** edit under `src/[fsd]/` as requiring a restart, while `src/pages/`
edits HMR normally.

Related: [[artifact_bucket_fixture_delete_silently_fails_404]]
