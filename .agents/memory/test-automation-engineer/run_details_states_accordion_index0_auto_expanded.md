---
name: Run Details STATES accordion — index-0 row is auto-expanded, click toggles
description: expand_run_details_state_row() on the list's first variable COLLAPSES it (defaultExpanded), not a no-op
type: project
---

`RunStateDialog.jsx`'s STATES section maps `variables` into `BasicAccordion`
items with `defaultExpanded={!index}` — only **list index 0** (the first
state variable rendered, order = pipeline `state:` YAML key order) starts
expanded. Every other row starts collapsed.

`PipelineDetailPage.expand_run_details_state_row(variable)` is a raw click —
its own docstring says "no-op if already expanded" but that's wrong for a
MUI accordion: clicking an ALREADY-EXPANDED `AccordionSummary` **toggles it
closed**. If you loop `expand_run_details_state_row()` over ALL state
variables (as ELITEA-2453's first draft did), the index-0 variable's row
gets collapsed instead of staying open — its Before/After value boxes then
report `hidden` in the next assertion.

**Fix:** skip the click for whichever variable is at list index 0 in your
pipeline's `state:` YAML (for ELITEA-2453's fixture, `custom_text` — the
first key in `_TYPED_STATE_VARS_INSTRUCTIONS`). Only click the remaining
rows to expand them.

Same underlying mechanism as ELITEA-2452's `messages`-at-LLM1 case, which
sidesteps this because it only ever expands ONE row per test.
