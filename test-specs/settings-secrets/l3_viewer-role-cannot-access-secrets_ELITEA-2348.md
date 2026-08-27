# Test Case: Viewer role cannot access the Secrets section

## Metadata
- **TMS ID**: ELITEA-2348
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2348.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, DEV backend), projects 399 + 471
- **User set**: `${TEST_USER}` — **no second identity required** (see § The role vantage)
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-28
- **Status**: **ready-for-automation** — for the **Viewer half only**. The Monitor half
  (case steps 4-6) is **un-executable: Elitea has no Monitor role**. See
  § ⚠️ Case-text divergence — nothing is silently dropped.
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: **#1909** — `[CLARIFICATION][ELITEA-2348]` Elitea has no "Monitor" role.
  Comment added to **#1314** (the "no viewer credential" question card) recording that a
  viewer vantage does exist via project scoping.

## The role vantage (why this needs no new credential)

Elitea roles are **project-scoped**, and the shared `${TEST_USER}` already holds
different roles in different projects. Verified live 2026-08-28:

```
GET {ELITEA_API_BASE}/admin/users/prompt_lib/{project_id}   (roles of ${TEST_USER})
  399 Private              -> ['editor', 'viewer']      <- settings.elitea_project_id
  400 UI Testing           -> ['admin']                 <- settings.users_team_project_id
  406 Bugs & Features      -> ['viewer']
  25  Elitea Development   -> ['viewer']
  471 Elitea Testing Team  -> ['viewer']                <- settings.elitea_team_project_id
```

`useCheckPermission` reads `state.user.permissions`, refetched **per selected project**
(`GET /auth/permissions/prompt_lib/{id}`). Live counts: project 400 → 360 permissions,
8 of them `configuration.secrets.*`; project **471 → 158 permissions, ZERO containing
`secret`**. So selecting project 471 puts the app in a genuine viewer-role state — the
product computes it, the test does not fabricate it. **No substitution of any kind.**

## ⚠️ Case-text divergence — the Monitor role does not exist

Case steps 4-6 ask to log in as a **Monitor** and repeat the check. Verified live:

```
GET {ELITEA_API_BASE}/admin/roles/default/{project_id}
  399 -> ['admin', 'editor', 'viewer']    406 -> ['admin', 'editor', 'viewer']
  400 -> ['admin', 'editor', 'viewer']    25  -> ['admin', 'editor', 'viewer']
  471 -> ['admin', 'editor', 'viewer']
grep -rni "'monitor'|\"monitor\"" ../EliteaUI/src/   -> 0 hits
```

