---
name: Catalog category grouping cannot be scoped — no container testid
description: RESOLVED (PR #1464 fix-round-1) — container testid now exists; card-under-category is provably scoped
type: feedback
---

**Status: RESOLVED**, 2026-08-12 (PR #1464 fix round 1). The gap this entry
originally documented is closed — do not treat "heading + card checks are
independent, page-wide" as current truth. Kept as the pattern reference for
the next area that needs the same "X is a descendant of category section Y"
proof (e.g. Agents-tab `AgentCategorySection.jsx`, still ungapped as of this
writing — see note below).

**Original finding** (reviewing ELITEA-2595/2596/2598): both AFS files
claimed the published skill "appears under its selected Category group," but
the implementation checked it as TWO independent, page-wide assertions —
`get_visible_category_heading_texts()` (heading text present ANYWHERE) and
`get_skill_card(skill_name)` (card present ANYWHERE via the page-wide
`SKILL_CARD_PREFIX`). Neither was scoped to the other, because
`SkillCategorySection.jsx`'s wrapping `<Box>` (heading + card grid) carried
no testid — only the heading `<Typography>` and each `SkillCard` root did.

**Fix (implementer, fix round 1):** added `data-testid="catalog-category-
section-{slug}"` (same slugify convention as `catalog-category-heading-
{slug}`) to `SkillCategorySection.jsx`'s outer `<Box>`
(`EliteaAI/EliteaUI@c80de351`, verified this Box is the actual parent of
both the heading and the `SkillCard` grid — real DOM descendance, not a
sibling container). `AgentHubPage.get_skill_card(skill_name, category=...)`
now scopes via `CATEGORY_SECTION.format(slug)).locator(SKILL_CARD_PREFIX)`
when `category` is given — this genuinely proves descendance, not just a
narrower page-wide guess. Confirmed by reading both the JSX and the page
object directly (not trusting the PR description).

**Pattern for reuse:** when a case needs "element X is under category-
section Y" proven with testid-only locators, add a testid to the SECTION
CONTAINER (not just the heading), scoped-name `{feature}-category-section-
{slug}`, then `page.locator(SECTION.format(slug)).locator(CHILD_PREFIX)`.
`AgentCategorySection.jsx` (Agents-tab equivalent) does NOT have this
container testid yet as of PR #1464 — same gap, unaddressed because no test
on that branch exercises an agent-card-under-category check
(`.agents/testing.md` "referenced = called on the executed path" — adding it
speculatively would be an unreferenced testid). Flag it the same way if a
future Agents-tab case needs it.
