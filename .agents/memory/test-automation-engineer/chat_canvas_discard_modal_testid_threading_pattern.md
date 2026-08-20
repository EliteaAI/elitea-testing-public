---
name: Chat-canvas Discard modal testid threading pattern
description: BaseEditor/EditorHeader already support discard-modal + confirm-button testid props (ELITEA-2076) — only the Pipeline call site supplies them; Agent/MCP/Toolkit still need their own.
type: feedback
---

`pages/NewChat/components/BaseEditor.jsx` -> `EditorHeader.jsx` is the shared
chrome for every in-chat "Create New X" canvas (Agent/Pipeline/Toolkit/MCP).
`EditorHeader.jsx` already rendered `Button.DiscardButton` (`[fsd]/shared/ui/
button/DiscardButton.jsx`) unconditionally when `!isPublic`, and that
component ALREADY supports `modalDataTestId`/`confirmButtonDataTestId` props
internally (proven live pre-ELITEA-2076 by `CredentialsTabBar.jsx`'s direct
usage, `credential-discard-confirm-modal`/`credential-discard-confirm-button`)
— but `EditorHeader.jsx`'s own call only ever forwarded `dataTestId`
(the header Discard button itself), never the modal/confirm-button testids.

ELITEA-2076 added two new optional props all the way through the chain:
`discardModalTestId` / `discardConfirmButtonTestId`, threaded
`BaseEditor.jsx` -> `EditorHeader.jsx` -> `Button.DiscardButton`'s existing
`modalDataTestId`/`confirmButtonDataTestId` props — same shape as the
pre-existing `discardButtonTestId` (added by ELITEA-2089 for the Agent
canvas's header Discard button, but ELITEA-2089 never clicked it or needed
the modal).

**Supplied at two call sites now.** `PipelineEditor.jsx`
(`pipeline-canvas-discard-button` / `pipeline-canvas-discard-confirm-modal`
/ `pipeline-canvas-discard-confirm-button`, `EliteaAI/EliteaUI@d4edc6e5`,
ELITEA-2076) and, as of ELITEA-2081 (`EliteaAI/EliteaUI@bc08563f`),
`ToolkitEditor.jsx` — `toolkit-canvas-discard-*` / `mcp-canvas-discard-*`
(same `isMcpTestIdScope` conditional as its other three chrome testids).
Confirmed live for Toolkit: create-mode Discard reverts to the type-picker
(`setEditToolDetail(null)`), NOT to a blank form on the same type — distinct
from Pipeline's Discard, which only resets Name/Description on the SAME
form. The sibling `AgentEditor.jsx` (has `discardButtonTestId=
"agent-discard-button"` already, but NOT the two new modal props) still does
NOT supply `discardModalTestId`/`discardConfirmButtonTestId`. If a future
case needs to click Discard-and-confirm on the Agent canvas, the props
already exist end-to-end in `BaseEditor.jsx`/`EditorHeader.jsx` — just add
the three-line call-site addition (mirrors `PipelineEditor.jsx`'s /
`ToolkitEditor.jsx`'s), don't re-derive the threading from scratch.

The confirmation dialog's body text (both Agent and Pipeline paths, same
`DiscardButton.jsx` default `alertContent`) is literally "Are you sure you
want to discard changes?" (`ModalConstants.WARNING_MESSAGES.DISCARD_CHANGES`),
title "Warning".
