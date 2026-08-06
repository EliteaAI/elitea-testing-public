---
name: SkillDetailPage.switch_version() onChange race
description: version-option click + wait_for_network can both resolve before MUI's onChange re-render lands — read the selector's own text and poll, don't trust network-idle alone
type: feedback
---

Found reviewing ELITEA-2440 (`test_skill_test_panel_version_instructions.py`,
`SkillDetailPage.switch_version()`, `automation/pages/skill_detail_page.py`).

- **The bug pattern**: `switch_version(name)` clicked the `version-option-{name}`
  row and then called `self.wait_for_network(timeout=5000)` before returning.
  Both the click and the network-idle wait can resolve *before* MUI's
  `onChange` re-render actually updates the VERSION selector's displayed text
  — a caller reading `get_version_selector_value()` immediately afterward can
  still observe the *previous* version. Not a flaky-sometimes thing observed
  live during this review, but a real logical race the implementer named and
  fixed in the same PR: no network round-trip has to be in flight for a React
  state update to still be pending on the next microtask/paint.
- **The fix** (now shipped): after the click + `wait_for_network`, poll
  `get_version_selector_value()` every 200ms against a deadline built from
  `timeout`, returning as soon as it equals the target `version_name`, and
  raising `RuntimeError` (not swallowing) if the deadline passes without it.
  This is the general pattern for any MUI selector-style control here:
  **verify the state you actually need by reading it back, don't infer
  "done" from network idle** — network idle proves the request finished, not
  that the DOM the test will next assert against has re-rendered.
- **Only caller at review time** was the new ELITEA-2440 test itself (checked
  via `grep -rn "\.switch_version(" automation/tests/ automation/pages/`), so
  the fix landed safely as a shared-method change with no other spec at risk
  of a behavior change. Re-check callers before assuming the same is still
  true next time this method is touched.
- Analyst's own live-exploration digest (`test-specs/skills/_surface.md`)
  does **not** mention this race — manual/live exploration has natural
  think-time between actions that automation's fast click-then-read doesn't,
  so this class of race is easy to miss at analysis time and only surfaces
  once a test drives the control at full speed. Worth a mention in
  `_surface.md` if another skill/version-selector case turns up something
  similar.
