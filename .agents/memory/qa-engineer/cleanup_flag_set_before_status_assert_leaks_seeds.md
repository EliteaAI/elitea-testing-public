---
name: Cleanup flag set before the status assert leaks seeded data
description: `deleted = True` right after the request returns (before asserting 204) skips teardown when the server refuses.
type: feedback
aliases: [cleanup flag leak, deleted flag before assert, seeded row leak, teardown skipped on non-204]
tags: [area/test-hygiene, type/pattern]
created: 2026-08-29
updated: 2026-08-29
---

## The shape

Seed-and-destroy specs guard their `finally` teardown with a flag:

```python
delete_response = users_page.confirm_delete()
deleted = True                                   # <-- set here
assert delete_response.status == 204, ...
...
finally:
    if not deleted:
        ...delete the seed...
```

`confirm_delete()` returns as soon as the DELETE *resolves* — with ANY status.
A `403`/`409`/`500` therefore sets `deleted = True`, the status assert fails,
and the `finally` block skips teardown even though the seeded rows are still
live members of a shared project. The flag means "we asked", but it is read as
"it is gone".

## The fix

Set the flag from the outcome, not the attempt — `deleted = delete_response.status == 204`
(or move the assignment below the assert). Costs one line; the failure it
prevents is invisible (a leaked row in shared live data, discovered waves later
as an "orphaned seed row" nobody can attribute).

Seen on PR #1976 (ELITEA-2298 / ELITEA-2299) — non-blocking there because the
happy path is overwhelmingly the common one, but the pattern is copied forward
every time a new seed-and-destroy spec is written from a neighbour.

Related: [[settings_users_delete_flow_handles]]
