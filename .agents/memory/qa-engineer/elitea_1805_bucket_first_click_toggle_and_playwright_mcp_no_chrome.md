---
name: ELITEA-1805 — bucket first-click doesn't expand tree + Playwright MCP has no Chrome binary
description: Live findings from the ELITEA-1805 (Artifacts landing page, empty bucket) analysis — a bucket's first-ever selection doesn't auto-expand its left-panel tree (toggle only fires on an already-active re-click, same root cause as #651), the main-panel toolbar is unmounted (not disabled) when a bucket is empty, and the Playwright MCP server in this container has no Chrome binary.
type: feedback
---

## First-click-doesn't-expand (filed EliteaAI/elitea-testing-public#2393, sibling of #651)

Confirmed live, deterministic 3/3: clicking a bucket row that has never been
selected in the page's lifetime highlights it (`data-selected="true"`) and
updates the main panel, but does **not** render its left-panel tree content
(`BucketContent.jsx` — the "No files in this bucket" sub-label, or any files/
folders for a non-empty bucket). A **second click on the same, now-already-
active row** is what actually toggles the tree open; a third click toggles it
closed again.

Root cause: `BucketItem.jsx`'s `handleSelectBucket` only calls `onToggle` when
`isActive` is true BEFORE the click:
```js
const handleSelectBucket = useCallback(() => {
  if (isActive) onToggle?.(bucket.name);
  onSelect(bucket);
}, [bucket, isActive, onSelect, onToggle]);
```
A never-before-selected row is not yet active at click time, so `onToggle`
never fires on the first click — regardless of `BucketsListContent.jsx`'s own
`useEffect` that superficially looks like it should auto-expand on
`selectedBucketName` change (it doesn't, live, on DEV).

**Workaround for automation**: after selecting a bucket for the first time, if
the left-panel tree content isn't yet visible, click the SAME row a second
time (a deliberate, known toggle — not a retry-until-pass loop) before
asserting on it. Alternatively, navigate directly via `?bucket=<name>` in the
URL — selection then happens on mount, and the tree renders expanded
immediately, no toggle needed.

This is the SAME code path `#651` already classified as intentional (not a
defect) for ELITEA-1824's "re-click an already-selected bucket" scenario —
ELITEA-1805 just hits the first-selection edge of it. Classified as a sibling
clarification, not a new bug.

## Toolbar unmounts (not disables) on empty bucket (filed #2394)

`ArtifactTableToolbar.jsx`'s whole right-hand action section
(`artifacts-file-search-input` / `-upload-files-button` / `-download-files-button`
/ `-delete-files-button`) is wrapped in `{!isEmptyFiles && (...)}` — for a
bucket with zero files, all four testids resolve to **zero** DOM matches, not
a disabled state. Any case asserting these icons "are present" for an empty
bucket is wrong; assert `.count() == 0` instead.

## Playwright MCP has no Chrome binary in this container

`mcp__playwright__browser_navigate` failed outright:
`Error: async initializeServer: Chromium distribution 'chrome' is not found
at /opt/google/chrome/chrome`. This is a different failure mode from the
"MCP unreachable via ToolSearch" entries already in `_surface.md` — the MCP
server itself launches but can't find ITS browser. A working chromium IS on
the box, just at a different path (`/opt/ms-playwright/chromium-1243` — the
same one `automation/.venv`'s `playwright` package resolves). Fallback: a
direct `playwright.sync_api` script, `p.chromium.launch(headless=True)` (no
channel override needed, no DISPLAY in this container either), loading
`.playwright-mcp/dev-storage-state.json` as the context's `storage_state`.
Worked immediately, no retries needed.
