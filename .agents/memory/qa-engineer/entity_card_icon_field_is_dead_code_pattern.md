---
name: entity_card_icon field is a recurring dead-code pattern
description: AgentsListPage.entity_card_icon and its Skills mirror are both unreferenced — the scoped-selector constant does the real work
type: feedback
---

## Context

`Card.jsx`'s shared `entity-card-icon` container testid is wired into list
page objects (`AgentsListPage`, and now `SkillsListPage` via ELITEA-2428) as
BOTH a page-wide `LocatorDescriptor` field (`entity_card_icon`) AND a
separate UPPER_CASE scoped-selector string constant
(`ENTITY_CARD_ICON_IMG_SELECTOR` / `CARD_ICON_SELECTOR`) used inside a
per-card helper method (`get_card_icon_src()` / `card_icon_locator()`).

## The gotcha

The scoped-selector method never actually calls `self.entity_card_icon` —
it re-derives the same testid as a raw string constant and chains it off
`card.locator(...)`. The `entity_card_icon` field itself is never invoked
anywhere (`grep -rn "\.entity_card_icon\b" automation/` returns nothing
outside its own definition). This was ALREADY true in `AgentsListPage`
(pre-existing tech debt, not flagged at the time) and got copied verbatim
into `SkillsListPage` by ELITEA-2428's implementation — new dead code
shipped in a fresh diff, not just inherited debt.

## The check

When a PR adds a `LocatorDescriptor` field for a card/collection element
AND a scoped sub-selector constant for the same testid used inside a
`card.locator(...)` helper: grep for `self.<field_name>` (or
`list_page.<field_name>` from the test) across the diff+page object. If the
plain field is never called, it's dead code — flag it (fold the helper to
use the field directly, scoped by `.filter()`, and drop the duplicate raw
constant; or drop the unused field and keep only the scoped-constant
pattern, which is what actually gets exercised).

## Where this came from

Reviewer slot, ELITEA-2428 (`tests/ELITEA-2428-skills-card-view-fields`,
PR #1440, 2026-08-12). Flagged `SkillsListPage.entity_card_icon` as
unreferenced — CHANGES_REQUESTED. Root pattern pre-dates this PR
(`AgentsListPage.entity_card_icon`, same shape, untouched by this diff).
