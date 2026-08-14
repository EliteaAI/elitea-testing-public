---
name: Edit-with-AI wizard step numbering is positional, not fixed
description: computeVisibleSteps() skips a step when the AI draft has no diff there — step_indicator numeral shifts
type: feedback
---

`AIEditSkillModal.jsx`/`AIEditAgentModal.jsx`'s wizard (General → Instructions
→ Summary) does NOT always render all three steps. Source:
`skillAIEditionSteps.helpers.js`/`agentAIEditionSteps.helpers.js`'s
`computeVisibleSteps(currentData, draftData)` — the General step is pushed
only if the AI draft's Name/Description differ from CURRENT (or nothing
differs at all, in which case every step renders so the user still gets a
full wizard); same logic for Instructions. Summary always renders last.

The step-indicator's numeral prefix
(`${activeStepIndex + 1}. ${label}`, `EditEntityStepIndicator.jsx:15`) is
POSITIONAL — so Summary reads "2. Summary" in a 2-step wizard (General
skipped) or "3. Summary" in a 3-step wizard. **Never hardcode
`get_step_indicator_text() == "3. Summary"` or assume the wizard opens on
"1. General"** — the LLM's actual diff on a given call determines which
steps exist. Live-confirmed ELITEA-2613: an edit prompt that changed only
Instructions produced a 2-step wizard, opening on "1. Instructions".

Robust pattern: assert the OPENING step is one of the plausible first labels
(`"1. General"` or `"1. Instructions"`), then advance with a bounded
"click Next until label contains 'Summary'" loop instead of a fixed N-click
sequence, and assert Summary by label-substring (numeral-agnostic).
