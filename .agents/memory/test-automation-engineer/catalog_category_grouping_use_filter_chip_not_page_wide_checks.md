---
name: Catalog "under Category X" needs the filter-chip idiom, not page-wide checks
description: heading-present + card-present anywhere ≠ grouping; click the category filter chip and assert single-heading + card
type: feedback
---

Fix round 1, ELITEA-2595/2596/2598 (PR #1464). Reviewer (qa-engineer) flagged
that `get_visible_category_heading_texts()` returning `CATEGORY_NAME` present
ANYWHERE + `get_skill_card(name)` existing ANYWHERE are two independent,
page-wide checks — neither is scoped to the other, so a card published under
the WRONG category would pass both unnoticed. See qa-engineer's
`catalog_category_grouping_cannot_be_scoped_no_container_testid.md` for the
finding; this entry is the resolution.

**No new container testid is needed.** `SkillCategorySection.jsx`/
`AgentCategorySection.jsx` wrap heading+grid in a testid-less `<Box>`, but the
Catalog already has a proven scoping mechanism: the category filter-rail chip
(`CategoryRail.jsx`, shared Agents/Skills tabs, `catalog-{agent,skill}-
category-filter-chip-{slug}`). Source read
(`useGroupedCategories.hooks.js` + `CatalogBody.jsx`): once ANY category chip
is selected, `groupedItems` only populates entries for categories present in
`selectedCategories`, sourced from each item's own server-declared category —
and `CatalogBody.renderSections()` only renders a section when its
`groupedItems[category]` is non-empty. So selecting exactly one chip renders
EXACTLY that category's section, unmounting every other one. This is the same
idiom the sibling agent case ELITEA-2352 already uses and reviewers already
accept (`visible_headings == [EXPECTED_CATEGORY_HEADING]`).

**Fix pattern:** click the (skill- or agent-scoped) category filter chip for
the target category, assert `get_visible_category_heading_texts() ==
[CATEGORY_NAME]` (exact single-element list, not `in`), THEN look up the card
by name — the page-wide card lookup is now real membership proof, since no
other category's cards can be rendered at that point. Added
`AgentHubPage.click_skill_category_filter_chip()` (mirrors the pre-existing
`click_category_filter_chip()`) — no new UI testid, the chip already exists
on `main` from ELITEA-2370.

**Generalize:** any future case asserting "X appears under/grouped-by
Category Y" on this Catalog surface should reach for the filter-chip idiom
first, not propose a new container testid — check for one before escalating a
`testid needed`.
