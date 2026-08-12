---
name: Interrupt before toggle — recurring Step-2-style omission across pipeline node AFS
description: ELITEA-2034/PR #1147 (3rd occurrence after Toolkit/LLM node AFS) — the inline "config renders" step routinely names both Interrupt before/after but implementations only assert the "after" toggle
type: feedback
---

## Pattern

Multiple pipeline-node-configuration AFS Coverage Maps (Toolkit, LLM, Decision
— ELITEA-2010/…/2034) have a "config renders inline" step whose Expected
Result says "Interrupt before/after switches" present, but the first
implementation pass only asserts `<node>_node_interrupt_after_toggle` and
skips "before". Root cause: "before" isn't a per-node-type static
`LocatorDescriptor` field — it's node-id-keyed (`NODE_INTERRUPT_BEFORE_TOGGLE`
template + `is_node_interrupt_before_toggle_visible(node_id, timeout)` helper,
ELITEA-2008), so it's easy to forget when every other field on the step is a
static class-level field.

## Fix (now the established pattern — reuse directly, no new locator work)

```python
assert pipeline_page.is_node_interrupt_before_toggle_visible(node_id), (
    "Interrupt before switch should be visible inline"
)
assert pipeline_page.<node_type>_node_interrupt_after_toggle.is_visible(), (
    "Interrupt after switch should be visible inline"
)
```

`is_node_interrupt_before_toggle_visible` already exists on
`PipelineDetailPage` and works for ANY node type sharing
`CommonInterruptSettings.jsx` — no page-object change needed, just call it in
the "config renders inline" step with the node's own id (the one returned by
`wait_for_node_on_canvas(...)` / `add_node(...)`).

## Preventive check for the next pipeline-node AFS implementation

Before shipping any "renders inline" step that lists Interrupt before/after,
grep the draft test for BOTH `is_node_interrupt_before_toggle_visible` AND
`_interrupt_after_toggle` — if only one hits, the Coverage Map row is
overclaiming, exactly the class of finding `afs_coverage_map_fixes_need_a_
full_sweep_not_the_named_row.md` describes.
