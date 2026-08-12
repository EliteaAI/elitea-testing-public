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
   row existing in the table is not the same as a usable login. **Confirmed dead
   end, not just unexplored (ELITEA-1904 run, same day):** the row's "Actions" cell
   offers only "Edit user role" and "Delete user" — no "Resend invite" / "Reset
   password" / any action that could mint a password for that row. `invite_users()`
   in `admin_users_page.py` is the only invite path and it produces the same
   unaccepted-row shape. There is no UI escape hatch here; stop checking it per case.
2. Do NOT self-downgrade `${TEST_USER}`'s own role via "Edit user role" to test the
   lower-privilege view. Project `400` is shared test data another merged suite
   depends on for a fixed user/role shape (`automation/pages/admin_users_page.py`
   docstring, ELITEA-2292's precondition) — there is no verified way to safely
   restore admin afterward if the downgraded role lacks `configuration.users.
   users.edit`.
3. If no genuine non-admin credential turns up: when the case still has an
   admin-provable half (an RBAC case with a "visible for admin/editor" branch),
   that's a **test-data gap, not a blocker for the WHOLE case** — automate the
   admin-role half fully (real coverage of the gating mechanism itself, e.g.
   `checkPermission(...)` source read + live admin-visible assertion), and put the
   non-admin half in § Blocked Steps. Classify `ready-for-automation`. **But when the
   case's entire premise IS the non-admin observable** (e.g. "button is NOT visible
   for viewer" — nothing to prove from the admin side), there is no partial-coverage
   path: classify `blocked` outright, per SKILL.md's reservation of `blocked` for
   when nothing meaningful can be automated. Don't force a workaround just because a
   sibling case in the same batch found a partial path — check whether an admin-side
   half actually exists for *this* case before assuming it does.
4. No API-level substitute exists either, for the same root cause: minting a token
   for `GET /api/v2/auth/permissions/prompt_lib/{id}` under a viewer identity still
   requires a working viewer login — the credential gap blocks both the UI path and
   any API-only fallback equally.

Worked examples: `test-specs/agents/l2_build-with-ai-button-visible-for-admin-and-editor-roles_ELITEA-1903.md`
(`ready-for-automation`, admin half only) and
`test-specs/agents/l2_build-with-ai-button-not-visible-for-viewer-role_ELITEA-1904.md`
(`blocked` outright, no admin-side half — same underlying gap). Third worked example,
same gap, different entity: `test-specs/skills/l2_edit-with-ai-skill-permissions_ELITEA-2613.md`
(`ready-for-automation`, Admin CTA-visibility half + a bonus fully-provable character-limit
half; Editor/Viewer halves blocked, commented onto tracking issue #1314 as a third case).

## See also

`fork_agent_flow_and_localhost_dev_token_permission_scoping.md` — a related but
DISTINCT caveat: the same admin-equivalent dev-token identity has non-uniform
*permission scope* across projects for specific entity operations (e.g. agent-delete
works in 399/400 but 403s in 471). That's about cross-project permission variance for
ONE identity; this entry is about the absence of any lower-privilege identity at all.
