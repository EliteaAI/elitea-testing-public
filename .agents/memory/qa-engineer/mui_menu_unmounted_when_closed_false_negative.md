---
name: MUI Menu unmounted-when-closed causes false "doesn't exist" reads
description: Before concluding a feature is missing/broken from a closed-state DOM check, open any overflow Menu/Popover first
type: feedback
---

## What happened (ELITEA-2454, 2026-08-09)

While analysing "Run Details — Delete Run from History"
(`test-specs/pipelines/l2_run-details-delete-run-from-history_ELITEA-2454.md`),
I executed a pipeline 3× in one embedded-chat conversation and checked
`document.querySelectorAll('[data-testid="pipeline-run-node-label"]').length`
— it returned `1` every time, and `document.getElementById('runNodes-history-menu')`
was `null`. I concluded the "run history" (multi-run accumulation) feature
was broken and filed `EliteaAI/elitea-testing-public#1377`.

It wasn't broken. `RunStateNodeGroup.jsx` only ever renders the CURRENT/last
run's label directly; every older run lives inside a MUI `Menu` that is
**entirely unmounted while `open=false`** (MUI's default — no `keepMounted`).
There WAS a toggle button to open it (a testid-less clock-icon `Box`,
sibling immediately before the visible run-node `Box`) — I just didn't look
for a plain, unlabelled sibling element before concluding absence. Opening
it revealed all 3 runs were correctly tracked. I retracted and closed the
issue in the same session with the corrected mechanism in the closing
comment.

## The generalizable lesson

**Before concluding "only N exist" / "feature X doesn't accumulate state"
from a closed-state DOM/count check, actively look for — and open — any
overflow control (Menu, Popover, Accordion, "N more" chip, clock/history
icon) that might be gating the rest.** A MUI `Menu`/`Popover` without
`keepMounted` renders ZERO children in the DOM while closed — a `count()`
or `getElementById` check performed before opening it is not evidence of
absence, it's evidence you haven't looked yet. Specifically:
- `querySelectorAll` / Playwright `.count()` on a testid that's reused
  inside AND outside a collapsible container will undercount whenever the
  container is closed.
- A raw `document.getElementById('some-known-id')` check for "is this menu
  ever used" is worthless if the id belongs to a conditionally-mounted
  component — always OPEN the trigger first.
- When a toggle/trigger element has literally nothing to grab (no testid,
  no aria-label, no Tooltip) — as `RunStateNodeGroup`'s clock icon did here
  — that itself doesn't mean it doesn't exist; check the DOM structure
  (siblings of a known-good testid) via `element.previousElementSibling` /
  `parentElement.children`, not just a targeted selector guess.

## Where this recurs in THIS codebase

Any feature with a "history"/"more"/"overflow" affordance backed by a MUI
`Menu`/`Popover` without `keepMounted` is a candidate for the same trap:
Run Details' own multi-run toggle (this case), and likely any future
"N more" chip pattern (cf. `entity-card-tag-overflow`, canon ruling #277 —
a different mechanism, but the same instinct of "check what's collapsed
before declaring what's missing" applies).
