---
name: toolkit_card_delete_hover_overlay_and_autopersist
description: Removing an agent-toolkit-card (Agent or Pipeline Tools section) needs a header-scoped hover + evaluate-click, and auto-persists (Save goes disabled)
type: feedback
---

Discovered automating ELITEA-2065 (Pipeline Tools-section MCP add/view/remove).
`ToolCard.jsx` is shared by Agent AND Pipeline TOOLS sections
(`agent-toolkit-card`, `agent-toolkit-delete-button`).

1. **Hover targeting.** The delete button's CSS `&:hover` reveal is scoped to
   the card's fixed-height HEADER row only (`styles.cardHeader`), not the
   whole card. A plain `card.hover()` targets the card's geometric center —
   fine on a collapsed card, but if the card is expanded (e.g. its "Show
   tools" panel is open, or any other content grows the card taller than the
   header), the center point lands outside the header and the button never
   reveals. Fix: `card.hover(position={"x": 10, "y": 10})` to always land
   inside the header regardless of expansion state.
2. **Click targeting.** `delete_btn.click(force=True)` reports success but
   can silently land on an invisible Tooltip overlay above the icon instead
   of the button — no exception, but the confirm dialog never opens. Use
   `delete_btn.evaluate("el => el.click()")` instead (dispatches directly on
   the element), per `.claude/rules/mui-patterns.md`'s existing
   "evaluate() for critical actions" guidance.
3. **Auto-persist on removal.** Like MCP-attach (#530/#1149), toolkit/MCP
   REMOVAL also auto-persists immediately —
   `useDisassociateToolkit.hooks.js`'s `savePipelineAfterToolkitRemoval` (or
   the Agent-side equivalent) fires its own `PUT
   .../application/prompt_lib/{project}/{id}` right after the disassociate
   `PATCH .../tool/prompt_lib/{project}/{toolkit_id}`, and resets the Formik
   baseline. This makes `agent-save-button` DISABLED afterward
   (`SaveApplicationButton.jsx`'s `isButtonDisabled` gates on
   `!isFormDirtyExcluding`) — a real disabled `<button>` suppresses even a
   forced JS `.click()`, so `save_and_wait_for_update()` will time out
   waiting for a PUT that never fires. If a case's steps say "Save — verify
   removal persists", assert the Save button is DISABLED (proof nothing is
   pending) and reload directly — don't try to click it.
