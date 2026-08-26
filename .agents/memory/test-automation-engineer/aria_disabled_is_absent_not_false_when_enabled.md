---
name: aria-disabled is ABSENT when enabled, never "false"
description: MUI emits aria-disabled="true" on disabled MenuItems and omits the attribute entirely when enabled — assert with :not(...), never == "false".
type: feedback
aliases: [aria-disabled, MUI disabled option, greyed out option, enabled state filter]
tags: [area/locators, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The fact

MUI's `MenuItem` renders `aria-disabled="true"` (plus `Mui-disabled`) when disabled and emits
**no `aria-disabled` attribute at all** when enabled. Confirmed live 2026-08-26 on the pipeline
entry-point Trigger select.

So the enabled check must be an absence/`:not()` filter:

```python
TRIGGER_OPTION_DISABLED = '[data-testid="select-option-{}"][aria-disabled="true"]'
TRIGGER_OPTION_ENABLED = '[data-testid="select-option-{}"]:not([aria-disabled="true"])'
```

`expect(...).to_have_attribute("aria-disabled", "false")` would never match — it fails as a
timeout, which reads like a product bug rather than a wrong assertion.

## Why it matters beyond the syntax

`.agents/testing.md` § Locator policy (PR #581) names `data-*` as the state filter. MUI exposes
this state only as `aria-disabled`, so filtering the existing testid on `aria-disabled` is a
**declared improvisation** (canon-gap card #1805) — declared in the docstring and PR, not
resolved silently. Adding a `data-disabled` mirror would edit a shared component for one case
AND land on `automation/testids` only: green on localhost, red on DEV. When the choice is
between a canon-shaped handle with a promotion gap and a semantic attribute already on `main`,
the one already on `main` wins for a spec that runs in the DEV suite — and you say so.

Related: [[testid_prefix_enumeration_can_match_a_child_icon]]
