---
name: structured_output messages+dict/list crash
description: LLM node structured_output=true + messages in output + dict/list custom var = backend crash (#1274)
type: project
---

Confirmed live 2026-08-06 (ELITEA-2453 analysis): an LLM pipeline node with
`structured_output: true` fails at execution with a raw backend error surfaced
directly in the chat response — `Error: sequence item 0: expected str instance,
dict found` — whenever its `output` mapping combines the built-in `messages`
variable together with `list`/`dict`-typed custom state variables. Filed as
`EliteaAI/elitea-testing-public#1274`.

Isolated via a live A/B in the same session: identical pipeline YAML, only
difference was `messages` present vs absent in the structured-output node's
`output` list. Present → crash, empty state. Absent → clean success, all custom
vars correctly typed in Run Details.

**Practical rule for any future structured-output fixture**: never include
`messages` in a `structured_output: true` node's `output` list if that node also
writes `list`/`dict`-typed custom state variables. Write `messages` via a SEPARATE
non-structured-output node/mapping if the case needs both observables.

Also confirmed: `PipelineAPI.create_pipeline()` (generic, already exists) accepts
a raw `instructions` YAML string with a top-level `state:` block — this is the way
to seed custom typed state variables via a fixture in one API call, no new API
method needed. `create_pipeline_with_nodes()` does NOT support `state:` (only
`entry_point`+`nodes`).
