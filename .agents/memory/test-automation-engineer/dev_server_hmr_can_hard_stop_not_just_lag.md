---
name: Dev server HMR can hard-stop, not just lag
description: Testid absent live after push+reload+3 fresh flows -> curl the served source; if stale, restart npm run dev, don't assume the JSX is wrong
type: feedback
---

Three prior sessions (ELITEA-2467/PR #1592, ELITEA-2207/PR #1599,
ELITEA-2076/PR #1610) documented a **transient** "first-run-after-push"
HMR-propagation LAG on `localhost:5173`: the very first navigation right
after pushing a testid commit briefly fails to find the new locator, but an
immediate standalone re-run (or two) passes clean. The established response
was "re-run once before treating it as a real defect."

**ELITEA-2077 (2026-08-20) hit a DIFFERENT, more severe variant: a hard
stop, not a lag.** After pushing `EliteaAI/EliteaUI@7b1e2c5a` (new
`subtitleTestId` prop on `PipelineEditor.jsx`), THREE separate full
create-pipeline flows — each preceded by a full page navigation, one even
after a completely fresh `page.goto()` — all rendered the OLD build with no
`pipeline-canvas-subtitle` node anywhere in the DOM. This was not settling:
`curl http://localhost:5173/src/pages/NewChat/PipelineEditor.jsx | grep
subtitleTestId` also returned NOTHING, i.e. the dev server's own served
(transformed) source was stale — proof the file-watcher had stopped
propagating changes for this file, not that the browser/React tree hadn't
re-rendered yet. Root cause suspected but not confirmed: a `npm run dev`
process that had been running for a very long time (since a much earlier,
unrelated session) on this OneDrive-backed checkout — chokidar file-watch
events over OneDrive sync are a documented slowness/flakiness source
(`.agents/workflow.md` § Traps). A SECOND, newer `npm run dev` process was
also found running on port 5174 (not 5173) — evidence of a prior session
starting a fresh server without ever killing the stale one bound to the
port automation actually targets.

**Fix**: kill BOTH the stale and any duplicate `vite`/`npm run dev`
processes (`ps aux | grep vite`, `lsof -i :5173 -sTCP:LISTEN` to find the
PID actually bound to the port under test), relaunch `npm run dev` fresh,
then retry. Fixed it immediately — the very next flow after restart served
the new testid correctly.

**Diagnostic step to run BEFORE concluding a testid was wired wrong**:
`curl http://localhost:5173/src/<path/to/file>.jsx | grep <newTestId>`.
- Present in curl output but absent live -> genuine settling lag (rare,
  re-run 1-2x per the three prior entries).
- Absent from curl output too, despite being present in the committed file
  on disk (`git show HEAD:<path> | grep <newTestId>`) -> the dev server
  itself is stale; check for a duplicate/zombie process and restart it,
  don't keep re-running the test.
