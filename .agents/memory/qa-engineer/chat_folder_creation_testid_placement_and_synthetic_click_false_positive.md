---
name: Chat folder creation — testid placement techniques + synthetic-click false positive
description: ELITEA-2132 — how to add testids on shared MUI icon components without violating the "no hardcode in shared component" ruling, the inputProps/slotProps.htmlInput channel for landing a testid on a real native <input> under a wrapper, and a confirmed self-inflicted MUI anchorEl console warning from a JS-evaluated click
type: feedback
---

ELITEA-2132 (Chat folder creation via CHATS header icon) found the entire
"Folders" feature (`EliteaUI src/[fsd]/features/chat/conversation-list/ui/folders/`
+ the header create-folder button in `Conversations.jsx`) had **zero**
`data-testid` coverage — confirm/cancel icons were bare `<div onClick>` with
no ARIA role and no `tabindex` (mouse-only, not keyboard-reachable — a real
a11y gap, not filed since out of this case's functional scope). Added 8
testids directly (EliteaAI/EliteaUI@6fceb3e2 on `automation/testids`),
mirroring the ELITEA-2114 precedent of analyst-added testids rather than
leaving a `ready-for-automation` case with 6+ open gaps.

**Technique 1 — testid on a shared icon component: add it at the CALL SITE,
never inside the shared component.** `FolderIcon` (`src/components/Icons/`)
and `StyledExpandMoreIcon` (`src/[fsd]/shared/ui/accordion/`) are both reused
by 4+ unrelated features. Both already spread `{...props}`/`{...rest}` onto
their underlying `SvgIcon`/`ArrowForwardIosSharpIcon`, so a bare
`data-testid="chat-folder-icon"` passed at the ONE call site in
`FolderAccordion.jsx` forwards correctly to the DOM without touching the
shared component's own source — exactly the EliteaUI PR #581 ruling's
"shared components never hardcode a feature-scoped testid" rule, applied via
the "or accept a prop / set it at the call site" branch, no `testId` prop
needed here since the icon component already spreads unknown props through.

**Technique 2 — `inputProps={{ 'data-testid': '...' }}` is the reliable
channel for a native `<input>` under an MUI TextField-family wrapper.** A
bare `data-testid` prop on `Input.StyledInputEnhancer` risks landing on the
outer `MuiFormControl`/`MuiInputBase` wrapper div depending on how far
`...leftProps` spreading goes before it's consumed. Tracing the prop chain
(`StyledInputEnhancer` → `InputBase.jsx` destructures `inputProps` separately
and passes it as `htmlInput: inputProps` — the MUI v6 `slotProps.htmlInput`
convention) confirms `inputProps={{ 'data-testid': 'chat-folder-name-input' }}`
lands directly on the real `<input>` DOM node. Live-verified:
`document.querySelector('[data-testid="chat-folder-name-input"]').tagName ===
'INPUT'`, value reads correctly. Use this pattern for any future testid on an
MUI `TextField`/`InputBase`-family field where `.fill()`/`.press()` needs to
target the actual input, not a wrapper.

**Technique 3 — threading state onto the SAME element as the testid, not a
new ancestor.** `chat-folder-item-{folder_id}` needed a new `folderId` prop
threaded `FolderItem.jsx` → `FolderAccordion.jsx` (FolderAccordion had no way
to know which folder it rendered before). Placed on the OUTER `StyledAccordion`
(not just the summary row) so one testid scopes both the header (icon, name,
expand-arrow, dot-menu) AND the body (empty-state / conversation list) as
descendants — same scope model as `chat-conversation-item-{id}`. Added
`data-expanded={expanded}` on that SAME element per the project's
state-via-data-attribute convention; confirmed live it flips `false`→`true`
correctly on click, using the same `expanded` state FolderAccordion already
tracks internally (no new state needed).

**Confirmed reuse, not a new gap:** the folder's dot-menu button resolves to
the exact same non-unique `conversation-menu-menu-button` testid already
documented in ELITEA-2114 for conversation items (same shared `DotMenu id=`
pattern) — scope it the same way (`chat-folder-item-{id} >>
conversation-menu-menu-button`). The delete-confirmation dialog also reuses
ELITEA-2114's generic `delete-confirm-dialog`/`-message`/`-button` testids
verbatim — zero new work needed for folder-delete cleanup.

**False positive, ruled out — do not re-file if seen again.** A
`page.evaluate(() => el.click())` on the folder's dot-menu trigger (bypassing
the real `mouseenter` that flips `isHovering`/reveals the hover-gated menu
button) produced a console error:
`MUI: The 'anchorEl' prop provided to the component is invalid. The anchor
element should be part of the document layout.` Re-tested twice with genuine
Playwright `hover()` + `click()` (the pattern real automation uses) — the
warning did NOT reproduce either time, and the menu opened correctly both
times. Per the Synthetic Input Hygiene guard: self-inflicted synthetic-input
session noise, not a product defect. If this exact warning surfaces again
during exploration, check whether the triggering interaction used a native
Playwright action or a `page.evaluate`/JS-dispatched click before treating it
as real.
