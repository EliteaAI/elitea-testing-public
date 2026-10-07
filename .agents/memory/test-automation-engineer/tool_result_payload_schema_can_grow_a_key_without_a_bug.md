---
name: Tool result payload schema can grow a key without a bug — verify via the REST sibling before widening the pin
description: An exact-dict-equality assertion on a tool-run payload breaks the moment the backend tool adds a field (not just re-serializes); confirm the new key isn't masking a real regression by diffing against the plain REST endpoint for the same read before widening the expected literal
type: feedback
tags: [area/toolkits, type/pitfall, area/triage]
created: 2026-10-07
---

## The shape

A test pins a toolkit tool's run-result payload with full-dict `==` equality
(`ELITEA-1866`'s `list_files`: `assert payload == {"total": 0, "rows": []}`).
The tool's OWN response schema grows a new key (`truncated: False`) — not a
re-serialization like the earlier `#2066` drift (Python-repr → pretty JSON),
a genuine new field in the business payload. The exact-match assertion now
fails on every run, even though the underlying observable (an empty bucket
listing) is still exactly correct.

**CI's own auto-filed issue guessed wrong** — its "Instructions" section
assumed the test's assertion logic was inverted. It wasn't. Reading the
diff (`got: {total: 0, rows: [], truncated: False}` vs expected
`{total: 0, rows: []}`) side by side immediately shows an ADDED key, not an
inverted condition — don't let an auto-generated issue's own narrative
pre-judge the triage class before you've looked at the actual diff.

## Before accepting the new key as benign — check a sibling surface

Don't just widen the pin and move on; a NEW key is exactly the shape a
reverse-masking trap could hide behind (what if the field reports something
wrong, and widening the pin to accept it silently buries a real bug?). This
tool runs server-side inside an ad-hoc conversation (no direct REST endpoint
of its own), but the SAME read usually has a plain REST sibling that's
independently documented:

```python
# fetch the live OpenAPI spec with the project's own API token
GET https://dev.elitea.ai/shared/openapi/?all=true   # Bearer <ELITEA_API_TOKEN>
# → confirms /api/v2/artifacts/artifacts/{mode}/{project_id}/{bucket} exists
#   ("List Artifacts"), then hit it directly:
GET /api/v2/artifacts/artifacts/default/{project_id}/{bucket}
# → {"retention_policy": {...}, "total": N, "rows": [...]}  — NO `truncated` key
```

Two things this check buys in one shot:
1. **Confirms the new key is tool-specific**, not a platform-wide schema
   change you'd expect to see on the REST sibling too (which would be a
   bigger finding, possibly worth flagging up rather than quietly absorbing
   at the test level).
2. **Lets you reason about what the field COULD be** (here: a pagination-
   style flag, since the tool's own parameter panel already exposes
   `skip`/`include`-style limiting) and therefore what value is actually
   correct for your specific case state — a bucket with nothing in it to
   truncate can only ever report `truncated: False`. That's the fact that
   licenses "safe to pin as `False`", not just "it's present, must be fine."

## The fix is a widen, not a relax — and that distinction matters for sign-off

```python
# before
EMPTY_LIST_FILES_RESULT = {"total": 0, "rows": []}
# after — SAME `==` equality, not a subset/`.get()` check
EMPTY_LIST_FILES_RESULT = {"total": 0, "rows": [], "truncated": False}
```

This is a **strengthening**: the comparison still rejects any key being
wrong, AND now also pins the new key at its only-correct value — strictly
more coverage than before, not less. It needs no human sign-off under the
preserve-the-nature rail (unlike the REJECTED tolerant alternative,
`payload["total"] == 0 and payload["rows"] == []`, which ignores whatever
key shows up next and genuinely would need sign-off). When a payload's
schema grows, reach for "widen the exact-match literal" before "loosen the
comparison" — they look similar but only one keeps full coverage.

Related: `automation/utils/toolkit_result_payload.py`'s own docstring
(the `#2066` precedent for the parsing-not-substring-matching move);
AFS `test-specs/artifacts/l2_create-bucket-via-toolkit-verify-list-files_ELITEA-1866.md`
§ Adjustment 2026-10-07.
