---
name: MUI icon auto-testid is dev-build-only — never locate on it
description: "@mui/material's createSvgIcon.js sets data-testid={displayName}Icon only when process.env.NODE_ENV !== 'production' — vite build (every deployed env) strips it to undefined. A locator chained off it (e.g. VisibilityIcon/VisibilityOffIcon) is green on localhost 100% of the time and silently unlocatable everywhere else."
type: project
---

Confirmed live (ELITEA-2343, fix round 2, reviewer finding PR #1224). Read
`node_modules/@mui/material/utils/createSvgIcon.js` in `EliteaUI` directly:

```js
"data-testid": process.env.NODE_ENV !== 'production' ? `${displayName}Icon` : undefined,
```

Any case that needs to distinguish two conditionally-swapped
`@mui/icons-material` components (e.g. `VisibilityIcon` ↔
`VisibilityOffIcon` for an eye-toggle, an expand/collapse chevron pair)
must NOT chain a `[data-testid=` sub-selector off this vendor-auto
attribute — even scoped off an already-testid parent button, even as a
"declared improvisation" per `.agents/role-overrides.md`. It only survives
`npm run dev` (Vite dev server never sets `NODE_ENV=production`); it does
NOT survive `npm run build` / any deployed env / the promotion gate.

**The fix:** add a REAL, app-authored `data-testid` prop directly on the
two icon call sites via `add-data-testid` — e.g.
`<VisibilityIcon data-testid="secret-row-visibility-icon-show" />`. This is
safe and simple: `createSvgIcon`'s own JSX spreads `...props` AFTER its
internal conditional auto-testid, so an explicit caller-supplied
`data-testid` prop overrides it in BOTH dev and prod builds (confirmed by
reading the same file). Naming: `{section}-{element}-{show/hide or state}`,
same convention as any other testid. This is canon ruling #277's
"same-element conditional pair" shape when both branches are asserted by
the test — name both, don't leave one `undefined`, since both need to be
locatable.

**Full case history:** `.agents/memory/qa-engineer/mui_icons_material_auto_testid_on_icon_svg.md`
(analyst/reviewer side — this entry is the implementer-facing action item).
