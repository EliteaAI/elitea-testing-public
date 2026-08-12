---
name: ELITEA-1789 version-selector rework testid map
description: Testid inventory for the agent-skills version-selector flow (SkillVersionSelector.jsx) — 2 confirmed on-automation/testids-only (draft #540), 3 needs-adding, plus the Menu-portals-to-body gotcha
type: project
---

## Context
REWORK pass on ELITEA-1789 (issue #31), 2026-07-15, framework-alignment audit.
Original AFS behind merged PR #47 shipped 11 raw-handle occurrences (`get_by_text`
+ `xpath=ancestor::div[N]` + `.version-text` CSS class + `get_by_role("menuitem")`)
for the attached-skill card's version selector — all replaced with testid rows in
this rework. AFS: `test-specs/skills/l3_attach-skill-to-agent-with-version-selector_ELITEA-1789.md`.

## Component
`EliteaUI/src/[fsd]/features/skill/ui/SkillVersionSelector.jsx` — rendered inside
`SkillCard.jsx` (which itself carries `data-testid="skill-card-${skill.skill_id}"`,
added by the ELITEA-1735 rework, same draft EliteaUI#540, still not on `main`).

## Testid inventory (verified via fresh `git fetch origin` + `git grep` both refs)

| Element | testid | provenance |
|---|---|---|
| Attached-skill card scope | `skill-card-${skill_id}` | on-automation/testids only (draft EliteaUI#540) |
| Agent add-skill button | `agent-add-skill-button` | on-automation/testids only (draft EliteaUI#540) — bonus finding, added since original AFS |
| Version-selector trigger (`.version-text` + chevron `Box`, line ~70) | none — `testid needed: skill-version-selector-trigger-{skill_id}` | needs-adding |
| "Versions" menu container (`Box` header, line ~98) | none — `testid needed: skill-version-selector-menu-{skill_id}` | needs-adding |
| Per-version `MenuItem` (line ~119) | none — `testid needed: skill-version-option-{version_name}` | needs-adding |

## Load-bearing gotcha: the Menu portals to `document.body`
Confirmed live via `browser_evaluate`: the "Versions" `<Menu>` is **not** a DOM
descendant of `skill-card-{id}` (`isMenuInsideCard: false`, `bodyChildMenuExists:
true`) — MUI portals it out. This means the menu/menu-item testids MUST carry
`skill_id`/`version_name` identity themselves; you cannot scope by DOM ancestry
under the card the way you can for elements that stay inside it.

## Naming collision avoided
Do NOT reuse the `version-option-{name}` key from the ELITEA-1738 rework
(`skill_detail_page.py`, EliteaUI commit `eb5361f`) — that's a different
component's own `buildVersionOption()` helper (the skill-detail-page's VERSION
combobox), unrelated to `SkillVersionSelector.jsx` which maps its own `versions`
array directly. Chose `skill-version-option-{version_name}` as a fresh, distinct
key for this component.

## Issue #46 split
Originally bundled "no testid" + "not keyboard-accessible". The testid portion
closes once the 3 `needs-adding` rows above are implemented. The keyboard/ARIA
portion (`tabIndex=-1`, `role=null`, `aria-label=null` on the trigger) is a
separate, narrower a11y concern, reconfirmed live this rework — stays open.
A real click (`page.locator('.version-text').click()`) works fine; only an
accessibility-snapshot/`ref=`-resolved click silently no-ops.
