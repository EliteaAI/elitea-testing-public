---
name: Code node multiselect input value no separator
description: get_code_node_input_value() concatenates multi-selected chips with no separator ("var_avar_b")
type: project
---

`PipelineDetailPage.get_code_node_input_value()` (ELITEA-2009) reads
`.text_content()` off the Code node's Input select container. For a SINGLE
selected variable this is fine (`"input"`, `"user_info"`, etc. — every case
before ELITEA-2449 only ever selected one). For a MULTI-variable selection
(confirmed live, ELITEA-2449, `var_a` + `var_b`), the chips render adjacent
with no separator in the DOM, so `.text_content()` returns `"var_avar_b"` —
NOT `"var_a, var_b"` or `"var_a,var_b"` (that comma-joined form is only the
hidden `<input>`'s value, e.g. via `get_attribute("value")` or the accessible
`textbox` node in a Playwright snapshot, which a `.text_content()` read on the
visible container does NOT surface).

Any assertion against a 2+-variable Code/LLM/Toolkit/MCP node Input selection
must use substring/membership checks (`"var_a" in value and "var_b" in
value`), never an exact-string equality — an exact match assuming a
comma-joined shape will fail even when the feature behaves correctly.

Also confirmed live: calling `select_code_node_input_variable()` (or the
LLM/Toolkit/MCP node equivalents — same `_select_multi_select_option_and_close`
helper) TWICE in a row, once per variable, is safe with no new method needed.
The helper presses `Escape` and waits for the popover to fully close after
each selection, so the second call's `open_*_select()` reopens a genuinely-
closed popover rather than toggling an already-open one shut.

See: `test-specs/pipelines/l3_code-node-input-filtering-selective-state-access_ELITEA-2449.md`,
`test-specs/pipelines/_surface.md` § Code node — input filtering.
