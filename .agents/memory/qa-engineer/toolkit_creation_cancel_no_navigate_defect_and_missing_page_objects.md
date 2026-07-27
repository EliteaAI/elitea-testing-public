---
name: Toolkit creation Cancel doesn't navigate + no page objects exist for the wizard
description: ELITEA-1868 — confirming Cancel on any New Toolkit/MCP/Application creation form only clears local state (never calls navigate()), stranding the user on the type-picker at the same URL instead of the entity list (filed #655); DiscardButton.jsx already supports dataTestId/modalDataTestId/confirmButtonDataTestId props that no call site wires; automation/pages/ has zero coverage of the Toolkits list or creation wizard at all
type: feedback
---

## The defect (#655, MAJOR, isolated — not blocking)

`src/pages/Toolkits/CreateToolkitToolTabBar.jsx` is the SHARED Save/Cancel tab-bar
for toolkit, MCP, and Application creation (`isMCP`/`isApplication` props switch
labels/routes, same component). Its Cancel flow:

```
Cancel click → DiscardButton opens a "Warning" confirm modal (always, no case-text
  mention needed — this is unconditional in DiscardButton.jsx)
→ Discard click → onCancel() → setWantToCancel(true)
→ effect: onClearEditTool() [= setEditToolDetail(null) in CreateToolkit.jsx]
         + formik.resetForm()
```

Neither step calls `navigate()`. Clearing `editToolDetail` just makes
`CreateToolkit.jsx` fall back to rendering `<ToolkitTypeSelector>` (the "Choose the
toolkit type" picker) again, at the SAME URL (`/toolkits/create/{type}` stays in the
address bar) — the user is never routed to the entity list
(`RouteDefinitions.ToolkitsWithTab`/MCPsWithTab/AppsWithTab), even though the
Save-success path (`onSaveEvent`, same file, ~40 lines below) DOES call `navigate()`
with exactly that route logic. Since this is the shared tab-bar, the same bug should
reproduce identically for MCP-creation Cancel and Application-creation Cancel — not
independently re-verified for those two, but the code path is byte-identical
(`isMCP`/`isApplication` only affect the destination route on the SAVE branch, never
touch the CANCEL branch at all).

Reproduced 2/2 (Artifact toolkit type) — run 2 used ONLY native Playwright
locator/role clicks (no `page.evaluate()`) specifically to rule out a
synthetic-input artifact, per the Synthetic Input Hygiene guard. Confirmed at the
network level too: zero `POST` to the toolkit-create endpoint ever fires on the
Cancel path across either run — the Cancel button never reaches the save/create
call at all, consistent with the root cause (it never gets far enough to call
`navigate()` either).

**Classification: isolated, not blocking.** The actual "no toolkit/bucket created"
claim any case built around Cancel would make still holds — verify it via UI search
(0 results) + network log (no POST), independent of where Cancel actually lands the
user. Recommend `expect.soft()` + `# Known defect: #655` on the post-cancel URL
check specifically, per this project's Sanctioned-RED merge-gate shape.

## The testid gap (trivial to close)

`DiscardButton.jsx` (`src/[fsd]/shared/ui/button/DiscardButton.jsx`) already accepts
`dataTestId`, `modalDataTestId`, `confirmButtonDataTestId` props (used by at least
one other call site in this codebase already). `CreateToolkitToolTabBar.jsx`'s
`<Button.DiscardButton title="Cancel" onDiscard={onCancel} alertContent="..." />`
call passes NONE of them — the Cancel button, its confirm dialog, and the dialog's
own Discard button are all testid-less purely because nobody wired 3 already-existing
props at this one call site. Any future case touching Cancel on ANY toolkit/MCP/
Application creation form will hit this same gap — check whether it's been closed
before re-flagging as `testid needed:`.

## The bigger gap: no page objects exist for this surface at all

`ls automation/pages/` confirmed (2026-07-19) zero coverage of the Toolkits list
page OR the creation wizard — only `toolkit_detail_page.py` exists, which is for an
EXISTING toolkit's detail/config view (credential-status indicators) and shares no
real behavior with the creation flow; don't extend it for wizard work. A future
implementer needs `toolkits_list_page.py` (mirror `agents_list_page.py`/
`mcp_list_page.py` — they already reuse the exact same shared `agent-search-input`/
`entity-card` testids this surface needs, don't reinvent) and a new
`toolkit_creation_page.py` for the type-picker + form + Cancel flow.

## Reusable technique confirmed again

`toolkit_mcp_create_form_quirks.md`'s "type-selector card click-locator-ambiguity
gotcha" recurred exactly the same way: `page.locator('div').filter({ hasText:
/^Artifact$/ }).first()` resolves to a non-interactive wrapper `<div>` and silently
no-ops. Always target the type card via `[data-testid="toolkit-type-card-{key}"]`
directly (confirmed present, template form, on `automation/testids` only as of this
session — not on `main` yet).
