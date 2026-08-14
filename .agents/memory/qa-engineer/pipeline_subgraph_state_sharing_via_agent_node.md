---
name: Pipeline subgraph state sharing via Agent node
description: "Subgraph" node type is deprecated; Agent node calling a pipeline-as-tool DOES share common-named state vars, confirmed live
type: feedback
---

ELITEA-2443 ("Subgraph State Sharing — Common State Variables") session, 2026-08-09.

- The flow-editor's dedicated `pipeline`/subgraph NODE TYPE (`SubgraphNode.jsx`) is
  legacy/deprecated — not in the Add Node menu's 11 modern types (ELITEA-2030's
  live-verified list has no "Pipeline" entry). The `elitea-pipeline` skill's
  `yaml-schema.md` says "Nested pipelines are gone → delegate to an `agent` node."
  A case titled "Subgraph ..." that describes "add an Agent node calling the child
  pipeline" is NOT case-text drift — it's naming the correct modern mechanism with
  a legacy noun. Don't go hunting for a nonexistent add-node "Pipeline" entry.
- An Agent node's `tool:` YAML field alone does NOT resolve a pipeline, even if the
  name is byte-correct — confirmed live: renders "Agent not found — select a
  replacement or delete this node" until the pipeline is ALSO attached via the
  Tools section's "+ Pipeline" popper (`agent-add-pipeline-button` →
  `select_pipeline_in_popper()`, same `application_relation` PATCH→201 mechanism
  as ELITEA-2064/2038). The attach is a real runtime precondition, not just a UI
  convenience — a fixture that pre-sets `tool:` in YAML still needs the attach step.
- Despite the Agent node's documented schema having only a `task`-string
  input_mapping (no state-mapping field), common-NAMED state variables ARE shared
  automatically between the calling (parent) pipeline and the called
  (pipeline-as-tool) child — confirmed live via Run Details Before/After: child's
  write to `state_1`/`state_2` shows up as the PARENT's own Run Details After value
  for the SAME-named variable. Sharing is keyed by variable-name identity across
  the two pipelines' `state:` blocks, not by any node-level mapping config.
- The child pipeline's own execution is NOT opaque in Run Details — its timeline
  steps nest inside the SAME panel as the parent's (5 entries for a 2-node parent +
  1-node child: parent-code, child-name×2, child-code, AGENT1). This is new
  territory vs ELITEA-2450/2451/2452/2453 (all single, non-nested pipelines) —
  don't assume a pipeline-as-tool call renders as one opaque timeline entry.
- Zero new testids were needed for this case — every handle (Tools-attach popper,
  Agent-combobox, Run Details timeline/state rows) already existed from
  ELITEA-2030/2038/2064/2450-2454's own implementation work.

Full writeup: `test-specs/pipelines/l2_pipeline-subgraph-state-sharing-common-vars_ELITEA-2443.md`
+ `test-specs/pipelines/_surface.md` § "Subgraph state sharing via Agent node...".
