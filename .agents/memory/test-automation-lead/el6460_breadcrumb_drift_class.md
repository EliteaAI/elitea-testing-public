---
name: EL-6460 breadcrumb drift — back-button is unreachable on every detail route
description: A red `back-button` spec is UI drift, not an outage or a promotion gap; repair shape is fixed and needs no new testid
type: project
aliases: [back-button, breadcrumb drift, EL-6460, BreadcrumbsOrTitle, back navigation red, hasBreadcrumbTrail]
tags: [area/ui-drift, type/repair-pattern]
created: 2026-09-10
updated: 2026-09-10
---

## The drift

EliteaUI@f1d4ea47 (*EL-6460, PR #884*) made `BreadcrumbsOrTitle` a binary switch:
`hasBreadcrumbTrail ? <Breadcrumbs/> : (<BackButton/> + title)`. `useHasBreadcrumbTrail()` is
**purely pathname-based**, so on every route in `BREADCRUMB_REGISTRY` the `<BackButton/>` branch is
unreachable **regardless of arrival path**, and `data-testid="back-button"` never mounts.

Covered today: toolkit, MCP, **agent**, **skill**, **pipeline** detail routes + sub-routes.

## Why it misleads triage

It fails deterministically 3/3, which reads like an outage or a promotion gap. It is neither —
`back-button` is still on `main`: **present in source, unreachable at runtime on that route**. The
closure-record grep says `main:YES testids:YES` and that is not a contradiction.

## The repair shape — copy it, don't re-derive

- Bind the ancestor crumb as `LocatorDescriptor(testid="breadcrumb-item")`. It is a **generic testid
  on a `src/[fsd]/shared/` component**, which is the policy-compliant form — so **no new testid is
  needed** and `add-data-testid` must not be run.
- Keep `back_button` bound for a first-class **absence assertion** (`to_have_count(0)`), so a future
  restoration of the arrow turns the spec red instead of the drift rotting in a comment.
- ⚠️ **Ordering is load-bearing**: breadcrumb container **visible FIRST**, `back-button` count 0
  **LAST**. `to_have_count(0)` is satisfied by a header that has not rendered, so alone it passes for
  the wrong reason — and it is the only thing keeping the drift enforced.
- The landing URL now inherits the detail page's `?name=<entity>` param (`Breadcrumbs.jsx:46`), so a
  `url.endswith("...?viewMode=owner")` assertion breaks **even after** the control is fixed. Assert
  path and params separately.
- Case text is stale everywhere it says "Back button" → file a `[Clarification]` `question` card
  (the #1731 disposition) and **do not rewrite the TMS steps yourself**. Not blocking.

Done: MCP (ELITEA-1961/#1731), agents (ELITEA-1869/#2145, PR #2178). Open: skills (#2176).

Related: [[gate_on_the_environment_the_repair_is_FOR]] · [[dev_goto_lifecycle_waiter_never_resolves]]
