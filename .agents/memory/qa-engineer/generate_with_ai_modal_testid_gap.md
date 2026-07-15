---
name: Generate-with-AI modal testid gap
description: Shared GenerateEntityModal/GenerateEntityButton ("Build with AI" flow) now supports testids end-to-end; the Agent wrapper wires them all through, the Skill wrapper still wires none — audit each entity wrapper separately
type: reference
---

Originally discovered during ELITEA-1915 analysis (agent "Build with AI"
generation failure/retry case); **updated during ELITEA-2001** (skill
equivalent) once the underlying gap had been partially fixed.

**Component tree**: `EliteaUI/src/[fsd]/entities/generate-entity-with-ai/`
(`GenerateEntityModal.jsx`, `GenerateEntityButton.jsx`) is the SHARED base
used by per-entity wrappers, e.g.
`EliteaUI/src/[fsd]/features/agent/ui/generate-agent-modal/`
(`GenerateAgentModal.jsx`, `GenerateAgentButton.jsx`) and
`EliteaUI/src/[fsd]/features/skill/ui/generate-skill-modal/`
(`GenerateSkillModal.jsx`, `GenerateSkillButton.jsx`). The `entityLabel` prop
and directory naming confirm both wrappers reuse the identical shared modal
— check for sibling `generate-<entity>-modal` directories under `features/`
before re-deriving this from scratch on a future pipeline/other-entity
"Build with AI" case.

**State as of ELITEA-1915 (original finding)**: `GenerateEntityModal.jsx`
rendered zero testids anywhere — not even `BaseModal`'s already-supported
`dataTestId`/`closeButtonDataTestId`/`confirmButtonDataTestId` props were
wired through.

**State as of ELITEA-2001 (this update) — the shared component was fixed,
but only ONE wrapper was updated to use it:**
- `GenerateEntityModal.jsx`/`GenerateEntityButton.jsx` now declare and wire
  NINE `*TestId` props end-to-end (`modalTestId`, `closeButtonTestId`,
  `promptInputTestId`, `errorAlertTestId`, `loadingIndicatorTestId`,
  `generateButtonTestId`, `cancelButtonTestId`, `backButtonTestId`,
  `approveButtonTestId`, plus `buttonTestId` on `GenerateEntityButton`) —
  the shared component fully supports testids now, capability-wise.
- `GenerateAgentButton.jsx`/`GenerateAgentModal.jsx` (Agent) DO pass all of
  these through, confirmed live: `generate-agent-open-button`,
  `generate-agent-modal`, `generate-agent-close-button`,
  `generate-agent-prompt-input`, `generate-agent-error-alert`,
  `generate-agent-loading-indicator`, `generate-agent-submit-button`,
  `generate-agent-cancel-button`, `generate-agent-back-button`,
  `generate-agent-approve-button` — all real, all present in the DOM.
- `GenerateSkillButton.jsx`/`GenerateSkillModal.jsx` (Skill) pass NONE of
  them — confirmed live via DOM inspection of the open dialog (only stray
  testid present was MUI's own default `ErrorOutlineIcon`, not anything
  app-wired). This is a pure wrapper-wiring gap now, not a shared-component
  capability gap — cheaper to fix than the original 1915 finding (no new
  plumbing needed anywhere, just add the 1+9 prop-passes to the two Skill
  wrapper files, mirroring `generate-agent-*` → `generate-skill-*`).

**Lesson**: a shared component gaining testid *support* does NOT mean every
entity wrapper *uses* it — audit each entity's own wrapper file
independently before assuming a sibling entity's fix carries over. If a
future case touches the Pipeline (or other) "Build with AI" variant, check
its wrapper's prop-passing the same way rather than assuming parity with
either Agent or Skill.

Full AFSes: `test-specs/agents/l2_build-with-ai-generation-failure-retry_ELITEA-1915.md`,
`test-specs/skills/l2_build-with-ai-generation-failure-retry_ELITEA-2001.md`.
