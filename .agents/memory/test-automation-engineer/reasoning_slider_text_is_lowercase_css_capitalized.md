---
name: Reasoning slider text is lowercase, CSS-capitalized
description: DiscreteSlider/ReasoningSlider mark labels are raw lowercase DOM text; visual "Low/Medium/High" is CSS text-transform, not DOM content
type: feedback
---

`LLMSettings.jsx`'s Reasoning slider (`ReasoningSlider.jsx` -> shared
`DiscreteSlider.jsx`, `src/[fsd]/shared/ui/slider/`) renders its three level
labels from `REASONING_EFFORT_VALUES` in `llmSettings.constants.js`, which
stores them **lowercase**: `{ Low: 'low', Medium: 'medium', High: 'high' }`.
The dialog LOOKS like it says "Low / Medium / High" because
`DiscreteSlider`'s label styles apply `textTransform: 'capitalize'` in CSS —
but a Playwright `.text_content()` read returns the raw, un-transformed DOM
text: `"low"` / `"medium"` / `"high"`.

An AFS analyst pass that eyeballs the rendered page (or uses a method that
respects CSS, like `inner_text()`) will correctly report "Low, Medium, High"
in its text dump — that is NOT case-text drift or a defect, it's a
`text_content()` vs `inner_text()` mismatch. If you assert against the
raw testid element's `.text_content()`, compare **case-insensitively**
(`label.lower() in text.lower()`) rather than amending the AFS or filing a
clarification — the visual capitalization is the intended UI, only the
extraction method differs from what the human eye (or the AFS's own script)
saw.

Same testid (`model-settings-reasoning-slider`, added ELITEA-1880) covers
the label text + all three marks in one `text_content()` read — no need for
per-mark locators.
