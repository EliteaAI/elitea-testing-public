---
name: Elitea roles are project-scoped — a viewer vantage needs no second credential
description: The shared TEST_USER is admin/editor in some projects and viewer in others; switch the project selector to act under a different role
type: project
aliases: [viewer role, monitor role, RBAC test user, role-differentiated cases, permissions per project]
tags: [area/auth, area/settings, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## The fact

Elitea roles are **per project**, not per account. The shared `${TEST_USER}` already
holds different roles across the five selectable projects (verified live 2026-08-28):

```
GET {ELITEA_API_BASE}/admin/users/prompt_lib/{project_id}
  399 Private              -> ['editor', 'viewer']   settings.elitea_project_id
  400 UI Testing           -> ['admin']              settings.users_team_project_id
  406 Bugs & Features      -> ['viewer']
  25  Elitea Development   -> ['viewer']
  471 Elitea Testing Team  -> ['viewer']             settings.elitea_team_project_id
```

`useCheckPermission` reads `state.user.permissions`, refetched per selected project via
`GET /auth/permissions/prompt_lib/{id}` — project 400 returns 360 permissions
(8 × `configuration.secrets.*`), project 471 returns 158 with **zero** `secret`
permissions. So `BasePage.switch_project(471)` genuinely puts the app in a viewer state.
No substitution, no second identity, no `auth_state_user_b` (which `pytest.skip`s on
localhost anyway).

**So question #1314 ("no editor/viewer test-user credential blocks RBAC cases") is only
half true** — commented there. Still genuinely blocked: two roles *simultaneously*, or
an admin-vs-viewer contrast on the *same* project.

## There is no `Monitor` role

`GET {ELITEA_API_BASE}/admin/roles/default/{p}` → `['admin','editor','viewer']` on all
five projects; `grep -rni "'monitor'" ../EliteaUI/src/` → 0 hits. Any case naming a
Monitor role is case-text drift (clarification #1909). Don't re-derive this.

## Useful probes

```bash
set -a; source automation/.env.test; set +a
curl -s -H "Authorization: Bearer $ELITEA_API_TOKEN" "$ELITEA_API_BASE/admin/users/prompt_lib/471"
curl -s -H "Authorization: Bearer $ELITEA_API_TOKEN" "$ELITEA_API_BASE/admin/roles/default/471"
curl -s -H "Authorization: Bearer $ELITEA_API_TOKEN" "$ELITEA_API_BASE/auth/permissions/prompt_lib/471"
```

Note the path split: **`/admin/users/prompt_lib/{id}`** but **`/admin/roles/default/{id}`**
(`roles/prompt_lib/` 404s). Cost ~4 turns to find.

Related: [[buildErrorMessage_has_no_fetch_error_branch]]
