---
name: expect.poll is not a Python Playwright API
description: expect.poll() is JavaScript-only; in Python it raises AttributeError at runtime — a spec using it has never been run
type: feedback
aliases: [expect.poll, Expect object has no attribute poll, polling assertion python playwright]
tags: [area/automation, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The fact

`playwright.sync_api.expect` is an instance of class `Expect`. It has **no `poll` attribute**.
`expect.poll(fn, timeout=...)` is the **JavaScript** API only. Verified in-venv on
Playwright 1.61.0:

```python
from playwright.sync_api import expect
hasattr(expect, "poll")   # False
```

At runtime a spec using it dies with:

```
AttributeError: 'Expect' object has no attribute 'poll'
```

## Why it matters beyond the typo

It fails at the *line*, not at import or collection, so lint/mypy/review can all pass. It is
therefore a reliable **tell that the spec has never actually been executed** — which is exactly
how it reached `automation/base` in `test_hitl_sensitive_action_authorization.py:303`
(ELITEA-2212, found 2026-08-27): the AFS specced the assertion in prose, the implementer reached
for the JS API from memory, and the module carried `pytest.mark.guardrails` so no gate ever ran it.

## What to write instead

For a **backend** condition (a REST read that flips), an explicit deadline loop is the honest
shape — it is not a UI wait, so it is not the `sleep()` the no-sleep rule forbids:

```python
deadline = time.time() + timeout_s
while time.time() < deadline:
    if file_key not in artifact_api.list_bucket_files(bucket):
        break
    time.sleep(3)
```

For a **UI** condition, use a real Playwright assertion (`expect(locator).to_...`) — those poll
natively.

Related: [[hitl_sensitive_action_authorize_never_executes]]
