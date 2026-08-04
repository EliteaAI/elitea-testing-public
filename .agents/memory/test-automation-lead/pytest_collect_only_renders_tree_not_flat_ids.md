---
name: pytest --collect-only renders a tree here, not flat node-ids
description: this project's custom reporter makes `--collect-only -q` print an indented Module/Class/Function tree instead of classic path::Class::test lines — grepping for "::" finds nothing; derive automation_test_id straight from source instead.
type: feedback
---

## The trap

Elsewhere, `pytest --collect-only -q` prints one flat node-id per line
(`tests/x/test_y.py::TestY::test_z`), easy to grep. In this repo (custom
reporter wired via conftest/plugins) it instead prints an indented tree:

```
<Module test_x.py>
  <Class TestX>
    <Function test_y>
```

Grepping that output for `::` to build a batch of `automation_test_id`
values (TMS back-write Form C, `.agents/test-automation.yaml` §
backwrite_on_done) returns nothing.

## What to do instead

Parse test files directly with a small Python script instead of relying on
pytest's collection output:

```python
import re
classes = re.findall(r'^class (\w+)', src, re.M)
funcs_indented = re.findall(r'^\s+def (test_\w+)', src, re.M)   # methods
funcs_top = re.findall(r'^def (test_\w+)', src, re.M)            # unclassed funcs
```

Then assemble `tests.<dotted.module.path>.<Class>.<func>` (or without the
class segment for an unclassed function) directly — this is exactly Form C.
Confirmed working for 33 cases in one pass, 2026-08-04.
