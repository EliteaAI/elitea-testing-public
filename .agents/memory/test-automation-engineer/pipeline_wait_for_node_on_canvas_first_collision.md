---
name: pipeline_wait_for_node_on_canvas_first_collision
description: wait_for_node_on_canvas(type) returns the WRONG node id on a non-empty canvas with a same-type node already present
type: feedback
---

`PipelineDetailPage.wait_for_node_on_canvas(node_type)` resolves via
`.locator(f".react-flow__node-{type}").first` — DOM/document order, not
identity. Fine on an empty canvas (its only pre-existing caller,
ELITEA-2030's add-node-menu test, adds to an empty pipeline). **Wrong** when
the canvas already has a node of the same type — e.g. `pipeline_with_llm_id`
already has "LLM 1"; adding a second LLM node and calling
`wait_for_node_on_canvas("llm")` returns `"LLM 1"` (pre-existing), not the
real new node's id ("LLM 2"). Confirmed live 2026-08-08 (ELITEA-2029, Flow→YAML
sync case).

**Reliable pattern:** snapshot `get_node_ids()` before the add, snapshot
again after, take the set difference for the new node's real id. Still call
`wait_for_node_on_canvas(type, …)` first to settle/wait for the DOM attach —
just don't trust its return value when the canvas wasn't empty beforehand.

Also confirmed same session: a freshly-added, unconnected second node has
**no `transition:` key at all** in its YAML block (distinct from the
entry-point/only-node default of always-present `transition: END`) — until
it's wired to a target or the pipeline is saved.

Full write-up: `test-specs/pipelines/_surface.md` § "Flow → YAML sync +
wait_for_node_on_canvas() same-type collision".
