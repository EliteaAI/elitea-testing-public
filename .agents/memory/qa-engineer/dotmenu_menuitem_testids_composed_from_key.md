---
name: DotMenu menu-item testids are composed from `key` — grep the key, not the testid
description: Menu-item data-testids never appear literally in EliteaUI source; a missing `key` means no testid at all, and a label default leaks the label into the testid
type: reference
aliases: [DotMenu testid, controls-menu menuitem, menuitem testid missing, Copy link-menuitem, usePinMenu key, useCopyLinkMenu key]
tags: [area/elitea-ui, type/locator]
created: 2026-08-24
updated: 2026-08-24
---

## The mechanism

`src/components/DotMenu.jsx` wires `testId: item.key` (line 422) and renders
`data-testid={testId ? \`${testId}-menuitem\` : undefined}` (line 58).

Three consequences that keep costing time:

1. **The composed testid never appears in EliteaUI source.** `toolkit-actions-delete-menuitem`
   is nowhere in `src/`; only the key `toolkit-actions-delete` is (`DeleteToolkitButton.jsx:72`).
   A provenance / closure-record grep must search the **key**, or it reports a false
   "not on main" — exactly the runtime-composed case `.agents/workflow.md` § Closure record warns about.
2. **A menu-item hook that builds its item with no `key` renders NO testid at all.**
   `useExportToolkitMenu()` (`ExportToolkitButton.jsx:38-40`) is the live example — the MCP/toolkit
   detail menu's `Export` item has no testid. Fix shape: add an *optional* `key` param
   (as `usePinMenu` already did for ELITEA-2049) and pass it from the call site. Additive, zero
   functional impact.
3. **A hook defaulting `key: key || label` leaks the LABEL into the testid — spaces and all.**
   `useCopyLinkMenu()` (`CopyLinkToEntityButton.jsx:44`) produces `data-testid="Copy link-menuitem"`
   on the MCP detail menu. It *works* as a selector but violates `{section}-{element}-{type}` and
   pollutes the presence-based coverage metric. The hook already accepts `key` — pass one at the
   call site (`ToolkitsControls.jsx:43`).

## Where this bit (2026-08-24, ELITEA-1946/1959)

MCP detail three-dot menu: of five items, `Fork` and `Delete` had proper testids, `Export` and
`Pin to top` had **none**, and `Copy link` had the label-leaked one. Same `ToolkitsControls.jsx`
call site for all three fixes.

Related: [[mcp_surface_notes]] · full handle detail lives in the committed digest
`test-specs/mcp/_surface.md` § MCP DETAIL three-dot ("controls") menu.
