---
name: A bare `x in y` assertion admits a vacuous pass when `x` is an empty string
description: Python's `"" in anything` is always True — a substring/containment assertion used to check "does the captured value match" silently passes if the captured value is ever empty (rendering race, regression, wrong selector), hiding exactly the defect it exists to catch.
type: feedback
---

Reviewer finding on GAP-073 (PR #1061): Step 4 asserted
`detail_title in captured_row_text` to check that the user-detail title
(a testid's `.text_content()`) matched the leaderboard row that was
clicked. If `detail_title` is ever `""` — a rendering race, or a regression
that mounts the title node before the backing data resolves — the check
passes regardless of `captured_row_text`'s actual content, because Python's
`in` operator on an empty left-hand string is unconditionally `True`. The
exact defect the assertion was written to catch (title doesn't match the
clicked row) would then ship silently green.

**Fix:** guard any `x in y` / `x.startswith(y)`-style containment or
matching assertion with an explicit truthiness check on `x` FIRST, whenever
`x` is read from a live DOM node rather than a hardcoded literal:

```python
detail_title = analytics_page.user_detail_title_text()
assert detail_title, "title should be non-empty — an empty value would make the substring check below pass vacuously"
assert detail_title in captured_row_text, f"..."
```

**Generalize:** any test that reads a dynamic string from the page and then
uses it as the CONTAINED side of an `in` check (not the container side) is
at risk of this same vacuous-pass class. `x in y` is safe when `y` might be
empty (an empty container legitimately contains nothing); it is NOT safe
when `x` might be empty, because the empty string is a subset of every
string including `y == ""` itself. Worth a self-review pass on any existing
spec using this pattern for a captured/dynamic value.
