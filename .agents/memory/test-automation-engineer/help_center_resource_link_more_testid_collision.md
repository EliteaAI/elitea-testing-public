---
name: help-center resource-card "More..." testid collision (fixed)
description: EliteaUI's resources/index.jsx slugifies each backend-CMS link.title into help-center-tour-link-{slug} with NO card-awareness — any two cards sharing an identical generic link title (e.g. "More...") produce the identical data-testid. Fixed on automation/testids by prefixing generic titles with the card's category; watch for the same class of collision if a new resource card or link title is ever added.
type: reference
---

## What happened (ELITEA-2223/ELITEA-2224, 2026-08-14)

`src/[fsd]/pages/resources/index.jsx` renders every resource card's links via
one shared `links.map((link, idx) => ...)`, computing
`data-testid={`help-center-tour-link-${slugify(link.title)}`}` per link. The
Video Library card's "More..." link and the Tutorials card's "More..." link
both slugify to `more` → identical
`data-testid="help-center-tour-link-more"` on two different `<a>` elements,
page-wide. `document.querySelectorAll('[data-testid^="help-center-tour-link-"]')`
confirmed exactly 2 hits for that one testid, 1 each for every other link.

## The fix (on `automation/testids`, `EliteaAI/EliteaUI@81d7a377`)

Added a `testidCategory` field to each `RESOURCE_CARD_CONFIGS` entry
(`documentation` / `release-notes` / `video-library` / `tutorials` /
`interactive-tours`) and prefixed ONLY the generic `more` slug with it:
`help-center-tour-link-video-library-more` /
`help-center-tour-link-tutorials-more`. Every other link testid (unique
titles) is untouched — including the already-merged
`help-center-tour-link-sidebar-interactive-tour` /
`-chat-interactive-tour` from ELITEA-2227, so no regression to that suite.

## Why this matters for the NEXT case touching this page

If a future Help Center case (or a backend CMS content change) introduces
another link whose title happens to collide across cards — not just
"More..." — the SAME collision class will recur, because the fix is
special-cased to the literal string "more", not a general
collision-detection pass. Before trusting any `help-center-tour-link-{slug}`
locator, sanity-check for duplicates the same way this session did:

```js
const els = [...document.querySelectorAll('[data-testid^="help-center-tour-link-"]')];
const testids = els.map(el => el.getAttribute('data-testid'));
testids.filter((t, i) => testids.indexOf(t) !== i);  // should be []
```

## Full live link inventory (2026-08-14, all confirmed against real `href`s)

See `test-specs/help-center/_surface.md` § "Resolved/added during
ELITEA-2220/2221/2222/2223/2224 implementation" for the complete table — it's
the single source, not duplicated here.
