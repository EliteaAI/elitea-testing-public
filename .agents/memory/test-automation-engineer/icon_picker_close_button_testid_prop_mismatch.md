---
name: icon picker close button testid prop mismatch
description: agent-icon-picker-close-button never actually rendered — SelectIconDialog.jsx passed the wrong prop name to BaseModal
type: feedback
---

Found + fixed during ELITEA-2604 (skill custom icon upload/validation),
2026-08-12.

`SelectIconDialog.jsx` (the SHARED icon picker used by Agent/Skill/Pipeline)
passed `closeButtonDataTestId="agent-icon-picker-close-button"` to
`BaseModal`, but `BaseModal.jsx` destructures the prop as
`closeButtonTestId` (no "Data" in the middle). React silently drops the
unrecognized prop, so `data-testid={closeButtonTestId}` on the close
`IconButton` rendered `undefined` — **the close button had NO working
testid at all**, despite `agent_detail_page.py` / `skill_form_page.py`
declaring `icon_picker_close_button = LocatorDescriptor(testid="agent-icon-picker-close-button")`
as "pre-existing" (inherited from ELITEA-2602's AFS, which itself never
actually clicked it).

Symptom: `Locator.click()` on `icon_picker_close_button` times out after
10s with "waiting for get_by_test_id(...)" and NO "resolved to N elements"
line — i.e. it never resolves, not a strict-mode/visibility issue. The
element is visibly present on screen (screenshot shows a normal-looking X
button) — this is NOT a "add-data-testid" gap (testid exists in the
codebase, spelled correctly, in the right JSX), it's a prop-name typo one
call frame up.

Fix (EliteaAI/EliteaUI@72a6f788): rename the prop at the call site to
`closeButtonTestId`.

**Lesson — a testid declared "pre-existing" in an AFS/page-object is only
proven if some PRIOR test actually exercised it on its executed path.** A
testid can exist correctly in the DOM-defining JSX yet still be dead if a
wrapper component's prop name doesn't match what the shared component
destructures. If a locator that's supposedly pre-existing times out with
zero elements resolved (not a strict-mode collision, not a visibility
timing issue), suspect a prop-forwarding mismatch in a shared modal/dialog
wrapper before assuming a wait/timing bug — grep the component tree for
where the testid string literal actually lands vs. what prop name the
receiving component reads.
