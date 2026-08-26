---
name: Pipeline Trigger restriction greys out instead of hiding (EL-6128)
description: Restricted trigger options are present-but-disabled, so name-list assertions no longer discriminate
type: project
aliases: [EL-6128, TriggerTypeSelector, trigger restricted, aria-disabled option]
tags: [area/pipelines, type/product-drift]
created: 2026-08-26
updated: 2026-08-26
---

## What changed

`TriggerTypeSelector.jsx`, EliteaAI/EliteaUI@cb70a64e + @15099206 + @07e0e9b1 (on `origin/main`
2026-08-24/25): restricted trigger options moved from `filter`ed-out (hidden) to `{...opt, disabled:true}`
(greyed out in place). Predicate widened to `hasInteractiveElements || hasDelegatedOauthToolkit`.

- Restricted: all 3 options present; `select-option-schedule` / `-webhook` carry `aria-disabled="true"`.
- Unrestricted: **no `aria-disabled` attribute at all** — absent, not `"false"`. Test "enabled" with
  `:not([aria-disabled="true"])`.
- Save-gating unchanged: restriction reads the last-SAVED YAML, not the live canvas.

## The reusable lesson

When a product moves a state from **presence** to **attribute**, every assertion written against the
presence list silently stops discriminating — the "restore" half of a lifecycle test becomes a no-op that
can never fail. Repairing such a test means asserting the *new* state axis on **both** sides of the cycle,
not just relaxing the failing assertion. ELITEA-2008's Step 8 was the concrete case.

Related: [[select_option_prefix_collides_with_selected_icon_testid]]
