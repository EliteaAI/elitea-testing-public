---
name: MUI Select aria-expanded is a leading indicator, not a backdrop oracle
description: aria-expanded flips false before the Modal backdrop unmounts — confirm menu-gone via option count, not the trigger attribute alone
type: reference
---

Verified statically 2026-09-09 against `EliteaUI/node_modules/@mui/material` **7.3.11**
(`Select/SelectInput.js:475`) while reviewing PR #2058 (issue #2052).

**The attribute is a true two-state oracle.** `aria-expanded={open ? 'true' : 'false'}`
— always present, never `undefined`. It sits on the `SelectSelect` display node
(`role="combobox"`), which is exactly where `SelectDisplayProps` is spread
(`...SelectDisplayProps` comes AFTER the aria attrs, so a caller-supplied
`data-testid` lands on the same node). So `[data-testid="X-combobox"][aria-expanded="false"]`
is a legitimate testid-keyed state filter per `.agents/testing.md` § Locator policy.

**But it is a LEADING indicator of dismissal, not proof.** `open` is React state on the
`Select`; the `Modal`/`MuiBackdrop-root` stays mounted through the Grow **exit
transition** (`transitionDuration: 'auto'`, ~200-300 ms). So there is a real window in
which the trigger reports `aria-expanded="false"` while the invisible full-viewport
backdrop still intercepts every pointer event. Playwright's own click actionability
retry absorbs it, so it is not a false-green — but if you need "the menu is GONE",
assert the option locator's count is 0 (the options unmount with the Menu), not the
trigger attribute.

**Companion fact — why page-level Escape can be swallowed on a searchable Select.**
`SingleSelect.jsx` with `withSearch` renders `SingleSelectDropdown.jsx` →
`<SimpleSearchBar onKeyDown={e => e.stopPropagation()} />`. `SimpleSearchBar.jsx`
autofocuses (100 ms `setTimeout` re-focus) and its `handleKeyDown` maps Escape to
`onSearchClear()` *before* calling the external handler — which then
`stopPropagation()`s. While focus sits there the MUI `Modal` never sees Escape and the
menu stays open forever. `Locator.press("Escape")` on a MenuItem focuses the option
first, so the keydown originates in the MenuList and does reach the Modal.
