---
name: visibility:hidden blocks real hit-testing — case step describing an "attempt" on such a control is unreachable
description: CSS visibility:hidden (unlike opacity:0/pointer-events untouched) removes an element from browser hit-testing — a real mouse click can never land on it, even though it's still in the DOM
type: feedback
---

Found during ELITEA-2192 analysis (chat-remaining wave-11): the case's step 4 asked to "attempt to
trigger a delete action on the owner row" and expected a red error toast. Live investigation
(`UserMenu.jsx`'s `userItemStyles`) showed the delete `IconButton` for the owner's own row is ALWAYS
present in the DOM but has `visibility: hidden` as its base state, and the `&:hover` rule only flips it
to `visible` for a *selectable* row (never true for the owner's own row, `isSelectable = selectable &&
user.entity_meta?.id !== currentUserId`).

**Key fact, worth remembering for any future "attempt an action on a hidden/disabled-looking control"
case step:** `visibility: hidden` removes an element from the browser's own hit-testing — a genuine
mouse click at that screen position lands on whatever is visually *beneath* it, not the hidden element.
This is different from `opacity: 0` (still hit-testable) or a merely visually-obscured-but-present
element. So a case step describing "a user attempts to click X" where X is CSS-`visibility:hidden` for
that state is **not reachable by any real user interaction** — no force-click, no keyboard path, no
alternate route exists, because the browser itself refuses to dispatch the click there.

**Classification consequence**: this is a reverse-masking case-text-drift CLARIFICATION, not a defect —
the product is often MORE protective than the case describes (the affordance never renders as
clickable at all, vs. the case's implied "clickable but guarded with an error"). Don't force a synthetic
click via `page.evaluate()`/`.click({force:true})` to manufacture the observable the case asks for —
that would be a fidelity-policy substitution (the click itself is not something a real user can ever
produce). Route it as documented in `.agents/testing.md` § Fidelity policy / reverse-masking guard:
assert the ACTUAL (stronger) guarantee the covering test already proves, and file the mechanism
mismatch as a clarification.

Quick verify recipe for a similar future case: `getComputedStyle(el).visibility` on the target element
(not hover-dependent, works on the base/rest state) plus a read of the CSS rule that governs the
`:hover` transition, to confirm whether ANY interaction path exists before concluding "unreachable".
