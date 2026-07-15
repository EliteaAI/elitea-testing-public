---
name: MCP attach/remove quirks (implementer)
description: McpAuthModal keepMounted hidden-dialog gotcha breaking Dialog.wait_for() for MCP cards specifically, plus UnifiedDropdown shared-testid confirmation and Agent/Pipeline add-button testid gap (from ELITEA-1950)
type: feedback
---

## Context

ELITEA-1950 — attaching a Remote MCP to an agent via the Tools section's
"+ MCP" button, mirroring the existing Toolkit attach/remove flow
(`AgentDetailPage.add_toolkit()` / `remove_toolkit()`).

## McpAuthModal `keepMounted` breaks `Dialog.wait_for()` for MCP cards

`ToolCard.jsx` renders `McpLogInButton` for any unauthenticated MCP card,
which mounts `McpAuthModal.jsx` — a MUI `<Dialog open={open} keepMounted>`.
Because of `keepMounted`, this dialog stays in the DOM **hidden** even when
closed (never unmounts). When a test later opens the "Remove MCP?"
confirmation dialog (via the toolkit card's delete icon), the DOM now has
TWO `[role="dialog"]` elements: the permanently-hidden `McpAuthModal` and
the real, visible confirmation dialog. `components.mui.Dialog.wait_for()`
does `page.locator('[role="dialog"]').first.wait_for(state="visible")` —
`.first` binds to whichever matches first in DOM/portal order, which was
the hidden `McpAuthModal` in this run, and the call timed out even though
the real dialog was fully visible and interactive on screen (confirmed via
a failure screenshot: "Remove MCP?" rendered correctly with a clickable
"Remove" button).

**Fix**: added `Dialog.wait_for_visible(page, timeout)` in
`automation/components/mui.py` — identical to `wait_for()` but scopes the
locator to `[role="dialog"]:visible` (Playwright's `:visible` pseudo-class
is a real, supported selector extension). Additive sibling; `Dialog.wait_for()`
itself was NOT touched (it has many other merged callers across
chat/pipeline/skill page objects — page-objects.md shared-caller rule).
Also added `AgentDetailPage.remove_mcp()` as an additive sibling to
`remove_toolkit()`, identical except it calls `Dialog.wait_for_visible()`
instead of `Dialog.wait_for()`.

**Any future MCP-card interaction needing a confirmation/generic dialog
should call `Dialog.wait_for_visible()`, not `Dialog.wait_for()`** — the
`keepMounted` OAuth modal is a permanent DOM fixture on any MCP card with
an unauthenticated "Log in" button, not a one-off flake.

## UnifiedDropdown testids are shared across entity types (confirmed via source)

`ToolMenu.jsx`'s "+ Toolkit"/"+ MCP"/"+ Agent"/"+ Pipeline" add buttons all
open the SAME `UnifiedDropdown.jsx` component. Its search input
(`toolkit-search-input`) and every menu item (`toolkit-menu-item`) carry
those testids unconditionally, regardless of which entity type opened the
popper — confirmed by reading `UnifiedDropdown.jsx` directly (not just
observing one flow live). Safe to reuse `add_toolkit()`'s
search/select-menuitem pattern verbatim for a new `add_mcp()`. One real
difference: MCP names are NOT space-stripped in the popper (unlike Toolkit
names, which strip spaces) — match on the exact name for MCP.

## Testid gaps found (out of scope to fix in a same-PR dispatch)

- `ToolMenu.jsx`'s Agent and Pipeline add buttons carry **no** `data-testid`
  at all — only Toolkit (`agent-add-toolkit-button`) and MCP
  (`agent-add-mcp-button`) do. Any case wanting to assert all 4 buttons
  needs `add-data-testid` on the Agent/Pipeline buttons first.
- The attached MCP card's disconnected-status icon (a MUI `Tooltip` whose
  `title` text isn't in the DOM until hover) and the "Log in" button
  (`McpLogInButton.jsx`) also carry no `data-testid`. Can't be asserted
  under the testid-only/no-fallback locator policy without adding new
  testids.

Both gaps were scoped out of the ELITEA-1950 test (documented in that
case's AFS as a same-PR amendment) rather than adding testids, because the
case's dispatch explicitly sealed `automation/testids` to the analyst's
already-merged `agent-add-mcp-button` commit for that PR. A future case
that specifically needs 4-button or connection-status coverage should run
`add-data-testid` for these elements first.
