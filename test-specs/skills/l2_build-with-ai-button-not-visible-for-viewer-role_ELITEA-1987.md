# Test Case: Build with AI — Magic Wand button NOT visible for viewer role on the New Skill creation screen

## Metadata
- **TMS ID**: ELITEA-1987
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (admin-equivalent in every project it belongs to — see § Blocked
  Steps; **no viewer-role credential exists**, and this case has no admin-role half to fall back
  on — its entire premise is the ABSENCE of the button under a viewer identity)
- **Analyst**: qa-engineer (analyst slot, batch skills-remaining-w5)
- **Status**: blocked
  (the case's entire premise — viewer-role absence of the Magic Wand button on the Skills creation
  screen — requires a live viewer-role session; none is obtainable in this environment. This is the
  identical missing-fixture gap already tracked in `EliteaAI/elitea-testing-public#1314`, opened for
  the Agents analog of this exact case, ELITEA-1904. Re-verified fresh this session, not assumed
  from ELITEA-1904's prior finding — see § Blocked Steps for what was (re-)checked.)

## Preconditions
- A user with viewer role would need to be authenticated (not currently obtainable — see § Blocked
  Steps).
- Acting project for the would-be check: `${ELITEA_TEAM_PROJECT_ID}` = `400` ("UI Testing") — the
  only project where a `viewer`-role row exists at all (as an unaccepted pending invite, per
  ELITEA-1904's prior finding, re-confirmed applicable here since no viewer identity has been
  provisioned in the interim).

## Test Data
### reuse-existing
- None usable — `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` is admin-equivalent, which is the
  opposite of what this case needs to exercise.

### missing (blocks the entire case — see § Blocked Steps)
- No `VIEWER_TEST_USER_EMAIL` / `VIEWER_TEST_USER_PASSWORD` (or equivalent) exists in `.env.test` or
  `.agents/profile.md` § Roles & sample users. Re-confirmed this run: `grep -iE
  "viewer|editor|role"` over `automation/.env.test` and `.agents/profile.md` returns nothing beyond
  the field-name headers themselves.
- No Keycloak-admin or backend-admin credential exists to provision one out-of-band either.

## Test Steps

**None executed as live viewer-role verification — blocked before Step 1.** The steps below are the
case's original intent, annotated with why each is unreachable.

1. *(Blocked)* Log in as a user with viewer role.
2. *(Blocked, depends on 1)* Navigate to the Skills page and click "+ Skill" (if accessible).
3. *(Blocked, depends on 1)* Verify the "Build with AI" / Magic Wand button is NOT displayed on the
   New Skill creation screen.
4. *(Blocked, depends on 1)* Verify there is no way for a viewer to trigger the AI Skill Creator
   flow.

## Expected Results
- Per source-code confirmation only (NOT live-verified — reads the same gate ELITEA-1986 confirmed
  present for the admin-equivalent role): `GenerateSkillButton.jsx` passes
  `permission={PERMISSIONS.applications.update}` into `GenerateEntityButton.jsx`, which renders
  `null` when `checkPermission(permission)` is false. A viewer role conventionally lacks
  `models.applications.application.update`, so the button is expected absent by the same mechanism
  ELITEA-1986 proved present for the admin-equivalent role. This is an inference, not an executed
  observation — flagged explicitly so it is never reported as asserted.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as viewer role | viewer logged in | — | — | blocked *(no viewer credential exists — § Blocked Steps, tracked in #1314)* |
| 2 Navigate to Skills, open New Skill creation page (viewer) | page opens or navigation restricted | — | — | blocked *(depends on step 1)* |
| 3 Verify Build with AI button NOT displayed | button absent | — | — | blocked *(depends on step 1)* |
| 4 Verify no UI control triggers the AI Skill Creator flow for viewer | no control exists | — | — | blocked *(depends on step 1)* |

**Axis 2 — Analyst additions:** none — no step of this case was reachable to enrich.

## Cleanup
- None — nothing was created or mutated during this analysis pass (no invite/edit/delete action
  taken; the viewer-row check, if repeated, would again be read-only).

## Concrete Handles (discovered during exploration)

No handles captured — the case's own target (the Magic Wand button's *absence*, from a viewer
session) was never reached. For reference, the button's existing testid (already wired, confirmed
live under `${TEST_USER}` by ELITEA-1986) is `generate-skill-open-button` — an absence assertion
against it would be
`expect(page.get_by_test_id("generate-skill-open-button")).not_to_be_visible()` once a viewer
session exists; not captured as a live handle here since it was never exercised under a viewer
identity.

