---
name: Edit with AI wizard — remaining testid gaps + navigation/error findings
description: entities/edit-entity-with-ai shared shell — which wizard-phase testids are wired vs still gapped, plus Refine-Prompt/Close/failure/validation mechanics
type: project
---

`entities/edit-entity-with-ai/` is a SHARED shell consumed by Skill
(`features/skill/ui/ai-edit-skill-modal/`), Agent
(`features/agent/ui/ai-edit-agent-modal/`), and Project Context
(`features/settings/ui/project-context/ai-edit/`) "Edit with AI" flows —
distinct from each entity's separate "Build with AI" CREATION flow.

**Current testid state (updated 2026-08-12, ELITEA-2612 analysis — supersedes
the "zero wizard-phase coverage" claim from the ELITEA-2611-era version of
this entry).** The PROMPT phase was always fully testid'd. The WIZARD phase
gap has been PARTIALLY closed for skills: step indicator, all 3 "Apply
changes" checkboxes, Previous/Next/Save, and the 3 Summary-step inputs are now
wired and on `main` (`EliteaAI/EliteaUI@cddfd6d4` + fix-round-1
`EliteaAI/EliteaUI@3e1e5c73`). **Still unwired for skills: "Refine Prompt" and
"Save as Version"** — `AIEditSkillModal.jsx`'s `<EditEntityModal>` call site
leaves `refinePromptButtonTestId`/`saveAsVersionButtonTestId` unset (canon
#511 — no case exercised either control until ELITEA-2612, which needs
"Refine Prompt": naming lands as `ai-edit-skill-wizard-refine-prompt-button`,
see `test-specs/skills/l3_edit-with-ai-navigation-error-handling_ELITEA-2612.md`
§ Concrete Handles for the exact prop-wiring). If you land on an Agent- or
Project-Context-flavored Edit-with-AI case, check that consumer's OWN call
site independently — it likely mirrors this same wired/unwired split, but
verify rather than assume (each consumer wires its own prefix,
`ai-edit-agent-*` / `ai-edit-project-context-*`).

**Navigation/error mechanics (ELITEA-2612, all confirmed correct live, no
defects):**
- **"Refine Prompt" (the case's "Back") preserves the prompt text; "Close"
  does NOT.** `handleRefinePrompt` resets phase/draftData/activeStepIndex but
  NOT `description`; `handleClose` (and the `!open` effect) reset all of
  those PLUS `description`. Intentional asymmetry — Refine Prompt = "let me
  tweak and resend the same ask", Close = "abandon entirely".
- **Once the wizard phase is reached, "Cancel" (`ai-edit-skill-cancel-button`)
  no longer exists in the DOM at all** — `renderActions()` returns `null`
  outside `PHASES.PROMPT`. The only dismissal control past the prompt phase
  is the modal-level Close (X), `ai-edit-skill-close-button`. A case saying
  "click Cancel or close the wizard" from a wizard step means Close, not
  Cancel — don't go looking for a wizard-phase Cancel button.
- **No product-side lever forces a real generation failure.** Automate via
  `page.route()` intercepting exactly one `generate_skill_draft` POST with a
  mocked 5xx + JSON body (`{error: "..."}` round-trips verbatim into
  `ai-edit-skill-error-alert`'s text), then let subsequent calls through.
  There is no separate "Retry" control/testid — "Generate Draft" itself
  (still visible+enabled in the prompt phase after a failure) IS the retry
  path.
- **Empty/whitespace-prompt validation is disable-only — no message ever
  renders.** `disabled={!description.trim()}` covers both (`.trim()` of
  whitespace-only is falsy too). No `ai-edit-skill-error-alert` or any other
  validation-message element fires. Case text describing a "Prompt is
  required" message is case-text drift, not a product bug — clarification
  filed: elitea-testing-public#1478.

Also (from ELITEA-2611, still true): the Summary step is NOT an itemized
"these fields will change" list — it's ONE merged, directly-editable form per
field, value = current-or-suggested depending on that field's checkbox. Same
guarantee the case wants, different presentation. Don't misread it as a
defect.
