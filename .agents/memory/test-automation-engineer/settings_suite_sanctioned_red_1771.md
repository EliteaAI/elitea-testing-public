---
name: Settings sidebar spec carries a sanctioned-RED for #1771
description: tests/ui/settings/test_settings_sidebar_item_navigation.py fails by design — soft-assert on open defect #1771; never chase it as a regression
type: project
aliases: [settings sidebar red, 1771, disableUnderline warning, settings-w01 sanctioned red]
tags: [area/settings, type/known-defect]
created: 2026-08-26
updated: 2026-08-26
---

## The fact

`tests/ui/settings/test_settings_sidebar_item_navigation.py::TestSettingsSidebarItemNavigation::test_settings_sidebar_item_navigation`
is **merged on `automation/base` as a sanctioned-RED** (landed by settings-w01,
PR #1779). It fails deterministically with:

```
Failed: Test flow completed and all functional assertions passed, but
known-defect soft failures were recorded:
Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1771:
disableUnderline console warning(s) on 'ai-personality' click: 1 occurrence(s)
```

Per `.agents/testing.md` § Merge gate, an `expect.soft` / `soft_failures`
aggregation IS a pytest FAILED outcome — so this spec shows up red in any
blast-radius or suite-wide run that includes `tests/ui/settings/`.

## Why it matters to a gate

It is **not a regression** and must never be reported as one. Verify the same
way each time: the spec is absent from the batch diff
(`git diff origin/automation/base...<trunk> --name-only | grep <spec>` → 0) and
the failure text names the `Known defect` URL. Flips green only when #1771 ships.

Related: [[per_testid_reads_cannot_prove_dom_order]]
