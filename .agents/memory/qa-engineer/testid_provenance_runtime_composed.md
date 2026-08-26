---
name: Testid provenance — runtime-composed testids defeat a bare-string grep
description: Verify composed testids (toolkit-field-<key>-radio-<slug>) by DIFFING the component file between refs, not by grepping the rendered string
type: feedback
aliases: [provenance row, on-main check, composed testid, toolkit-field-auth-radio, closure record grep]
tags: [area/locators, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

AFS PROVENANCE rows and closure-record greps search for the *rendered* testid
string (`toolkit-field-auth-radio-delegated`). Schema-driven Elitea testids are
built at runtime:

- `ToolSection.jsx:290` → `testId={`toolkit-field-${sectionKey}-radio`}`
- `RadioButtonGroup.jsx:37` → `` `${testId}-${item.value.toLowerCase()}` ``
- `ToolBaseProperty.jsx:390-391` → `` `toolkit-field-${k}-checkbox{,-field}` ``

`git grep 'toolkit-field-auth-radio-'` returns **no** on `origin/main` AND on
`origin/automation/testids` — the string exists nowhere in source. Both stages of
`workflow.md`'s closure-record grep are blind to it (the file's own caveat).

## The check that works

```bash
git --no-pager diff origin/main origin/automation/testids -- <component file>
```
Empty diff ⇒ the testid renders identically on main ⇒ **already promotable**.

## Why it matters (observed 2026-08-24, ELITEA-1981/1982 review)

Both AFS files carried `on automation/testids only (…@c8d5c6af, ELITEA-1962) —
awaiting human cherry-pick` for the auth radios and the
`auto_refresh_token` checkbox. The files were **byte-identical on main** — the
UI team had landed equivalent wiring independently. A stale row like this
understates promotability in the closure record (the #19 failure class, mirrored).

Corollary: a testid commit sitting only on `automation/testids` does NOT imply
the testid is absent from `main` — check the rendering site, not the commit.

Related: [[credential_form_blur_commits_value]]
