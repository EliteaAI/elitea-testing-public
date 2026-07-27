---
name: Fork wizard and ProjectSelect testid passthrough
description: ELITEA-1893 — Fork wizard testid gaps (menuitem/confirm-button/project-select), the ProjectSelect/SingleSelect data-testid passthrough chain, and the fork_entity_card_toggle.count()==1 trick for proving "no Nested entities section"
type: feedback
---

## Fork wizard shares ImportWizardModal with the Agents-list Import flow

`agent-import-preview-dialog` / `agent-import-complete-dialog` (same
container, testid swaps testid in place once the fork/import succeeds) are
used by BOTH flows. Fork is triggered from `AgentDetailPage`'s actions
overflow menu, Import from `AgentsListPage`'s toolbar — different page
objects, same live testids. Re-declaring the identical testid string as a
class field on both page objects is correct here, NOT method duplication:
it's the same shared component addressed from two different page contexts.
`AgentDetailPage` now has its own `fork_wizard_dialog`/`fork_complete_dialog`/
`fork_main_entity_name`/etc. fields alongside `AgentsListPage`'s pre-existing
`import_preview_dialog`/`import_complete_dialog`/etc.

## `fork_entity_card_toggle.count() == 1` proves "no Nested entities" without a dedicated testid

Every rendered entity-preview card (Main entity + each nested dependency, if
any) carries the SAME `agent-import-preview-card-toggle` testid — there's no
separate "Nested entities section absent" testid, and text-based absence
checks (`get_by_text("Nested entities").count() == 0`) would violate the
testid-only locator policy. Counting the shared toggle testid is a clean,
policy-compliant proxy: exactly 1 toggle = Main-entity-only card rendered,
>1 = nested dependencies present. Reusable for any future case that needs to
assert "this wizard shows only the main entity, no nested deps" without a
text/role locator.

## `ProjectSelect`/`SingleSelect` already has `data-testid` passthrough — check the call site, not the leaf component, before adding a prop

`SingleSelect.jsx` (`src/[fsd]/shared/ui/select/SingleSelect.jsx`) already
destructures `'data-testid': dataTestId` from its props and forwards it to
the underlying MUI `<Select data-testid={dataTestId} ...>`. `ProjectSelect.jsx`
spreads any unlisted prop (`...last`) straight onto its `<Select.SingleSelect>`
child. So a testid gap on a `<ProjectSelect>` usage is NEVER a
`ProjectSelect.jsx`/`SingleSelect.jsx` change — it's always a missing
`data-testid="..."` prop at the SPECIFIC call site rendering it (e.g.
`IWModalContent.jsx`'s `<ProjectSelect>`, used by both the Import and Fork
wizards, differentiated by the in-scope `isForking` flag —
`data-testid={isForking ? 'agent-fork-project-select' :
'agent-import-project-select'}`). Before touching a shared Select/leaf
component for a testid gap, grep the component for a `data-testid`
destructure/spread — if found, the fix is one line at the call site, not a
component change.

## Fork wizard testid additions (ELITEA-1893, EliteaUI automation/testids commit 61328689)

1. **Fork menuitem** — `agent-actions-fork-menuitem`. One-line fix:
   `ForkEntityButton.jsx`'s `useForkEntityMenu()` menuItem object never set
   `key`; added `key: 'agent-actions-fork'`, exact mirror of the sibling
   Export menuitem's `key: 'agent-actions-export'` (`ExportApplicationButton.jsx`).
2. **Fork confirm button** — `agent-fork-confirm-button`. `data-testid` prop
   added to `IWModalForkButton.jsx`'s bare `Button.BaseBtn`, mirroring the
   sibling Import button's existing `agent-import-confirm-button`
   (`IWModalImportButton.jsx`).
3. **Fork wizard Project selector** — `agent-fork-project-select` (see
   passthrough note above) — `IWModalContent.jsx` call site, not
   `ProjectSelect.jsx`/`SingleSelect.jsx`.

This is the same recurring shape already logged in
`pin_toggler_widget_testid_gaps.md`/`entity_icon_...`/mcp-node sessions: a
shared component family gets testids on SOME call sites/siblings but not
others — diff against the nearest sibling (Export vs Fork, Import-button vs
Fork-button) rather than assuming parity, and check for prop-passthrough
before assuming a leaf component itself is missing the capability.
