---
name: Cleanup in a finally must never be guarded by the asserted element
description: Guard a shared-state restore on the thing the test asserts and it fails open on the test's own failure path — restore unconditionally and swallow restore errors
type: feedback
aliases: [finally guard, fails open, restore project cleanup, shared state pollution, teardown guard]
tags: [area/implementation, type/anti-pattern]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

A spec that reads an ABSENCE under a switched vantage (another project, another
user, a toggled org setting) restores that shared state in a `finally`. Writing
the restore as *"only if I'm still on the bad vantage"* —

```python
finally:
    if not drawer.nav_item(SECRETS_TAB_ID).count():   # the asserted element!
        drawer.switch_project(control_project)
```

— fails open on **exactly** the failure the spec exists to catch: if the element
is wrongly PRESENT, `count()` is non-zero, the restore is skipped, and every
later spec in the invocation inherits the polluted state. Caught in review on
ELITEA-2348 (settings-w05, PR #1911).

## The shape that works

```python
def restore_active_project(drawer, project_id) -> None:
    try:
        drawer.switch_project(project_id)          # unconditional — re-selecting
    except Exception:                              # the active project is a no-op
        logger.exception("Failed to restore the active project to %s", project_id)
```

Two properties, both load-bearing:
- **Unconditional.** `BasePage.switch_project()` on the already-active project is
  a harmless re-select, so a guard buys nothing and costs the failure path.
- **Swallows its own errors.** An exception raised inside `finally` REPLACES the
  test's real failure — cleanup must never become the reported cause.

Extract it as a module-level helper rather than inlining it: that makes it
unit-testable with a stub drawer, which is how the regression got pinned
(`automation/tests/unit/test_secrets_access_and_error_spec_invariants.py`).

Related: [[.agents/testing.md § Suite-health pointer]] — the `#1082` shared-state
pollution class this compounds.
