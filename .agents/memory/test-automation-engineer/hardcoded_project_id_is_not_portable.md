---
name: A hardcoded project id is never portable — resolve it from the API
description: Fixed project ids break on CI; each matrix cell is its own autotest_user_<n> with its own memberships.
type: project
aliases: [project id, ELITEA_PROJECT_ID, USERS_TEAM_PROJECT_ID, public_project_id, ProjectAPI, fork target project, select-option-399]
tags: [area/test-data, type/portability]
created: 2026-08-26
updated: 2026-08-26
---

## The rule

**No test may hardcode a numeric Elitea project id.** Locally `ELITEA_PROJECT_ID`
resolves to the operator's OWN private project (399 = `project_user_659`); in CI
`.github/workflows/test-ui-custom.yml` gives every matrix cell its own
`autotest_user_<n>` with `TEST_USER_PROJECT_<n>` and a completely different
membership set. `USERS_TEAM_PROJECT_ID` (default `"400"`) is **never passed by the
workflow**, so it too is localhost-only truth.

Consequence: **no fixed id is valid on both localhost and DEV.** A constant like
`TARGET_PROJECT_ID = 399` is green locally and dead on CI (ELITEA-2051 / issue #1800:
the merged test selected 399 as source AND target and timed out on
`select-option-399`).

## What to do instead

- The **user's own project** is `settings.elitea_project_id`. That is the only id
  that is correct on every environment — use it for whatever the case calls the
  user's private/home project.
- **Any second project** is discovered at runtime, never assumed:
  `ProjectAPI(browser_cookies=...).list_projects()` (`automation/api/client.py`) hits
  `GET /projects/project/default/{settings.public_project_id}?check_public_role=true`
  — the identical request `EliteaUI/src/api/project.js` issues, so the API identity
  matches the browser's. Filter out the ids you can't use, prefer
  `settings.users_team_project_id` **only when the user is actually a member**, then
  fall back to `sorted(candidates)[0]` for determinism.
- Precondition unmeetable (user has only one project) ⇒ `pytest.fail` with an
  explicit message. **Never `pytest.skip`** — skip precedent in this suite is
  reserved for a missing external credential (`GIT_HUB_TOKEN`); a skip here hides a
  broken environment as green (lead ruling, 2026-08-26).

## Two traps this pairs with

1. **Fork excludes the currently-selected project from its target dropdown**
   (`EliteaUI/src/[fsd]/entities/import-wizard/lib/hooks/useForkProjectIds.hooks.js`:
   `excludedProjectIds = [PUBLIC_PROJECT_ID, selectedProjectId]`). Source and target
   MUST be different projects — a same-project pair can never render its option.
2. **A comment can lie.** `e42e71536` labelled 399 *"shared test project (fixed across
   environments)"*; it is one specific user's private project. Describe projects by
   ROLE in docstrings/step labels and interpolate the resolved id at runtime.

Related: [[afs_is_a_work_order_not_gospel]]
