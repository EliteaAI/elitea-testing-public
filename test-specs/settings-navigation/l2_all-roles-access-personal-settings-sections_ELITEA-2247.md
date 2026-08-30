# Test Case: All authenticated roles can access PERSONAL settings sections

## Metadata
- **TMS ID**: ELITEA-2247
- **Linked Story**: none
- **Priority**: l2 (case frontmatter `priority: high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (`testbot@elitea.ai`) across **three real role
  vantages** — `admin` @ project 400, `editor`+`viewer` @ project 399,
  `viewer` @ project 471 (see § Roles are project-scoped)
- **Analyst**: qa-engineer (Sage), batch `settings-w12`, 2026-08-30
- **Status**: ready-for-automation (**case-text drift on the role list and one
  section name — asserts the LIVE contract**)
- **Surface digest**: `test-specs/settings-navigation/_surface.md`
- **Filed**: nothing new. The non-existent "Monitor" role is already the OPEN
  clarification **EliteaAI/elitea-testing-public#1909**; the
  "Personalization" → **Preferences** rename is already the OPEN clarification
  **EliteaAI/elitea-testing-public#1772**. New occurrences commented there, not
  re-filed (`.agents/profile.md` § Bug filing).
- **Cluster**: dispatched with ELITEA-2245 and ELITEA-2246 (one live session);
  the three differ in **steps**, so each has its own AFS.
- **surface_key**: `settings-drawer-role-access`

---

## Roles are project-scoped — the vantages are real, nothing is substituted

Verified live 2026-08-30 (`GET /api/v2/admin/users/prompt_lib/{pid}`,
`GET /api/v2/auth/permissions/prompt_lib/{pid}`, Bearer `ELITEA_API_TOKEN`):

| Vantage | Project | id | Role held by `testbot@elitea.ai` | Permissions |
|---|---|---|---|---|
| **admin** | UI Testing | **400** | `admin` | 360 |
| **editor** (+viewer) | Private (personal project) | **399** | `editor`, `viewer` | 299 |
| **viewer** | Elitea Testing Team | **471** | `viewer` | 158 |

Switching the sidebar project selector re-fetches `state.user.permissions` per
project, so each switch puts the app in a genuinely different, product-computed
role state. No injected state, no fabricated permission payload, no stubbed client
(`.agents/testing.md` § Fidelity policy).

---

## ⚠️ Case-text drift — read this before implementing

| Case text | Live product (verified 2026-08-30) |
|---|---|
| "all four roles" — Admin, Editor, Viewer, **Monitor** (steps 1-4) | **Elitea has exactly THREE roles**: `GET /api/v2/admin/roles/default/{pid}` returns `['admin','editor','viewer']` for **every** project checked (399, 400, 471, 406, 25) — there is no `Monitor`. Clarification #1909. |
| PERSONAL = "Personalization, Personal Tokens, Notifications" | PERSONAL = **Profile, Preferences, AI Personality, Memory, Personal Tokens, Notifications** (6 items). **"Personalization" is now "Preferences"**. Clarification #1772. |

**The Monitor step is `un-executable`, not skipped.** There is no such role to log in
as, so there is no observable to assert — this is a subject the product does not
have, not a masked assertion (same disposition ELITEA-2348's merged spec already
took for its own Monitor half). The spec covers the **three roles that exist**, and
the docstring must say so with the #1909 pointer.

---

## Preconditions
- User logged in (`auth_state`; login skipped on localhost via `VITE_DEV_TOKEN`).
- The spec moves the active project three times and **must restore** it to
  `settings.elitea_project_id` (399) in a `finally` — shared app state, `#1082`
  pollution class (`.agents/testing.md` § Teardown-guard ordering).

## Test Data
### reuse-existing
None created, edited or deleted. Pure read-only navigation across three vantages.
The three PERSONAL sections under test are **user-scoped**, so nothing project-level
is touched.

---

## Test Steps

Parameterized over the three role vantages (one pytest param each, so a failure names
the role):

| Param id | Project id source | Role in that project |
|---|---|---|
| `admin` | `settings.elitea_admin_project_id` (400) | `admin` |
| `editor` | `settings.elitea_project_id` (399) | `editor` + `viewer` |
| `viewer` | `settings.elitea_team_project_id` (471) | `viewer` |

For each vantage:

1. **Switch to the vantage's project and open Settings.**
   - `switch_project(project_id)`, then `navigate("/settings/project-general")`.
   - **Verify**: `settings-drawer-menu` is visible and `nav_item_ids_in_order()`
     returns more than one id (drawer-health guard — otherwise every later read is
     vacuous).
   - **Verify (the role vantage really changed)**: assert a role-discriminating
     observable so the parameterization cannot silently run three identical passes —
     `settings-nav-item-secrets` is **visible** on 400 and 399 and has
     **count 0** on 471 (measured live: `secrets` perms 8 / 6 / 0). This is the same
     product signal ELITEA-2348's merged spec asserts, reused here purely as a
     vantage guard.

2. **Verify the three PERSONAL sections named by the case are offered.**
   - **Verify**: `settings-nav-item-preferences` (the case's "Personalization"),
     `settings-nav-item-tokens` ("Personal Tokens") and
     `settings-nav-item-notifications` ("Notifications") are all visible, under the
     `settings-section-header-personal` group.

3. **Click each of the three and verify it loads without a permission error.**
   Via `click_nav_item(tab_id)` for `preferences`, `tokens`, `notifications`:
   - **Verify**: URL is `/settings/{tab_id}`.
   - **Verify**: the nav item carries `data-active="true"`.
   - **Verify**: `settings-content` is visible and its trimmed text is non-empty,
     and contains the section's own heading — live-observed headings:
     `Preferences`, `Personal Tokens`, `Notifications Center`.
   - **Verify (no permission error)**: `settings-content` text does **not** match
     `/access denied|forbidden|403|not authorized|no permission/i`, **and** no
     `/api/v2/` response with status 403 was observed while the section loaded.
   - **Verify**: zero console errors for that section
     (`utils.console_errors.collect_console_errors(page)`, strict zero — none of the
     three routes visits `ai-personality`/#1771 or the Secrets page/#1203/#1773).
     Measured live: **zero** on all three sections in all three vantages.

4. **Restore the active project (teardown).**
   - `finally:` `switch_project(settings.elitea_project_id)` — unconditional,
     exceptions logged not raised (copy `restore_active_project`'s shape from
     `automation/tests/ui/admin/test_viewer_role_cannot_access_secrets.py`).

---

## Expected Results
- In each of the three real role vantages, Preferences / Personal Tokens /
  Notifications are all offered in the PERSONAL group, all load their own route with
  non-empty content, and none shows an access-denied state or produces a 403.
- Zero console errors throughout.
- The Monitor vantage is not exercised — the role does not exist (#1909).
- The active project is restored to 399.

---

## Handles Reference (testid-only)

PROVENANCE verified with `cd ../EliteaUI && git fetch origin` on 2026-08-30.

| Element | Testid | On `main`? | On `automation/testids`? |
|---|---|---|---|
| Drawer menu container | `settings-drawer-menu` | no | **YES** |
| PERSONAL group header | `settings-section-header-personal` | no | **YES** |
| Nav item (dynamic) | `settings-nav-item-{tabId}` + `data-active` | no | **YES** |
| Content pane | `settings-content` | no | **YES** |
| Project selector trigger | `project-selector-trigger` (+ `-combobox`) | YES | YES |
| Project option (dynamic) | `select-option-{projectId}` | YES | YES |
| Preferences section header | `preferences-general-section-header` | no | **YES** |
| Personal Tokens add | `personal-tokens-add-button` | YES | YES |
| Notifications search | `notifications-search-input` | no | **YES** |

**No new testid is required.** The last three rows are optional content-anchors if
the implementer prefers a testid over the heading text for step 3's "the right page
rendered" check — all three are already live on `automation/testids`.

Page objects to reuse: `SettingsDrawerPage` (`automation/pages/settings_drawer_page.py`)
for the drawer + `switch_project`; `personal_tokens_page.py` /
`notification_center_page.py` / `settings_personalization_page.py` already exist for
the three destinations — do not re-declare their locators on the drawer.

---

## Automation Hints
- **New config key** (shared with ELITEA-2245): `settings.elitea_admin_project_id`
  (default `400`) in `automation/config.py` + `.env.test`. If ELITEA-2245 lands
  first, reuse it.
- `@pytest.mark.parametrize` over the three vantages with readable ids
  (`admin` / `editor` / `viewer`) so a failure names the role.
- Markers: `ui`, `settings`, `p2`, `regression`.
- Every step wrapped in `with allure.step("Step N — …")`.
- No sleeps: `click_nav_item()` waits on `data-active="true"`; the project switch is
  confirmed by the selected-option checkmark / a re-render, **never** by
  `wait_for_network()` (`networkidle` races the persistent `/socket.io/` poll —
  issue #1847).

## Known traps
- **Do not assert the full PERSONAL inventory here** — that is ELITEA-2242's spec
  (`test_settings_page_sections_and_default_tab.py`). This case's subject is
  *access across roles*, so assert only the three sections the case names, plus the
  vantage guard.
- **The vantage guard is load-bearing.** Without step 1's Secrets presence/absence
  check, a project switch that silently failed would let all three params pass
  identically and the test would prove nothing about roles.
- **Restore the project.** A spec that leaves the session on 400 or 471 poisons every
  later spec in the invocation.
- Personal settings are **user-scoped**: all three vantages are the same human, so
  this case proves "no project role gates the personal sections", which is exactly
  what it claims — do not oversell it as multi-identity coverage.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition — user is logged in | — | `auth_state` fixture | fixture | asserted (setup) |
| Step 1 — Admin role: Personalization, Personal Tokens, Notifications each load without error | authenticated, loads | param `admin` (project 400), steps 1-3 | steps 1-3 | asserted ("Personalization" → **Preferences**, drift #1772) |
| Step 2 — repeat for Editor role | completes without error | param `editor` (project 399, role `editor`+`viewer`) | steps 1-3 | asserted |
| Step 3 — repeat for Viewer role | completes without error | param `viewer` (project 471) | steps 1-3 | asserted |
| Step 4 — repeat for Monitor role | completes without error | — | — | **un-executable** — Elitea has no Monitor role (`admin/editor/viewer` only, verified across 5 projects). Clarification #1909; see § Case-text drift |
| Step 5 — all four roles access all three PERSONAL sections without permission error | condition holds | steps 1-3 for the **three roles that exist** | step 3 (denial regex + no-403 + zero console errors) | asserted for 3 of the 4 named roles; the 4th is un-executable, not skipped |
| Expected final state | — | step 3 | step 3 | asserted (scoped to existing roles) |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why (grounded) |
|---|---|
| Vantage guard — `secrets` nav present on 400/399, count 0 on 471 | Turns the parameterization into a proof that the role vantage actually changed; without it three identical passes are indistinguishable from a failed project switch. Grounded in live permission counts (8 / 6 / 0) |
| Drawer-health guard before any read | A failed drawer render would make the presence assertions vacuous |
| `data-active="true"` on each clicked item | The product's own selection signal — catches a click that navigated without selecting |
| Transport-level "no 403" alongside the text-level denial regex | The case says "without any permission error"; on this product a permission failure can surface as a 403 with **no** access-denied UI at all (that is exactly bug #1773 on the Secrets route), so a text-only check can pass over a real denial |
| Zero console errors | `.agents/testing.md`; measured zero on all 9 (3 roles × 3 sections) loads |
| Active-project restore in `finally` | `#1082` shared-state pollution class |

## Blocked Steps
None. (Step 4's Monitor role is *un-executable*, not blocked — no environment change
or access grant could unblock it; the role does not exist in the product.)

## Known Defects (observed, not caused by this case)
- None on the three PERSONAL sections in any vantage — zero console errors, zero
  4xx/5xx across all nine loads (verified live 2026-08-30).
