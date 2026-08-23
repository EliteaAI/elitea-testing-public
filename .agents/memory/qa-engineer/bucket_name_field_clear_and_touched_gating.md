---
name: New-Bucket name field — clearing it, and when validation text appears
description: fill_bucket_name("") never clears the field, and "Name is required" only renders after a blur
type: feedback
aliases: [clear bucket name, Name is required, formik touched, empty bucket name, disabled Save]
tags: [area/artifacts, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## Clearing the field

`ArtifactsPage.fill_bucket_name("")` does **not** empty the Name field: it clicks,
`select_text()`s, then calls `Locator.type("")`, and typing an empty string is a silent
no-op — the original text stays (selected, but present). To clear:
`click()` → `select_text()` → `press("Delete")`. Same shape applies to
`set_retention_value("")`.

## When the validation message appears

`CreateBucket.jsx:243-244` gates both `error` and `helperText` on `formik.touched.name`,
which Formik sets on **blur or submit only**. With an empty name the submit path is
unreachable too, because Save is `disabled` while `!formik.values.name`. So:

- right after clearing: `artifacts-bucket-name-helper-text` `count() == 0`,
  `aria-invalid="false"`, Save **disabled** (its `click()` raises Playwright
  `TimeoutError: element is not enabled`);
- after one `press("Tab")`: helper text `"Name is required"`, `aria-invalid="true"`.

Assert `count() == 0` for the pre-blur state — the node is absent, not hidden.
Note the asymmetry with a *non-empty but invalid* name (ELITEA-1811): there Save stays
**enabled** and the click is what sets `touched`.

Filed as case-text CLARIFICATION EliteaAI/elitea-testing-public#1680 (ELITEA-1813).

Related: [[no_playwright_mcp_use_sync_playwright_script]]
