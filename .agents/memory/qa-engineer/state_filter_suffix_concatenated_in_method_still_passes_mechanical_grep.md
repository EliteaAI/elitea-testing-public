---
name: data-* state-filter suffix concatenated in a method body still passes the mechanical grep
description: a testid template + raw `[data-selected="true"]` literal concatenated at the call site references a compliant class constant, so the reviewer's literal grep rule waves it through — even though testing.md's own worked example shows the combined testid+state selector as ONE class-level constant
type: feedback
---

Seen on ELITEA-2352 (PR #1213, `AgentHubPage.is_category_filter_chip_selected`):

```python
selected_chip = self.page.locator(
    self.CATEGORY_FILTER_CHIP.format(_slugify_category(category_label)) + '[data-selected="true"]'
)
```

`.agents/testing.md` § Locator policy's own worked example for a testid+state
combo is a SINGLE class-level constant
(`'[data-testid="x"][data-expanded="false"]'`), not a runtime concatenation of
a class template + a literal defined only in the method body. Strictly, the
literal `'[data-selected="true"]'` is a locator fragment invented inside a
method — the same shape the "never construct a locator inside a method body"
rule targets — but `.agents/role-overrides.md`'s reviewer mechanical-grep
check ("a hit is COMPLIANT ... OR references an UPPER_CASE class constant
whose class-level definition is a `[data-testid=` string/template — one-hop
check") is satisfied here because the line DOES reference `CATEGORY_FILTER_CHIP`.
The grep's one-hop check doesn't verify the ENTIRE selector string traces to
class-level text, only that *a* class constant is referenced somewhere on the
line.

**Verdict reached:** not blocking — the appended fragment is the
canonically-sanctioned data-* state-filter shape (not a new raw/role/text
handle, no coverage-metric corruption), and the implementer declared the
concatenation reasoning explicitly (single-sourcing the testid to avoid two
templates drifting). Treated as a declared-improvisation nit, not a violation.

**For the next reviewer:** if you want the letter of testing.md's own example
followed exactly, ask for a combined class constant instead
(`CATEGORY_FILTER_CHIP_SELECTED = CATEGORY_FILTER_CHIP + '[data-selected="true"]'`)
— but don't block solely on the mechanical grep's silence here; it isn't
built to catch this shape.
