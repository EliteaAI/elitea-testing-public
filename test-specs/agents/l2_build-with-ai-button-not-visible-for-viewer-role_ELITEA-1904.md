# Test Case: Build with AI — Magic Wand button NOT visible for viewer role in New Agent creation flow

## Metadata
- **TMS ID**: ELITEA-1904
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (admin-equivalent in every project it belongs to — see § Blocked Steps;
  **no viewer-role credential exists**, and unlike ELITEA-1903 this case has no admin-role half to
  fall back on)
- **Analyst**: qa-engineer (analyst slot, batch 1298)
- **Status**: blocked
  (the case's entire premise — viewer-role absence of the Magic Wand button — requires a live
  viewer-role session; none is obtainable in this environment. Re-verified fresh this session, not
  assumed from ELITEA-1903's prior finding — see § Blocked Steps for what was checked.)

## Preconditions
- A user with viewer role would need to be authenticated (not currently obtainable — see § Blocked
  Steps).
- Acting project for the would-be check: `${ELITEA_TEAM_PROJECT_ID}` = `400` ("UI Testing") — the
  only project where a `viewer`-role row exists at all (as an unaccepted pending invite).

## Test Data
### reuse-existing
- None usable — `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` is admin-equivalent, which is the
  opposite of what this case needs to exercise.

### missing (blocks the entire case — see § Blocked Steps)
- No `VIEWER_TEST_USER_EMAIL` / `VIEWER_TEST_USER_PASSWORD` (or equivalent) exists in `.env.test` or
  `.agents/profile.md` § Roles & sample users.
- No Keycloak-admin or backend-admin credential exists to provision one out-of-band either.

## Test Steps

**None executed as live viewer-role verification — blocked before Step 1.** The steps below are the
case's original intent, annotated with why each is unreachable.

1. *(Blocked)* Log in as a user with viewer role.
2. *(Blocked, depends on 1)* Navigate to Agents and attempt to open the New Agent creation page.
3. *(Blocked, depends on 1)* Verify the Magic Wand button is NOT displayed anywhere on the creation
   page.
4. *(Blocked, depends on 1)* Verify there is no way for a viewer to trigger the AI Agent Creator flow.

## Expected Results
- Per source-code confirmation only (NOT live-verified — see ELITEA-1903's AFS, which reads the same
  gate): `GenerateEntityButton.jsx` renders `null` when
  `checkPermission(PERMISSIONS.applications.update)` is false. A viewer role conventionally lacks
  `models.applications.application.update`, so the button is expected absent by the same mechanism
  ELITEA-1903 proved present for the admin-equivalent role. This is an inference, not an executed
  observation — flagged explicitly so it is never reported as asserted.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as viewer role | viewer logged in | — | — | blocked *(no viewer credential exists — § Blocked Steps)* |
| 2 Navigate to Agents, open New Agent creation page (viewer) | page opens or navigation restricted | — | — | blocked *(depends on step 1)* |
| 3 Verify Magic Wand button NOT displayed | button absent | — | — | blocked *(depends on step 1)* |
| 4 Verify no UI control triggers the AI Agent Creator flow for viewer | no control exists | — | — | blocked *(depends on step 1)* |

**Axis 2 — Analyst additions:** none — no step of this case was reachable to enrich.

## Cleanup
- None — nothing was created or mutated during this analysis pass (only a read-only admin Settings →
  Users page load, no invite/edit/delete action taken).

## Concrete Handles (discovered during exploration)

No handles captured — the case's own target (the Magic Wand button's *absence*, from a viewer
session) was never reached. For reference, the button's existing testid (already wired, from
ELITEA-1903) is `generate-agent-open-button` — an absence assertion against it would be
`expect(page.get_by_test_id("generate-agent-open-button")).not_to_be_visible()` once a viewer session
exists; not captured as a live handle here since it was never exercised under a viewer identity.

## Network Behavior
- `GET /api/v2/auth/permissions/prompt_lib/{project_id}` — the authoritative source for whether
  `generate-agent-open-button` renders (`models.applications.application.update` presence/absence in
  the response array). ELITEA-1903 confirmed this is TRUE for the admin-equivalent role on both
  project `399` and `400`; the viewer-role counterpart of this response was never observed (no
  viewer token to call it with).

## Known Defects Found During Exploration
None found. (No defect — the blocker is a missing test-data fixture, not a product bug.)

## Blocked Steps

**The entire case is blocked — no live viewer-role session is obtainable in this environment.**
Re-verified fresh this session (not carried over unchecked from ELITEA-1903):

