---
name: pipeline YAML output field round-trips as block-style
description: raw-YAML flow-style edits to a node's output list re-serialize as block-style on reload — assert parsed value, not literal typed text
type: feedback
---

Confirmed live, ELITEA-2067 (`test_pipeline_yaml_flow_sync.py`,
`test_yaml_edit_persists_after_save_and_reload`): editing an LLM node's
`output: []` to flow-style `output: [messages]` via `edit_yaml_line()`, saving,
and reloading — the server round-trips it back as standard block-style YAML
(`output:\n      - messages`), not the flow-style text that was typed.

This is correct/expected YAML behavior (flow and block styles are semantically
identical lists), not a product defect. A post-reload assertion that does a
literal-string `"output: [messages]" in get_yaml_content()` check will FAIL
against a correctly-functioning product — reverse-masking guard territory.

**Fix:** after any Save+reload round-trip of a raw-YAML edit, parse with
`yaml.safe_load(get_yaml_content())` and assert the parsed field value
(`node["output"] == ["messages"]`), not the literal input text. Immediately
after typing (before any save/reload), the literal-string check IS still valid
— the CodeMirror editor shows exactly what was typed until the next
save-then-reload cycle re-serializes it server-side.

Same caution likely applies to any other multi-item YAML field edited via
`edit_yaml_line()` in flow-style (`input: [x, y]`, etc.) — always re-verify
serialization shape live before asserting a literal post-reload string.
