---
name: Multi-select re-selecting a pre-filled chip toggles it off
description: select_code_node_input_variable() on an already-checked chip deselects it — verify pre-set multi-selects read-only
type: feedback
---

`PipelineDetailPage.select_code_node_input_variable()` (and the sibling
`select_llm_node_output_variable()`/etc — all built on
`_select_multi_select_option_and_close()` → `select_open_listbox_option()`)
performs a plain `option.click()` on the MUI multi-select `MenuItem`. This is
a TOGGLE, not an idempotent "ensure selected": clicking an option that is
ALREADY checked deselects it.

**Where this bites:** a fixture that pre-sets a Code/LLM node's `input:`/
`output:` via raw YAML `instructions` at pipeline creation (the
`PipelineAPI.create_pipeline()` pattern used throughout the Code-node family,
ELITEA-2446/2447/2448/2449). If the AFS/case text says "set Input combobox to
include X, Y" and you dutifully call `select_code_node_input_variable("X")`
then `("Y")` against a fixture whose Input is ALREADY `[X, Y]`, both calls
DESELECT their chip — `get_code_node_input_value()` comes back `""`.
Confirmed live during ELITEA-2449: this exact sequence against the
recommended YAML-pre-set fixture emptied the Input field, when the AFS's own
"confirmed live, safe to use as-is" note was based on a probe pipeline whose
Input started EMPTY (a different pipeline than the one the AFS then
recommends for automation).

**Rule of thumb:** before writing `select_*_variable()` calls in a test whose
fixture builds via raw YAML, check whether the target node's `input`/`output`
list in that YAML ALREADY contains the values you're about to "select". If
yes — the case's "set the combobox to X" step is asking you to VERIFY
pre-configured state, not perform a fresh UI action; write a read-only
assertion (`get_code_node_input_value()` substring/membership check) instead
of re-invoking the select method. The two-call select sequence itself is
correct and gotcha-free (composes cleanly, no popover race) — but only when
starting from an empty/different selection, e.g. a freshly `add_node()`-ed
node (ELITEA-2009's own test never has this problem for exactly that reason).
