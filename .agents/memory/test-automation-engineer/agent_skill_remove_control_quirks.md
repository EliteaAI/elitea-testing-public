---
name: Agent Skill card remove-control quirks (implementer)
description: is_remove_skill_button_visible() false-positives from residual real-mouse hover after popper clicks (fix: mouse.move(0,0)); attach vs detach PATCH share the same trailing skill-id in the URL — distinguish by status 201 vs 200, not URL alone (from ELITEA-1792)
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
icon button (`get_by_role("button", name="remove skill")`, scoped to the
card) → `Dialog.wait_for()` + `Dialog.click_first_button(dialog, "Remove",
"Confirm", "Delete")` → `wait_for_network()` → wait for the card to hide.
Any future "remove X from card" flow on this codebase should follow the
same shape.
