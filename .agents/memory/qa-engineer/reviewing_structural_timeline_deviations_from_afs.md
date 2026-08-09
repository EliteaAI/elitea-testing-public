---
name: Reviewing structural timeline deviations from AFS
description: When implementer's fixture yields a different nested-timeline shape than the AFS's live session, verify the mechanism (state Before/After tied to whichever node is selected), not the label
type: feedback
---

## Context

ELITEA-2443 (pipeline subgraph state sharing) review: the AFS's live session
observed a 5-entry nested Run Details timeline ending in a distinct `AGENT1`
wrap-up dot; the implementer's own (structurally-similar) fixture produced
only 4 entries with no trailing `AGENT1` — the timeline instead ends on the
child's own code node. The AFS's own Automation Hints already authorized
asserting structurally instead of the literal shape, so this is NOT AFS
drift — but it changes what "select the last entry" actually selects.

## How I verified it wasn't a defect

Checked `get_run_details_state_before_value`/`_after_value` in
`pipeline_detail_page.py` — they read the Before/After box for whichever
timeline step is currently selected (`select_run_details_timeline_step`),
keyed only by variable name, not by node label. So selecting "whichever
entry is last" (regardless of whether that's `AGENT1` or the child's own
code node) still shows the state as-of-entering/leaving THAT node. Since the
child's own code node is what performs the write in both fixture shapes, the
Before/After assertions hold either way. This is what makes the
"select last, assert structurally" pattern sound rather than a coincidence
— confirm the underlying state-panel binding (keyed by selection, not label)
before trusting a structural rewrite of a literal AFS assertion.

## Where

`automation/tests/ui/pipelines/test_pipeline_subgraph_state_sharing.py`,
`automation/pages/pipeline_detail_page.py:7287` (`get_run_details_state_before_value`).
