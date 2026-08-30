---
name: Elitea roles are project-scoped — one account, three real vantages
description: Switch the sidebar project to get a real admin/editor/viewer state; no second identity, no substitution
type: reference
aliases: [role vantage, admin project, viewer project, project-scoped roles, monitor role]
tags: [area/settings, area/permissions]
created: 2026-08-30
updated: 2026-08-30
---

## The fact

`testbot@elitea.ai` (id 659, `personal_project_id` 399) holds DIFFERENT roles per
project, so a role-based case needs no second login:

| Project | id | role | permissions |
|---|---|---|---|
| UI Testing | 400 | **admin** | 360 |
| Private (personal) | 399 = `settings.elitea_project_id` | editor+viewer | 299 |
| Elitea Testing Team | 471 = `settings.elitea_team_project_id` | viewer | 158 |
| Bugs & Features / Elitea Development | 406 / 25 | viewer | 158 |

Verified 2026-08-30 via `GET /api/v2/admin/users/prompt_lib/{pid}` and
`/auth/permissions/prompt_lib/{pid}` (Bearer `ELITEA_API_TOKEN`,
`https://dev.elitea.ai/api/v2`). Switching the project selector re-fetches
`state.user.permissions`, so the app enters a genuinely product-computed role state.

**Project 400 is not in `config.py`** — a spec needing the admin vantage adds
`elitea_admin_project_id`.

**There is no Monitor role** — `/admin/roles/default/{pid}` returns exactly
`['admin','editor','viewer']` everywhere. Case steps naming Monitor are
*un-executable*, not skipped (clarification #1909).

Cheapest vantage guard: the `settings-nav-item-secrets` drawer entry — present on
400/399, `count 0` on 471. Sharpest admin-only observable: `user-row-edit-button` /
`user-row-delete-button` on the Users page (absent entirely for a viewer).

Related: [[settings_drawer_handles]] · `test-specs/settings-navigation/_surface.md`
