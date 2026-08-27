---
name: Agent Skill card remove-control quirks
description: Attached-skill card icon buttons are hover-revealed (absent from a11y tree until hovered); "remove skill" opens a confirm dialog, not instant removal; detach PATCH returns 200 vs attach's 201
type: feedback
---

## Context

Found during ELITEA-1792 (Remove attached Skill from Agent) analyst pass,
localhost:5173, agent detail page Skills accordion (`ApplicationSkills.jsx` /
`SkillCard.jsx`, same components documented for ELITEA-1735/1789).

## Findings

1. **Icon buttons are hover-revealed, not always in the DOM/a11y-tree.** Each
   attached-skill card's `"open in new tab"` and `"remove skill"` icon buttons
   (both accessible-name-only, no `data-testid`) are **absent from a Playwright
   accessibility snapshot of an unhovered card** — confirmed by diffing a
   before/after snapshot of the same card, hover in between. An implementer
   using a bare `get_by_role('button', { name: 'remove skill' })` without first
   hovering the specific card risks a "not found" flake, depending on whether
   the automation framework's click implicitly hovers first. **Always hover
   the target card (or its wrapper) before locating the icon buttons.**
   Scope the locator to the specific card (e.g. via an ancestor `has_text`
   filter on the skill's name), same pattern as the existing `.version-text`
   scoping documented for ELITEA-1789.

2. **"remove skill" opens a confirmation dialog — removal is not instant.**
   Clicking the icon button opens a **"Remove skill?" dialog**: heading
   "Remove skill?", body "Are you sure to remove the {skill-name} skill from
   agent?", buttons "Cancel" / "Remove". This is the *same* confirmation-dialog
   component/pattern as the existing `remove_toolkit()` "Remove toolkit?" flow
   (`automation/pages/agent_detail_page.py:465`,
   `Dialog.click_first_button(dialog, "Remove", "Confirm", "Delete")`) — a
   `remove_skill()` page-object method should follow the identical
   hover-card → click-icon → confirm-dialog pattern, not a single click.

3. **Detach PATCH returns `200 OK`, attach returns `201 Created`.** Both hit
   the same endpoint (`PATCH
   /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}`), auto-saved with
   no agent-level Save-button click needed (same pattern as attach,
   ELITEA-1789/1735) — the agent's `Save` button stays `disabled` throughout.
   The differing status code is a clean signal for traffic-based wait
   strategies that need to distinguish an attach request from a detach
   request on the same URL pattern.

## Where used

`test-specs/skills/l3_remove-attached-skill-from-agent_ELITEA-1792.md` (Test
Step 4/5, Handles Reference, Coverage Map Axis 2).
