---
name: A union over a component's TERMINAL renders is a sound settle — verify the LOADING branch is anonymous
description: How to prove a "results settled" wait can't resolve early — read the component's render branches, not the page
type: feedback
aliases: [settle wait, networkidle replacement, SEARCH_RESULTS_SETTLED, render commit wait, union locator]
tags: [area/ui, type/review-pattern]
created: 2026-09-10
updated: 2026-09-10
---

## The pattern

Replacing a `wait_for_network()`/`networkidle` settle (the #1847 class) with a wait on a
**union of the component's terminal renders** — e.g.
`'[data-testid^="catalog-agent-card-"], [data-testid="catalog-no-results-title"]'` — is sound
**only if the LOADING branch carries no testid in the union**. That is a source claim, not a
reasoning claim: open the component and read its render branches.

Worked example (EliteaUI `src/[fsd]/shared/ui/category/CatalogBody.jsx`, verified 2026-09-10):
its left column renders exactly one of three things — `isLoading` → 25 anonymous MUI `<Box>`
skeletons with **no testid**, else category sections (agent cards), else `NoResultsMessage`
(`catalog-no-results-title`). Union of branches 2 and 3 ⇒ can never resolve during loading.

## Reviewing the "stale previous results" objection

The real question is not "could a stale card satisfy the union" but **when does the store get
cleared relative to the request**. In `useAgentHubData.searchAndCategorize()` both
`setLoading('global_search', true)` and `resetSearchByTag()` → `clearCache()` run
**synchronously before** `await fetchApplications(...)`, and `AgentsTab` computes
`isLoading={isFetching && Object.keys(applicationsByTag).length === 0}`. React commits the
skeleton before the request is even issued, so by the time Playwright's `expect_response`
resolves the old cards are already gone. A conservative "residual stale-grid window"
declaration in that shape is *safe but over-declared*.

## Two cheap checks that go with it

- **Tab/route exclusivity** — a union built on a SHARED testid (`catalog-no-results-title`
  lives in a `src/[fsd]/shared/` component) is only unambiguous if the sibling consumer is
  unmounted. Check the parent: `{isSkillsTab ? <SkillsTab/> : <AgentsTab/>}` ⇒ safe.
- **`Locator.is_visible(timeout=)` is documented `Deprecated: This option is ignored`** — a
  one-shot `assert loc.is_visible(timeout=X)` never retried, whatever the argument says.
  Converting it to `expect(loc, msg).to_be_visible(timeout=X)` asserts the same observable and
  is not a weakening.

Related: [[a_teardown_id_read_after_the_assertions_is_not_a_guard]]
