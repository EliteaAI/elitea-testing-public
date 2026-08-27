---
name: Prefix testid selector passes the locator grep
description: '[data-testid^="…"] prefix constants are compliant testid-only locating even though the mechanical grep rule names [data-testid=' 
type: feedback
aliases: [prefix selector, data-testid^=, sort icon count, SORT_ICON_PREFIX_SELECTOR]
tags: [area/review, type/locator-policy]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

`.agents/role-overrides.md` § Reviewer slot says a `page.locator(...)` hit is compliant
only if the line "contains a literal `[data-testid=` selector OR references an UPPER_CASE
class constant whose class-level definition is a `[data-testid=` string/template".

Read literally, a **prefix** constant fails it: `'[data-testid^="personal-token-sort-icon-"]'`
contains `[data-testid^=`, not `[data-testid=`. Blocking on that is wrong — the selector is
100% testid-based (it exists precisely to COUNT testids), and the shape has established
in-repo precedent as class-level UPPER_CASE constants:

- `toolkit_test_settings_page.py:95` `TOOL_OPTION_ANY_SELECTOR`
- `pipeline_detail_page.py:557 / 652 / 1185` (`*_PREFIX`, `*_ANY_SELECTOR`)
- `personal_tokens_page.py` `SORT_ICON_PREFIX_SELECTOR` (ELITEA-2279)

## The rule to apply

Compliant when **all** hold: the constant is class-level UPPER_CASE, its value is a
`[data-testid` selector (`=`, `^=`, or a `{}`-template), and the call site is a page-object
method (never a spec file). Anything anchoring on a class, role, or text still blocks.

Same reasoning for the state-filter shape `'[data-testid="x"][data-state="y"]'`, which
`.agents/testing.md` § Locator policy explicitly sanctions.

Related: [[579_claim_check_component_already_forwards_testid_prop]]
