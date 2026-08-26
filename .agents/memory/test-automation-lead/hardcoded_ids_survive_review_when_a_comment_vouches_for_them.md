---
name: A false comment is what lets a hardcoded id survive review
description: Env-specific ids pass review when a comment vouches for them; demand prose that names roles, not literal ids
type: feedback
aliases: [hardcoded project id, fixed across environments, env-specific test data, false comment, ELITEA-2051, fork target project]
tags: [area/test-data, type/review-gate]
created: 2026-08-26
updated: 2026-08-26
---

## What happened

`test_pipeline_fork_to_different_project` (ELITEA-2051) shipped with:

```python
# Target/fork-into project — shared test project (fixed across environments).
TARGET_PROJECT_ID = 399
```

399 is **not** shared and **not** fixed — it is the acting user's own project,
which `ProjectSelect.jsx:99-104` relabels to the literal string "Private". The
comment was written from that label. Commit `e42e71536` then moved
`settings.elitea_project_id` to the *source* side "for flexibility", making
source == target, and the test could never pass anywhere. It took a full triage
card (#1800) to undo.

## The generalisable part

**A comment asserting a value's scope is an unverifiable claim that review
treats as verified.** Nothing in the locator grep, the provenance grep, the AFS
triangulation or the N×-green gate can contradict it — and a wrong one actively
misleads the next author, which is exactly how the regression happened.

## What to demand

- Prose describes each id **by role** ("the acting user's own project", "a
  second project the user belongs to"), never by literal value. Literal ids
  appear only as illustrative "locally this resolves to…" notes.
- An id that varies per user or per environment is **resolved at runtime** from
  the real system (a memberships read), not defaulted — and an unmeetable
  precondition **fails loudly**, never skips.
- Watch the config types: a key defaulting to `0`/`""` produces an id that is
  never a real membership, so it slips past a candidate filter and dies far
  downstream with a non-diagnostic locator timeout. Guard for non-positive at
  the front.

## Smell test, applicable in one read

If a comment says **"fixed across environments"**, **"shared"**, or **"stable"**
about a numeric id, ask what verified it. Usually nothing did.

Related: [[a_parked_case_is_a_hypothesis_not_a_verdict]]
