---
name: Three-dot menu "Share" is never literally "Copy link"; Pin to top has zero testid
description: useCopyLinkMenu() always overrides its label to "Share" at every call site; usePinMenu() has no key param at all — 3rd/1st occurrence respectively
type: feedback
---

## "Copy link" case text never matches the live label

`useCopyLinkMenu()` (`src/components/CopyLinkToEntityButton.jsx`) defaults its
menu-item `label` to `'Copy link'`, but **every call site observed so far
overrides it to `'Share'`** (`ApplicationControls.jsx` ×2, `SkillControls.jsx`
×2, `AgentHubModalMenu.jsx`, `SkillHubModalMenu.jsx`, `ToolkitsControls.jsx`).
A TMS case that says "click Copy link" will never find that literal text
anywhere in this app's UI — it's always a menu item labelled "Share" instead.
This is confirmed case-text drift, filed as a sibling clarification on each
new surface it's hit: #1288 (Agent Detail page), #1218 (Agent Hub modal),
#1337 (Pipeline Detail page), #1451 (Skill Detail page, ELITEA-2439 —
`share-version-menuitem`/`share-skill-menuitem`, reviewed PR #1452 confirmed
the `DotMenu.jsx` `data-testid={testId ? \`${testId}-menuitem\` : undefined}`
composition live against source — a bare-substring grep for these testids on
`main`/`automation/testids` finds NOTHING because the value is built from
`key: 'share-version'` at the call site, not a literal string; verify via
source (`SkillControls.jsx`'s `useCopyLinkMenu({ key, link })` calls +
`DotMenu.jsx`), never conclude "missing" from grep alone here). If a 5th
surface (Toolkit/Credential three-dot menu) hits it, file another sibling —
don't assume it's already covered just because the pattern repeats; each is
a genuinely different screen/object per `.agents/profile.md`'s dedup rules.

**Disambiguation trap**: when TWO "Share" items exist on the same menu
(VERSION-group vs entity-group, e.g. `share-version-menuitem` vs
`share-agent-menuitem`), they're visually identical — always assert BOTH are
present as a negative control before clicking either, or a test can silently
wire to the wrong one and still pass (wrong URL shape, but no visible
difference in the click itself).

## `usePinMenu()` — the one shared menu-item hook with no `key` at all

`src/[fsd]/widgets/pin-toggler/lib/hooks/usePinMenu.hooks.jsx` returns a
menu-item object with `label`/`icon`/`disabled`/`onClick` but **no `key`
field** — every sibling hook in the same file/pattern family (`useCopyLinkMenu`,
`useForkEntityMenu`, `useDeleteApplicationMenu`, etc.) sets one. `DotMenu.jsx`
wires `testId: item.key`, so "Pin to top" renders with **zero** `data-testid`
at all 4 of its call sites (`ApplicationControls`/`SkillControls`/
`ToolkitsControls`/`CredentialsControls`). Confirmed live via direct DOM query
on a pipeline detail page (ELITEA-2049, 2026-08-08): `data-testid: null`.

Fix shape (per ELITEA-2049's AFS): thread an optional `key` param through
`usePinMenu({ isPinned, onTogglePin, isLoading, key })`, pass an entity-scoped
key from the ONE call site your test touches (mirrors
`ForkEntityButton.jsx`'s `FORK_MENU_ITEM_KEY_BY_ENTITY` map for the same
multi-caller situation) — don't touch the other 3 untouched call sites.
