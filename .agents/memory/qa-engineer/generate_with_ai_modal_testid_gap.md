---
name: Generate-with-AI modal testid gap
description: Shared GenerateEntityModal/GenerateEntityButton ("Build with AI" flow) has zero data-testid anywhere despite BaseModal already supporting the props — one shared fix benefits every entity type
type: reference
---

Discovered during ELITEA-1915 analysis (agent "Build with AI" generation
failure/retry case).

**Component tree**: `EliteaUI/src/[fsd]/entities/generate-entity-with-ai/`
(`GenerateEntityModal.jsx`, `GenerateEntityButton.jsx`) is the SHARED base
used by per-entity wrappers, e.g.
`EliteaUI/src/[fsd]/features/agent/ui/generate-agent-modal/`
(`GenerateAgentModal.jsx`, `GenerateAgentButton.jsx`). The `entityLabel` prop
("agent" in this case) and directory naming strongly suggest skill/pipeline
equivalents reuse the same shared modal — check for sibling
`generate-<entity>-modal` directories under `features/` before re-deriving
this from scratch on a future skill/pipeline "Build with AI" case.

**The gap**: `GenerateEntityModal.jsx` renders `<Modal.BaseModal ... />`
(`EliteaUI/src/[fsd]/shared/ui/modal/BaseModal.jsx`) WITHOUT passing
`dataTestId` / `closeButtonDataTestId` / `confirmButtonDataTestId` —
`BaseModal` already supports all three (lines 32/108/122/144 of
`BaseModal.jsx`), the wiring is just missing at the call site. Beyond that,
every other interactive element inside `GenerateEntityModal.jsx`
(prompt `TextField`, error `Alert`, Generate/Cancel/Back-to-prompt/
Create-<Entity> buttons, loading indicator) is a plain MUI component with
zero testid props anywhere in the file.

**Implication for `add-data-testid`**: fixing `GenerateEntityModal.jsx` once
(pass the 3 BaseModal props + add testids to the TextField/Alert/buttons)
benefits every entity type's "Build with AI" flow simultaneously — don't
scope a fix to just the agent variant if a future case touches skill/
pipeline generation.

Suggested names used in the ELITEA-1915 AFS (adjust `agent` → the relevant
entity if reused): `generate-agent-modal`, `generate-agent-prompt-input`,
`generate-agent-error-alert`, `generate-agent-submit-button`,
`generate-agent-cancel-button`, `generate-agent-loading-indicator`,
`generate-agent-back-button`, `generate-agent-approve-button`.

Full AFS: `test-specs/agents/l2_build-with-ai-generation-failure-retry_ELITEA-1915.md`.
