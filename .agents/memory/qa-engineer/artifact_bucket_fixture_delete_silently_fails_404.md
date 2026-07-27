---
name: artifact_bucket fixture delete silently fails (404, both URL formats)
description: The shared `artifact_bucket` pytest fixture's teardown calls ArtifactAPI.delete_bucket() but the delete request 404s on both the plain-name and compound-ID URL formats in the dev environment, so buckets leak silently on every test run that uses the fixture (directly or transitively via artifact_toolkit).
type: feedback
---

## What happens

`automation/fixtures/data_fixtures.py:487-491` — the `artifact_bucket` fixture's
teardown wraps `artifact_api.delete_bucket(name)` in a try/except that only
logs a WARNING on failure, never fails the test. Verified live (2026-07-19,
localhost:5173 → dev.elitea.ai backend, project 399) that this WARNING fires
every time:

```
Failed to delete artifact bucket 'autotest-...': 404 Client Error: Not Found
for url: https://dev.elitea.ai/api/v2/artifacts/buckets/default/399/p--399.autotest-...
```

`ArtifactAPI.delete_bucket()` (`automation/api/client.py:1205-1224`) already
has a two-attempt fallback: plain bucket name first, then the compound
`p--{project_id}.{bucket_name}` ID format on a 404. Both attempts 404 in this
environment — the compound-ID fallback URL exactly matches the `id` field
`create_bucket()` itself returned at creation time, so this isn't a
name-mismatch bug; the DELETE endpoint itself (or its path shape) appears to
be wrong or environment-specific.

## Why it matters

Every test using `artifact_bucket` (directly, or transitively via
`artifact_toolkit`) leaks one bucket per run, permanently, in whatever
project it targets. This is NOT new — it explains the ~65 pre-existing
orphaned `autotest-*` buckets already observed in the `Private` project
(ELITEA-1832's AFS noted this as "matches existing project convention,
harmless" without diagnosing the cause). Confirmed both `test_artifacts_multi_file.py`
(ELITEA-1327, via `artifact_toolkit`) and the new ELITEA-1832 upload-cancel
test hit this identically.

## What to do about it

- Don't treat "buckets aren't being deleted" as expected/harmless in future
  analyst or review passes — it's a real defect in `ArtifactAPI.delete_bucket()`
  / the fixture's teardown, not a design choice.
- Fixing it is a shared-fixture change (affects every artifact test) — out of
  scope for any single case-specific automation PR. Route as its own ticket
  against `automation/api/client.py::ArtifactAPI.delete_bucket()` +
  `automation/fixtures/data_fixtures.py::artifact_bucket`, not bundled into
  a feature PR.
- If diagnosing further: the retry-with-compound-ID fallback already matches
  the bucket's own `id` field from `create_bucket()`'s response, so the next
  debugging step is almost certainly the DELETE endpoint/path itself (wrong
  version, wrong verb, or a real API bug on the dev backend), not a
  client-side ID-construction mistake.