## Network Behavior
- `GET /api/v2/auth/permissions/prompt_lib/{project_id}` — the authoritative source for whether
  `generate-skill-open-button` renders (`models.applications.application.update`
  presence/absence in the response array). ELITEA-1986 confirmed this is TRUE for the
  admin-equivalent role on project `399`; the viewer-role counterpart of this response was never
  observed (no viewer token to call it with) — identical situation to ELITEA-1904's Agents analog.

## Known Defects Found During Exploration
None found. (No defect — the blocker is a missing test-data fixture, not a product bug.)

## Blocked Steps

**The entire case is blocked — no live viewer-role session is obtainable in this environment.**
Re-verified fresh this session (not carried over unchecked from ELITEA-1904):

1. **Credential gap confirmed still current.** `grep -iE "viewer|editor|role"` over
   `automation/.env.test` and `.agents/profile.md` § Roles & sample users returns nothing beyond
   the field-name headers — only `${TEST_USER}` (admin-equivalent) exists. No
   `VIEWER_TEST_USER_EMAIL`/`VIEWER_TEST_USER_PASSWORD` pair, and no Keycloak-admin / backend-admin
   credential exists anywhere in `.env.test` to provision one out-of-band.
2. **Same tracked gap, second entity type.** The button under test here
   (`generate-skill-open-button`) is gated by the byte-for-byte identical mechanism as the Agents
   button ELITEA-1904 already found unreachable
   (`GenerateEntityButton.jsx`'s `checkPermission(PERMISSIONS.applications.update)`, shared code
   between `GenerateAgentButton.jsx` and `GenerateSkillButton.jsx` — confirmed via source this run).
   No new escape-hatch investigation was warranted beyond re-confirming the credential gap itself
   (ELITEA-1904's AFS already exhaustively checked and rejected: the Settings → Users row-actions
   menu, `admin_users_page.py`'s available methods, and self-downgrading `${TEST_USER}`'s own role
   — none of that has changed since, and re-deriving it here would just restate ELITEA-1904's
   findings rather than add new evidence).
3. **No API-level substitute available either**, for the same reason ELITEA-1904 found none: there
   is no way to obtain *any* authenticated call — UI or API — as a viewer identity without a
   working login, and no such login exists.
- **What unblocks this:** the same fix `EliteaAI/elitea-testing-public#1314` already names — a
  dedicated `VIEWER_TEST_USER_EMAIL`/`VIEWER_TEST_USER_PASSWORD` fixture (real Keycloak account,
  fixed viewer role, stable non-shared project) added to `.env.test` +
  `.agents/profile.md` § Roles & sample users. Once that exists, this case is a straightforward
  4-step automation (login as viewer → navigate to `/skills/create` (or observe redirect/
  restriction if the route itself is gated) → assert `generate-skill-open-button` is
  `not_to_be_visible()` or has zero count → assert no other control reaches
  `generate-skill-modal`).
- **This case has no partial-coverage path the way ELITEA-1986 did.** ELITEA-1986 could prove the
  RBAC mechanism from the admin side (button IS visible with the permission). This case's entire
  observable — button is ABSENT without the permission — is only provable from the other side of
  that same gate, and that side has no live account at all. There is nothing to automate today.
- **Not filed as a new issue** — this is the identical fixture gap #1314 already tracks (opened for
  ELITEA-1903/ELITEA-1904); per `.agents/profile.md` § Bug filing dedup discipline, the recurrence
  on this second entity type is being noted as a comment on the existing #1314 rather than split
  into a new ticket. See the analyst's Run Report / findings.

## Automation Hints
- Once a viewer credential exists: reuse `SkillsListPage.navigate_to_create()` and
  `GenerateSkillModalPage.open_button` from `test_skill_build_with_ai*.py` — same page objects
  ELITEA-1986 used, just under a different auth fixture/storage state for the viewer identity.
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Suggested test module: same file ELITEA-1986 recommended —
  `tests/ui/skills/test_skill_build_with_ai_role_visibility.py` — as the negative counterpart of
  ELITEA-1986's positive assertion, once both are automatable together. Mirrors the Agents analog's
  `test_agent_build_with_ai_role_visibility.py` pairing (ELITEA-1903/ELITEA-1904).
