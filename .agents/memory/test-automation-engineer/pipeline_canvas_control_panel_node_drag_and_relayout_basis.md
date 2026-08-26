---
name: Pipeline canvas control panel — node-drag threshold + relayout-basis gotcha
description: Node drag has an activation threshold (~4-6px) distinct from pane panning; toggle-cards-size internally re-layouts, so its baseline needs auto_arrange_canvas(), not fit_canvas_view().
type: feedback
---

Confirmed live during ELITEA-2057 (Pipeline Canvas Control Panel), 2 fix rounds:

1. **Node drag (`PipelineDetailPage.move_node()`) has an activation
   threshold ReactFlow's canvas-PANE panning does NOT have.** A 60px
   `move_node` request delivered ~56px of actual displacement (px-perfect
   for `pan_canvas`, NOT for node drags). Use `abs=6.0` (not `abs=1.0`) when
   asserting an exact node-drag delta; still tight enough to distinguish
   "moved" from "locked" (which shows ~0px).

2. **`FlowEditor.jsx`'s Toggle-cards-size button (`onExpandAll`) internally
   calls the SAME `onReLayout` (position recompute) Auto-arrange uses** — it
   is NOT a pure card-resize-in-place. If you establish a "before" baseline
   via a plain `fit_canvas_view()` on a node that was manually dragged
   earlier in the test, the baseline is fitted to the STALE manual position,
   while the post-toggle measurement is fitted to the freshly-recomputed
   layout — they don't share a scale/position basis, and an "exact height
   restored" assertion fails with a real-looking mismatch (232.9px vs
   251.2px, then 304.0px vs 251.2px on a naive retry). Fix: call
   `auto_arrange_canvas()` (not `fit_canvas_view()`) to establish the
   baseline before the first Toggle-cards-size click — this puts the canvas
   on the exact basis every subsequent toggle/re-arrange call will also
   land on.

Also has a latent (unconfirmed-as-defect) app-code quirk worth knowing about
if you're ever asserting node SPACING specifically during a compact-mode
transition: `onReLayout(specifiedExpandAll)` does
`specifiedExpandAll || expandAll` — when transitioning expanded→compact,
`specifiedExpandAll` is `false`, and `false || expandAll` silently falls
through to the stale `expandAll` closure value instead of the intended
`false`. Not visibly wrong in the ELITEA-2057 assertions (which don't
compare absolute spacing), but a future analyst touching node positions
during a compact transition should know this exists.

Full writeup + code pointers: `test-specs/pipelines/_surface.md`
§ "Canvas Control Panel" and
`test-specs/pipelines/lextend_pipeline-canvas-control-panel_ELITEA-2057.md`.
