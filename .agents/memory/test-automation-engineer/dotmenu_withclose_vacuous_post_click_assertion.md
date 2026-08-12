---
name: DotMenu withClose vacuous post-click assertion
description: DotMenu.jsx closes the three-dot menu on EVERY item click — a later "menu closed" assertion (e.g. Escape) after any item click is vacuous unless you re-open first.
type: feedback
---

## What happened

ELITEA-2049 (pipeline three-dot menu actions test): the case's Step 6 asked
to press `Escape` and verify the menu closes. The test clicked a menu item
in Step 4 (PIPELINE-group "Share"), then pressed `Escape` in Step 6 without
re-opening the menu. `DotMenu.jsx`'s `withClose` wrapper fires on **every**
item click, so the menu was already closed by Step 4 — Step 6's assertion
passed trivially and could never fail even if Escape-to-close regressed.
Caught at review (fresh-session reviewer), fixed in round 1.

## The pattern to watch for

Any AFS/case flow shaped like: **click a menu item → later assert the menu
is closed/absent** (whether via Escape, click-outside, or any other
close-trigger) is a vacuous-assertion trap on this component family. The
click itself already closes the menu — the later assertion is testing
nothing about the close-trigger it claims to verify.

## The fix

Before the close-trigger assertion, **re-open the menu explicitly**
(`actions_menu_button.click()` + wait for `actions_menu` visible), THEN
apply the close-trigger and assert. This makes the assertion exercise real
behavior instead of a menu that's already closed.

## Where else to check

Any other three-dot-menu test in this suite that does
`<click a menu item>` followed by `<assert menu closed via some OTHER
trigger>` without an explicit re-open in between has the same vacuous-
assertion shape. Worth a quick grep (`click.*menuitem` followed by
`Escape`/`click outside`/menu-hidden assertions) across
`tests/ui/**/test_*menu*.py` if reviewing a batch of menu-action tests.
