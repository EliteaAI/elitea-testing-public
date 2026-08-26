# Test Case: Build with AI — Magic Wand button visible for admin and editor roles on the New Skill creation screen

## Metadata
- **TMS ID**: ELITEA-1986
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (admin-equivalent in every project it belongs to — see § Blocked Steps)
- **Analyst**: qa-engineer (analyst slot, batch skills-remaining-w5)
- **Status**: ready-for-automation
  (admin-role half fully explored and automatable end-to-end; editor-role half is the same
  missing-test-data-fixture gap already tracked for the Agents analog of this case
  (`EliteaAI/elitea-testing-public#1314`, opened for ELITEA-1903/ELITEA-1904) — see § Blocked Steps.
  Per the skill's contract, `blocked` is reserved for when the analyst cannot complete meaningful
  automation at all; here the case's core RBAC-gating mechanism is fully proven for one role and the
  gap for the other is scoped, documented, and already tracked — not silently skipped.)

## Preconditions
- `${TEST_USER}` is authenticated via the `auth_state` fixture (localhost `VITE_DEV_TOKEN` bypass —
  no Keycloak login form on localhost).
- Acting project: `${ELITEA_PROJECT_ID}` (Private, id `399`) — `${TEST_USER}`'s own private project,
  confirmed live to carry the `models.applications.application.update` permission (same permission
  gate as every other `generate-*-open-button`; see Concrete Handles / Network Behavior).
- The Skills page (`/skills/all`) and New Skill creation screen (`/skills/create`) are reachable —
  confirmed live.

## Test Data
### reuse-existing
- `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` — admin-equivalent (owner) in the default private
  project; used for the admin-role half.
- `${ELITEA_PROJECT_ID}` = `399` (Private) — where the admin-role half runs.

### missing (blocks the editor-role half — see § Blocked Steps)
- No `EDITOR_TEST_USER_EMAIL` / `EDITOR_TEST_USER_PASSWORD` (or equivalent) exists in `.env.test` or
  `.agents/profile.md` § Roles & sample users. Re-confirmed this run: `grep -iE "viewer|editor|role"`
  over `automation/.env.test` and `.agents/profile.md` returns nothing beyond the field-name headers
  themselves — no credential pair.

## Test Steps

1. Authenticate as `${TEST_USER}` via `auth_state` (admin-equivalent role).
   - **Verify**: dashboard/app shell loads (`Elitea is connected` status, side-bar visible).
2. Navigate to Skills (`/skills/all`) and click the sidebar "+ Skill" create button.
   - **Verify**: `/skills/create` loads; the "New Skill" tab is selected in the page-level tab bar;
     the Name field is present (page ready) — confirmed live via `navigate_to_create()`'s deep-link
     equivalent (same destination the click-based route reaches; see Concrete Handles).
3. Verify the "Build with AI" / Magic Wand button is visible on the New Skill creation screen.
   - **Verify**: `generate-skill-open-button` is visible, has accessible text "Build with AI", and
     is clickable — confirmed live via `page.evaluate` DOM inspection (`data-testid`, `textContent`,
     computed visibility all returned as expected).
4. *(Editor role — blocked, no live login path. See § Blocked Steps.)*
5. *(Editor role — blocked.)*
6. *(Editor role — blocked.)*

## Expected Results
- Step 3: the Magic Wand button is present, visible, and functional for the admin-equivalent
  `${TEST_USER}` on the New Skill creation screen — **live-confirmed** this run.
