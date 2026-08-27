---
name: Grep the page object before building a locator in a spec
description: SecretsPage already owned get_row_names() and toast_alert_with_severity() — both were re-implemented inline and blocked at review
type: feedback
aliases: [spec locator, duplicate accessor, get_row_names, toast_alert_with_severity, hard don'ts locators]
tags: [area/implementation, type/anti-pattern]
created: 2026-08-28
updated: 2026-08-28
---

## What happened

ELITEA-2349 built two locators in the spec file — a severity-scoped toast
(`page.locator(SecretsPage.TOAST_ALERT_SEVERITY.format("error"))`) and a
row-name read (`secret_row.locator(SECRET_NAME_CELL_SELECTOR).all_inner_texts()`).
Both accessors **already existed** on `SecretsPage`
(`toast_alert_with_severity()`, `get_row_names()`), so the violation of
`.agents/conventions.md` § Hard don'ts ("never build locators inside methods or
spec files") was also pure duplication. `CHANGES_REQUESTED`.

## The habit

Referencing a page-object CONSTANT from a spec (`secrets_page.SOME_SELECTOR`) is
the tell: a class constant is an ingredient for a page-object method, never for a
spec. When you reach for one, grep the page object for the method that already
uses it:

```bash
grep -n "SOME_SELECTOR" automation/pages/<page>.py
```

`SecretsPage` is ~1000 lines with ~40 accessors — the one you need is usually
there.
