---
name: Skill card tag overflow cap
description: A Skill/Agent card only ever renders 2 tag chips (MAX_NUMBER_TAGS_SHOWN); the rest collapse into a "+N" overflow badge.
type: feedback
---

## What

`EliteaUI/src/components/CardTagSection.jsx` hardcodes
`MAX_NUMBER_TAGS_SHOWN = 2`. A card (skill, agent, pipeline — shared
component) with more than 2 tags never renders a 3rd/4th chip via
`entity-card-tag-chip`; the overflow is a `entity-card-tag-overflow` testid
badge reading `"+N"` instead. `SkillsListPage.get_card_tags()` therefore
returns at most 2 strings even when the skill actually has 4 tags — this is
NOT a persistence bug, just the compact-card design.

## Where it bit

ELITEA-2434 ("multiple tags persist on creation and edit") — the analyst's
AFS step 5 assumed the card shows all 4 tags; live/source-side check proved
it caps at 2 + overflow. Amended the AFS in-PR (case-text drift, not a
defect) and added `SkillsListPage.get_card_tag_overflow_text()` +
`CARD_TAG_OVERFLOW` template constant (`'[data-testid="entity-card-tag-overflow"]'`)
so a 3+-tag card assertion can prove membership of the visible chips PLUS
the correct overflow count, instead of asserting full membership (which
will always fail past 2 tags).

## Rule of thumb

Any AFS/case assertion of "the card shows tag X" for a skill/agent/pipeline
with **more than 2 tags** needs the overflow-aware check, not
`get_card_tags()` alone. Same shape already documented for the Agent Hub
catalog's per-category display cap
(`agent_hub_catalog_per_category_display_cap.md`) — cards in this app
consistently truncate list-like content and surface a "+N" overflow badge
rather than rendering everything.
