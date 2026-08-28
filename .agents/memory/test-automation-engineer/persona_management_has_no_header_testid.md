---
name: PERSONA MANAGEMENT accordion has no header testid
description: Observe its collapse through content visibility, not aria-expanded — no per-item testId is passed
type: feedback
aliases: [ai-personality-persona-section, accordion header, aria-expanded, BasicAccordion]
tags: [area/locators, area/settings]
created: 2026-08-29
updated: 2026-08-29
---

## Fact

`AIPersonalityPersonalization.jsx` passes `data-testid="ai-personality-persona-section"` to
`BasicAccordion` but **no per-item `testId`**, so — unlike the `/settings/preferences` and
`/settings/memory` sections, which do have `…-section-header` handles — the summary carrying
`aria-expanded` is unreachable testid-only.

## Consequence

"Did the section collapse?" is asserted through its **content**: collapsing hides the body
(`visibility: hidden`) rather than unmounting it, so
`ai-personality-persona-select-combobox` / `ai-personality-user-instructions-textarea` still
being visible is the equivalent observable. Reaching for `get_by_role("button")` in the spec
would be a raw handle in a spec file — blocked by the locator policy.

## The safe "click outside" target

`SettingsPersonalizationPage.click_neutral_content_area()` — bottom-left corner of the
`settings-content` `<main>` pane. The form wrapper is centred at `maxWidth: 50rem` and short,
so that point is empty `<main>`. React `onBlur` is `focusout` and bubbles from the field
being left, so it reliably fires `useFormikAutoSaveOnBlur`. **Never the accordion header** —
that collapses the section.
