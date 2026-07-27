---
name: Agent Skill card remove-control quirks (implementer)
description: is_remove_skill_button_visible() false-positives from residual real-mouse hover after popper clicks (fix: mouse.move(0,0)); attach vs detach PATCH share the same trailing skill-id in the URL — distinguish by status 201 vs 200, not URL alone; testid-only rework (skill-card-remove-button) requires .is_visible() not .count()>0 since the button is always DOM-present, only CSS display:none pre-hover (from ELITEA-1792 + rework)
type: feedback
---

## Context

Implementing ELITEA-1792 ("Remove attached Skill from Agent") on top of the
analyst's AFS (`test-specs/skills/l3_remove-attached-skill-from-agent_ELITEA-1792.md`,
which already documented the hover-reveal + confirm-dialog behavior). Two
implementer-side (infrastructure) gotchas surfaced that the AFS couldn't have
caught from manual exploration:

## 1. Residual real-mouse hover breaks "unhovered" checks

`AgentDetailPage._skill_card(...).get_by_role("button", name="remove skill")`
is meant to be absent from the accessibility tree until the card is hovered
(confirmed live by the analyst). But a naive point-in-time check
(`count() > 0`) run right after `attach_skill()` calls came back **True**
even without an explicit `.hover()` call.

Root cause: Playwright's `click(force=True)` (used inside
`Popper.select_menuitem()` during attach) still moves the *real* mouse
cursor to the clicked element's screen position — `force` only skips
actionability checks, it doesn't skip the mouse move. Once the popper
closes, the just-rendered skill card can end up directly under that
leftover cursor position, keeping the card's CSS `:hover` state engaged
with no test code ever calling `.hover()` on it.

Fix: `page.mouse.move(0, 0)` before any check that depends on genuine
"unhovered" state. Added as the first line of
`AgentDetailPage.is_remove_skill_button_visible()`.

## 2. Attach and detach PATCH share the same URL suffix

`PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill_id}` is used
for BOTH attach (`201 Created`) and detach (`200 OK`) — same URL, same
method, only the status code differs. A network-assertion filter like
`req["url"].endswith(f"/{skill_id}")` over-matches: it picks up the skill's
own earlier attach request too. Filter on **both** URL suffix AND
`status == 200` (detach) vs `status == 201` (attach) to isolate the call
you actually mean to assert on.

## Reusable pattern

`AgentDetailPage.remove_skill(skill_name)` mirrors the pre-existing
`remove_toolkit(toolkit_name)`: hover the card → click the hover-revealed
icon button (now `SKILL_CARD_REMOVE_BUTTON_SELECTOR`, `[data-testid=
"skill-card-remove-button"]`, scoped to the card — see rework note below)
→ `Dialog.wait_for()` + `Dialog.click_first_button(dialog, "Remove",
"Confirm", "Delete")` → `wait_for_network()` → wait for the card to hide.
Any future "remove X from card" flow on this codebase should follow the
same shape.

## 3. Testid-only rework (2026-07-15): `.count() > 0` breaks on hover-revealed testids

The original PR #50 handle was `card.get_by_role("button", name="remove
skill")` — a policy violation (no testid), fixed in the rework (PR #283) by
adding `data-testid="skill-card-remove-button"` to `SkillCard.jsx`'s
"remove skill" `IconButton` and introducing
`SKILL_CARD_REMOVE_BUTTON_SELECTOR = '[data-testid="skill-card-remove-
button"]'` as a class constant, scoped via `card.locator(...)` (mirrors
`remove_toolkit()`'s inline `[data-testid="agent-toolkit-delete-button"]`
string, promoted to a proper class constant per the page-objects rule).

**Gotcha:** porting `is_remove_skill_button_visible()` naively to
`card.locator(SELECTOR).count() > 0` broke the "button not visible before
hover" assertion — it now always returned `True`. Root cause:
`SkillCard.jsx`'s `actionButton` style is `display: none` by default,
flipped to `display: flex` only by the card's CSS `:hover` rule (`&:hover
{ '#DeleteButton': { display: 'flex' } }`) — the element (and its
`data-testid`) is **always present in the DOM**, hover only toggles CSS
visibility. The old `get_by_role` handle queried the *accessibility tree*,
which excludes `display:none` elements, so it encoded the hover-reveal
semantics for free; a raw testid `.locator(...).count()` check does not
inherit that. **Fix: use `.is_visible()` instead of `.count() > 0`.**

**Generalizable rule:** when replacing a `get_by_role`/accessibility-tree
handle with a `[data-testid=]` DOM selector on any element that's
hover-revealed via CSS `display` toggle (not conditional React rendering),
switch presence checks from `.count() > 0` to `.is_visible()` — DOM
presence and CSS-visible state diverge exactly on these elements, and
`get_by_role`'s accessibility-tree semantics silently encoded the
CSS-visible check that a testid locator does not get automatically. The
"open in new tab" sibling button (`OpenInNewTabButton`, still no testid —
out of scope for this rework, not touched by this test) uses the identical
hover-toggle CSS shape and would hit the same gotcha if a future case
needs it.
