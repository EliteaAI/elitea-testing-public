---
name: Pipeline canvas add-node position collision-avoidance is exact-coordinate only
description: calculatePositionForNewNode only dodges identical (x,y), not bounding-box overlap — new nodes can visually overlap existing ones
type: reference
---

`EliteaUI/src/[fsd]/features/pipelines/flow-editor/lib/helpers/flowEditor.helpers.js`
`calculatePositionForNewNode(xStartPos, yStartPos, flowNodes)`: loops, offsetting by
`+60/+60` px, **only** while a node exists at the *exact* same `(x, y)` (0.01
tolerance). It does not know node card dimensions and does not check for bounding-box
overlap against nearby-but-not-identical positions. `pipeline_detail_page.py`'s
`add_node()` doesn't pass explicit coordinates either — it always lands wherever this
helper computes (viewport-center-relative).

Relevance: during PR #1141 review (ELITEA-2008), the implementer diagnosed a
click-misdirection bug where a `force=True` Playwright click on a node's "Interrupt
before" switch silently landed on "some other canvas element" after an earlier
add/delete-node cycle, and fixed it with a JS-evaluate `.click()` on the (relocated)
testid'd native input. The fix is real and verified (root cause: MUI v7 `Switch` drops
a legacy `inputProps` testid; the relocated testid + JS click do land on the correct
element). But I could not rule out — and didn't have time to root-cause deeper,
statically — whether the underlying "wrong element is topmost" symptom is itself a
real product UX defect (node cards visually overlapping post add/delete, which a real
user's mouse would hit too) rather than a pure Playwright/synthetic-event artifact.
If this pattern recurs (another case doing add/delete cycles on the pipeline canvas
before interacting with a node control), it's worth an actual live repro with the
Elements panel open to identify what's really on top, before assuming it's
test-tooling-only.
