---
name: Catalog tab-switch content signal and filter-chip-count race
description: how ELITEA-2370 verified Agents<->Skills content switch without a main-element testid, and a chip-count read race caught mid-implementation
type: feedback
---

## The "main content switched" observable, without a wrapper testid

`EliteaCatalog.jsx` renders `{isSkillsTab ? <SkillsTab .../> : <AgentsTab .../>}`
directly inside `<Box sx={styles.body}>` — there is no `data-testid` on that
`Box`, and under this project's testid-only locator policy, reading the raw
`<main>` element's text content (what two prior, now-stripped ELITEA-2370
attempts specced) is out of contract.

**Don't add a wrapper testid just to prove "content switched."** Both
`AgentsTab` and `SkillsTab` already thread a `chipTestIdPrefix` prop into the
shared `CategoryRail.jsx` right-panel rail:
`catalog-agent-category-filter-chip-*` vs `catalog-skill-category-filter-chip-*`.
Confirmed live: this prefix cleanly swaps 11↔0 / 0↔11 on every tab click,
completely independent of whether the project currently has any agents/skills
loaded (the rail is driven by static per-project category config, not the
live result set) — a more robust signal than the row-count of agent/skill
cards themselves would be. Combine with `wait_for_any_agent_card()` /
`wait_for_agent_card_count(0)` (already existed) for a second, independent
confirmation that the OTHER tab's component tree actually unmounted.

This generalizes: for any tabbed/multi-view surface where the AFS reaches for
a generic content-area handle (`main`, a wrapping `div`), check whether the
two views already emit DIFFERENT testid-prefixed elements (a feature-scoped
filter rail, a feature-scoped empty state, feature-scoped card testids) before
adding a new wrapper testid — the swap between two already-existing prefixes
is often a stronger, testid-compliant proxy for "which view is mounted" than
inventing one more identity to track.

## The chip-count race

A **one-shot** `.count()` read on `get_visible_category_filter_chips()` /
`get_visible_skill_category_filter_chips()` taken immediately after
`wait_for_agent_card_count(0)` (or `wait_for_any_agent_card()` on initial
load) intermittently under-read the chip set — once observed 3 instead of 11
right after a tab click. The card-count signal and the filter-rail's own
categories fetch are two SEPARATE async completions from the same tab-switch;
they don't land in the same tick.

**Fix:** use Playwright's auto-retrying `expect(locator).to_have_count(n,
timeout=...)` for chip-count assertions instead of `assert
locator.count() == n`. No `wait_for_timeout`/sleep needed — the web-first
assertion just polls until the count matches or the timeout elapses.
