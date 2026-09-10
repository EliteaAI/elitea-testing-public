---
name: Breadcrumb trail replaced the back-arrow on every entity detail route
description: back-button never mounts on agent/pipeline/skill/MCP/toolkit detail routes since EL-6460; the ancestor breadcrumb-item link is the go-back control
type: reference
aliases: [back-button missing, back-button count 0, breadcrumb-item, BreadcrumbsOrTitle, EL-6460, f1d4ea47]
tags: [area/ui-drift, type/locator]
created: 2026-09-10
updated: 2026-09-10
---

## The fact

EliteaAI/EliteaUI@`f1d4ea47` (2026-09-01, *feat: [EL-6460] Add Breadcrumb Navigation
to Agent, Pipeline, and Skill Details Pages*, #884) added
`src/[fsd]/shared/ui/breadcrumbs/BreadcrumbsOrTitle.jsx`, which renders
`hasBreadcrumbTrail ? <Breadcrumbs/> : (<BackButton/> + title)`.

`useHasBreadcrumbTrail()` is **purely pathname-based** and `BREADCRUMB_REGISTRY`
(`src/[fsd]/shared/lib/constants/breadcrumb.constants.js`) declares a `parent` for
every entity detail route. ⇒ the `<BackButton/>` branch is **unreachable** on those
routes no matter how the user arrived, so `data-testid="back-button"` never mounts.
Confirmed live on `dev.elitea.ai`, `/app/agents/all/<id>`: `back-button` count **0**.

## The replacement control

`<nav data-testid="breadcrumbs">` containing crumbs from `BreadcrumbItem.jsx`:

- non-current ancestors → hardcoded `data-testid="breadcrumb-item"` (a **generic
  shared-component testid**, which is policy-compliant); the `testId` registry prop
  is IGNORED on this branch
- the current crumb → `data-testid={testId ?? 'breadcrumb-current'}`, e.g.
  `agent-detail-title` / `skill-detail-title` / `pipeline-detail-title` /
  `toolkit-detail-title`

The ancestor crumb is a react-router `<Link>` (client-side, no reload) and
`Breadcrumbs.jsx:46` passes the CURRENT location's `search` into `to`, so the landing
URL carries the detail page's params through — e.g. `/agents/all?viewMode=owner&name=Echo%20Agent`.
The extra `name` param is inert (the list request goes out with `query=` empty).

## How to handle it in tests

Mirror `McpFormPage` (ELITEA-1961 / CLARIFICATION #1731), the already-merged precedent:
declare `breadcrumbs` + `breadcrumb_parent_link` `LocatorDescriptor`s, and keep the
`back_button` field bound for an **absence assertion** (`to_have_count(0)`) so the drift
stays test-enforced instead of documentation-only.

**Count-then-index, never bare `.first`** on `breadcrumb-item`:
`applyBreadcrumbLabels` (`breadcrumb.helpers.js:65-68`) DROPS any non-current ancestor
whose label is empty, so trail depth is not guaranteed. See
`PipelineDetailPage.close_run_history` for the guarded shape.

**After clicking the crumb, wait for the first `entity-card-name` to be VISIBLE.**
Awaiting the list re-fetch response plus `networkidle` is not enough — measured a `[]`
read once (the `/socket.io/` polling vs networkidle race, [[#1847]]).

Related: [[project_briefing]]
