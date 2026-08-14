---
name: users batch edit roles cleanup leak diagnosis
description: ELITEA-2304's finally-block cleanup loop silently/hard-aborts on the 2nd seeded row, leaking rows into shared project 400
type: feedback
---

Diagnosed (batch-stabilize, 2026-08-05) the ELITEA-2304 hardening-gate RED
(`test_users_batch_edit_roles.py` line 78, `to_have_count(4)` actual 5).

**Live evidence (read-only inspection of project 400's Users table):** at
diagnosis time the table held exactly 4 rows — the 2 real baseline rows
(`Levon Dadayan`, `Test Bot`) plus **2 STRAY leftover invited rows**, both
carrying the `elitea-batch-edit-test2-<suffix>@example.com` pattern (from two
DIFFERENT historical suffixes — i.e. two separate past runs). No `test1`-suffixed
stray existed. That is the fingerprint of a specific bug, not random data noise.

**Root cause — `tests/ui/admin/test_users_batch_edit_roles.py:171-186`, the
`finally` cleanup loop:**

```python
for email in seeded_emails:            # [test1, test2]
    row = users_page.get_row_by_text(email)
    if row.count() > 0:                # <-- one-shot snapshot, no retry
        delete_response = users_page.delete_user_row(row)
        assert delete_response.status == 204, (...)
        expect(users_page.get_row_by_text(email)).to_have_count(0, timeout=ROW_WAIT_TIMEOUT)
```

Two compounding defects, both landing on the SAME symptom (only the 2nd/last
seeded email ever leaks):

1. **`if row.count() > 0` is a single non-retrying DOM snapshot.** Deleting
   `test1` invalidates the `useUserListQuery` cache and the table
   re-renders/refetches; if `test2`'s row lookup lands during that refetch
   window, `.count()` can read 0 and the guard silently skips deletion —
   no exception, no evidence in any report, the row just stays forever.
2. **The `for` loop has no per-item exception isolation.** If instead an
   `assert`/`expect` DOES raise while processing `test1` (e.g. the 204 check
   or the up-to-15s `to_have_count(0)` wait timing out under load), the loop
   aborts outright and `test2` is never even attempted.

Either mechanism explains the observed fingerprint (first item always
processed/cleared, second item leaks) and neither throws a visible error
in the run that leaks — the only symptom is the NEXT run's Step-2
`to_have_count(4)` assertion failing on a higher, stale count, because this
test seeds into SHARED, PERSISTENT, non-namespaced live project data
(`.agents/testing.md` § Test data strategy) with a hardcoded absolute
baseline (`2 known rows + 2 new == 4`) instead of a delta off the count
observed at Step 1.

**Not a batch/multi-process interaction** — reproduces on a lone rerun of
just this one spec (confirmed: the prior hardening-gate memory entry hit
this same 5-vs-4 mismatch running ONLY this spec, single process, Run 1).
`test_users_page_layout.py` (the other spec sharing `AdminUsersPage`) is
read-only and never touches invite/delete — ruled out as a contributor.

**Fix shape (not applied — diagnosis only):** (a) make the cleanup loop
defensive per-item (try/except each email, continue on failure, raise an
aggregated error at the end so nothing is silently skipped), and (b) stop
hardcoding the absolute baseline — capture the row count at Step 1 and
assert `initial_count + 2` at Step 2, so the assertion self-heals instead
of permanently breaking after any single leaked row. Manual cleanup of the
2 currently-stray `test2` rows in project 400 is also needed before the
next gate run, independent of the code fix.
