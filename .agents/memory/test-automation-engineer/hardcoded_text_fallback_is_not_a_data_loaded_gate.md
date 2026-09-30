---
name: A text node with a hardcoded fallback is not a data-loaded gate
description: Waiting on a title that falls back to a source default returns while the data-driven content is still skeletons — gate on an element that only the loaded branch renders
type: feedback
aliases: [skeleton race, defaultTitle, hardcoded fallback wait, config loading gate, title is not a gate, one-shot count reads zero]
tags: [area/playwright, area/waits, type/gotcha]
created: 2026-09-30
updated: 2026-09-30
---

## The trap

A component that renders `data?.field || HARDCODED_DEFAULT` **paints immediately**, before
its request resolves. So waiting on it proves nothing about the data, and any *one-shot*
read that follows (`.count()`, `get_attribute()`, `text_content()`) sees the loading state.

Worked case (ELITEA-2219, Help Center). `ResourcesPage.jsx` renders each card as
`configValues[config.titleKey] || config.defaultTitle`, while the card's LINKS live in
`ResourceCard`'s `!isConfigLoading && hasLinks` branch behind `<Skeleton>`s. Measured live
at the instant `help-center-card-documentation-title` became visible:

| Observable | Value |
|---|---|
| card title text | `'Documentation'` (the hardcoded default — looks loaded) |
| `<Skeleton>` nodes | **16** |
| `[data-testid^="help-center-tour-link-"]` | **0** (`querySelector` → `null`) |

Gating on the first link instead: 19 links, 0 skeletons.

The AFS asserted the opposite ("asserting a card's title implicitly waits past the skeleton
via Playwright's auto-retry") and it was wrong — auto-retry can only help if the thing you
wait on is absent while loading. A fallback makes it present.

## The rule

Pick a gate that **only the loaded branch can render**. Here: the first resource link, since
links exist solely in the `!isConfigLoading && hasLinks` branch, so their presence IS the
product saying the response landed — a real condition, not a sleep.

**Preventive check, before choosing any wait on a data-driven surface:** read the component
and ask *what does this element render while the request is in flight?* If the answer is
"the same thing, from a default", it is not a gate. Grep the JSX for `|| ` next to the
value you were about to wait on.

Auto-retrying `expect()` assertions hide this (they keep polling), which is why the failure
mode is a **silent flake** in whatever runs first as a one-shot read — not a clean red.

Related: [[a_settle_can_be_fragile_and_vacuous_at_once]] · [[expect_response_wrapper_races_an_auto_select]]
