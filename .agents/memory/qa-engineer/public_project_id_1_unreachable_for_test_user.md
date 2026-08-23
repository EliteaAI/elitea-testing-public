---
name: Public project (id 1) is unreachable for the automation test user
description: Any TMS case with a "Public project" step is blocked — the acting user has no public role and no route into project 1
type: project
aliases: [public project, PUBLIC_PROJECT_ID, project type, isPublic, project selector]
tags: [area/projects, type/blocker]
created: 2026-08-23
updated: 2026-08-23
---

## The fact

Elitea's three project types are decided purely by id
(`src/[fsd]/shared/lib/hooks/useProjectType.hooks.js`):
`isPrivate = id === personal_project_id`, `isPublic = id === PUBLIC_PROJECT_ID`,
`isTeam = neither`. **`PUBLIC_PROJECT_ID` is 1** — readable without touching `.env`
from the selector's own feed request:
`GET /api/v2/projects/project/default/1?check_public_role=true`.

For `${TEST_USER}` that response returns only `400 UI Testing`, `471 Elitea Testing
Team`, `25 Elitea Development`, `399 project_user_659` (rendered `Private`),
`406 Bugs & Features`. **Project 1 is not in it** — no public role — and the sidebar
selector renders exactly those five `select-option-{id}` entries.

There is **no alternative route**: selection lives in redux +
`localStorage`/`sessionStorage`. Forcing the stored project id to `1` and reloading
does NOT switch the app (verified 2026-08-23 — it stayed on Private, requests still
`?project_id=399`).

## Consequence

A case step "navigate to a Public project" is **blocked**, not a puzzle. Do not
manufacture the context (forced storage / mocked project list / API-seeded project) —
that is a terminal substitution. Route it: AFS `blocked` + a clarification issue asking
a human to either re-scope the case or provision the public role.
Worked example: ELITEA-2491 → `EliteaAI/elitea-testing-public#1699`.

Related: [[bucket_dot_menu_composition_by_project_type]]
