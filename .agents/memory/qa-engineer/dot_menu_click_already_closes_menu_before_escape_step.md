---
name: dot_menu_click_already_closes_menu_before_escape_step
description: DotMenu.jsx's withClose auto-closes the menu on ANY item click — a later "press Escape, verify menu closes" step runs against an already-closed menu and proves nothing
type: feedback
---

`DotMenu.jsx` wires every menu item's `onClick` through `withClose(item.onClick)`
(`src/components/DotMenu.jsx`) — clicking ANY item (Share, Export, Delete, …)
closes the overflow menu as a side effect, independent of the item's own
action. A test that (a) clicks an item to exercise its action, THEN (b) later
presses `Escape`/clicks-away and asserts the menu is closed, is asserting on a
menu that was already closed by step (a) — the later assertion is vacuous: it
would pass identically even if Escape/click-away handling were completely
broken, because there is nothing left open to close.

Caught reviewing ELITEA-2049 (`test_pipeline_three_dot_menu_actions.py`): Step 4
clicks `share_agent_menuitem` (closes the menu via `withClose`), Step 6 presses
`Escape` and asserts `actions_menu` is hidden — trivially true regardless of
Escape. The sibling test `test_agent_copy_version_link.py` (ELITEA-1898) got
this right and says so explicitly in its `_copy_link_via_menuitem` docstring:
"The menuitem's own click closes the actions menu … so no separate close step
is needed."

**When a case has a distinct "open menu → close menu" step AFTER an
item-click step**, either (a) drop the redundant close-step as already-covered
by the click (like ELITEA-1898 did, with a docstring note), or (b) if the case
genuinely wants Escape/click-away coverage, re-open the menu first so the
close action has something real to close. Check any new DotMenu-based
menu test for this before approving — grep the test for a menu-item click
followed by a separate "menu closed" assertion with no re-open in between.
