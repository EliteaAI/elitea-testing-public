---
name: EL-6616 Custom node permanently removed from add-node picker
description: Custom node type deprecated/hidden from every add-path on DEV (2026-09-11) — any case whose premise is adding a NEW Custom node is unreachable by design, not drift.
type: reference
---

**EL-6616** (EliteaUI commit `0cd5e792`, PR #993, 2026-09-11) added `PipelineNodeTypes.Custom`
to `DeprecatedConstants.DeprecatedOrInvisibleNode`. `AddNodeMenu.jsx`'s `getVisibleNodeTypes()`
filters on that list, so "Custom" no longer renders in the canvas Add-node picker; the
drag-to-connect path (`ConnectionDropdown.jsx`) applies the identical filter. Source comment:
*"Existing Custom nodes will keep working — please select a specific node type (Toolkit, MCP,
LLM, Code, etc.) instead."* **No surviving UI route to add a NEW Custom node.** Existing ones
(already in a saved pipeline) still open/configure fine.

**Two shapes of fallout, don't conflate them:**
- **Menu-list / count cases** (e.g. ELITEA-2030) — fixed by adjusting the expected list 11→10
  plus an additive absence-assertion. Precedent: PR #2324, clarification sign-off #2323.
  This shape fits squarely in `adjust-automated-test` class **A** (UI drift) — straightforward.
- **"Add + configure a new Custom node" cases** (e.g. ELITEA-2036) — there is no UI path left
  to even start the flow. Doesn't fit any adjust-automated-test class cleanly (not A: nothing
  to climb the ladder for; not B/C: deliberate, not a bug; not E: no testid replacement exists;
  not quite F: permanent, not a temporary handle gap awaiting work). This is a scope decision
  (retire the case / re-point it to a different node type / repurpose as a deprecation guard) —
  file a `question` issue with options + a recommendation, don't adjust solo. ELITEA-2036 →
  question #2413 (unresolved as of 2026-10-07): recommended re-pointing to `Toolkit`, the node
  type the deprecation's own source comment names as the replacement for Custom's use case.

If another case's CI failure traces to the Custom node picker or a "Custom" menu item being
unreachable, check which shape it is before triaging further — don't assume class A.
