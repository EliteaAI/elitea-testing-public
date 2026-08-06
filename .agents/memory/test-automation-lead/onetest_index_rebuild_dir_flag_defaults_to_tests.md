---
name: onetest _index.py --dir flag defaults to 'tests', not test-automation.yaml's cases_dir
description: Passing --dir tests/automated-full-regression-ui (matching cases_dir) to the indexer silently drops every case outside that subfolder from index.json
type: feedback
---

While back-writing ELITEA-2391 (issue #899), I ran the onetest indexer scoped to
`test-automation.yaml`'s `intake.cases_dir` on the (wrong) assumption that the
indexer's scope should match the intake selector's scope:

```bash
python3 onetest-tms/scripts/_index.py --dir tests/automated-full-regression-ui --out index.json
```

This "indexed" only 717 cases and silently dropped the other 2055 (2772 → 717) —
`cases_dir` scopes the INTAKE sweep, not the indexer. `_index.py`'s own `--dir`
default is `tests` (the whole tree — other subfolders exist, e.g. Xray cases under
`tests/alita-sdk/`). Caught only because `git diff --stat index.json` showed
55168 deletions for what should have been a ~10-line single-case diff — fixed by
re-running with NO `--dir` (uses the correct default) before committing/pushing.

**Rule:** never pass `--dir` to `_index.py` at all — the default is correct. If you
do pass one, sanity-check `git diff --stat index.json` before committing: for a
routine back-write, the deletion count should be small (a handful of lines for the
one case you touched, maybe a few dozen more if the index was already drifted —
see `onetest_index_json_drift_needs_periodic_rebuild.md`). A deletion count in the
thousands means the scope was wrong, not that the index was "that stale."

This is a distinct pitfall from `tms_index_backwrite_surgical_not_full_rebuild.md`
(which argues against a full rebuild at all, in favor of a surgical single-entry
edit) — if you do choose the full-rebuild path, this is the flag mistake that
makes it actively destructive instead of merely noisy.
