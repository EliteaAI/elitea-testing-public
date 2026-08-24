---
name: MCP list filter survives a detail round-trip, scroll position does not
description: search term lives in the redux search slice (survives route change, dies on reload); no list scroll restoration exists
type: reference
aliases: [list state preserved, search filter preserved back navigation, EliteACustomTabPanel scroll, mcps all filter URL]
tags: [area/mcp, type/behaviour]
created: 2026-08-24
updated: 2026-08-24
---

## The fact (measured live 2026-08-24, twice, two search terms)

| List state | Survives detail → back? | Mechanism |
|---|---|---|
| Search filter (term + filtered card set) | **YES** | `src/slices/search.js`, an **in-memory redux slice**. Survives a client-side route change; dies on `page.reload()`. |
| Scroll position | **NO** | `#EliteACustomTabPanel` `scrollTop` 99 → 0 on return, still 0 at +2 s. No list scroll-restoration code anywhere in `src/` — never implemented. |

Two traps this closes:

1. **The filter is never in the URL.** `/mcps/all` carries no query string while filtered.
   Read it from `agent-search-input`'s value + the rendered card set, never `location.search`.
2. **Never `reload()` mid-flow** in a case that depends on the filter surviving.

Scroll half filed as CLARIFICATION
[#1732](https://github.com/EliteaAI/elitea-testing-public/issues/1732) — asserted in **neither**
direction by ELITEA-1961's AFS (asserting preservation reverse-masks; asserting reset-to-0
cements a possibly unintended behaviour; and the scroller has an `id`, not a `data-testid`).

**List scroll range is tiny:** 19 MCPs at 1920×1080 give `scrollHeight` 900 vs `clientHeight`
801 — ~99 px. Below ~19 cards the list does not scroll at all, so any scroll-dependent
assertion is vacuous unless it first checks `scrollHeight > clientHeight`.

Related: [[mcp_detail_breadcrumb_replaced_back_button]]
