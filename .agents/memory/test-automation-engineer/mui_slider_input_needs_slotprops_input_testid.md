---
name: MUI Slider's interactive input needs its own slotProps.input testid
description: DiscreteSlider.jsx's testId prop lands on the outer Box wrapper (same family as TextField/Switch). To focus + arrow-key the slider you need the real <input type=range>, which needs a SEPARATE testid threaded via `slotProps={{ input: { 'data-testid': x } }}` on the MUI <Slider> — confirmed working in @mui/material@^7.0.2. Do not reuse the AFS's suggested aria-label handle or copy the pre-existing raw `input[aria-valuemin=...]` selector in user_profile_settings_page.py::set_speed() (tech debt, not precedent).
type: feedback
---

## Rule

`src/[fsd]/shared/ui/slider/DiscreteSlider.jsx` puts `data-testid={testId}` on
its outer `<Box>` wrapper only — the real `<input type="range">` that
Playwright must `.focus()` + `keyboard.press("ArrowRight"/"ArrowLeft")` on is
a separate internal node the wrapper's testid never reaches (same family as
`testid_lands_on_mui_wrapper_not_input.md`).

Fix at the source, one extra prop: `DiscreteSlider` also accepts an optional
`inputTestId`, threaded onto MUI's `<Slider slotProps={{ input: {
'data-testid': inputTestId } }} />`. Confirmed live (ELITEA-2436) it lands on
the real `<input>`, and `.focus()` + `ArrowRight` reliably moves the value and
enables the dialog's Apply button.

**Scope discipline (canon #511):** only pass `inputTestId` from the caller
(e.g. `CreativitySlider.jsx`) whose test actually DRIVES the slider. A
sibling consumer of the same shared `DiscreteSlider` (e.g. `ReasoningSlider`)
that only asserts presence/text, never interaction, should NOT also get
`inputTestId` — that would be an orphan testid on this test's un-executed path.

**Don't fall back to the AFS's suggested `[aria-label="Creativity level"]`
raw handle, and don't copy `user_profile_settings_page.py::set_speed()`'s
`input[aria-valuemin="0.5"][aria-valuemax="2"]` CSS-attribute selector** —
both are pre-existing tech debt (#25/#42), not sanctioned precedent, and both
fail the reviewer's mechanical grep as new-code additions.

## Seen 1×

- ELITEA-2436 (Skill test panel LLM model settings) — `CreativitySlider.jsx`
  needed its Creativity slider MOVED (not just checked for presence) to
  prove the Apply button enables on change.
