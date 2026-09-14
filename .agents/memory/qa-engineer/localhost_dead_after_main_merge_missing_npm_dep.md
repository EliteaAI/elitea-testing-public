---
name: Localhost blank/500 after a main merge — a missing npm dep, not your case
description: Vite 500s on one module and the whole SPA renders blank; curl the module URL to read Vite's error, then npm install
type: feedback
---

**Symptom.** Every localhost test fails at step 1 — `agent-information-section` (or any page-ready
testid) never becomes visible, `document.body.innerText` is EMPTY, and the only console error is a
bare `Failed to load resource: the server responded with a status of 500 (Internal Server Error)`
with no URL. The dev server answers `200` on `/`, so a health check says it's fine.

**Cause (2026-09-09, ELITEA-1899 repair).** The session's `main` → `automation/testids` merge brought
a NEW npm dependency (`jsonc-parser`, imported by `src/[fsd]/shared/lib/utils/jsonBlock.utils.js`)
and `npm install` had not been re-run. Vite returns 500 for that one module; because it is imported
from a shared barrel, the entire app fails to boot — so it presents as "the whole product is broken",
not as "one feature is broken".

**Diagnosis in one command** — Playwright's console API does not give you the URL, but the network
listener does; then fetch the module yourself and read Vite's error JSON:

```bash
curl -s "http://localhost:5173/src/%5Bfsd%5D/shared/lib/utils/<module>.js" | head -20
# → {"message":"Failed to resolve import \"jsonc-parser\" from \"…\". Does the file exist?"}
```

A tiny standalone Playwright script that logs every `response.status >= 400` finds the module URL in
~10 s and needs no fixtures (localhost auth is `VITE_DEV_TOKEN`).

**Fix.** `cd ../EliteaUI && npm install` — 20 s, no dev-server restart needed (Vite re-optimizes).
`.agents/workflow.md` § Sync already says "if `package.json`/`package-lock.json` changed → re-run
`npm install`"; this is what skipping it looks like from the test side.

**Cost of not knowing it:** three full test invocations were spent "reproducing" a localhost failure
that had nothing to do with the case under analysis, and it nearly produced a false
"DEV-only / env-conditional" verdict.
