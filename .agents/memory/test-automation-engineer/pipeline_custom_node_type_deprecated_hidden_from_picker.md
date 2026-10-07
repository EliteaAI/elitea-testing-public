---
name: Pipeline Custom node type deprecated, hidden from Add Node picker
description: EL-6616 removed "Custom" from the Add Node menu permanently — any test that adds a NEW Custom node via the UI will time out forever
type: project
---

**Finding (2026-10-07, ELITEA-2036/#2409 triage):** `test_pipeline_custom_node_configuration.py::test_custom_node_configuration`
times out at `pipeline_detail_page.py::add_node()` —
`get_by_role("menuitem", name="Custom", exact=True)` never appears — because
the "Custom" node type was **intentionally deprecated and hidden from the
node picker**, not because of a selector/locator drift.

Root cause (EliteaUI, `origin/main`, commit `0cd5e792` —
"feat: [EL-6616] Deprecate and hide Custom node from pipeline node picker
(#993)", 2026-09-11): `deprecated.constants.js` added
`PipelineNodeTypes.Custom` to `DeprecatedNodes`, which `DeprecatedOrInvisibleNode`
derives from. **Both** node-add surfaces filter on this list:
`src/pages/Pipelines/Components/AddNodeMenu.jsx` (`getVisibleNodeTypes()` —
the "+" button `add_node()` actually clicks, `data-testid="pipeline-add-node-button"`)
and `ConnectionDropdown.jsx` (`nodeCreationMenuItems`, the drag-to-connect
variant). There is **no surviving UI path to add a new Custom node** — the
deprecation message itself says so: "This node is deprecated and hidden from
the node picker. Existing Custom nodes will keep working — please select a
specific node type (Toolkit, MCP, LLM, Code, etc.) instead."

**Why this isn't class A/E (adjustable) or B/C (bug):** it's not a locator
rename (the "Custom" label text is unchanged in `PipelineNodeDisplayNames`)
and it's not broken-per-source — it's a deliberate, documented, *permanent*
product removal. The entire TMS case (ELITEA-2036 — "add + configure a NEW
Custom node") now tests a capability that can never be reached again through
the UI. This doesn't fit the skill's class table cleanly (F is for a
*temporary* handle gap awaiting a testid addition, not a feature pulled on
purpose) — treated as its own declared-improvisation class: **do not adjust,
do not file a bug, escalate to the lead/human for a scope decision** (retire
the case, or re-point it at a still-addable node type under explicit
sign-off since that changes WHAT is tested).

**If you hit a red test anywhere else that adds a Custom node via the UI
picker** (not just ELITEA-2036), this is almost certainly the same root
cause — check `DeprecatedConstants.DeprecatedNodes` in EliteaUI before
re-deriving the triage.
