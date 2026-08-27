---
name: Importing a Test* class into a unit test re-runs the whole UI spec
description: pytest collects Test* classes bound into ANY module namespace — import the spec MODULE, not its class
type: feedback
aliases: [unit test imports ui spec, inspect.getsource spec, Test class collection leak, source-inspection unit test]
tags: [area/pytest, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## What happens

`automation/tests/unit/` holds a family of source-inspection unit tests that pin a
UI spec's helpers or its assertion shapes (`test_console_error_capture_includes_url.py`,
`test_secret_create_inline_known_defect_1203_matcher.py`, …). Writing one as:

```python
from tests.ui.admin.test_secrets_search_filter import TestSecretsSearchFilter, _pick_probe
```

binds `TestSecretsSearchFilter` into the *unit* module's namespace, and pytest's default
`python_classes = Test*` collects it **there too**. Measured 2026-08-27 (ELITEA-2334, fix
round 1): `pytest tests/unit/<one file> -q` launched a browser, drove the full live
Settings → Secrets flow and reported the spec's sanctioned-RED `#1203` failure — from a
run that was supposed to take 0.04 s and touch no network.

## The shape that works

Import the module, alias the private helpers, and reach the class through it:

```python
import tests.ui.admin.test_secrets_search_filter as spec

_pick_probe = spec._pick_probe
source = inspect.getsource(spec.TestSecretsSearchFilter.test_search_field_filters_secrets_by_name)
```

Module attributes are not collected; only names bound in the collected module are. Audited
the other five unit tests that import from `tests.ui.*` — all import functions only, so this
was the single occurrence, but the copy-paste hazard is live for the next one.

Related: [[project_briefing]]
