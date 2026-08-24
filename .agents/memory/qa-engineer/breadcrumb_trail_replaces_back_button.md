---
name: Breadcrumb trail replaces the back button on trail-declaring routes
description: On any route listed in breadcrumb.constants.js the shared BackButton is unreachable; the detail title moves INSIDE the breadcrumbs nav
type: reference
aliases: [breadcrumbs, breadcrumb-item, back-button, breadcrumb-current, toolkit-detail-title]
tags: [area/ui-shell]
created: 2026-08-24
updated: 2026-08-24
---

## What

`EditToolkit.jsx` (and the sibling detail pages) render
`hasBreadcrumbTrail ? <Breadcrumbs/> : (<BackButton/> + <Typography data-testid="toolkit-detail-title"/>)`.
`useHasBreadcrumbTrail()` is **purely route-based** (`resolveBreadcrumbTrail(pathname).length > 0`),
so on a route that declares a trail in `src/[fsd]/shared/config/breadcrumb.constants.js`
the `back-button` branch is **unreachable no matter how the user arrived** — card click
or deep link. Verified live 2026-08-24 for `/mcps/all/:id` (ELITEA-1961).

## Consequences for locators

- `breadcrumbs` — the `<nav>` wrapper (`shared/ui/breadcrumbs/Breadcrumbs.jsx:20`).
  Present on detail routes with a trail, **absent on list routes** → the cleanest
  detail-vs-list discriminator, and a legitimate `to_have_count(0)` absence assertion.
- `breadcrumb-item` — only **non-current** crumbs (`BreadcrumbItem.jsx:30`, an `<a>`).
  A 1-level trail therefore yields exactly ONE. Assert count-then-text, not `.first`.
- The **current** crumb renders `data-testid={testId ?? 'breadcrumb-current'}` — i.e. the
  page's own detail-title testid (e.g. `toolkit-detail-title`) now lives **inside** the
  breadcrumbs nav. Any existing "title is at the top of the page" assumption is stale.
- A TMS case that says "click the back arrow" on such a route is **case-text drift**, not
  a defect — assert the breadcrumb link and add `back-button → to_have_count(0)` so the
  drift stays test-enforced (worked example: ELITEA-1961, clarification #1731).

Related: [[project_briefing]]
