---
name: Wizard step / MUI checkbox condition-waits that replace a sleep
description: ELITEA-2611 fix round 1 — expect().not_to_have_text()/not_to_have_class() patterns for step-transition and Mui-checked toggles, no fixed timeout
type: feedback
---

## Pattern

Two `page.wait_for_timeout()` shapes replaced with real Playwright
condition-waits in `ai_edit_skill_modal_page.py`:

**Step/wizard transition (click Next/Previous, wait for content to change):**
```python
previous_step = self.get_step_indicator_text()
self.next_button.click()
expect(self.step_indicator).not_to_have_text(previous_step, timeout=timeout)
```
Works because the transition is a synchronous React state update
(`activeStepIndex`) — the indicator's own text IS the completion signal, no
need to guess an animation duration.

**MUI checkbox toggle (the `Mui-checked` class-list workaround, see
`testid_lands_on_mui_wrapper_not_input.md`-adjacent entries — testid lands
on the `BaseCheckbox` root `<span>`, not the native `<input>`, so
`is_checked()` doesn't work):**
```python
self.general_description_checkbox.click()
expect(self.general_description_checkbox).not_to_have_class(re.compile("Mui-checked"))
```
`expect(locator).to_have_class(pattern)` / `not_to_have_class(pattern)` do a
regex **search** against the full `class` attribute string (confirmed
against the Playwright 1.61.0 docstring's own example
`re.compile(r"(^|\s)selected(\s|$)")`), so `re.compile("Mui-checked")` alone
is a safe substring match — no need to anchor or match the whole class list.

Both replace a magic-number sleep with a real wait that fails fast if the
state genuinely never changes (surfacing a real defect) instead of silently
racing it.

## When this applies elsewhere

Any page object reading `Mui-checked` off a class attribute
(`admin_users_page.py`, `artifacts_page.py`, this file) that currently
sleeps after a checkbox click to "let it settle" can drop the sleep for this
`expect(...).not_to_have_class(...)` / `to_have_class(...)` pair instead.
