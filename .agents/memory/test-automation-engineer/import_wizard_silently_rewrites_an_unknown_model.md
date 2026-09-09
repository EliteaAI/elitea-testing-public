---
name: Import wizard silently rewrites an unknown model to items[0]
description: A stale model literal in an import fixture yields a green wizard and a wrong agent; derive from the live catalog and pick items[1].
type: feedback
aliases: [import wizard model fallback, getDefaultModel, items[0] fallback, stale model literal, model catalog turnover]
tags: [area/agents, type/data-drift]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

`EliteaAI/EliteaUI src/[fsd]/entities/import-wizard/lib/helpers/importWizardModels.helpers.js:4-13`
(`getDefaultModel`) matches the imported file's `model_name` against the project's
model catalog. **If it does not match, it substitutes `modelsList[0]?.name || ''`
— with no toast and no error.** The import succeeds, the wizard looks healthy, and
the created agent is configured with a model the file never named.

So a hardcoded model literal in an import fixture is a time bomb: it does not fail
when it goes stale, it produces a *wrong* agent and a confusing red at whatever
assertion happens to read the model. ELITEA-1901 (board #2083) failed exactly this
way when the DEV catalog dropped every OpenAI entry, `gpt-5.2` included.

## The fix, and the one detail that matters

Derive the fixture model at run time from the catalog the wizard itself reads —
`GET /configurations/models/{project_id}?include_shared=true`, wrapped as
`CredentialAPI.list_models(include_shared=True)` (`automation/api/client.py`).

**Pick `items[1]`, never `items[0]`.** `items[0]` IS the fallback value, so
expecting it makes the assertion pass whether carry-through worked or not — a
tautology that silently destroys the coverage. Guard `len(items) >= 2` (and that
the chosen model's `display_name` differs from `items[0]`'s); a project too small
to distinguish the two is a legitimate environment `blocked`, not something to
weaken around.

## Two field names, not interchangeable

- fixture frontmatter `model:` / API payload -> `items[i]["name"]`
  (`getDefaultModel` matches `m.name === model_name`)
- `model-selector-name` renders -> `display_name`, falling back to `name`
  (`LLMModelSelector.jsx:110,199`)

`gpt-5.2` / `"GPT-5.2"` being near-identical hid this distinction for months. For
most models the two strings differ substantially.
