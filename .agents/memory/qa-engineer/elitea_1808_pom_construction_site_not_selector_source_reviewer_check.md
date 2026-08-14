---
name: ELITEA-1808 POM check — construction site, not selector source
description: Reviewing for "locators only in page-object methods" — the compliance test is where page.locator()/.format() executes, not whether the format string traces back to a page-object class constant. A class-level dynamic-testid constant with zero page-object-method consumers is the tell.
type: feedback
---

## What happened (PR #643, ELITEA-1808 reviewer pass)

`test_artifacts_create_bucket_upload_file.py:280-283` did this in the SPEC file:

```python
tree_item = page.locator(
    artifacts_page.ARTIFACTS_TREE_ITEM.format(FILE_NAME)
)
tree_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
```

`ARTIFACTS_TREE_ITEM` is a real, correctly-placed page-object class constant
(`artifacts_page.py:112`, `'[data-testid="artifacts-tree-item-{}"]'`) — declared
at class level, testid-based, looks compliant on a skim. But `.agents/testing.md`
§ Locator policy and `.claude/rules/page-objects.md` both ban this shape anyway:
*"never construct a locator inside a method body ... and never in spec files."*
The rule gates the **construction site** (where `page.locator(...)` /
`.format(...)` actually executes), not whether the underlying selector string is
testid-based or where the format-string constant lives.

## The check that catches it

Don't just verify a dynamic-testid constant is declared at class level in the
page object — that's necessary but not sufficient. Also count its **consumers**:

```bash
grep -n "CONSTANT_NAME" automation/pages/*.py automation/tests/**/*.py
```

If the only call site outside its own declaration is inside a `test_*.py` file
(or any spec file), that's the violation — a page-object method should wrap it
instead. In this PR, `ARTIFACTS_TREE_ITEM` had exactly ONE consumer in the whole
diff (the test file itself), unlike its correctly-scoped siblings `BUCKET_ROW`
and `BUCKET_MENU_BUTTON`, each consumed only inside a page-object method
(`wait_for_bucket_in_list()` / `open_bucket_menu()`).

## Why this is worth a standing check

A reviewer scanning only for "is there a raw CSS/XPath string in the test file"
will miss this — the string itself (`artifacts_page.ARTIFACTS_TREE_ITEM`) reads
as a page-object reference. The violation is structural (which file calls
`page.locator()`), not lexical (what the selector string looks like). Grep for
every dynamic-testid class constant added in a diff and count its call sites
across BOTH the page object and the spec file — a constant with a spec-file-only
consumer is the class of bug to flag, every time, regardless of how "compliant"
the constant's own declaration looks.

Filed as [Important] in the PR #643 review comment; recommended fix: add a
`wait_for_tree_item(item_path, timeout=...)` page-object method mirroring
`wait_for_bucket_in_list()`'s shape.
