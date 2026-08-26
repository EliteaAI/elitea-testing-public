---
name: Chat attachment chip icon is generic, not type-aware
description: FileList.jsx renders one AttachedFileIcon for every attachment type; a case asking for "type-appropriate icons" is case-text drift, not a defect
type: reference
---

`EliteaUI/src/components/Chat/FileList.jsx` (chat attachment chip / "+N" overflow
component) renders the exact same `AttachedFileIcon` SVG for every attachment
chip and every overflow-menu item, unconditionally — confirmed via source (no
branching on extension/MIME anywhere) AND live (`.png`/`.pdf`/`.txt` attachments
all render byte-identical `<svg>` outerHTML).

If a TMS case for this surface says "icons reflect file type" / "type-appropriate
icon", that is case-text drift, not a defect — there's no partial/broken
type-icon wiring in `FileList.jsx` (looks like it was never built that way, not a
regression). Contrast: the app DOES have a type-aware icon/preview system
elsewhere (`EliteaUI/src/slices/fileTypes.js` + the Artifacts feature's
`FilePreviewCanvas`) — `FileList.jsx` just doesn't reuse it. Filed as
EliteaAI/elitea-testing-public#1591 (ELITEA-2199).

Truncation (`text-overflow: ellipsis` via shared `TypographyWithConditionalTooltip`)
IS genuine — assert via `scrollWidth > clientWidth` on the name element, not by
trusting the CSS rule alone. The same component also shows a hover tooltip with
the full name only when genuinely overflowing (`useTextOverflow` hook) — no
testid on it yet if a future case wants to assert that too.

The "+N" overflow button (`chat-attachment-overflow-button`) is a REAL
click-to-expand control: click flips `aria-expanded` → `"true"` and opens a MUI
`role="menu"` populated by `chat-attachment-overflow-item-{index}`. Existing
tests only click it as plumbing (to read hidden names for a count assertion) —
if a case explicitly asks to verify the click/expand interaction itself, that's
a genuine gap, not already covered.
