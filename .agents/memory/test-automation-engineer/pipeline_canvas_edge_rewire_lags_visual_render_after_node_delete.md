---
name: Pipeline canvas edge auto-rewire lags the visual render after node delete
description: ReactFlow's rendered edges array does not recompute immediately after deleting a middle node, even though the underlying YAML/nodes model already has the correct auto-rewired transition — assert the rewire via the YAML tab right after delete, the canvas edge only reliably appears after a fresh mount (view-toggle or reload).
type: feedback
---

ELITEA-2018 (Pipeline Canvas — Delete Node, PR #1028): deleting a middle node
(`Code 1` in `LLM 1 -> Code 1 -> END`) correctly auto-rewires `LLM 1`'s YAML
`transition:` field to `END` (Code 1's own former downstream target)
INSTANTLY and reliably — confirmed via the YAML tab immediately after
confirming the delete dialog, well before any Save. But the ReactFlow
CANVAS's own rendered edge (`rf__edge-xy-edge__LLM 1---EliteAPipelineEnd`)
does **not** appear at that same moment — reproduced deterministically:
0 edges in the DOM even after an 8-second pure wait with zero interaction,
and `fit_view()` alone doesn't trigger it either. What DOES force it to
appear: switching to the YAML view and back to Flow view (a full
FlowWrapper remount that re-derives nodes+edges together from the
current YAML), or a full page reload.

**Conclusion — assertion technique, not a product defect:** when a case
needs to prove "the transition auto-rewired" at the moment immediately
after a client-side-only delete (before Save), assert it via
`get_yaml_content()` (switch to YAML view, parse, check the `transition:`
field) — NOT via `edge_exists()` on the canvas. Reserve the canvas
`edge_exists()` check for AFTER a Save + reload, where the fresh page
mount reliably shows the correct edge. An AFS that says "a new edge X -> Y
now exists" right after delete may be describing the LOGICAL state (which
the AFS itself may frame as "assert it via the YAML `transition:` field,
not just the edge visually disappearing" — read the AFS's own Axis-2
reasoning carefully before picking canvas-vs-YAML as the handle).

This is a "which layer to assert" implementer technique call (Phase 2/3
latitude), not a scope change and not a filed defect — the underlying data
model IS correct instantly; only the ReactFlow visual re-render lags.
