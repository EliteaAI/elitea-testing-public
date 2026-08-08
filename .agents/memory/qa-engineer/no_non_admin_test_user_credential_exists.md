---
name: No non-admin (editor/viewer) test-user credential exists
description: TEST_USER is admin-equivalent in every project — RBAC/role-gated cases need a flagged test-data gap, not exploration
type: project
---

## The gap

`.env.test` / `.agents/profile.md` § Roles & sample users define exactly ONE UI
credential pair — `${TEST_USER}` (`TEST_USER_EMAIL`/`TEST_USER_PASSWORD`) — and it is
**admin-equivalent in every project it belongs to**. Live-confirmed (ELITEA-1903 run,
2026-08-08) via `GET /api/v2/auth/permissions/prompt_lib/{project_id}`:

- Project `399` (Private, TEST_USER's own project): full permission set, incl.
  `models.applications.application.update`.
- Project `400` ("UI Testing" team project): SAME full set, PLUS
  `configuration.roles.roles.create/edit/delete` + `configuration.users.users.create/
  edit/delete` — i.e. TEST_USER is project-**admin** there too, not merely a member.

There is no project where this identity holds `editor` or `viewer`. Don't assume
switching the project selector exercises a different role — it doesn't, for this
identity.

## What this means for a role-gated / RBAC case

If a TMS case's objective is "verify X is visible/hidden for role Y" where Y ≠ admin,
**you cannot exercise it live with `${TEST_USER}` alone, no matter which project you
switch to.** Before spending exploration time hunting for a role-switch mechanism:

1. Check Settings → Users on project `400` — it DOES sometimes list `editor`/`viewer`
   rows, but as of 2026-08-08 these were unusable leftover pending-invite fixtures
   from an unrelated test (`Last login: "-"`, never accepted, no known password) — a
   row existing in the table is not the same as a usable login.
2. Do NOT self-downgrade `${TEST_USER}`'s own role via "Edit user role" to test the
   lower-privilege view. Project `400` is shared test data another merged suite
   depends on for a fixed user/role shape (`automation/pages/admin_users_page.py`
   docstring, ELITEA-2292's precondition) — there is no verified way to safely
   restore admin afterward if the downgraded role lacks `configuration.users.
   users.edit`.
3. If no genuine non-admin credential turns up, this is a **test-data gap**, not a
   blocker for the WHOLE case: automate the admin-role half fully (it's real
   coverage of the RBAC-gating mechanism itself — e.g. `checkPermission(...)` source
   read + live admin-visible assertion), and put the non-admin half in § Blocked
   Steps with a concrete unblock ask (a dedicated `EDITOR_TEST_USER_EMAIL/PASSWORD`
   fixture, or an accepted API-level permissions-endpoint proxy). Classify
   `ready-for-automation`, not `blocked` — SKILL.md reserves `blocked` for when
   nothing meaningful can be automated at all.

Worked example: `test-specs/agents/l2_build-with-ai-button-visible-for-admin-and-editor-roles_ELITEA-1903.md`.

## See also

`fork_agent_flow_and_localhost_dev_token_permission_scoping.md` — a related but
DISTINCT caveat: the same admin-equivalent dev-token identity has non-uniform
*permission scope* across projects for specific entity operations (e.g. agent-delete
works in 399/400 but 403s in 471). That's about cross-project permission variance for
ONE identity; this entry is about the absence of any lower-privilege identity at all.
