---
name: CHAT HISTORY value field serializes as YAML list not string
description: A Fixed-type Value field holding literal text "[]" parses via yaml.safe_load() as an empty list, not the string "[]"
type: feedback
---

Confirmed live 2026-08-08 (ELITEA-2027, pipeline LLM node YAML verification): the LLM node's
CHAT HISTORY section (and by the same mechanism, any other `input_mapping.*` Fixed-type Value
textarea) does NOT force a string type when serialized to the pipeline's YAML view. It round-trips
whatever text was typed as raw YAML.

- Typing the two-character text `[]` (valid YAML flow-sequence syntax) and saving produces
  `value: []` in the YAML — **unquoted**, so `yaml.safe_load()` parses it as an empty Python
  `list`, not the string `"[]"`.
- Typing a control string that is NOT valid YAML on its own, e.g. `[][]`, produces
  `value: '[][]'` — **quoted**, parses as `str`.

So a case/test-data table that writes `CHAT HISTORY value: "[]"` (implying a string) must still
assert the field as `== []` (an empty list) after `yaml.safe_load()`, not `== "[]"` — asserting
the string form fails against the live, correctly-functioning product. This is not a defect; it's
correct YAML behavior (an unquoted value that happens to also be valid list syntax parses as a
list). Same reasoning likely applies to any other Fixed-type Value field whose typed text happens
to be syntactically valid YAML for a non-string type (e.g. a typed `true`/`123`/`{}` would likely
suffer the same fate) — verify live via a before/after probe (type the value, check YAML; type a
deliberately-invalid-YAML variant, confirm it quotes) before asserting a YAML-parsed Fixed value's
type in any new case, rather than assuming string.

See `test-specs/pipelines/lextend_pipeline-node-config-verified-via-yaml_ELITEA-2027.md` Axis 2
and `test-specs/pipelines/_surface.md` for the full live-probe evidence (unquoted-vs-quoted pair).
