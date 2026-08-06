---
name: Agent Hub My Liked cross-tab reload
description: ELITEA-2365 — no reload icon exists (same #1212 drift); cross-tab sync needs a full page reload; chip selection resets on reload
type: reference
---

## What I confirmed live (ELITEA-2365, 2026-08-06)

- The "reload/refresh icon next to the My Liked section header" case-text
  claim is the SAME drift already tracked as
  [EliteaAI/elitea-testing-public#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212)
  (filed for ELITEA-2352's "Business Analyst" category instance). Root
  cause is identical: `AgentCategorySection.jsx`'s `headerContainer` renders
  only a `Typography` for EVERY category (it's one shared component with no
  category-specific branching) — "My Liked" gets zero special treatment.
  **Any future Agent Hub case whose text mentions a reload/refresh icon next
  to ANY category section header (Trending, My Liked, a named category) is
  this same drift — cite #1212, do not re-file.**
- There is no manual UI refresh control anywhere on `/elitea-catalog`. The
  only way another tab's like becomes visible in a tab's already-rendered
  "My Liked" section is a fresh fetch — i.e. a full page reload
  (`page.goto()` / `BasePage.reload_and_wait()`). No websocket/live push
  exists for cross-tab like sync on this surface (there IS a fully automatic
  throttled `useCatalogAutoRefresh` background poll per the `_surface.md`
  digest, but I didn't wait it out — a reload is the deterministic,
  fast-to-assert path for a test).
- **Gotcha for any test that reloads mid-flow on this page:** the category
  filter-rail chip's selected state is CLIENT-ONLY (no URL param) and does
  NOT survive `page.goto()`/reload. You must re-call
  `click_category_filter_chip(...)` after any reload before re-reading a
  filtered section — otherwise you're reading the unfiltered default view
  and will misclassify what you see.
- Cross-tab pattern in this suite: `page.context.new_page()` (same
  `BrowserContext`, same auth — no re-login needed), same idiom already used
  in `test_guardrails_live_reload.py` (`ctx.new_page()`) and
  `test_ghost_skill_after_agent_removed.py`.

Full detail: `test-specs/agent-hub/l3_agent-hub-my-liked-reload-cross-tab-sync_ELITEA-2365.md`,
`test-specs/agent-hub/_surface.md`.
