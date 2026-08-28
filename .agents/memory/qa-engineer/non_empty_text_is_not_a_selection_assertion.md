---
name: Non-empty-text is not a "a value is selected" assertion
description: expect(combobox).not_to_have_text("") passes on a rendered placeholder — assert the selected label, not mere non-emptiness
type: feedback
aliases: [not_to_have_text, empty select assertion, placeholder passes, combobox selected]
tags: [area/assertions, type/review-lens]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

A case step "the dropdown shows a selected option" is often implemented as
`expect(combobox).not_to_have_text("")`. That assertion only proves the display
element renders *something*. Every `SingleSelect` in EliteaUI takes
`showEmptyPlaceholder` / `emptyPlaceholder` (e.g. `VoiceConfigControls.jsx`
passes `emptyPlaceholder={<em>Default</em>}`), so a future build that renders a
placeholder instead of leaving the display blank flips the assertion green while
**nothing is selected** — the exact defect the step exists to catch.

Stronger shapes, in order of preference:
1. assert the display text equals a known option label read from the open list;
2. assert it matches the option-label set (regex / membership), never `!= ""`.

Seen on ELITEA-2385 (PR #1968), where the assertion is deliberately soft +
`# Known defect: #1965`, so it is currently red and the weakness is latent — it
becomes real the day the defect is fixed with a placeholder.

Related: [[mui_v7_switch_input_testid]]
