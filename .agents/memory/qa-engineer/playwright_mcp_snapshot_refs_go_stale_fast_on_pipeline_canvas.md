---
name: Playwright MCP snapshot refs go stale fast on the pipeline canvas
description: browser_snapshot [ref=eN] targets on the Flow canvas expire between calls; use CSS/testid/text selectors as the target instead
type: feedback
---

## What happened

Exploring ELITEA-2450 (Run Details panel) on `/pipelines/all/{id}` in Flow
view, `[ref=eNNN]` targets returned by `browser_snapshot` consistently failed
with `"[ref=eNNN]" does not match any elements` on the VERY NEXT tool call —
even immediately after the snapshot that produced them, with no other action
in between. Re-snapshotting produced the same (or a new, still-stale) ref.
This happened repeatedly for the embedded chat's message textbox and for
in-canvas node elements.

## Root cause (likely)

The pipeline detail page has a live ReactFlow canvas + Socket.IO-driven state
(the run node, node config panels) that re-renders frequently even when idle
— e.g. control-panel/canvas internals churn on a timer or on any socket
heartbeat. The accessibility tree the ref was resolved against goes stale
before the next call's locator resolution runs.

## Fix that worked

Pass a **CSS selector or Playwright text/testid locator string directly as
`target`** instead of a snapshot `[ref=...]` — the tool's `target` param
accepts "exact target element reference from the page snapshot, **or a
unique element selector**". This resolves live at call time, immune to
tree churn:

```
browser_click(target='[data-testid="chat-message-input"]', ...)
browser_click(target='text="Run 1 details"', ...)
```

A CSS selector matching multiple elements throws a clear Playwright
strict-mode-violation error (lists every match) rather than silently
mis-clicking — safe to iterate on.

## When to reach for this

Any page with a live/animating canvas or frequent socket-driven re-renders
(pipeline Flow view, chat with streaming responses) — prefer
testid/CSS/text `target` strings over snapshot refs from the first
interaction, don't wait to hit the stale-ref error first.
