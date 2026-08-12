---
name: wait_for_timeout copied despite AFS warning
description: Implementer copied skill_form_page.py's wait_for_timeout tech debt into a new page object even though the AFS explicitly warned not to
type: feedback
---

## What happened (ELITEA-2272, PR #1169)

The AFS for ELITEA-2272 (Project Context character limit) explicitly cited
`skill_form_page.py`'s `fill_instructions()`/`select_existing_tag()` as a
CodeMirror-clearing pattern to mirror — then added an explicit caveat in its
own § Automation Hints: that file uses several `wait_for_timeout` calls,
that is pre-existing tech debt, and "don't carry the timeout habit over
either." The implementer copied the clearing pattern (click → select_text →
Backspace) correctly, but ALSO copied three `wait_for_timeout` calls
(100ms after Backspace, 300ms after clipboard-paste, 200ms after the extra
keystroke) into the new `automation/pages/project_context_page.py` — the
exact anti-pattern the AFS named and warned against, and a direct violation
of `.agents/conventions.md`'s hard rule "No `sleep`/`waitForTimeout` —
framework waits only."

## Lesson for review

When an AFS's Automation Hints section calls out a *specific* anti-pattern
in a precedent file ("mirror X's structure but not its timeout habit"),
treat that as a **targeted grep target** during review — search the new
page object for the literal name of the thing the AFS warned against
(`wait_for_timeout`), not just the general mechanical-handle grep. A
precedent citation that includes an explicit caveat is a strong signal the
implementer is at elevated risk of copying the caveated part too.

## Lesson for implementers

A `text_content()` / `.select_text()` read immediately after a paste or
keystroke with no framework wait is a real race (CodeMirror updates its DOM
async). The fix is a **condition wait** — e.g. poll
`expect(locator).to_have_text(...)` or a small retry loop on the read value
— never a fixed sleep, even when the precedent file already contains one.
