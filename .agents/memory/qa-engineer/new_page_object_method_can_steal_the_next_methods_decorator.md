---
name: New page-object method can steal the next method's decorator
description: An insertion made just above an existing decorated method lands BETWEEN its decorator and its def — check the seam, not just the added lines
type: feedback
aliases: [stolen decorator, action decorator seam, page object insertion point, double @action]
tags: [area/page-objects, type/review-check]
created: 2026-08-23
updated: 2026-08-23
---

## The trap

A unified diff of an insertion into a large page object shows the added block with
a plausible context line above it. When that context line is a **decorator**
(`@action("...")`) whose `def` is BELOW the insertion point, the new block lands
*inside* the decorator/def seam. Result, invisible in the added lines alone:

- the FIRST new method gets double-decorated (`@action("Edit file preview content")`
  stacked on its own `@action(...)`) — wrong log/allure name;
- the PRE-EXISTING method silently loses its decorator, so its callers lose
  failure-screenshot capture and step logging. On a shared-caller file that is a
  non-additive regression (Hard Rules → 3) affecting specs not in the diff.

Caught on PR #1688 (`automation/pages/artifacts_page.py`,
`click_file_preview_discard` / `edit_file_preview_content`). Nothing fails at
runtime — `functools.wraps` keeps `inspect.signature` working — so no gate sees it.

## Review check

For every new method added to an existing page object, read the file at the
insertion seam (`sed -n '<start>,<end>p'`), not only the `+` lines. Fast grep:

```bash
git diff <base>...HEAD -- automation/pages/ | grep -B2 '^+.*@action' 
# and: confirm every pre-existing `def` adjacent to the hunk still owns its decorator
python3 - <<'PY'   # or simply eyeball: two @action lines with no def between them
PY
```

Two `@action` lines with no `def` between them is always the signature of this bug.

Related: [[afs_claims_need_full_sweep_and_grep]]
