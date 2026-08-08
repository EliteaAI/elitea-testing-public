---
name: Build with AI — Back vs Cancel prompt preservation
description: GenerateEntityModal's handleBack() keeps the typed prompt; handleClose() clears it — verify via source, not just live behavior
type: reference
---

`GenerateEntityModal.jsx` (shared shell for both Agent and Skill Build-with-AI
modals) has two review-step exit paths that look similar live but differ at
the source level:

- `handleBack()` (wired to `back_button`, "Back to prompt"): resets `step` to
  `STEPS.INPUT` and `draftData` to `null`, calls `resetGenerate()` — but never
  touches `description` (the prompt textarea's state). The typed prompt
  survives verbatim.
- `handleClose()` (wired to the INPUT-step "Cancel" button AND the review-step
  X/"Close" icon): resets `step`/`description`/`draftData`/`isApproving`, then
  calls `resetGenerate()` + `onClose()`. The prompt is cleared.

When a case's Pass criteria hinge on "is state X preserved or cleared" across
a modal's exit paths, **read the source function each control is wired to**
(`onClick={handleX}` in `renderActions()`) rather than trusting a single live
observation — a live run only proves the ONE path you exercised; the source
diff between sibling handlers is what tells you WHY, and whether the same
distinction reappears for Skill's Build with AI (same shared component,
`GenerateSkillModalPage`'s `back_button`/`close_button`, unexplored as of
2026-08-08 — check `handleBack`/`handleClose` there too if a similar case
ever lands for Skills).

Confirmed live (ELITEA-1919, 2026-08-08): clicking `back_button` from the
review step fires zero new network requests (pure client-side reset) and
leaves review-form field testids fully removed from the DOM, not hidden.
