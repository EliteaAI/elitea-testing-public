---
name: svgr icons accept a testid at the call site
description: "@/assets/*.svg?react components spread props onto the generated <svg> — name the icon at the call site instead of reaching for the #579 raw-handle exception"
type: project
aliases: [svgr, svg?react, icon testid, startIcon testid, LogoutIcon, vite-plugin-svgr]
tags: [area/locators, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The fact

EliteaUI's icons imported as `@/assets/<name>.svg?react` are **svgr-generated
components** (`vite-plugin-svgr` 4.5.0), and svgr's default template spreads
incoming props onto the generated `<svg>` root. So a `data-testid` passed at the
**call site** lands on the rendered `<svg>`:

```jsx
startIcon={<LogoutIcon data-testid="settings-profile-logout-icon" />}
```

Verified live 2026-08-24 (ELITEA-2252): the attribute is present on the rendered
`<svg>` in the DOM. Precedents already in the repo: `catalog-skills-tab-icon`
(`EliteaCatalog.jsx`), `version-option-pin-icon` (`version.helpers.jsx`).

## Why it matters

An inline SVG icon looks like a `#579` "no testid can be placed" case — it has no
app JSX of its own, and wrapping it in a `<span>` to host a testid would trip the
zero-functional-impact check. Both readings are wrong. The compliant testid-only
shape IS reachable, costs one attribute, is feature-scoped at the call site, and
needs no edit to the shared `.svg` asset (which would be a blanket-add across
every consumer of that icon).

An AFS may still spec the scoped raw `svg` handle — ELITEA-2252's did. Amend it;
do not build the exception when the compliant shape exists.

## Sibling fact

`BaseBtn` (`src/[fsd]/shared/ui/button/BaseBtn.jsx`) spreads `...restProps` onto
`MuiButton`, so `data-testid` on any `BaseBtn` call site passes straight through
to the rendered `<button>` — no prop plumbing.

Related: [[new_testid_zero_elements_can_be_hmr_lag]]
