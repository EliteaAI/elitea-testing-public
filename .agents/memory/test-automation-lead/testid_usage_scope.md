---
name: Testid-usage extraction scope
description: Where to grep and how far to trace when answering "which testids does this case touch" — the two questions the mechanical checks keep getting scoped too narrowly
type: feedback
---

## Rule A — the locator-policy grep is scoped to `automation/`, whole diff

Not `pages/` + `tests/` (role-overrides names those as examples, not a whitelist)
and never "the file where the last finding lived". `components/`, `fixtures/`,
`utils/` are exactly where a new raw handle hides, because they escape page-object
scrutiny. Two live escapes: a raw `page.locator('[role="dialog"]…')` inside a new
`components/mui.py::Dialog.wait_for_visible()`, and an inline
`self.page.get_by_test_id("artifacts-file-row").filter(...)` inside a new
`ArtifactsPage.get_file_row_text()` — the latter survived FOUR review rounds
because R2's reviewer ran the exactly-correct pattern **against the spec file only**.

- When auditing a reviewer's grep evidence, check **which files they say they
  grepped**, not just which patterns.
- Classify each hit as new-vs-existing code: `git show <base>:<path> | grep
  <method-name>` — absent in base means wholly new, and new code gets zero benefit
  of surrounding-file precedent, whatever its docstring claims. A docstring that
  cites an existing bad pattern as its own justification is a *stronger* tell than
  an unexplained raw handle.

## Rule B — "is this testid used" is a call-path question, not a presence question

Grep the `LocatorDescriptor` **field name followed by `.`** (an actual invocation)
across the whole diff and the test's reachable helpers — not `<field> =` (the
declaration) and not the testid string.

- **Zero hits anywhere** = orphan = solo-FAIL.
- **Wired into a real method the test never calls** = also solo-FAIL since the #511
  ruling (no carve-out for reusable scaffolding, parameterized methods reused by
  siblings with other args, or plausible future use).
- **`data-testid={cond ? A : B}` disambiguation pairs (#277)** are a *distinct,
  still-open* axis — never cite #511 to fail one.
- An AFS naming a *pair* of elements in a gap note does not mean both need testids
  if the case only exercises one.

## Rule C — closure-record testid sets are traced, never summarized

Do not start from "which testids does the PR/AFS narrative mention", and never
reuse a sibling test's known handle family. Walk the NEW test's own call sites, one
hop into each page-object method body, and count `wait_for(...)` targets buried
inside helpers as real dependencies — methods reached indirectly (open a shared
3-dot menu before clicking a named menuitem; hover a card before clicking
open-in-new-tab) are exactly where a narrative-driven trace stops short.

**Script it, scoped per file.** A global `field -> testid` dict silently loses
mappings when two page objects both define `save_button`; build the map fresh
**inside** the per-file loop, parse with `ast`, and also catch UPPER_CASE
`'[data-testid="…'` template constants plus inline `get_by_test_id("…")` legacy
calls. Treat the output as a strong candidate set to spot-check, not truth.

A reviewer finding that is purely a PR-description evidence gap ("no code change
required") can be closed by the orchestrator's own `gh pr edit` instead of a full
redispatch — but that never substitutes for the independent gate re-run.

## Rule D — runtime-composed testids need FOUR checks, not two

For `${id}-menu-button`-style composition, check independently: call-site fragment
on `main`; call-site fragment on `automation/testids`; composition mechanism on
`main`; composition mechanism on `automation/testids`. It is NOT safe to assume the
shared mechanism is settled — `SingleSelect.jsx`'s `${dataTestId}-combobox`
derivation was itself testids-only, introduced by an unrelated case. When absent
from main, resolve its own commit via
`git log origin/main..origin/automation/testids -- <file>`.

## Seen 8×

- #70 / ELITEA-1950 / PR #531 — raw locator in `components/mui.py`, grep never ran there; reviewer claimed "no raw non-testid locators".
- #212 / ELITEA-1808 / PR #643 — inline `get_by_test_id` in a new page-object method, missed by 4 rounds (spec-file-scoped grep).
- #75 / ELITEA-1888 / PR #533 — 2 of 6 new testids declared as fields, never called.
- …plus 5 earlier occurrence(s) — full per-case detail in the source entries below.

See also: locator_grep_must_cover_components_dir.md ·
inline_get_by_test_id_in_new_page_object_method_missed_by_file_scoped_reviewer_grep.md ·
testid_reference_check_must_include_page_object_fields.md ·
scoping_testid_usage_extraction_per_file.md · shared_caller_enumeration_gap.md ·
orphan_testid_vs_wired_but_uninvoked.md ·
testid_enumeration_copied_from_sibling_handle_family.md ·
runtime_composed_testid_mechanism_can_itself_be_testids_only.md ·
canon_ruling_511_referenced_means_on_test_code_path.md
