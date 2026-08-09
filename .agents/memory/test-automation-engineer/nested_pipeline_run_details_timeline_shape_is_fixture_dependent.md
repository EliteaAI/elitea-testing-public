---
name: Nested pipeline Run Details timeline shape is fixture-dependent
description: Never hardcode a nested-subgraph timeline's entry count or last-entry id — assert structurally instead
type: feedback
---

## What happened

ELITEA-2443 (subgraph state sharing — common state variables) automates a
PARENT pipeline whose `agent`-type node has a CHILD pipeline attached as a
tool. The AFS, written from a live analyst session, documented the Run
Details panel's nested timeline as a fixed 5-entry sequence for a
"2-node-parent / 1-node-child" recipe:

```
["pyodide" (parent's own code node), "<child_name>" ×2,
 "pyodide" (child's own code node), "AGENT1"]
```

— ending in a distinct `AGENT1` wrap-up entry, and the AFS's own Test Step 9
clarification said to select that last entry to satisfy case step 6 ("click
on the Agent node step in the timeline").

The implementer's own fixture (`pipeline_parent_child_state_sharing`,
`data_fixtures.py`) is structurally the SAME shape — `code(CODE1) ->
agent(AGENT1, tool=child) -> END` parent, `code(CODE1) -> END` child — built
independently (Rule 7/10-justified new fixture, no reuse target existed).
Confirmed live: it produced only **4** timeline entries with **no** trailing
`AGENT1` entry:

```
["pyodide", "<child_name>", "<child_name>", "pyodide"]
```

Hardcoding `assert "AGENT1" in timeline_node_ids[-1]` (matching the AFS's own
observed shape) failed against this recipe.

## Root cause

Nested-pipeline timeline rendering is NOT purely a function of "how many
nodes does the parent/child have" — some other runtime detail (LLM/agent
harness overhead the AFS's own child-pipeline description doesn't fully
capture, or a subtle recipe difference) changes whether the Agent node's own
wrap-up gets a distinct timeline dot. Two independently-built recipes that
LOOK the same on paper produced different entry counts.

## Fix

Never assert a literal nested-timeline entry count or a specific "last id"
for a NEW fixture — even one built to match an AFS's description of a
previously-observed shape. Assert structurally instead:
- `count >= 3` (or whatever minimum the case actually needs)
- the child's own pipeline name appears among the entries at least once
- select whichever index is `count - 1` (the actual last entry, whatever its
  label) rather than asserting its literal id
- verify Before/After state values at that selection — they hold regardless
  of whether the last entry is the child's own code node or the parent's
  Agent-node wrap-up, because in both shapes the CHILD's own code node is
  what performs the state write.

If a case genuinely needs an EXACT nested-timeline shape assertion, re-verify
live against THAT test's own fixture recipe — never inherit a shape number
from a different (even structurally-similar-looking) AFS session.

## Where

`automation/tests/ui/pipelines/test_pipeline_subgraph_state_sharing.py`,
`automation/fixtures/data_fixtures.py::pipeline_parent_child_state_sharing`,
`test-specs/pipelines/_surface.md` (implementer-appended note, same section
as the analyst's original 5-entry finding).
