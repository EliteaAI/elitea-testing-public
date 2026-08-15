---
name: DotMenu.jsx shared-component hardcoded testid leak
description: chat-move-to-submenu-popover hardcoded literal in shared src/components/DotMenu.jsx (16+ consumers) — violates shared-component testid rule, caught in ELITEA-2147 review
type: feedback
---

## The situation

ELITEA-2146/2147/2148 (PR #1544, `tests/2146-2147-2148-folder-list-scroll-and-states`)
added `data-testid="chat-move-to-submenu-popover"` via
`slotProps={{ paper: { 'data-testid': 'chat-move-to-submenu-popover' } }}`
directly in `EliteaUI/src/components/DotMenu.jsx`'s nested `<Menu>` (the
"Move to" submenu popover Paper) — commit `EliteaAI/EliteaUI@1787ad67`.

`DotMenu.jsx` is a genuinely shared component: `grep -rln "DotMenu"` across
`src/` turns up 16+ consumers (settings, artifacts, pipelines, sidebar,
run-history, applications, chat, …), not just the chat "Move to" flow. Today
only `ConversationItem.jsx` (chat) passes `subMenuItems`, so there's no
*runtime* collision yet — but the testid is a **chat-feature-scoped literal
baked into a shared file**, which is exactly the anti-pattern
`.agents/testing.md` § Locator policy / `role-overrides.md` § Reviewer slot
name explicitly: *"A component under `src/components/` or `src/[fsd]/shared/`
gets either a GENERIC testid or a caller-supplied `testId` prop wired at the
feature's call site... never the shared component's first consumer (the
`agent-search-clear-button`-on-shared-SearchBar mistake)."*

The irony: the SAME `DotMenu.jsx` file already demonstrates the CORRECT
pattern two lines below the violation — `testId: subMenuItem.key` wires each
submenu item's testid from the call site's own data, not a hardcoded string.
The popover-Paper testid should have followed the identical shape (a new
`submenuTestId` prop threaded from `ConversationItem.jsx` down through
`BasicMenuItem`/`DotMenu`), not a literal in the shared file.

## The reusable check

When a new testid lands via `slotProps`/prop pass-through on a component
under `src/components/` or `src/[fsd]/shared/`, grep how many OTHER files
render that component (`grep -rln "<ComponentName" src/`) before approving —
a literal string one call site needs, hardcoded into a component 10+ others
also use, is a violation regardless of whether a live collision exists today
(no other caller happens to hit that code path yet). The AFS itself may
raise a "confirm this doesn't collide" caveat (as ELITEA-2147's did) — that
caveat addresses RUNTIME collision, not the separate NAMING-CONVENTION
question of whether the literal belongs in the shared file at all. Both
need checking independently.
