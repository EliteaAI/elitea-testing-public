---
name: MUI icons-material auto-testid on icon svg
description: "@mui/icons-material icon <svg>s carry an auto data-testid={ExportName} — but ONLY in dev builds; vite build (prod/deployed) strips it to undefined. Verified NOT safe as a locator basis."
type: project
---

**UPDATE (ELITEA-2343 review, 2026-08-06) — the improvisation this entry
originally flagged is NOT sound; ruled CHANGES_REQUESTED.** Read
`node_modules/@mui/material/utils/createSvgIcon.js` (EliteaUI):

```js
"data-testid": process.env.NODE_ENV !== 'production' ? `${displayName}Icon` : undefined,
```

The attribute is **conditional on `NODE_ENV`, not a stable library
constant.** `npm run dev` (Vite dev server, what the local batch pipeline
and hardening gate run against) leaves `NODE_ENV=development`, so it's
present and a locator built on it passes locally 100% of the time. `npm run
build` (`vite build` — confirmed used by `EliteaAI/EliteaUI`'s own release
workflows, `tag_build_release.yml`/`build_and_release.yml`) sets
`NODE_ENV=production`, and Vite's `define` plugin has no override in this
repo's `vite.config.js` — so on every **deployed** env (dev.elitea.ai,
next.elitea.ai — a production build) the attribute is `undefined` and
`[data-testid="VisibilityIcon"]`-style selectors find **nothing**. A test
built on this locator is GREEN on localhost and RED on every deployed
promotion gate, for a reason that looks exactly like a real regression.

**Rule going forward: never use an MUI-auto `data-testid` on an icon `<svg>`
as a locator basis, in any capacity** — not even as the "scoped
sub-selector, declared improvisation" shape this entry originally sanctioned
as plausible. It is a debug-only artifact, not a stable handle. If a case
needs to distinguish two conditionally-rendered icon components, either (a)
assert the functionally-primary observable instead (e.g. the value-cell text
swap that already proves the state — this is what ELITEA-2343's own AFS
listed as its documented fallback), or (b) ask a human/`add-data-testid` to
put a REAL, app-authored `data-testid` on the two icon call sites
(`<VisibilityIcon data-testid="…visible" />` / `<VisibilityOffIcon
data-testid="…hidden" />`) — that's a one-line JSX change and turns this
from a landmine into a normal testid.

**Original (superseded) framing**, for context: analysis mistakenly read
"present with zero app-authored prop, confirmed live" as evidence of
stability, without checking whether that presence survives a production
build. "Confirmed live" against a dev server is not sufficient verification
for a selector that must also survive CI's deployed-env promotion gate —
same lesson as any dev-only convenience (React DevTools hooks, source maps,
`__reactProps$*` internals): confirm behavior across BOTH build modes before
trusting it as a handle.
