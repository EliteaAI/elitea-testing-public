---
name: Config project-id keys have MIXED types — int vs str
description: elitea_project_id is int but users_team_project_id is str; an id-exclusion comparison silently no-ops if you assume one type.
type: reference
aliases: [project id type, elitea_project_id, users_team_project_id, public_project_id, project exclusion]
tags: [area/config, type/trap]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

`automation/config.py` types its project-id keys inconsistently:

| Key | Type | Notes |
|---|---|---|
| `elitea_project_id` | `int` (default `0`) | has a `field_validator(mode="before")` coercing `""` -> `0` |
| `elitea_team_project_id` | `Optional[int]` (default `0`) | same validator shape |
| `users_team_project_id` | **`str`** (default `"400"`) | no validator — callers must `int(...)` it |
| `public_project_id` | `int` (default `1`) | added 2026-08-26, ELITEA-2051 |

Any code doing membership/exclusion arithmetic on project ids must normalise.
`int(p["id"]) not in (settings.users_team_project_id, ...)` is **always True** —
a silent no-op that excludes nothing, with no error and no type warning.

Worked example (correct): `_resolve_source_project_id()` in
`automation/tests/ui/pipelines/test_pipeline_fork_to_different_project.py`
excludes the fork target via `int(p["id"]) not in (TARGET_PROJECT_ID, settings.public_project_id)`
— sound only because `elitea_project_id` happens to be `int`; the neighbouring
`users_team_project_id` in the same function is explicitly wrapped `int(...)`.

## Second trap: the `0` default

`elitea_project_id` defaults to `0` when `ELITEA_PROJECT_ID` is unset, so a
missing env var does not fail fast — it produces a *valid-looking* id `0` that
only surfaces much later as a locator timeout on a `select-option-0`-style
handle. That mis-symptom class is exactly what issue #1800 cost a full triage
cycle for. Guard project ids at the top of a spec that routes on them.

Related: [[hardcoded_project_id_is_not_portable]]
