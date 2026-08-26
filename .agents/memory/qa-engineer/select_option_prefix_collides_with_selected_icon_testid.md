---
name: select-option-* enumeration is poisoned by select-option-selected-icon
description: Enumerating MUI listbox options by the select-option- prefix returns a spurious empty entry for the selected option
type: feedback
aliases: [select-option-selected-icon, SELECT_OPTION_PREFIX, empty option in dropdown, get_open_listbox_option_names]
tags: [area/pipelines, area/locators, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The collision

`EliteaAI/EliteaUI@b0a7d61a` (2026-08-24, on `automation/testids` **only**, not on `main`) added
`data-testid="select-option-selected-icon"` to the ✓ `ListItemIcon` *inside* the currently-selected
`MenuItem` (`src/[fsd]/shared/ui/select/SingleSelectMenuItem.jsx:141`).

`PipelineDetailPage.SELECT_OPTION_PREFIX = '[data-testid^="select-option-"]'`
(`pages/pipeline_detail_page.py:1580`) matches it, so `get_open_listbox_option_names()` returns an extra
empty string for whichever option is selected:

```
localhost, Trigger dropdown baseline: ['Chat Message', '', 'Schedule', 'Webhook']
```

Confirmed live 2026-08-26 (ELITEA-2008 triage). **Localhost-only today** — DEV/`main` doesn't have the
testid, which is exactly why a DEV GHA failure and the local reproduction showed *different* symptoms.
It breaks DEV the moment a human cherry-picks that commit to `main`.

## What it costs you

Triaging a red test, the local repro disagreeing with CI is the confusing part — don't assume the local
symptom IS the CI symptom. Root fix: rename the icon testid out of the `select-option-` namespace. Cheap
hardening: enumerate `li[data-testid^="select-option-"]` / `[role="option"]…`. Best defence in a new
spec: assert **per-value** handles (`select-option-schedule`) instead of enumerating the family.

Same commit also added `data-selected` on options — likewise `automation/testids`-only, so it is a trap
for any test that must be green on dev.elitea.ai.

Related: [[trigger_restriction_greys_out_instead_of_hiding]]
