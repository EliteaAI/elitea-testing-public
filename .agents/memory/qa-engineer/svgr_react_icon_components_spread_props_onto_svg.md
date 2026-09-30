---
name: SVGR react icon components spread props onto the svg
description: '@/assets/x.svg?react icons pass unconsumed props straight to the rendered <svg>, so an icon testid can go at the call site instead of adding a prop to a shared wrapper.'
type: reference
aliases: [vite-plugin-svgr, icon testid, GradientIconWrapper, svg data-testid]
tags: [area/testids, area/elitea-ui]
created: 2026-09-30
updated: 2026-09-30
---

## The fact

EliteaUI icons imported as `@/assets/help-center.svg?react` (vite-plugin-svgr) spread
**unknown props onto the rendered `<svg>` element**.

Proof observed live (ELITEA-2219, 2026-09-30): `ResourcesButton.jsx` renders
`<HelpCenterIcon sx={styles.icon} />`, and the DOM shows

```html
<svg width="14" height="14" viewBox="0 0 14 14" fill="none" sx="[object Object]">
```

`sx` is not a valid SVG attribute and the SVGR component never consumes it — yet it
reached the DOM verbatim. `data-testid` lands the same way, and more cleanly since it is
a real `data-*` attribute.

## Why it matters for the testid-only policy

It lets an icon testid be added **at the feature's call site** without touching a shared
component. Concretely: `GradientIconWrapper` (`src/[fsd]/shared/ui/icon/`) destructures
only `{children, size, sx}` with **no rest-spread**, so putting a testid on the wrapper
would require adding a `testId` prop to a shared component. Passing it to the icon
instead —
`<config.Icon data-testid={`help-center-card-${config.testidCategory}-icon`} … />` —
keeps the change inside the page that owns the naming, and is a direct attribute on an
existing node (zero functional impact, passes `add-data-testid` § Step 5.5).

Check the target component's destructure before assuming a prop is needed: a missing
rest-spread is what forces the prop, and SVGR components are the common exception.
