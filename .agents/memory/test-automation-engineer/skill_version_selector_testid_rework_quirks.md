---
name: Skill version selector testid rework quirks (implementer)
description: SkillVersionSelector.jsx's Versions <Menu> portals to document.body (not a DOM descendant of skill-card-{id}), so its new testids must carry skill_id/version_name identity directly; resolving skill_id from skill_name via a card's own data-testid attribute; is_versions_menu_open()/get_versions_menu_item_names() needed a new skill_name param since the menu testid is dynamic (from ELITEA-1789 rework)
type: feedback
---

## Context

ELITEA-1789 rework (2026-07-15): PR #47 (merged) had shipped 11 raw-handle
occurrences for the agent-skill version-selector flow (`get_by_text` +
`xpath` ancestor-walks, `.version-text` CSS-class, `get_by_role("menuitem")`)
— all in violation of the testid-only locator policy. This rework closed the
gap by adding three new testids to `SkillVersionSelector.jsx`
(`EliteaUI/src/[fsd]/features/skill/ui/`) via `add-data-testid`, and
rewriting `AgentDetailPage`'s version-selector methods around them.

## Load-bearing findings

1. **The "Versions" `<Menu>` portals to `document.body`.** Confirmed via
   `browser_evaluate`: `isMenuInsideCard: false`, `bodyChildMenuExists: true`.
   It is NOT a DOM descendant of the skill's `skill-card-{skill_id}`
   container. Both new testids (`skill-version-selector-menu-{skill_id}`,
   `skill-version-option-{version_name}`) therefore carry identity directly
   in the testid itself, and are looked up **page-wide** (`self.page.locator(...)`),
   never scoped under the card locator. A naive "menu testid inside the
   card" assumption would silently never match.

2. **skill_id isn't known to page-object callers up front** (only
   `skill_name` is, from test data) — but the version-selector testids are
   keyed by `skill_id`, not `skill_name`. Solved by parsing `skill_id` back
   out of the already-resolved card's own `data-testid="skill-card-{id}"`
   attribute (`_get_skill_id_from_card()`): `card.get_attribute("data-testid").removeprefix("skill-card-")`.
   Cheaper than adding an API round-trip just to get the id.

3. **`_skill_card()` resolution without a known skill_id**: filters
   `[data-testid^="skill-card-"]` (prefix-match, scoped to the Skills
   section content container) via `.filter(has_text=skill_name)` — same
   pattern already used elsewhere in this file for toolkit cards
   (`_get_toolkit_card()`). Replaces the old `get_by_text(exact=True)` +
   `xpath=ancestor::div[3]` walk.

4. **Enumerating ALL version-menu entries** (`get_versions_menu_item_names()`)
   can't use the per-name-keyed `skill-version-option-{version_name}` testid
   (name isn't known in advance when enumerating) — used a **prefix-match**
   selector (`[data-testid^="skill-version-option-"]`) instead. Safe because
   MUI unmounts `MenuItem`s while their `<Menu>` is closed — only the
   currently-open menu's items are ever in the DOM. Still 100% testid-based
   (no CSS/role/xpath), just a prefix instead of an exact match — a
   declared-improvisation technique, not a canon violation.

5. **`is_versions_menu_open()` / `get_versions_menu_item_names()` needed a
   new required `skill_name` param** (previously took only `timeout`) since
   the menu testid is now dynamic per-skill. Checked via grep that this
   test file (`test_skill_agent_version_selector.py`) is the ONLY caller of
   both methods before changing the signature — not a shared-file break.

6. **`get_skill_version_text()`'s public signature stayed unchanged**
   (`skill_name`, `timeout`) even though its internals now resolve
   `skill_id` and hit the new trigger testid — this method has 2 other
   merged callers (`test_export_agent_with_attached_skills.py`,
   `test_remove_attached_skill_from_agent.py`); both re-ran green after the
   swap, confirming pure internal-implementation change with no caller
   impact.

## Testid naming decision

`skill-version-option-{version_name}` was deliberately kept **distinct**
from the pre-existing `version-option-{name}` pattern (ELITEA-1738,
`SkillTabBar.jsx`'s own `buildVersionOption()` helper) — different
component, different `versions` array, no shared helper. Reusing the exact
same key across two unrelated version-selector implementations would create
a false equivalence in the coverage/testid inventory.

## Process note

The EliteaUI testid dual-target flow worked cleanly: commit straight onto
`automation/testids` (integration branch, dev server serves it live) →
cherry-pick onto a fresh worktree branch off `origin/main` → draft PR to
`main` (EliteaUI#545). Cherry-pick applied with zero conflicts since the
touched file (`SkillVersionSelector.jsx`) had no other pending changes on
either ref.
