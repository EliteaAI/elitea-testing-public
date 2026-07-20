---
name: POM discipline is a separate reviewer check from locator-identity
description: A testid-compliant page.locator(...) call constructed directly in a spec file still violates the "locators live only as page-object class fields" rule — two independent reviewer passes, not one
type: feedback
---

## What happened (ELITEA-1866, PR #670, round 2)

R1 fixed 3 non-testid locators (`get_by_role`) flagged by a mechanical grep
scoped to locator-*identity* (`get_by_role|get_by_label|...|page\.locator`
patterns, checked against whether the resolved selector uses
`[data-testid=`). That grep passed clean on R2's re-review — zero
non-testid hits.

But a **fresh** reviewer pass (not a repeat of R1's check) found a
different violation at the *same* 3-line span
(`test_toolkit_creation_create_bucket_verify_list_files.py:529,534,538`):
the test body called
`page.locator(ToolkitTestSettingsPage.TOOL_OPTION_ANY_SELECTOR)` /
`page.locator(ToolkitTestSettingsPage.TOOL_OPTION.format(TOOL_KEY))`
directly — reaching into *another* page object's class constant and
constructing the Locator inline, in the spec file, rather than through a
method on that page object.

This is **testid-compliant** (the constant itself resolves to a
`[data-testid=...]` template — that's why the identity grep missed it) but
**not POM-compliant** — `.claude/rules/page-objects.md` and
`.claude/rules/ui-tests.md` both separately require "locators live only as
page-object class fields — never inside methods or specs," independent of
whether the locator is testid-based.

## The generalizable lesson

**Locator-identity compliance (testid-only, no `get_by_role`/`get_by_label`/
CSS) and POM-discipline compliance (no raw `page.locator()` construction in
spec files, even from a compliant constant) are two separate checks.**
Passing one says nothing about the other. When self-checking after a
locator-identity-scoped fix, ALSO grep for any `page.locator(...)` /
`.locator(...)` call sitting directly in the test file — regardless of
whether the resolved selector is a `[data-testid=` template — and confirm
each one is a call to a page-object *method*, not an inline construction:

```bash
grep -n "page\.locator\|\.locator(" automation/tests/**/*.py
```

Any hit that isn't itself an attribute/method access on a page-object
instance (e.g. `test_settings.get_tool_option(x)`) is a POM-discipline
violation, even if the underlying template is 100% testid-compliant.

## The fix pattern

Add a thin Locator-returning wrapper method on the owning page object,
mirroring the existing `get_type_card(type_key)` / `get_param_field(field_key)`
style already established in this codebase — return the raw `Locator` (not
a pre-computed `int`) when the caller needs Playwright's auto-retrying
`expect(...).to_have_count(...)` / `expect(...).to_be_visible(...)` right
after a state change (e.g. a dropdown just opened), rather than a
`count_*()`-style int getter which evaluates once and doesn't retry.

## Where it lives

`automation/pages/toolkit_test_settings_page.py`: `get_tool_options()` /
`get_tool_option(tool_key)`, added round 2 of ELITEA-1866/PR #670.