1. **Credential gap confirmed still current.** `grep -iE "viewer|editor|role"` over
   `automation/.env.test` and `.agents/profile.md` § Roles & sample users returns nothing beyond
   `${TEST_USER}` (admin-equivalent). No `VIEWER_TEST_USER_EMAIL`/`VIEWER_TEST_USER_PASSWORD` pair,
   and no Keycloak-admin / backend-admin credential exists anywhere in `.env.test` to provision one
   out-of-band (the full env-var list was enumerated this session — only third-party toolkit
   credentials and the single `TEST_USER_*` pair exist).
2. **Live re-check of the Settings → Users row-actions menu (new this session, not in ELITEA-1903's
   AFS) — no escape hatch found.** Navigated live to `/settings/users?project=400` as `${TEST_USER}`
   and took a fresh accessibility snapshot of the `viewer`-role row
   (`elitea-batch-edit-test2-70fda701@example.com`, `Last login: "-"`, unaccepted pending invite —
   same leftover fixture ELITEA-1903 found). The row's **only** available actions are "Edit user
   role" and "Delete user" — there is no "Resend invite," "Reset password," or any other action that
   could mint a live, password-known session for that row. This closes off the one avenue ELITEA-1903
   hadn't explicitly checked (whether a row-level action existed to set a password directly).
3. **`admin_users_page.py` re-confirmed to expose no such capability either** — the page object's
   methods are limited to `invite_users()` (creates the same kind of unaccepted, passwordless row),
   `select_role_in_invite_dialog()`, and role-edit/delete; no `reset_password` / `resend_invite`
   method exists in the automation layer, consistent with the live UI check above.
4. **Self-downgrade / mutating shared project-role state** — same rejection as ELITEA-1903: project
   `400` is shared test data another merged suite (`ELITEA-2304`/`test_users_batch_edit_roles.py`)
   depends on for a fixed user/role shape, with no verified rollback path for `${TEST_USER}` itself.
   Unlike ELITEA-1903, self-downgrade here isn't even a viable option in principle — the case needs
   `${TEST_USER}` to log in *as a distinct viewer identity* to prove absence, not to gain the viewer
   role itself (proving "viewer-you can't see the button" from an account that used to be admin,
   mid-session, would not be the same observable the case asks for even if a rollback existed).
5. **No API-level substitute available either, unlike ELITEA-1903's Blocked Steps option (b).**
   ELITEA-1903's editor-role gap had a scoped fallback: assert an editor token's
   `GET /api/v2/auth/permissions/prompt_lib/{id}` response *contains* the permission (structural
   proof, no UI session needed) — but minting that token still requires a live login for that role.
   The same substitute is unavailable here for the identical reason: there is no way to obtain
   *any* authenticated call — UI or API — as a viewer identity without a working login, and no such
   login exists.
- **What unblocks this** (same missing-fixture-primitive as tracked in
  `EliteaAI/elitea-testing-public#1314`, filed during ELITEA-1903's pass): a dedicated
  `VIEWER_TEST_USER_EMAIL`/`VIEWER_TEST_USER_PASSWORD` fixture — a real Keycloak account provisioned
  with a fixed viewer role in a stable, non-shared project — added to `.env.test` +
  `.agents/profile.md` § Roles & sample users. Once that exists, this case is a straightforward
  4-step automation (login as viewer → navigate to `/agents/create?viewMode=owner` (or observe
  redirect/restriction if the route itself is gated) → assert
  `generate-agent-open-button` is `not_to_be_visible()` or has zero count → assert no other control
  reaches `generate-agent-modal`).
- **This case has no partial-coverage path the way ELITEA-1903 did.** ELITEA-1903 could prove the
  RBAC mechanism from the admin side (button IS visible with the permission). This case's entire
  observable — button is ABSENT without the permission — is only provable from the other side of
  that same gate, and that side has no live account at all. There is nothing to automate today.

## Automation Hints
- Once a viewer credential exists: reuse `AgentsListPage.navigate_to_create()` and
  `GenerateAgentModalPage.open_button` from `test_agent_build_with_ai*.py` — same page objects
  ELITEA-1903 used, just under a different auth fixture/storage state for the viewer identity.
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Suggested test module: same file ELITEA-1903 recommended —
  `tests/ui/agents/test_agent_build_with_ai_role_visibility.py` — as the negative counterpart of
  ELITEA-1903's positive assertion, once both are automatable together.
