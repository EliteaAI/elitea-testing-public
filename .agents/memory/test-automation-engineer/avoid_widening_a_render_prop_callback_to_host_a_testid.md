---
name: Avoid widening a render-prop callback to host a testid or state attribute
description: Adding a param to a useCallback render prop trips zero-functional-impact grep 1; look one level up instead
type: feedback
aliases: [customRenderOption isSelected, useCallback grep hit, render prop widening]
tags: [area/testids, area/elitea-ui]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

A component often *already receives* the state you want to expose, one
parameter away. EliteaUI example (ELITEA-2240): `SidebarProjectSelect.jsx`'s
`customRenderOption = useCallback(option => …)` is invoked as
`customRenderOption(option, isSelected)` at
`src/[fsd]/shared/ui/select/SingleSelectMenuItem.jsx:101` — the second argument
exists and is unused. Widening the arrow to `(option, isSelected)` looks like a
pure no-op.

It is not free: it **modifies the `useCallback(` line**, which is a direct hit on
the reviewer's zero-functional-impact grep #1
(`^\+.*\buse(State|Effect|Memo|Callback|Ref)\(`). Declarable as mandatory
plumbing, but avoidable — and an avoidable declaration is one the reviewer will
rightly ask about.

## The move instead

**Look one level UP the tree for a component that already destructures the
state.** The MUI `MenuItem` root in `SingleSelectMenuItem.jsx` already has
`isSelected` as a prop, so the attribute went there —
`data-selected={isSelected ? 'true' : 'false'}` — a pure attribute addition,
0 hook hits, 0 new-DOM-node hits. The feature's own testid then sits on a
descendant, and the locator becomes ancestor-state + descendant-testid:

```python
PROJECT_SELECTOR_OPTION_SELECTED = '[data-selected="true"] [data-testid="project-selector-option-{}"]'
```

Still testid-anchored with a `data-*` state filter, i.e. the canon shape in
`.agents/testing.md` § Locator policy. The trade is a two-part selector for a
clean diff — worth it.

Corollary: an attribute added in a **shared** component must be generic
(`data-selected`, `select-option-selected-icon`), never feature-scoped.

## Related

[[elitea_ui_prettier_forces_jsx_tag_reflow_when_adding_a_testid]]
