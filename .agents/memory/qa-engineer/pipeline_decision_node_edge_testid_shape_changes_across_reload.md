---
name: Decision node edge testid shape changes pre-save vs post-reload
description: Same edge's data-testid differs live-drag vs parsed-from-YAML; use edge_exists() without handle_suffix
type: feedback
---

Confirmed live 2026-08-04 (ELITEA-2034 analysis). Decision node's DECISION
OUTPUTS and default-output edges render with a DIFFERENT `data-testid` shape
depending on whether they were just interactively drag-connected (live
`onConnect`) or re-parsed from the persisted YAML after Save + reload:

- `nodes`-handle (DECISION OUTPUTS) edge: pre-save
  `rf__edge-xy-edge__{source}nodes-{target}target` → post-reload
  `rf__edge-xy-edge__{source}---{target}` (the `nodes` handle-suffix
  disappears).
- `default_output` edge: pre-save
  `rf__edge-xy-edge__{source}default_output-{target}target` → post-reload
  `rf__edge-xy-edge__{source}default_output---{target}` (suffix stays, but
  the separator changes from concatenation to `---`).

Root cause: the live-drag id comes from ReactFlow's own `onConnect` default
construction (same shape as HITL's route edges); the post-reload id comes
from `parsePipeline.helpers.js`'s `handleNewDecisionNode`, which builds it
independently as `` `${EDGE_PREFIX}${id}---${branch}` ``.

**Use `PipelineDetailPage.edge_exists(source_id, target_id)` WITHOUT the
`handle_suffix` kwarg** for Decision node edges in either state — its
prefix+substring matching tolerates both shapes. Do NOT use
`edge_testid_present()`/`EDGE_TESTID`/`get_edge_locator()` (exact `---`-only
match) for Decision edges — contrast with Router node (ELITEA-2033), whose
routes edges use the `---` shape in BOTH states and so ARE safe with the
exact-match helpers.

Full writeup: `test-specs/pipelines/l2_pipeline-decision-node-configuration_ELITEA-2034.md`
§ Concrete Handles / Automation Hints; digest: `test-specs/pipelines/_surface.md`.
