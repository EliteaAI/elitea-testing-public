---
name: DotMenu shared testid leak fixed via caller prop
description: How ELITEA-2147's DotMenu.jsx hardcoded-testid finding was resolved — submenuTestId prop pattern, reusable for other shared-component testid leaks.
type: feedback
---

## What happened

ELITEA-2147 (PR #1544) implementer pass added `data-testid="chat-move-to-
submenu-popover"` as a **literal string** inside `DotMenu.jsx`'s nested
submenu `<Menu>` (`slotProps={{ paper: { 'data-testid': '...' } }}`).
`DotMenu.jsx` is shared across 16+ consumers (`grep -rln "DotMenu" src/`);
only `ConversationItem.jsx` (chat) passes `subMenuItems` today, so there was
no *runtime* collision, but the literal still violated the shared-component
testid rule (`.agents/testing.md` § Locator policy: a shared component gets
either a generic testid or a caller-supplied prop, never a feature-scoped
literal baked into the shared file — the `agent-search-clear-button`-on-
shared-SearchBar precedent). Caught at review, unaddressed in round 1
(missed entirely — no attempt visible in the diff), fixed in round 2.

## The fix pattern (reusable)

`DotMenu.jsx` already had the CORRECT shape two lines away for per-item
testids: `testId: subMenuItem.key` — wired from the call site's own data,
not hardcoded. The popover-Paper testid needed the identical shape:

1. Add a new prop (`submenuTestId`) to `BasicMenuItem`'s destructured props.
2. Use it conditionally in the nested `<Menu>`'s `slotProps`:
   `slotProps={submenuTestId ? { paper: { 'data-testid': submenuTestId } } : undefined}`
3. Thread it through `DotMenu`'s `commonProps` builders (there were TWO —
   one for the single-column render path, one for the multi-column path;
   both needed `submenuTestId: item.submenuTestId` added, easy to miss the
   second one).
4. At the call site (`ConversationItem.jsx`), add `submenuTestId:
   'chat-move-to-submenu-popover'` to the menu-item object literal that
   already carries `subMenuItems: moveToFoldersMenuItems`.

Net effect: zero new DOM nodes, zero new hooks — purely additive prop
threading. Passed all three zero-functional-impact greps
(`add-data-testid` § Step 5.5) cleanly. Testid VALUE and every test-repo
locator/assertion stayed unchanged — only the JSX origin of the string
moved from the shared file to the feature call site.

## Where to check for the same anti-pattern

Any `slotProps`/prop-pass-through testid landing directly in
`src/components/` or `src/[fsd]/shared/` as a literal string is this same
shape. Before approving (or before writing one), `grep -rln "<ComponentName"
src/` to see how many consumers exist — if >1, the testid must be a prop,
not a literal, regardless of whether another consumer currently exercises
that code path.
