---
name: DEV model catalog turnover — gpt-5.2/5.4/5.4-mini removed
description: settings.default_model_name="gpt-5.2" is stale; DEV project catalogs no longer list it, so imports/selects fall back or time out
type: project
aliases: [gpt-5.2, default_model_name, model catalog, model selector fallback, GPT-5.2 missing]
tags: [area/models, type/environment]
created: 2026-09-09
updated: 2026-09-09
---

## The fact

As of 2026-09-09 the DEV backend's LLM catalog no longer offers `gpt-5.2`
(nor `gpt-5.4` / `gpt-5.4-mini`). Verified live via the exact endpoint the UI
itself calls, `GET {api}/configurations/models/{project}?include_shared=true`:

| project | n | contains gpt-5.2 | items[0] |
|---|---|---|---|
| 399 (Private, main test project) | 8 | **no** | `eu.anthropic.claude-sonnet-4-5-…` → "Anthropic Claude 4.5 Sonnet" |
| 471 (team) | 13 | **no** | same |
| 400 | 8 | **no** | same |
| 1 (Public/global) | 24 | yes | same |

`gpt-5.2` survives only in the global project 1 and is NOT surfaced into the
working projects even with `include_shared=true`. Confirmed in the live chat
composer dropdown too (8 options, no GPT-5.2).

`automation/config.py:278` still says `default_model_name = "gpt-5.2"`, and
~5 specs hardcode the `"GPT-5.2"` display literal.

## Why it bites differently in different places

`../EliteaUI/src/[fsd]/entities/import-wizard/lib/helpers/importWizardModels.helpers.js:4-13`
(`getDefaultModel`) — if the requested `model_name` is not in the project's
list the product **silently substitutes `modelsList[0].name`**. So:

- **Import flows** go green-path but land on the wrong model → assertion
  failure ("got: 'Anthropic Claude 4.5 Sonnet'"). Board #2083.
- **Explicit `select_model("GPT-5.2")` flows** simply time out — the option
  does not exist. Board #2112 (`test_image_creation`).

## The trap when repairing

Do NOT pick `items[0]` as the expected model in an import test: that is
exactly what the fallback produces, so a genuinely broken carry-through would
still pass. Pick a model that is provably **not** `items[0]`.

Related: [[project_briefing]]
