---
name: Conversation-menu and DeleteEntityModal testid wiring (ELITEA-2114, ELITEA-2132)
description: Where the 7 conversation-context-menu-item testids and the BaseModal/DeleteEntityModal title+cancel testids actually live, plus the project-context menu-item-count trap and the DotMenu key->testid mechanism generalizing to OTHER DotMenu callers (e.g. FolderItem.jsx) — needed by any future case touching ConversationItem.jsx/FolderItem.jsx's DotMenu or the shared delete-confirmation dialog.
type: feedback
---

## Conversation context-menu items (ConversationItem.jsx)

`DotMenu`'s `BasicMenuItem` already renders `data-testid={testId}-menuitem`
whenever the item object carries a `key` (`testId: item.key` wired in
`DotMenu.jsx`'s `commonProps`) — this plumbing predates ELITEA-2114 and needed
ZERO changes to `DotMenu.jsx`/`BasicMenuItem`. The only gap was
`ConversationItem.jsx`'s `menuItems` `useMemo` array never setting `key` on
its 7 objects. Fix: add `key: 'chat-conversation-menu-<slug>'` to each
(`rename`, `move-to`, `playback`, `make-public`, `share`, `pin`, `delete`) —
`pin` covers both "Pin on top"/"Unpin" labels with ONE stable key (state is
the label text, not a second testid). Don't add `key` to the SEPARATE
`isPlayback` branch's items unless a case actually touches playback mode —
scope discipline (testing.md § Locator policy) applies per-branch, not
per-array.

**Menu items don't need per-conversation scoping** — unlike the 3-dot
trigger button (`conversation-menu-menu-button`, which IS duplicated because
every `ConversationItem` renders its own `IconButton` with the same static
`id="conversation-menu"`), the menu ITEMS only exist in the DOM while their
own conversation's MUI `Menu` is open, and MUI `Menu`/`Popover` unmounts
children when closed (no `keepMounted` passed here) — confirmed live: with 2
conversations on screen, only ONE conversation's menu-item testids were ever
present in the DOM at a time, regardless of which was open.

**Project-context trap:** menu item COUNT is not a fixed 7 — `menuItems`
filters out "Make public" and "Share" via `display: 'none'` whenever
`projectId == personal_project_id` (or `PUBLIC_PROJECT_ID`). A conversation
created via the plain `conversation_api` fixture (this project's
`.env.test` default, `ELITEA_PROJECT_ID=399`) comes back `is_private: true`
— i.e. IS the account's personal project — so only 5 items render (no Make
public/Share). Don't trust a case's or a prior AFS's "N items, live-verified"
claim without re-checking live against the SAME project context the
automated test actually creates data in — analysis-time and
automation-time can silently differ. (ELITEA-2114 CLARIFICATION-2.)

## Delete-confirmation dialog (DeleteEntityModal.jsx via BaseModal.jsx)

- **Title testid**: `BaseModal.jsx` had NO title testid mechanism before
  ELITEA-2114 despite `IWModalEntityCardWrapper.jsx` (a DIFFERENT shared
  component, import-wizard) already establishing the `titleTestId`/
  `subtitleTestId` prop-name convention (`data-testid={titleTestId}` on the
  title node). Extended that exact convention to `BaseModal.jsx`: new
  `titleTestId` prop, applied to the `Box sx={styles.titleWrapper}` wrapping
  the title (works whether `title` is a string or a custom node). Call site
  (`DeleteEntityModal.jsx`) passes `titleTestId="delete-confirm-title"`.
  Deliberately NOT on `id="alert-dialog-title"`/`#alert-dialog-title` — that
  id doesn't exist in the DOM at all (BUG #694, the real title `<h2>` has
  `id="variables-dialog-title"`, a stale leftover) — the new testid
  side-steps the bug without touching it.
- **Cancel button testid**: the AFS diagnosed this as "`BaseModal.jsx`'s
  `renderActions()` never receives a `cancelButtonTestId` from the call
  site" — true but incomplete. `DeleteEntityModal.jsx` builds its OWN
  `actionsNode` (Cancel + `OneClickButton` Delete) and passes it via
  `actions={actions ?? actionsNode}` — since `BaseModal.renderActions()`
  early-returns `actions` when set (`if (actions) return actions;`), the
  `cancelButtonTestId` prop plumbing is bypassed ENTIRELY for this modal.
  The actual fix is a `data-testid="delete-confirm-cancel-button"` added
  directly on the Cancel `Button.BaseBtn` inside `DeleteEntityModal.jsx`'s
  `actionsNode` — not a prop threaded through `BaseModal`. If another
  `BaseModal` consumer needs `cancelButtonTestId` to actually work, check
  first whether IT also passes a custom `actions=` prop (same bypass would
  apply).

## Live-verify before writing assertions

Before writing the AFS-recommended testids into a page object AND a test's
assertions, drive the change live (playwright-cli against the local dev
server, HMR picks up JSX edits instantly) BEFORE committing. Caught the
menu-item-count drift above at zero cost this way, rather than discovering
it as a test failure during Phase 4 Execute.

## The `item.key` -> testid mechanism generalizes to every DotMenu caller (ELITEA-2132)

The ELITEA-2114 finding above ("`DotMenu.jsx` needed zero changes — the gap
was ConversationItem.jsx's `menuItems` never setting `key`") is not a
ConversationItem-specific fact — it's a property of the shared `DotMenu`/
`BasicMenuItem` component itself (`testId: item.key` -> `data-testid=
"${item.key}-menuitem"`), so it applies to EVERY caller. `FolderAccordion.jsx`
wires `<DotMenu id="conversation-menu">{menuItems}</DotMenu>` with
`menuItems` supplied by `FolderItem.jsx` — same shared component, same
mechanism, but `FolderItem.jsx`'s own `menuItems` array (Rename/Pin on top/
Delete) had no `key` field either. One-line fix, identical shape: add
`key: 'chat-folder-menu-delete'` to the Delete item only (scope discipline —
this case's test only clicks Delete, for cleanup). **When you meet a new
`<DotMenu>` consumer with un-testid'd menu items, check for a missing `key`
field before assuming a testid needs inventing from scratch — the rendering
plumbing is almost certainly already there.**

## Watch for "out of budget" claims contradicted by the AFS's own later sections

The ELITEA-2132 analyst pass characterized the folder Delete menu item as
"out of this case's testid budget since the case doesn't require selecting a
specific menu item" — but that same AFS's own § Cleanup requires clicking
Delete to tear down every run's created folder. An element a test's
cleanup touches IS in scope under the testid-only policy (`.agents/
role-overrides.md`: "missing testid alone ⇒ add it," scope = elements the
test actually touches — cleanup counts). When absorbing an AFS, cross-check
"out of budget" / "not needed" claims in the Concrete Handles table against
§ Cleanup and § Automation Hints, not just the numbered case steps — a
Phase-1 read that only walks the Coverage Map can miss this class of
self-contradiction.
