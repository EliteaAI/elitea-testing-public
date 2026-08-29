---
name: AI-provider create form re-render wipes typed values
description: wait_for_schema_field() does not close the wipe window on the llm_model form — use the *_verified setters
type: feedback
aliases: [schema re-render wipe, create-ai-provider typing, set_display_name_verified, 043574]
tags: [area/settings-ai-providers, type/gotcha]
created: 2026-08-30
updated: 2026-08-30
---

## What happens

`/settings/create-ai-provider/{type}` forms are schema-driven: after
`GET /configurations/available/?section=...` resolves, the form RE-RENDERS and any
value typed in the gap is silently cleared.

`AiProviderFormPage.wait_for_schema_field(<schema-only field>)` was written to close
that window (ELITEA-2399) and does close it on `open_ai`. It does **NOT** close it on
`llm_model`: on ELITEA-2416, with the schema-only `name` field already visible,
`autotest_2416_model_1788043574` arrived in the Display Name field as `043574` — the
field was cleared mid-typing and the remaining keystrokes landed on the empty input.

## What to use instead

`AiProviderFormPage.set_display_name_verified()` / `.set_schema_field_verified()`
(added ELITEA-2416): type, read back, re-type what the form discarded, up to 3
attempts, with the FINAL attempt still asserting — so a field that genuinely refuses
a value fails loudly. Nothing is normalised or masked.

Plus a settle assertion on the schema DEFAULTS landing, which is the last thing the
`llm_model` form does before it stops re-rendering:

```python
expect(form.field("context_window")).to_have_value("128000")
```

Cheaper and more honest than a settle sleep.

Related: [[sanctioned_red_specs_should_carry_flaky_reruns_zero]]
