---
name: MUI accordion-summary testid is not a scoping parent
description: A testid on an MUI AccordionSummary cannot scope the accordion's content — cards live in the sibling Details, so whole-page queries silently mix sections
type: feedback
aliases: [accordion scoping, section testid, isolate_section, summary button testid]
tags: [area/ui-locators, type/gotcha]
created: 2026-08-30
updated: 2026-08-30
---

## The trap

When a testid is threaded onto an MUI `AccordionSummary`, it lands on the **summary
button**, not the accordion root. The accordion's `Details` content is a **sibling**, so:

- `section_header.locator(child)` finds nothing.
- A whole-page query for a generic repeated child testid returns **every expanded
  section's** children at once.

Measured on Elitea's Settings -> AI Providers (2026-08-30): queries meant for the Image
Generation section kept returning the Vector Storage seed card, purely because Vector
Storage happened to be expanded. Nothing errors — the count is just wrong, so the test
goes green while asserting about the wrong section.

## The tell, and the fix

Tell: a "section" testid whose `outerHTML` starts `<button class="…MuiAccordionSummary-root…">`.

Fix: collapse every section and expand exactly one before counting anything
(`AIProvidersPage.isolate_section()` is this project's implementation). Do **not** try to
scope off the header locator, and do not "fix" it by adding a second testid to the root —
isolation is the honest shape, because the content genuinely is not inside the handle.

## Related

Same page also renders the default value as **plain untestable text in the collapsed
summary**, moving it into a real `role="combobox"` only on expand — so "read the selector"
and "the section is collapsed" are mutually exclusive states.

Related: [[creating_a_config_can_silently_become_the_default]]
