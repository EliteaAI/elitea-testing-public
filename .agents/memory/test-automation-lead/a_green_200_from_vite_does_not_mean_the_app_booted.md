---
name: A 200 from the vite dev server does not mean the app booted — and build_index can report ✓ on 0 cases
description: Two silent-success traps that both passed a naive check this session: the EliteaUI dev server served HTTP 200 while rendering only EnvMissingPage with zero testids, and the onetest-tms build_index verb printed "✓ wrote index.json / 0 cases indexed". Assert on rendered content and on non-zero counts, never on exit status.
type: gotcha
---

## Trap 1 — HTTP 200 from vite proves only that `index.html` is being served

Handing a target to an analyst, I verified it with
`curl -s -o /dev/null -w "%{http_code}" http://localhost:5173` → **200**, and reported it ready.
The analyst found one step later that the app rendered **only `EnvMissingPage`** —
*"System env missing: `VITE_BASE_URI`, `VITE_PUBLIC_PROJECT_ID`"* — with a
`[data-testid]` count of **0**. `EliteaUI/.env` held 4 of `.env.example`'s 12 keys,
and the master `<workspace>/.env` symlink target that `.agents/architecture.md`
describes does not exist in the factory container.

**A 200 is the web server answering. It says nothing about whether React mounted.**
Readiness for this dev server must assert on *rendered app content*: a known
`[data-testid]` is present, or `EnvMissingPage` is absent. Filed as #2386.

Two keys worth knowing if it happens again (both behaviourally safe on localhost):
`VITE_BASE_URI=` empty is inert — the gate rejects only `null`/`undefined` and
`routes.js:160` is `return DEV ? '' : VITE_BASE_URI`, so `APP_PREFIX=""` semantics
hold; `VITE_PUBLIC_PROJECT_ID=1` is this environment's value.
`VITE_ELITEA_ASSISTANT` is **not** cosmetic — it selects which of two
mutually-exclusive sidebar-footer renders mounts (see #2385).

## Trap 2 — `build_index` prints a ✓ and indexes nothing

`.agents/test-automation.yaml` § `backwrite_on_done` makes rebuilding `index.json`
mandatory after a back-write (stub CI; a stale ref = a silent 🟥 coverage gap).
The documented verb returned:

```
✓ wrote index.json
---
0 cases indexed
```

It cannot resolve the case tree from the test repo's cwd. Had it hit the real file
it would have replaced a 2.5 MB, ~1000-case index with an empty one, signalled by a
checkmark. Verified nothing was damaged (`git status` clean but for the intended
edit; `index.json` byte-identical to HEAD; no `index.json` modified anywhere in the
workspace in the last 10 min) — but that was luck about cwd, not a safeguard.

**Do this instead:** patch the single entry surgically, then validate the file parses
and the entry reads what you intended. Two independent reasons, not just expedience:
`index.json` carries **Windows path separators**, so a Linux rebuild rewrites every
path in the file; and upstream's own concurrent commits don't touch `index.json`
either, so nobody is rebuilding it on Linux today.

## The shared shape

Both traps are **success-signalled failures**: a status code that reports the wrong
layer, and an exit that reports the wrong quantity. The general rule for this
container — *verify the thing you actually depend on, not the nearest cheap proxy*:
assert rendered content, not a status code; assert a non-zero count, not a ✓. Same
family as the ledger's "a green invocation is not a clean invocation" (read
`reruns.json`, not the pytest tail).
