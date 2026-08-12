---
name: Catalog category grouping cannot be scoped — no container testid
description: "Appears under Category" can't be proven with current testids; heading + card checks are independent, page-wide
type: feedback
---

Found reviewing ELITEA-2595/2596/2598 (PR #1464, `test_skill_publish_wizard_happy_path.py`
/ `test_skill_publish_warn_status_allows_publishing.py`). Both AFS files claim the
published skill "appears under its selected Category group" — matching the TMS case's
own wording — and both AFS Coverage Maps cite this as `asserted`. In the implementation
it is checked as TWO independent, page-wide assertions:

1. `AgentHubPage.get_visible_category_heading_texts()` — `CATEGORY_NAME` is present
   ANYWHERE among the rendered `catalog-category-heading-*` elements.
2. `AgentHubPage.get_skill_card(skill_name)` — a card with that name exists ANYWHERE
   via the page-wide `SKILL_CARD_PREFIX` (`[data-testid^="catalog-skill-card-"]`).

Neither is scoped to the other. Source read of both `SkillCategorySection.jsx` and
`AgentCategorySection.jsx` (EliteaUI) confirms why: each wraps its heading + card grid
in a plain `<Box>` with **no testid on the container** — only the heading `<Typography>`
and each `SkillCard`/`AgentCard` root carry testids. There is currently no testid-only
way to assert "this specific card is a child of that specific category section" — a
skill/agent published under the WRONG category would pass both checks unnoticed, since
the target category section is populated by other items regardless, and the card
renders somewhere on the page regardless of which section it's actually under.

**If a future case needs the real "under Category X" relationship asserted**: this is a
`testid needed` gap on the section container (e.g. `catalog-category-section-{slug}`
wrapping both heading and grid) — flag it via `add-data-testid`, don't try to fake
scoping with CSS ancestor/sibling traversal (violates testid-only policy). Until that
testid exists, "heading text present" + "card present" is the best available proxy and
should be flagged as such in the AFS rather than claimed as the full case behavior.
