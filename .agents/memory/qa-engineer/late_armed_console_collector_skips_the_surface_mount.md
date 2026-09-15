---
name: Late-armed console collector skips the surface's own mount
description: Arming collect_console_errors after a transit guard settles excludes the list page's own first render on EVERY run, not just on guarded ones — check what the arming point drops before accepting "nothing is filtered"
type: feedback
aliases: [console collector arming point, late arm console axis, open_list console scope]
tags: [area/social-folders, type/review-trap, status/open]
created: 2026-09-15
updated: 2026-09-15
---

## The trap

A spec-wide "Axis 2 — no unexpected console errors" is armed by `collect_console_errors(page)` —
a plain `page.on("console", …)` that captures from the arming point onward. PR #2306 (fix round on
ELITEA-3208/3209/3210) moved the arming from test start to *after* `EntityTypeBinding.open_list()`
returns, so the #2305 redirect's create-picker noise (#1971 404, #656 React key warning) stops
deciding the verdict. The docstrings say "nothing is dropped, windowed or text-filtered once it is
armed" — true, but the **arming point itself** is a window: the list page's own mount (the very
surface whose FOLDERS panel the case exercises) is now outside Axis 2 on every run, including the
runs where #2305 never fired.

## The reviewer question

For any change to WHERE a collector is armed: list what the old arming point captured that the new
one does not, and decide whether that is transit-only (fine, declare it) or the surface under test's
own render (a coverage narrowing to name explicitly). A narrower mechanism exists — arm at test
start and `console_errors.clear()` only when the guard actually re-navigates — which keeps the
successful mount covered and drops only the redirected attempt. Raised for the #2301 canon card.

Related: [[project_briefing]]
