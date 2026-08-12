---
name: Mechanical grep misses JS-string raw selectors
description: The standard reviewer grep (get_by_*/page.locator/query_selector) does not catch document.querySelector('[data-testid=...]') embedded inside wait_for_function/evaluate JS payloads
type: project
---

## What happened (ELITEA-1898, PR #1289)

The reviewer's mandated mechanical grep
(`get_by_role|get_by_label|get_by_text|get_by_placeholder|get_by_title|get_by_alt_text|get_by_test_id|query_selector|page\.locator|\.locator\(`)
matches **Python-syntax** Playwright calls. It does NOT match
`document.querySelector('[data-testid="..."]')` written as **JavaScript**
inside a triple-quoted string passed to `page.wait_for_function(...)` /
`page.evaluate(...)`. The PR's own "0 hits" grep output was accurate for
what it checks, yet the test file still duplicated two testids
(`agent-version-selector-trigger`, `copy-version-id`) that already exist as
`LocatorDescriptor` fields on `AgentDetailPage`, by re-typing them as raw
CSS strings inside a `new_page.wait_for_function(...)` predicate in the
SPEC file — a real "no raw selectors in spec files / one testid in exactly
one file" violation the grep is blind to.

Context: this exact raw-`document.querySelector` pattern is established,
legitimate PAGE-OBJECT-internal precedent (`agent_detail_page.py`'s
`confirm_new_version()` / `select_version_by_name()` — a three-way
trigger-text/version-id/URL convergence wait that plain Playwright
locator polling can't express well). That precedent legitimizes the
*technique* — it does NOT legitimize reimplementing it ad hoc inside a
TEST file instead of adding/reusing a page-object method. The fix is
always "make it a page-object method the test calls," never "leave the
JS string in the spec because a similar JS string exists elsewhere."

## Reviewer action item

When a diff's `wait_for_function`/`evaluate` calls contain multi-line JS
string literals, grep those payloads separately for
`data-testid=` / `querySelector` — the standard grep will silently pass
a real violation.

## Refinement (ELITEA-2051, PR #1339): the precedent has a boundary — condition count

`PipelineDetailPage.confirm_fork_complete()` (a page-object method, not a
spec file — so it superficially matches the "legitimate PAGE-OBJECT-internal
precedent" carve-out above) added `page.wait_for_function()` +
`document.querySelector('[data-testid="copy-id"]')` to poll for the
post-navigation `copy-id` text to settle to the new pipeline's id — even
though `copy_id_button` already exists as a `LocatorDescriptor` field on
the SAME class.

The carve-out does NOT cover this case: `agent_detail_page.py`'s cited
precedent is a genuine **three-way convergence** (trigger-text + version-id
+ URL) that plain locator polling can't express in one wait. This new
instance is a **single condition** (one field's text equals one expected
string) — textbook `expect(locator).to_have_text(expected, timeout=...)`
territory. Verdict: CHANGES_REQUESTED — raw JS is legitimate only for the
genuinely-multi-condition case; a single-condition wait against an existing
`LocatorDescriptor` field must use Playwright's native polling assertion
instead of re-deriving the same testid as a fresh JS string.

**Reviewer test going forward:** when a `wait_for_function`/`evaluate` hit
also has a class-level `LocatorDescriptor` field for the same testid,
ask "does this predicate combine 2+ independent conditions?" — one
condition → block, native `expect()` replaces it; 2+ genuinely independent
conditions → the established precedent applies, approve.