There is **no observable to assert** — this is not a tooling or credential gap, the
subject of steps 4-6 is absent from the product. Per `.agents/testing.md`
§ Fidelity policy and the implementation skill's reverse-masking guard, the live product
is ground truth and the case text is the hypothesis: the spec asserts the **Viewer**
contract and the drift is **filed** (#1909) rather than papered over. Steps 4-6 are
dispositioned `un-executable` in the Coverage Map below — visible, not dropped.

## Preconditions
- User logged in (`auth_state` — localhost bypass via `VITE_DEV_TOKEN`).
- `settings.elitea_project_id` (399) — user holds `secrets.list`. **Control** vantage.
- `settings.elitea_team_project_id` (471) — user's only role is `viewer`, no secrets
  permissions. **Subject** vantage.
- **Read-only case.** Nothing is created, edited or deleted; only the project selector moves.

## Test Data
### reuse-existing
- The two project ids above, both already in `automation/config.py` — no new env keys.
- No secret data is read; the case is about section *availability*.

## Test Steps (all executed live 2026-08-28, framework run)

1. **Establish the control vantage** — load `/settings/project-general` on project 399
   (a project where the user DOES hold `configuration.secrets.secret.list`).
   - **Verify**: `settings-nav-item-secrets` is **visible**.
   - *Live:* nav items rendered = `project-general, ai-providers, project-context,
     secrets, analytics, usage, profile, preferences, ai-personality, memory, tokens,
     notifications` — `secrets` **present**.
   - **Why this step exists (Axis 2):** without it, the step-2 absence assertion is
     vacuous — it would also pass if the whole drawer failed to render. This proves the
     absence is *caused by the role*, not by a broken page.

2. **Switch to the viewer-role project** (471) via the sidebar project selector
   (`BasePage.switch_project`), then verify the Secrets section is not offered.
   - **Verify**: `settings-nav-item-secrets` has **count 0** (canon #511 extension —
     an absence assertion on a testid IS a reference).
   - **Verify**: the drawer is still healthy — `settings-drawer-menu` visible and the
     rendered nav-item list is **non-empty** and still contains `project-general`.
   - *Live:* nav items = `project-general, ai-providers, project-context, users,
     analytics, usage, profile, preferences, ai-personality, memory, tokens,
     notifications` — `secrets` **absent**, 12 items still rendered.

3. **Re-verify on a fresh load** of `/settings/project-general` while project 471 stays
   selected — proves the hiding survives a full remount, not just an in-session
   permission refetch.
   - **Verify**: `settings-nav-item-secrets` count 0; drawer still healthy.
   - *Live:* identical nav list, `secrets` absent.

4. **Restore the control project** (399) and re-assert `settings-nav-item-secrets` is
   visible again — proves the test left no residual state and that the difference is
   reversible and role-driven.
   - *Live:* `secrets` present again.

### Steps NOT automated, and why

| Case step | Disposition |
|---|---|
| 1 — "Log in as a user with Viewer role" | **satisfied differently, honestly**: role is project-scoped, so selecting project 471 IS acting as a Viewer. No separate login exists to perform (localhost auth is a dev-token bypass). |
| 4-6 — Monitor role | **un-executable — the product has no Monitor role** (#1909). |

## Deliberately NOT asserted (and why)

- **The deep-linked `/settings/secrets` route on the viewer project.** Verified live:
  it still renders `secrets-page-title` + an **enabled** `secrets-add-button` +
  `No secrets`, shows **no** "Access Denied", and fires **zero** secrets requests. That
  is bug **#1773**, already filed. The case's step 3 is an explicit **OR** — *"not
  visible in the sidebar **OR** shows an Access Denied error"* — and the sidebar branch
  is the one the product actually satisfies. Asserting the deep-link branch would make
  this spec a duplicate red for #1773 rather than coverage of ELITEA-2348.
- **Console errors on the Secrets page.** The spec never lands on `/settings/secrets`,
  so #1203 is out of its path entirely. Do **not** add a console-error axis that visits
  that route on project 471 — measured **144** `Maximum update depth exceeded` errors
  there this session (#1203's unbounded variant).

## Handles Reference
| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Settings drawer menu | `settings-drawer-menu` | **on-main ✓** | `SettingsDrawerPage.settings_drawer_menu` |
| Secrets nav item | `settings-nav-item-secrets` | **on-main ✓** | via existing `SETTINGS_NAV_ITEM` class template; asserted **present** (399) and **count 0** (471) |
| General nav item | `settings-nav-item-project-general` | **on-main ✓** | drawer-health control |
| All nav items in menu | `SETTINGS_NAV_ITEMS_IN_MENU` class constant | **on-main ✓** | `[data-testid="settings-drawer-menu"] [data-testid^="settings-nav-item-"]`; `nav_item_ids_in_order()` |
| Project selector trigger | `project-selector-trigger-combobox` | **on-main ✓** | `BasePage.project_selector_trigger` |
| Project option | `select-option-{id}` | **on-main ✓** | `BasePage.SELECT_OPTION` template |

*(Provenance verified with `cd ../EliteaUI && git fetch origin` in the same command block, 2026-08-28.)*

**No new testid is needed for this case.** Every handle already exists and is already
wired into `SettingsDrawerPage` / `BasePage`.

## Implementer notes
- Reuse `SettingsDrawerPage.nav_item()` / `nav_item_ids_in_order()` and
  `BasePage.switch_project()` — no new page-object primitive is required. Any addition
  must be **additive** (`SettingsDrawerPage` has many merged callers).
- **Restore project 399 in a `finally`** — the project selection is persisted app state
  shared with every other spec in the suite. Leaving the session on 471 would break
  unrelated tests.
- Use `expect(...).to_have_count(0)` for the absence (auto-retrying), not a bare
  `.count() == 0` read, so a slow permission refetch cannot produce a false green.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: log in as a user with Viewer role | user acts under the `viewer` role in project 471 (roles are project-scoped) | Step 2 | `switch_project(471)` + the permission set the product refetches | **asserted** (satisfied by project scoping, not a second login) |
| Step 2: navigate to Settings → Secrets | Settings drawer loads on the viewer project | Steps 2-3 | `settings-drawer-menu` visible, nav list non-empty | **asserted** |
| Step 3: section is not visible in the sidebar **OR** shows "Access Denied" | the **sidebar** branch holds — `settings-nav-item-secrets` is not rendered | Steps 2-3 | `to_have_count(0)` on `settings-nav-item-secrets` | **asserted** (OR-branch 1; branch 2 is #1773 — see § Deliberately NOT asserted) |
| Step 4: log out, log in as Monitor role | — | — | — | **un-executable — Elitea has no Monitor role** (#1909) |
| Step 5: repeat steps 2-3 as Monitor | — | — | — | **un-executable** (#1909) |
| Step 6: verify Monitor is also blocked | — | — | — | **un-executable** (#1909) |
| Expected Final State: Monitor also blocked | — | — | — | **un-executable** (#1909) |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| Step 1 control — `settings-nav-item-secrets` **visible** on project 399 | makes the step-3 absence assertion non-vacuous: without it the test would also pass if the drawer never rendered at all |
| Drawer health during the absence check (menu visible, nav list non-empty, `project-general` present) | distinguishes "Secrets is hidden by permission" from "the drawer is broken" — the exact failure a naive absence assertion masks |
| Step 4 restore — Secrets reappears on project 399 | proves the difference is role-driven and reversible, and that the spec leaves no residual project state for the rest of the suite |

## Known Defects / Clarifications
- **#1909 (question/clarification, filed this session)** — Elitea has no `Monitor` role;
  case steps 4-6 name a subject the product does not have. Decision needed: amend the
  case, substitute `editor`, or confirm Monitor is planned.
- **#1773 (bug, OPEN)** — deep-linking `/settings/secrets` on a no-permission project
  renders the normal page with an enabled "+" instead of an access-denied state. Out of
  this spec's path by design.
- **#1203 (bug, OPEN)** — `Maximum update depth exceeded` on the Secrets page mount,
  **unbounded** on a no-permission project. Out of this spec's path by design.
- **#1314 (question, OPEN)** — "no editor/viewer test-user credential". Partially
  superseded by this case's finding (commented there): a viewer vantage exists via
  project scoping. Still blocking: two roles simultaneously, or an admin-vs-viewer
  contrast on the *same* project.

## Blocked Steps
- None for the Viewer half. Steps 4-6 are **un-executable**, not blocked — there is no
  work that would unblock them short of the product gaining a Monitor role (#1909).
