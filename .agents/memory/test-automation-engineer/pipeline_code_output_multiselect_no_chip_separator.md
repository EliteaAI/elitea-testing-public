---
name: Pipeline Input/Output multi-select chips have NO text separator
description: get_code_node_output_value()/get_code_node_input_value() with 2+ selected vars concatenate chip text with no comma/space -- comma-split silently breaks
type: feedback
---

`PipelineDetailPage.get_code_node_output_value()` / `get_code_node_input_value()`
read `text_content()` on the Input/Output multi-select. With a SINGLE selected
variable this is fine (`"user_info"`). With 2+ selected variables (confirmed
live, ELITEA-2447, `pipeline-code-node-output-select` with `summary`, `count`,
`tags` selected) the returned string is the chip texts concatenated with
**zero separator characters**: `"summarycounttags"`, not `"summary, count,
tags"` or `"summary,count,tags"`. Each chip is a separate DOM sibling with no
comma/whitespace text node between them.

**A `.split(",")` order-independent set comparison silently produces a
single-item set and fails** (looks like "wrong labels", isn't). The correct
order-independent check is substring-membership + total-length equality:

```python
output_value = pipeline_page.get_code_node_output_value()
for var_name in expected_vars:
    assert var_name in output_value
assert len(output_value) == sum(len(v) for v in expected_vars)  # catches extras
```

The length check matters — without it, `all(v in output_value for v in vars)`
alone would pass even with an extra/wrong variable chipped in, as long as the
expected names all happen to be substrings.
