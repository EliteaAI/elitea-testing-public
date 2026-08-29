---
name: AI-provider form schema remount and select-option traps
description: Four traps on Settings -> AI Providers that each cost a full run — schema remount wiping typed values, the select-option prefix matching the selected-icon, whole-page card counts, and no-op default re-selection.
type: feedback
aliases: [ai providers, ai-provider form, pgvector, embedding model, select-option, isolate_section, wait_for_schema_field]
tags: [area/settings, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## `wait_for_form()` settles on the PRE-schema shell

`AiProviderFormPage.wait_for_form()` waits for `toolkit-field-label-input`, which the
create form renders BEFORE `GET /configurations/available/?section=…` resolves. The
schema-driven re-render that follows **wipes anything typed in the gap** — and the wipe
can land AFTER your assertions pass. Measured on ELITEA-2399: Display Name typed, read
back correctly, `Save` observed ENABLED — and `Save` was still disabled 10 s later at
the click, because the label had been cleared in between.

Fix: `AiProviderFormPage.wait_for_schema_field(field_key)` — wait for a field that only
exists in the schema render (`connection_string` for pgvector, `name` for
llm_model/embedding_model). Then nothing typed after can be wiped.

## `[data-testid^="select-option-"]` also matches the selected-icon

The shared `SingleSelect` renders a checkmark with `data-testid="select-option-selected-icon"`
inside the SELECTED option. A 2-option dropdown with one selected resolves to **three**
elements on the bare prefix. Exclude it:
`'[data-testid^="select-option-"]:not([data-testid="select-option-selected-icon"])'`
(still testid-only — both halves are `data-testid` matches).

## Re-selecting an already-selected option fires NO request

Any helper that wraps the click in `expect_response` (e.g.
`AIProvidersPage.select_tier_model`) will hang its full timeout. Read the persisted
state back from the section's models GET first, and only re-select when it moved.

## `get_configuration_card_count()` is whole-page and NOT stable across a Save

The LLMs accordion auto-expands only on a **fresh page load**, so a baseline taken
before a Save and a count taken after the app's own navigation back are not comparable
(measured 15 → 4). Cards are not descendants of their section header, so no locator
scopes a count to one section. Use `AIProvidersPage.isolate_section()` — collapse every
section, expand one.

## `press_sequentially` can drop the first keystroke

On a freshly-mounted MUI input, typing can start before the click's focus settles:
`text-embedding-3-small` arrived as `ext-embedding-3-small`. Confirm focus first
(`expect(field).to_be_focused()`); `replace_secret_value()` additionally needs a **blur**
to commit the value into form state.

Related: [[ai_providers_vector_storage_project_and_default_traps]]
