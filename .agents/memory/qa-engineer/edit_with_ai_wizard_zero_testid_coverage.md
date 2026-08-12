---
name: Edit with AI wizard — zero testid coverage (shared shell)
description: entities/edit-entity-with-ai wizard phase (Skill/Agent/Project-Context) has no testids past the prompt phase
type: project
---

`entities/edit-entity-with-ai/` is a SHARED shell consumed by Skill
(`features/skill/ui/ai-edit-skill-modal/`), Agent
(`features/agent/ui/ai-edit-agent-modal/`), and Project Context
(`features/settings/ui/project-context/ai-edit/`) "Edit with AI" flows —
distinct from each entity's separate "Build with AI" CREATION flow.

**The PROMPT phase is fully testid'd** (`modalTestId`/`promptInputTestId`/
`generateButtonTestId`/etc props, threaded per-consumer, e.g.
`ai-edit-skill-*`). **The WIZARD phase (post-generate) has ZERO testid
coverage** — confirmed by reading every file under
`entities/edit-entity-with-ai/ui/` (2026-08-12, ELITEA-2611 analysis): no
testid on the step indicator ("1. General"/"2. Instructions"/"3. Summary"),
the per-field "Apply changes" checkboxes, the 5 wizard-footer buttons (Refine
Prompt/Previous/Next/Save/Save as Version), or a Summary step's merged-value
inputs (skill-specific `SummaryStep.jsx`, likely mirrored in the Agent
variant — not yet checked).

If you land on an Agent- or Project-Context-flavored Edit-with-AI case, expect
the SAME gap and the SAME fix shape: thread new `xxxTestId` props through
`EditEntityModal`/`GeneralStep`/`InstructionsStep`/`EditEntityStepIndicator`
(shared, generic prop names) and wire them at each consumer's call site with
that consumer's own prefix (`ai-edit-agent-*`, `ai-edit-project-context-*`).
Don't re-derive this from scratch — full prop/component/testid-name table is
in `test-specs/skills/l2_edit-with-ai-skill-happy-path_ELITEA-2611.md` §
Concrete Handles, and the general write-up is in
`test-specs/skills/_surface.md` § Edit with AI.

Also: the Summary step is NOT an itemized "these fields will change" list —
it's ONE merged, directly-editable form per field, value = current-or-suggested
depending on that field's checkbox. Same guarantee the case wants, different
presentation. Don't misread it as a defect.
