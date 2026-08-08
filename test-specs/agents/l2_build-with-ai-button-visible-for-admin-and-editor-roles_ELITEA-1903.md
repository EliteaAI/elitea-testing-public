# Test Case: Build with AI — Magic Wand button visible for admin and editor roles in New Agent creation flow

## Metadata
- **TMS ID**: ELITEA-1903
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (admin-equivalent in every project it belongs to — see Blocked Steps)
- **Analyst**: qa-engineer (analyst slot, batch 1298)
- **Status**: ready-for-automation
  (admin-role half fully explored and automatable end-to-end; editor-role half is a genuine
  test-data/environment gap — see § Blocked Steps. Per SKILL.md, `blocked` is reserved for when the
  analyst cannot complete meaningful automation at all; here the case's core RBAC-gating mechanism is
  fully proven for one role and the gap for the other is scoped and documented, not silently skipped.)

## Preconditions
- `${TEST_USER}` is authenticated via the `auth_state` fixture (localhost `VITE_DEV_TOKEN` bypass —
  no Keycloak login form on localhost).
- Acting project: `${ELITEA_PROJECT_ID}` (Private, id `399`) — `${TEST_USER}`'s own private project,
  confirmed live to carry the `models.applications.application.update` permission.
- The Build with AI feature is enabled (confirmed live — no feature flag gate observed; gating is
  pure RBAC, see Concrete Handles / Network Behavior).

## Test Data
### reuse-existing
- `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` — admin-equivalent (owner) in the default private
  project; used for the admin-role half.
- `${ELITEA_PROJECT_ID}` = `399` (Private) — where the admin-role half runs.

### missing (blocks the editor-role half — see § Blocked Steps)
- No `EDITOR_TEST_USER_EMAIL` / `EDITOR_TEST_USER_PASSWORD` (or equivalent) exists in `.env.test` or
  `.agents/profile.md` § Roles & sample users.

## Test Steps

1. Authenticate as `${TEST_USER}` via `auth_state` (admin-equivalent role).
   - **Verify**: dashboard/app shell loads (`Elitea is connected` status, side-bar visible).
2. Navigate to Agents (`/agents/all`) and click the sidebar "+ Agent" create button.
   - **Verify**: `/agents/create?viewMode=owner` loads; the "New Agent" tab is selected in the
     page-level tab bar; the Name field is present (page ready).
3. Verify the Magic Wand ("Build with AI") button is visible in the General section header.
   - **Verify**: `generate-agent-open-button` is visible, has accessible text "Build with AI",
     and is clickable (opens the `generate-agent-modal` dialog).
4. *(Editor role — blocked, no live login path. See § Blocked Steps.)*
5. *(Editor role — blocked.)*
6. *(Editor role — blocked.)*

## Expected Results
- Step 3: the Magic Wand button is present, visible, and functional for the admin-equivalent
  `${TEST_USER}` on the New Agent creation page.
- Steps 4–6 (editor role): expected, per the source-code RBAC gate (`checkPermission`), that an
  editor-role user ALSO sees the button — editor is conventionally granted `applications.update`
  in role-based systems of this shape — but this is **not verified live** in this AFS; it is an
  inference from code reading, not an executed observation. Flagged explicitly so it is never
  reported as asserted.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as admin role | dashboard displayed | step 1 | `step 1`: side-bar + connected status visible | asserted |
| 2 Navigate to Agents, click "+ Create" | creation page opens, tab bar visible | step 2 | `step 2`: URL + "New Agent" tab + Name field visible | asserted |
| 3 Verify Magic Wand button visible (admin) | button present in "tab bar" | step 3 | `step 3`: `generate-agent-open-button` visible | asserted *(location clarified — see below)* |
| 4 Log out, log in as editor role | editor logged in | — | — | blocked *(no editor credential exists — § Blocked Steps)* |
| 5 Navigate to Agents, click "+ Create" (editor) | creation page opens | — | — | blocked *(depends on step 4)* |
| 6 Verify Magic Wand button visible (editor) | button present for editor | — | — | blocked *(depends on step 4)* |

