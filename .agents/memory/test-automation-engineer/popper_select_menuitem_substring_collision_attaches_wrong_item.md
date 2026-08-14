---
name: Popper select_menuitem_by_testid substring collision attaches the wrong item
description: Test-data names where one is a substring of another cause Popper.select_menuitem_by_testid (.filter(has_text=...).first) to attach the wrong entity
type: feedback
---

`Popper.select_menuitem_by_testid()` (`components/mui.py`) resolves a menu
item via `popper.locator('[data-testid="toolkit-menu-item"]').filter(has_text=text).first`
— `has_text` is a SUBSTRING match, not exact. Used by
`AgentDetailPage.attach_skill()` (and the equivalent toolkit/participant
attach flows) to select from the "+ Skill"/"+ Toolkit" popper by name.

**Gotcha:** if two seeded entities' names have one as a literal substring of
the other (e.g. `valid-skill-2601-<x>` is a substring of
`invalid-skill-2601-<x>`), attaching the SHORTER name matches BOTH menu
items and `.first` silently picks whichever the popper lists first (not
necessarily the one you asked for) — the wrong entity gets attached, with
no error, no exception, just a downstream assertion failure several steps
later that looks unrelated (hit live on ELITEA-2601: attaching
`valid-skill-...` actually attached `invalid-skill-...`, since the popper
lists items alphabetically and "i" < "v").

**Fix pattern:** when a test seeds multiple entities that will be attached
via a search/select popper by display name, pick names with NO substring
containment between any pair — don't reuse a shared root like
`valid-skill-<x>` / `invalid-skill-<x>` (prefix collision) or `skill-<x>` /
`skill-2-<x>`. Verify before writing: no name in the set is `in` any other
name in the set. This is a distinct failure mode from
`llm_selector_misattribution_check_substring_collision.md` (that one is a
false NEGATIVE-check failure on response text; this one is a wrong-item
SELECTION during attach, silent until a later assertion).
