---
name: Mechanical grep passes non-testid but spec-file locators still violate POM
description: The role-overrides.md reviewer mechanical grep only filters testid-vs-non-testid handles; it does NOT clear the separate "never construct a locator in a spec/test file" rule — both checks are required on every PR
type: feedback
---

## What happened

Reviewing PR #620 (ELITEA-1955), the PR description's self-check claimed
"Mechanical non-testid-handle grep on the full diff: 1 hit, compliant." An
independent re-run of the exact same grep command from the dispatch prompt
(`git diff <base>... | grep -nE '^[+].*(get_by_role|...|page\.locator|\.locator\(')`)
found **3 hits**, not 1. Two of the three were raw `.locator()` calls
constructed directly inside the test/spec file
(`test_pipeline_mcp_node_empty_toolkit_before_attach.py:110,113`):

```python
assert popper.locator(pipeline_page.TOOLKIT_SEARCH_INPUT_SELECTOR).count() > 0
assert popper.locator('[data-testid="toolkit-menu-item"]').count() > 0
```

## Why the implementer's self-check missed it

`.agents/role-overrides.md` § Reviewer slot defines the mechanical grep's
COMPLIANT filter narrowly: "a hit is COMPLIANT only if the line contains a
literal `[data-testid=` selector OR references an UPPER_CASE class constant
whose class-level definition is a `[data-testid=` string/template." Both
hits above satisfy that — one is a literal `[data-testid="..."]`, the other
references `TOOLKIT_SEARCH_INPUT_SELECTOR`, a real UPPER_CASE class constant
whose definition IS a `[data-testid=` string. Applying ONLY that filter, an
implementer's self-check will wave both hits through as "compliant" — which
is exactly what happened (the PR claimed 1 hit, the constant-in-page-object
one from inside `select_mcp_in_popper()`, and silently missed that 2 more
hits exist in the test file itself).

## The gap

That mechanical-grep filter answers ONE question: "is this a testid-based
handle or a raw CSS/role/text handle?" It does NOT answer a second,
independent question: "is this locator constructed in the right layer?"
That second question is governed by a separate, unconditional rule stated at
FOUR levels in this project — CLAUDE.md (top-level, override-all): "Locators
live only as page-object class fields — never inside methods or specs.";
`.agents/testing.md` § Locator policy: "...and never in spec files.";
`.claude/rules/page-objects.md`: "Locators live only as class-level fields
on page objects — never constructed inside method bodies, never in
test/spec files."; `.claude/rules/ui-tests.md` § Common Anti-Patterns:
`page.locator('input').fill("Test")` in a test is explicitly "BAD - breaks
abstraction" — no testid carve-out anywhere in any of the four.

A hit can pass the narrow testid-vs-non-testid filter and still be a real,
blocking POM-discipline violation if it lives in a spec file.

## The fix (for review going forward)

Run BOTH checks, not just the mechanical grep:
1. The mechanical grep (testid vs non-testid) — per role-overrides.md.
2. A location check on every hit: does this line live in `automation/pages/`
   (compliant location) or `automation/tests/` (never compliant, regardless
   of what the selector looks like)? `grep -l` the hit's file path is enough
   — any hit inside `automation/tests/*.py` blocks, full stop.

The correct remediation is to wrap the selector in a page-object method
(e.g. `PipelineDetailPage.get_popper_menu_item_count(popper)`) so the test
calls a page-object method instead of constructing `.locator()` itself — the
same PR's own `select_mcp_in_popper()` demonstrates the compliant shape
(`self.TOOLKIT_SEARCH_INPUT_SELECTOR` used *inside* the page object).

## Recurrence — PR #670/ELITEA-1866 (round 2, 2026-07-20)

Third confirmed instance of this exact shape (after PR #620 above and
PR #643/ELITEA-1808, entry `elitea_1808_pom_construction_site_not_selector_source_reviewer_check.md`).
`test_toolkit_creation_create_bucket_verify_list_files.py:529,534,538`
called `page.locator(ToolkitTestSettingsPage.TOOL_OPTION_ANY_SELECTOR)` /
`page.locator(ToolkitTestSettingsPage.TOOL_OPTION.format(TOOL_KEY))`
directly in the test body for steps 27-28. Notably this PR had ALREADY been
through one full CHANGES_REQUESTED round (3 non-testid `get_by_role` findings,
all correctly fixed) — round 1's own mechanical grep listed these exact 3
lines and correctly marked them "compliant" under the narrow testid filter,
but never ran the second (location) check, so the POM violation rode along
unflagged into round 2. Confirms this is a genuinely separate check that has
to be re-run on every pass, independent of how clean the testid-identity grep
comes back — a PR can be 100% testid-compliant and still fail POM
encapsulation.
