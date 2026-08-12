---
name: SkillDetailPage.get_version_id() returns skill_id on base, not the real DB version id
description: On a skill's base version the URL has only one digit segment, so get_version_id() falls back to returning the skill_id — NOT the real database version_details.id. Never use it for lineage (parent_version_id) comparisons on base; fetch the real id via SkillAPI.get_skill()["version_details"]["id"] instead.
type: feedback
---

## The gotcha

`SkillDetailPage.get_version_id()` derives its return value from the current URL's
digit path segments: `/skills/all/{skillId}` (base version, ONE segment) vs
`/skills/all/{skillId}/{versionId}` (a named version is active, TWO segments). Its
own docstring says "on the initial base version ... the Version ID equals the
Skill ID" — this is a deliberate simplification for its EXISTING callers
(Save-As-Version before/after URL-change polling, `test_skill_export_import.py`'s
own-URL-didn't-change assertions), where the caller only needs "did the URL's
trailing segment change", not the true value.

**It is NOT the real database version id.** Confirmed live via `SkillAPI` during
ELITEA-2602/2603 exploration: a freshly-created skill's base version has its own
distinct integer id in a SEPARATE counter from the skill id —
e.g. `skill.id=1495` but `version_details.id=1554` (~59 apart in this session,
offset varies). Comparing `get_version_id()` (which would return `"1495"`, the
skill id) against a Fork response's `meta.parent_version_id` (which correctly
holds `1554`, the real version id) would silently produce a WRONG-BUT-PLAUSIBLE
mismatch (or worse, a false pass if you also derive the "expected" side the same
wrong way).

## Fix / correct pattern

For any assertion that needs the REAL base-version database id (lineage checks,
`parent_version_id` comparisons), fetch it via the API instead of the URL:

```python
skill = skill_api.get_skill(skill_id)          # SkillAPI.get_skill(), added ELITEA-2602
real_base_version_id = skill["version_details"]["id"]
```

For a NON-base version created via `save_as_version(name)`, `get_version_id()` IS
reliable — once a named version is active, the URL always carries a real two-digit
segment and the method returns the LAST one correctly (confirmed: this is the
actual DB version id in that case, not a fallback). Capture it immediately after
`save_as_version()` succeeds, while that skill's own URL is still current — once
you navigate elsewhere (e.g. onto a forked copy's single-segment URL),
`get_version_id()` will read THAT url instead and silently return the wrong value.