**Clarification (case-text drift, not a defect):** the case says the button is "visible in the
creation tab bar." Live-confirmed the button is NOT inside the page-level `tablist` ("New Agent"
tab) — it renders as a pinned pill button in the top-right corner of the **General accordion
section's header row**, a sibling of the "GENERAL" chevron/title, positioned well below the tab
bar. The button itself is genuinely present/visible; only its described location is stale. Source:
`EliteaUI/src/[fsd]/features/agent/ui/generate-agent-modal/GenerateAgentButton.jsx`. Recommend filing
a case-text clarification against ELITEA-1903 (not a `bug`) per `.agents/profile.md` § Bug filing —
routed by the orchestrator per the seeded policy.

**Axis 2 — Analyst additions:**
- Step 3 also asserts the button's accessible name is exactly "Build with AI" (not just "some
  button exists") — *added: without a name/testid pairing check, a regression that renamed the
  wrong button to overlap the wand's position would slip through a bare visibility check.*
- Step 3 optionally asserts the button actually opens `generate-agent-modal` on click (not just
  DOM presence) — *added: presence-without-function (e.g. a disabled/non-interactive ghost button)
  would still satisfy "the button is visible" too literally; the case's real intent is "the AI
  Agent Creator flow is reachable for this role."* This assertion is a light reuse of the existing
  `GenerateAgentModalPage.open_modal()` helper already exercised by `test_agent_build_with_ai.py`.

## Cleanup
- None — no agent is created (the modal is closed via `Cancel`/`X` without generating a draft; the
  agent-create form itself is abandoned, not saved).

## Concrete Handles (discovered during exploration)

