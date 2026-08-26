---
name: AFS node count must include synthetic END node
description: PipelineDetailPage.get_node_count() counts the always-present END node too — AFS "total node count" wording is off by one if it doesn't
type: feedback
---

`PipelineDetailPage.get_node_count()` counts every `.react-flow__node`
element on canvas. The platform always renders a synthetic `END` node for
every pipeline — even an "empty" one, and even a lone node with no outgoing
edge gets `transition: END` (confirmed in `test-specs/pipelines/_surface.md`).

So an "empty" pipeline (per most AFS Preconditions in this feature area)
already has **1 node (`END`) before any Add-Node action**. After adding N
user-visible nodes via the Add Node menu, `get_node_count()` returns **N+1**,
not N.

**When writing/reviewing an AFS Test Step or Coverage Map row that states a
"total node count" after N Add-Node actions on an otherwise-empty pipeline,
state N+1, not N** — and say why (name the synthetic END node), so the
number isn't re-derived wrong by whoever reads it next. Caught at review on
ELITEA-2061 (PR #1353, fix round 1): AFS said "total node count == 2/3" for
2/3 user-added LLM/Code nodes; the shipped, correct test asserted
`get_node_count() == 3/4`. The test code was right all along — only the AFS
prose needed the +1.

This is specific to `get_node_count()` / the `.react-flow__node` DOM count.
If a future page-object method counts only user-created nodes (excluding
`END`), this offset would not apply — check which method the AFS/test
actually calls before assuming +1.
