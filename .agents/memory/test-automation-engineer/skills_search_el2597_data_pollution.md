---
name: test_skill_search.py name-search polluted by leftover el-2597-modify-* skills
description: test_search_skills_by_name fails on the shared DEV project — stale skills from unrelated ELITEA-2597 work widen the "content" search result set. Pre-existing, not caused by any local diff.
type: feedback
aliases: [el-2597-modify, placeholder-skill-2596, skills search pollution, test_search_skills_by_name flake]
tags: [area/skills, area/data-pollution]
created: 2026-09-09
updated: 2026-09-09
---

## Symptom

`tests/ui/skills/test_skill_search.py::TestSkillSearch::test_search_skills_by_name`
Step 2 (search "content", expect exactly `{content-writer, content-reviewer}`)
fails with extra names in the visible set:
`el-2597-modify-1786518306608`, `el-2597-modify-1786518334653`,
`el-2597-modify-1786518363172`, `el-2597-modify-1786518391268`,
`el-2597-modify-1786518459368`, `el-2597-modify-1786518489950`,
`el-2597-modify-1786518517731`, `placeholder-skill-2596`.

## Verified NOT caused by test/page-object code (2026-09-09)

Confirmed via matched control: byte-identical failure reproduces on pristine
`automation/base` with zero diff applied (stashed a navigate()-guard change
before running). This is leftover test data on the shared DEV project (id
`399`, "Private") from unrelated ELITEA-2597 work that was never cleaned up —
those skill names happen to satisfy the "content"-substring search query.
`test_skill_tag_filter.py` and `test_skill_pin_unpin.py` are unaffected
(different query/assertion shape).

## What to do when this fires again

Don't treat it as a regression from whatever diff you're testing — check
first whether the stale `el-2597-modify-*` / `placeholder-skill-2596` skills
still exist on project 399 (`skill_api.list_skills()` or the UI). If so, this
is the same pre-existing pollution, not your change. Cleaning it up (deleting
those skills via `skill_api`) is separately worth doing but is out of scope
for any narrowly-targeted repair task unless the task explicitly asks — it's
shared-environment cleanup, not a page-object/test fix.

Related: [[skills_navigate_response_status_guard]]