| Element | Locator (testid-only) | PROVENANCE | Fallback |
|---|---|---|---|
| Sidebar "+ Agent" create button | `LocatorDescriptor(testid="sidebar-create-button")` — **existing field**, `agents_list_page.py` `create_agent_button` | on-main ✓ AND on-`automation/testids` ✓ (`git grep` this run, EliteaUI, both refs fetched fresh) | none (testid-only; the field's pre-existing `fallback=` param is legacy tech debt, not to be used in new code) |
| New Agent creation page reached | `AgentsListPage.navigate_to_create()` deep-links `/agents/create?viewMode=owner` directly — existing page-object method; the click-based route via `create_agent_button` above is the literal case-step path this AFS specs | n/a (method, not a locator) | — |
| "New Agent" tab (tab bar) | no testid exists; not the AFS's primary target (see Clarification) — implementer should assert page-readiness via the existing `AgentFormPage.wait_for_form_load()` (waits for Name field) rather than a raw tab-bar handle | needs-adding *(only if a future case specifically needs to assert the tab itself — out of scope here per the "touches" rule)* | — |
| Magic Wand / "Build with AI" open button | `LocatorDescriptor(testid="generate-agent-open-button")` — **existing field**, `generate_agent_modal_page.py` `open_button` | on-main: no · on-`automation/testids`: ✓ (fetched fresh this run, `git grep -- "generate-agent-open-button" origin/automation/testids -- src/` hit; `origin/main` — no hit) | none — testid-only, already wired |
| Build with AI modal (post-click, for the functional-reachability addition) | `LocatorDescriptor(testid="generate-agent-modal")` — existing field, same page object, exercised via `open_modal()` | on-main: no · on-`automation/testids`: ✓ (same commit family as the open button — not independently re-verified this run; implementer should re-confirm alongside the open button before relying on it) | none |

No new testid work is required for this case — every handle it touches already exists as a
page-object field.

## Network Behavior
- Project switch / login triggers `GET /api/v2/auth/permissions/prompt_lib/{project_id}` — this is
  the authoritative source for whether `generate-agent-open-button` renders at all
  (`models.applications.application.update` must be in the response array). No action is required
  from the test beyond waiting for normal page load; call out only if a future flaky-visibility
  investigation needs it (e.g. a race between permissions fetch and the General section mount).
- No live LLM call is made in this case (the modal is opened and closed without submitting a
  prompt) — no `generate_application_draft` request to wait for or mock.

## Known Defects Found During Exploration
None found. (The case-text location drift documented above is a CLARIFICATION, not a defect — the
live product is correct; the case description is stale. Reverse-masking guard applies.)

## Blocked Steps

**Steps 4–6 (editor-role verification) are blocked — no live editor-role login path exists.**

- `.env.test` / `.agents/profile.md` § Roles & sample users define only `${TEST_USER}`
  (`TEST_USER_EMAIL`/`TEST_USER_PASSWORD`), which is admin-equivalent in every project it belongs
  to — live-confirmed via `GET /api/v2/auth/permissions/prompt_lib/{id}` for BOTH project `399`
  (Private, owner) and project `400` ("UI Testing" team project, where TEST_USER additionally holds
  `configuration.roles.roles.create/edit/delete` and `configuration.users.users.create/edit/delete`
  — project-admin there too, not a lesser role).
- Settings → Users on project `400` DOES list an `editor`-role row
  (`elitea-batch-edit-test2-45c8fb8d@example.com`) and a `viewer`-role row
  (`elitea-batch-edit-test2-70fda701@example.com`), but both are leftover pending-invite fixtures
  from an unrelated prior batch-edit-user-role test — `Last login: "-"`, never accepted, no known
  password. Not usable as a real login.
- Self-downgrading `${TEST_USER}`'s own role to editor via the Settings → Users "Edit user role"
  action was considered and rejected: project `400` is shared test data another merged suite relies
  on for a fixed 2-confirmed-user/role shape (`automation/pages/admin_users_page.py` module
  docstring, ELITEA-2292's precondition), and an editor role may lack
  `configuration.users.users.edit`, with no verified way to self-restore admin afterward. Mutating
  shared project-role state without a confirmed rollback is out of scope for an analyst pass.
- **What unblocks this:** either (a) a dedicated `EDITOR_TEST_USER_EMAIL`/`EDITOR_TEST_USER_PASSWORD`
  fixture — a real Keycloak account provisioned with a fixed editor role in a stable, non-shared
  project — added to `.env.test` + `.agents/profile.md` § Roles & sample users, or (b) an accepted
  substitute: an API-level check that an editor-role token's
  `GET /api/v2/auth/permissions/prompt_lib/{id}` response includes
  `models.applications.application.update` (proves the RBAC contract without a UI editor session,
  though it would not exercise the actual button-render path). This is a missing-fixture-primitive
  gap per `.agents/team-comms.md` § Escalation — recommend the orchestrator route it to whoever owns
  test-data provisioning rather than treating it as a per-case blocker only.
- **What is NOT blocked:** the case's core mechanism — RBAC-gated visibility of the Magic Wand
  button via `checkPermission(PERMISSIONS.applications.update)` — is fully verified for the
  admin-equivalent role, both via live UI observation (steps 1–3) and via source-code confirmation
  of the gating logic itself (`GenerateEntityButton.jsx`: `if (!checkPermission(permission)) return
  null;`). Automating steps 1–3 now is real, honest coverage of one authenticated point on this
  contract, not a stand-in for the whole case.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`), matches every neighboring
  `tests/ui/agents/test_agent_build_with_ai*.py` spec in this feature area.
- Page objects: `AgentsListPage` (`navigate()` + `create_agent_button`) and
  `GenerateAgentModalPage` (`open_button`, `modal`, `open_modal()`) — both already exist and need
  no new fields for this case.
- Suggested test module: a new file in `tests/ui/agents/` (e.g.
  `test_agent_build_with_ai_role_visibility.py`) rather than appending to
  `test_agent_build_with_ai.py` — that file's docstring scopes it to the generation-flow cases
  (ELITEA-1907/1909/1911/1915); this case's subject (RBAC-gated visibility) is a distinct concern
  even though it shares page objects.
- Wait strategy: no network wait is needed for the visibility assertion itself — `expect(...)
  .to_be_visible()` on `generate_agent_modal_page.open_button` after `AgentsListPage
  .navigate_to_create()` (or the click-based route) is sufficient; Playwright's own auto-wait
  covers the post-permissions-fetch render.
- If the lead/implementer decides to pursue the API-level editor-role substitute (§ Blocked Steps
  option b), that would live in `tests/api/`, not this UI module — a distinct test, not an
  extension of this one.
