---
name: Cleanup verification on shared state must soft-assert, not log-only
description: When a test's cleanup restores a SHARED cross-session baseline (like counts, toggles, etc.), verifying that restoration with logger.error only is a defect — route it into soft_failures/pytest.fail() so a failed cleanup can't silently pass while polluting sibling cases' baseline.
type: feedback
---

## The pattern

A test whose case mutates shared, cross-session product data (e.g. an
Agent Hub like count) must clean up in `finally` — that part is usually done
right. The trap is in how the cleanup's *own success* gets checked: it is
tempting to `logger.error(...)` on a non-204 response, a like-count that
never settles back to 0, or an unexpected console error on the cleanup
click, and leave it at that. That is silent from the test-result's point of
view — the test goes GREEN, the log line is easy to miss, and the shared
baseline stays polluted for every sibling case that runs after it and
assumes a clean starting state.

## The fix shape

Extract the verification into a small **pure** helper (inputs: the observed
status/count/errors; output: a `list[str]` of failure messages) and route
its output into the file's existing `soft_failures`/`pytest.fail()`
mechanism — the same idiom already used for a known, sanctioned-RED product
defect. Keep the `logger.error()` calls too (cheap, useful for local
debugging) but they are not sufficient on their own.

```python
def _cleanup_soft_failures(*, unlike_status, like_count_restored,
                            final_like_count, unexpected_unlike_errors) -> list[str]:
    failures = []
    if unlike_status != 204:
        failures.append(f"Cleanup unlike expected 204, got {unlike_status} — baseline may not be restored")
    if not like_count_restored:
        failures.append(f"Cleanup did not restore like count to 0, got {final_like_count}")
    if unexpected_unlike_errors:
        failures.append(f"Unexpected console errors on cleanup unlike click: {unexpected_unlike_errors}")
    return failures
```

Making it a pure function also gives you a cheap, fast regression test
(`tests/unit/test_<x>_cleanup_soft_failures.py`) instead of relying on a
live UI run to prove the branch logic — pin each failure mode + the clean
no-op case.

## Seen 1×

ELITEA-2354 / PR #1216 fix round 1 — `test_agent_hub_like_agent_list_view.py`'s
cleanup-unlike verification (204 status / count-restored-to-0 / no new
console errors) was `logger.error`-only; reviewer flagged it as unaddressed
after round 0 shipped it that way. Fixed via `_cleanup_soft_failures()` +
5-case unit test; live re-run confirmed cleanup succeeds cleanly (0 new
soft-failures fired) and the plumbing doesn't false-positive.
