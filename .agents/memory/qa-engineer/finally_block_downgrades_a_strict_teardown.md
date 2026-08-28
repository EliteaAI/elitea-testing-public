---
name: A finally block silently downgrades a strict teardown to best-effort
description: try/finally + best_effort makes a failed restore invisible on green runs — the strict-on-success half of the contract disappears
type: feedback
aliases: [teardown strictness, best_effort finally, shared account state leak, restore persona]
tags: [area/review, type/teardown]
created: 2026-08-29
updated: 2026-08-29
---

## The shape

The project's teardown contract for shared-account specs is **two-sided**:

* body PASSED -> a failed restore **is a failure** (it leaks shared state onto
  every later spec, and nothing else will ever notice);
* body FAILED -> restore **best-effort**, because a teardown exception replaces
  the real failure in the report (the original survives only as `__context__`).

That needs `try / except BaseException: <best_effort> ; raise / else: <strict>`.

A `try / finally:` block with `best_effort(...)` inside **looks** like the same
discipline and is not: it collapses both paths onto best-effort, so a restore
that fails on a green run is logged and thrown away.

Found on ELITEA-2384 (settings-w08, PR #1964), where the `finally` was reached
for a good reason — the spec also has conversation deletion to do on both paths
— and the restores were folded into it. Its three sibling specs in the same unit
(ELITEA-2381/2382/2383) all used the two-sided shape, so the asymmetry is the
tell.

## Fix shape

Keep `finally` for the genuinely both-path cleanup (API deletes), and put the
restores back on `except/else`:

```python
try:
    ...
except BaseException:
    best_effort(lambda: restore(...), "restore X"); raise
else:
    restore(...)          # strict
finally:
    delete_conversations()  # both paths
```

Related: [[teardown_that_reads_a_page_it_may_not_be_on]]