- Steps 4–6 (editor role): expected, per the source-code RBAC gate
  (`GenerateSkillButton.jsx` → `permission={PERMISSIONS.applications.update}` →
  `GenerateEntityButton.jsx`'s `if (!checkPermission(permission)) return null;`), that an
  editor-role user ALSO sees the button — editor is conventionally granted
  `applications.update` in role-based systems of this shape, and this is the identical gate/
  permission the Agents analog (ELITEA-1903) proved live for admin — but this is **not verified
  live** in this AFS for the editor role; it is an inference from code reading, not an executed
  observation. Flagged explicitly so it is never reported as asserted.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as admin role | dashboard displayed | step 1 | `step 1`: side-bar + connected status visible | asserted |
| 2 Navigate to Skills, click "+ Skill" | New Skill creation screen opens | step 2 | `step 2`: URL `/skills/create` + tabpanel "New Skill" + Name field visible | asserted |
| 3 Verify Build with AI button visible (admin) | button displayed on creation screen | step 3 | `step 3`: `generate-skill-open-button` visible, text "Build with AI" | asserted |
| 4 Log out, log in as editor role | editor logged in | — | — | blocked *(no editor credential exists — § Blocked Steps, tracked in #1314)* |
| 5 Navigate to Skills, click "+ Skill" (editor) | creation page opens | — | — | blocked *(depends on step 4)* |
| 6 Verify Build with AI button visible for editor | button displayed for editor | — | — | blocked *(depends on step 4)* |

**Axis 2 — Analyst additions:**
- Step 3 also asserts the button's accessible name is exactly "Build with AI" (not just "some
  button exists") — *added: without a name/testid pairing check, a regression that renamed the
  wrong button to overlap the wand's position would slip through a bare visibility check.* Reuses
  the existing pattern from the Agents analog (ELITEA-1903) and the skills-suite's own
  `GenerateSkillModalPage.open_button`.
- Confirmed zero console errors on the creation screen both before and after the permissions
  fetch resolves — *added: side-channel check, not itself required by the case's Pass criteria,
  but standard practice per this skill's methodology.*

## Cleanup
- None — no skill is created (this case only verifies button visibility; the creation form itself
  is never submitted).

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Locator (testid-only) | PROVENANCE | Fallback |
|---|---|---|---|
| Sidebar "+ Skill" create button | `LocatorDescriptor(testid="sidebar-create-button")` — same shared sidebar testid family as Agents/Chat/Credentials/Pipelines (confirmed live via `page.evaluate` on `/skills/all`: text "Skill", `data-testid="sidebar-create-button"`); not currently a dedicated field on `SkillsListPage` (which instead exposes `navigate_to_create()` as a direct deep-link — see next row) | needs-adding-if-used *(only if the implementer specifically wants the literal click-path over the existing deep-link method; the deep-link is the suite's established, accepted pattern for this exact flow — see ELITEA-1988's AFS)* | none (testid-only) |
| New Skill creation screen reached | `SkillsListPage.navigate_to_create()` deep-links `/skills/create` directly — **existing page-object method**, already the pattern all three merged `test_skill_build_with_ai.py` tests use (ELITEA-1988/1989/1990/2001/1991 lineage); this AFS specs the literal case-step path (click) but recommends the implementer reuse the existing method for consistency, exactly as ELITEA-1903's Agents analog did | n/a (method, not a locator) | — |
| "New Skill" tab (tab bar) | confirmed live present (`tab "New Skill" [selected]`) but not the AFS's primary target; implementer should assert page-readiness the same way the existing skills suite does — via the Name field / tabpanel being visible — rather than a raw tab-bar handle | needs-adding *(only if a future case specifically needs to assert the tab itself)* | — |
| Magic Wand / "Build with AI" open button | `LocatorDescriptor(testid="generate-skill-open-button")` — **existing field**, `generate_skill_modal_page.py` `open_button` (same class used by ELITEA-1988/1989/1990/1991/2001/1993) | on-main: unknown (not independently re-verified this run — see caveat below) · on-`automation/testids`: ✓ (confirmed live this run — button rendered with `data-testid="generate-skill-open-button"`, text "Build with AI", on the live dev server which runs `automation/testids`) | none — testid-only, already wired |

**Provenance caveat:** this run confirmed the testid live against the running dev server
(`automation/testids`) via DOM inspection, not via a fresh `git grep` against `origin/main` — the
closure-record verification (fetch + grep both refs) is the orchestrator's job at merge time per
`.agents/workflow.md` § Closure record, not re-derived here. ELITEA-1988's AFS (same button, same
feature area, analysed more recently in this same batch lineage) already establishes this testid
is live and stable on `automation/testids`.

No new testid work is required for this case — every handle it touches already exists as a
page-object field.

## Network Behavior
- Project switch / login triggers `GET /api/v2/auth/permissions/prompt_lib/{project_id}` — this is
  the authoritative source for whether `generate-skill-open-button` renders at all
  (`models.applications.application.update` must be in the response array — same permission gate
  as the Agents "Build with AI" button, confirmed via source: `GenerateSkillButton.jsx` passes
  `permission={PERMISSIONS.applications.update}` into the shared `GenerateEntityButton.jsx`). No
  action is required from the test beyond waiting for normal page load.
- No live LLM call is made in this case (the button's presence is checked; the modal is never
  opened or submitted) — no `generate_skill_draft` request to wait for or mock.

## Known Defects Found During Exploration
None found. Live product behavior matches the case's Pass criteria exactly for the admin-equivalent
role.

## Blocked Steps

**Steps 4–6 (editor-role verification) are blocked — no live editor-role login path exists.**

- Same missing-test-data-fixture gap already tracked in
  `EliteaAI/elitea-testing-public#1314` ("No editor/viewer test-user credential — blocks
  RBAC-role-differentiated cases (ELITEA-1903, ELITEA-1904)"), re-confirmed still open and still
  applicable this run: `.env.test` / `.agents/profile.md` § Roles & sample users define only
  `${TEST_USER}` (admin-equivalent in every project it belongs to). No
  `EDITOR_TEST_USER_EMAIL`/`EDITOR_TEST_USER_PASSWORD` pair exists, and no Keycloak-admin or
  backend-admin credential exists to provision one out-of-band.
- The mechanism being tested is byte-for-byte identical to the Agents "Build with AI" button
  (`GenerateEntityButton.jsx`'s `checkPermission(PERMISSIONS.applications.update)` gate, shared
  between `GenerateAgentButton.jsx` and `GenerateSkillButton.jsx`) — so this is the exact same
  fixture gap recurring on a second entity type, not a new distinct blocker requiring a fresh
  ticket. Per `.agents/profile.md` § Bug filing dedup discipline (consolidate evidence rather than
  split), the recurrence is being noted on the existing #1314 rather than filed as a new issue —
  see the analyst's Run Report / findings for the actual comment.
- **What unblocks this:** the same fix as #1314 already names — either (a) a dedicated
  `EDITOR_TEST_USER_EMAIL`/`EDITOR_TEST_USER_PASSWORD` fixture (real Keycloak account, fixed editor
  role, stable non-shared project) added to `.env.test` + `.agents/profile.md` § Roles & sample
  users, or (b) an accepted API-level substitute: an editor token's
  `GET /api/v2/auth/permissions/prompt_lib/{id}` response containing
  `models.applications.application.update` (structural proof, no UI session needed — but does not
  exercise the actual button-render path).
- **What is NOT blocked:** the case's core mechanism — RBAC-gated visibility of the Magic Wand
  button via `checkPermission(PERMISSIONS.applications.update)` — is fully verified for the
  admin-equivalent role, both via live UI observation (steps 1–3) and via source-code confirmation
  of the gating logic (`GenerateEntityButton.jsx`). Automating steps 1–3 now is real, honest
  coverage of one authenticated point on this contract.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`), matches every neighboring
  `tests/ui/skills/test_skill_build_with_ai*.py` spec in this feature area.
- Page objects: `SkillsListPage` (`navigate()` + `navigate_to_create()`) and
  `GenerateSkillModalPage` (`open_button`) — both already exist and need no new fields for this
  case.
- Suggested test module: a new file in `tests/ui/skills/` (e.g.
  `test_skill_build_with_ai_role_visibility.py`) rather than appending to
  `test_skill_build_with_ai.py` — that file's docstring scopes it to the generation-flow cases
  (ELITEA-1988/1989/1990/1991/1993/2001); this case's subject (RBAC-gated visibility) is a
  distinct concern even though it shares page objects. Mirrors the exact recommendation the Agents
  analog (ELITEA-1903) made for `tests/ui/agents/test_agent_build_with_ai_role_visibility.py` — if
  that file exists by the time this case is implemented, prefer keeping the pattern parallel
  (same module-naming convention across feature areas) but do not import across `tests/ui/agents/`
  and `tests/ui/skills/`; each surface owns its own test module.
- Wait strategy: no network wait is needed for the visibility assertion itself —
  `expect(generate_skill_modal_page.open_button).to_be_visible()` after
  `skills_list_page.navigate_to_create()` is sufficient; Playwright's own auto-wait covers the
  post-permissions-fetch render.
- If the lead/implementer decides to pursue the API-level editor-role substitute (§ Blocked Steps
  option b), that would live in `tests/api/`, not this UI module — a distinct test, not an
  extension of this one. It would also directly cover the identical Agents-side gap (#1314), so
  coordinate rather than duplicate if both cases reach implementation in the same batch.
