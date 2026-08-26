---
name: Help Center version-info tooltip no-space textContent
description: ResourceVersionInfo.jsx tooltip rows concatenate "name:" + version with no space in text_content() — 3rd confirmed instance of the flex-gap-not-a-space pattern
type: feedback
---

`ResourceVersionInfo.jsx`'s version-info tooltip (ELITEA-2225, 2026-08-14) renders each
component row as two adjacent inline `<Typography>` elements (`elitea_core:` / `0.673`)
inside a `Box` with `display: flex, gap: 0.25rem`. Confirmed live:
`version_info_tooltip.text_content()` returns
`"elitea_core:0.673admin:0.77notifications:0.21..."` — **no space or separator** between
name and value, or between rows. The visible gap is CSS flex `gap`, not a text character
or newline.

This is the **third confirmed instance** of the same pattern (see
`project_selector_text_content_has_no_whitespace.md` — combobox trigger — and
`information_section_trigger_row_no_space_textcontent.md` — pipeline Trigger row):
whenever two sibling `<Typography>`/inline elements are laid out via flex `gap` instead
of an actual text/whitespace node between them, `text_content()` concatenates with zero
separator, regardless of how much visual space CSS renders. `inner_text()` was NOT tried
here (skipped straight to the fix) — worth trying first next time, it may better emulate
rendered whitespace.

**Fix used:** assert via a whitespace-tolerant regex rather than a literal string —
`re.compile(rf"{name}:\s*{value}")` — instead of hardcoding either the spaced or
concatenated form, so the test survives either DOM shape.

**Rule of thumb going forward:** never assert an exact `"label: value"` string against
`text_content()` of a MUI flex-row without first confirming (via a live probe) whether a
real space/newline exists in the DOM — assume it does NOT until proven otherwise, and use
`\s*`-tolerant regex or per-node separate testids if precision without a probe is needed.
