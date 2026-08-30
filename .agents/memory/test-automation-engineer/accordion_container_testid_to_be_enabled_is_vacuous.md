---
name: to_be_enabled() on a container testid asserts nothing
description: Playwright treats any non-form element without aria-disabled as enabled — so "section is enabled" on an accordion/div div is a silent no-op assertion
type: feedback
aliases: [vacuous enabled assertion, accordion enabled, to_be_enabled div, section container testid]
tags: [area/assertions, type/test-quality]
created: 2026-08-30
updated: 2026-08-30
---

## The trap

Playwright's `to_be_enabled()` only ever reports "disabled" for a form control
carrying `disabled`, or for any element carrying `aria-disabled="true"`. On a plain
`<div>` / `<section>` container it is **always true** — it passes whether or not the
UI is interactive, and whether or not the section even rendered its controls.

An AFS row saying *"assert `<section>-section` is enabled"* is therefore a silent
no-op. It looks like an interactivity check in review and in Allure.

## What to do instead

Assert a real interactive control inside the section:

* a `<button>` / `<input>` — genuinely honours `disabled`;
* a **MUI select trigger** (`role=combobox`) — MUI sets `aria-disabled` on it, which
  `to_be_enabled()` does read, so this IS a real check
  (e.g. `ai-providers-section-llms-default-selector-combobox`);
* if the section owns no testid-bearing control, assert **visible**, and say in the
  docstring that no interactivity claim is being made — do not dress a visibility
  check as an enabled check.

If the only editable control has no testid, that is `add-data-testid` work, not a
reason to fall back to the container (ELITEA-2245 added
`project-general-edit-icon-button` for exactly this).

## Bonus fact

`BasicAccordion` (EliteaUI) defaults `defaultExpanded = true`, so accordion
contents are mounted on load — reaching a control inside one needs no expand click.

Related: [[vite_can_serve_stale_transform_after_testid_add]]
